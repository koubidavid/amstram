"""Scraping API — one button does everything."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.deps import get_db
from app.models.scraping_job import JobStatut, JobType, ScrapingJob
from app.schemas.scraping_job import ScrapingJobList, ScrapingJobRead

router = APIRouter(prefix="/api/scraping", tags=["scraping"])


PIPELINE_STEPS = [
    {"key": "collect",   "label": "Collecte des agences (API INSEE)",    "estimate_min": 3},
    {"key": "rnic",      "label": "Enrichissement RNIC (lots gérés)",    "estimate_min": 1},
    {"key": "pappers",   "label": "Enrichissement Pappers (CA, dirigeants)", "estimate_min": 2},
    {"key": "jobs",      "label": "Détection offres d'emploi (DuckDuckGo + sites)", "estimate_min": 3},
    {"key": "insights",  "label": "Calcul des scores et insights",      "estimate_min": 0.5},
]

# Keep activity logs in memory (JSON column has size limits)
_activity_logs: list[dict] = []
MAX_LOGS = 40


def _log_activity(db, job_id: str, step_index: int, message: str, icon: str = "info",
                  count: int | None = None):
    """Push an activity entry and update progression."""
    global _activity_logs

    now = datetime.now(timezone.utc).strftime("%H:%M:%S")
    entry = {"time": now, "step": step_index + 1, "msg": message, "icon": icon}
    if count is not None:
        entry["count"] = count
    _activity_logs.append(entry)
    if len(_activity_logs) > MAX_LOGS:
        _activity_logs = _activity_logs[-MAX_LOGS:]

    job = db.get(ScrapingJob, uuid.UUID(job_id))
    if not job:
        return

    total_steps = len(PIPELINE_STEPS)
    current = PIPELINE_STEPS[step_index]
    remaining_min = sum(s["estimate_min"] for s in PIPELINE_STEPS[step_index:])

    job.progression = {
        "step": step_index + 1,
        "total_steps": total_steps,
        "step_key": current["key"],
        "step_label": current["label"],
        "detail": message,
        "percent": round((step_index / total_steps) * 100),
        "eta_minutes": round(remaining_min, 1),
        "eta_display": f"~{int(remaining_min)} min" if remaining_min >= 1 else "< 1 min",
        "logs": list(_activity_logs),
    }
    db.commit()


def _run_full_pipeline(job_id: str):
    """Run the complete pipeline: collect + RNIC + Pappers + jobs + insights."""
    import logging
    logger = logging.getLogger(__name__)
    global _activity_logs
    _activity_logs = []

    from app.services.scraping_service import _step_collect, _step_enrich_rnic, _step_enrich_pappers, _step_generate_insights
    from app.services.job_scraper import scan_agency_jobs
    from app.models.insight import Insight
    from app.models.agence import Agence

    db = SessionLocal()
    try:
        logger.warning(f"[Pipeline] Starting job {job_id}")

        # Mark as running immediately
        job = db.get(ScrapingJob, uuid.UUID(job_id))
        if job:
            job.statut = JobStatut.running
            job.started_at = datetime.now(timezone.utc)
            db.commit()

        # ── Step 1: Collect from API ──
        _log_activity(db, job_id, 0, "Connexion à l'API recherche-entreprises.gouv.fr...", "search")

        errors = []
        new, updated = _step_collect_with_logs(db, errors, job_id)
        nb = db.query(Agence).count()

        _log_activity(db, job_id, 0,
                      f"Collecte terminée : {new} nouvelles + {updated} mises à jour = {nb} agences en base",
                      "success", count=nb)
        logger.warning(f"[Pipeline] Step 1 done: {nb} agences")

        # ── Step 2: Enrich with RNIC ──
        _log_activity(db, job_id, 1, f"Lecture du fichier RNIC (Registre National des Copropriétés)...", "database")
        rnic_matched = _step_enrich_rnic(db, errors)
        if rnic_matched > 0:
            _log_activity(db, job_id, 1,
                          f"{rnic_matched} agences enrichies avec données RNIC (nb lots, copropriétés, arrêtés de péril)",
                          "success", count=rnic_matched)
        else:
            _log_activity(db, job_id, 1, "Fichier RNIC non disponible sur ce serveur — étape ignorée", "warning")
        logger.warning(f"[Pipeline] Step 2 done: RNIC matched={rnic_matched}")

        # ── Step 3: Enrich with Pappers ──
        _log_activity(db, job_id, 2, "Requêtes API Pappers pour dirigeants et chiffre d'affaires...", "building")
        pappers_matched = _step_enrich_pappers(db, errors)
        if pappers_matched > 0:
            _log_activity(db, job_id, 2,
                          f"{pappers_matched} agences enrichies (dirigeant, CA, date de création)",
                          "success", count=pappers_matched)
        else:
            _log_activity(db, job_id, 2, "Clé API Pappers non configurée — étape ignorée", "warning")
        logger.warning(f"[Pipeline] Step 3 done: Pappers matched={pappers_matched}")

        # ── Step 4: Scan for job postings ──
        _log_activity(db, job_id, 3, "Scan des offres d'emploi via DuckDuckGo et sites agences...", "briefcase")
        found = _scan_jobs_with_logs(db, errors, job_id)
        _log_activity(db, job_id, 3,
                      f"{found} agence(s) recrutent activement (gestionnaires locatifs, copropriété...)",
                      "fire" if found > 0 else "success", count=found)
        logger.warning(f"[Pipeline] Step 4 done: {found} agencies hiring")

        # ── Step 5: Recalculate insights ──
        _log_activity(db, job_id, 4, "Suppression des anciens scores...", "calculator")
        db.query(Insight).delete()
        db.commit()
        _step_generate_insights(db)
        insights_count = db.query(Insight).count()
        high_score = db.query(Insight).filter(Insight.score_besoin >= 50).count()
        _log_activity(db, job_id, 4,
                      f"{insights_count} scores calculés — {high_score} cibles prioritaires détectées",
                      "success", count=insights_count)
        logger.warning(f"[Pipeline] Step 5 done: {insights_count} insights")

        # ── Finalize ──
        job = db.get(ScrapingJob, uuid.UUID(job_id))
        if job:
            job.nb_agences_scrappees = nb
            job.progression = {
                "step": len(PIPELINE_STEPS),
                "total_steps": len(PIPELINE_STEPS),
                "step_key": "done",
                "step_label": "Terminé",
                "detail": f"{nb} agences, {found} recrutent, {high_score} cibles prioritaires",
                "percent": 100,
                "eta_minutes": 0,
                "eta_display": "Terminé",
                "logs": list(_activity_logs),
            }
            job.statut = JobStatut.done
            job.finished_at = datetime.now(timezone.utc)
            if errors:
                job.erreurs = {"warnings": errors[:20]}
            db.commit()

        logger.warning(f"[Pipeline] Job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"[Pipeline] Job {job_id} failed: {e}", exc_info=True)
        _log_activity(db, job_id, 0, f"Erreur : {str(e)[:150]}", "error")
        job = db.get(ScrapingJob, uuid.UUID(job_id))
        if job:
            job.statut = JobStatut.failed
            job.finished_at = datetime.now(timezone.utc)
            job.erreurs = {"error": str(e)}
            db.commit()
    finally:
        db.close()


def _step_collect_with_logs(db, errors: list, job_id: str) -> tuple[int, int]:
    """Collect from government API with detailed progress logging."""
    import httpx
    from app.services.scraping_service import SEARCH_TERMS, NAF_CODES, GOV_API, _upsert_agence

    total_new = 0
    total_updated = 0
    terms_done = 0

    with httpx.Client(timeout=30.0) as client:
        for term in SEARCH_TERMS:
            terms_done += 1
            term_new = 0

            for page in range(1, 11):
                try:
                    resp = client.get(GOV_API, params={
                        "q": term, "page": page, "per_page": 25,
                        "activite_principale": NAF_CODES,
                        "etat_administratif": "A",
                    })
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    errors.append(f"{term} p{page}: {str(e)[:80]}")
                    break

                results = data.get("results", [])
                if not results:
                    break

                for entry in results:
                    new, updated = _upsert_agence(db, entry)
                    total_new += new
                    total_updated += updated
                    term_new += new

                db.commit()

            # Log every 5 terms or when we find new agencies
            if terms_done % 5 == 0 or term_new > 0:
                _log_activity(db, job_id, 0,
                              f"Recherche « {term} » — {term_new} nouvelles ({total_new} total, {terms_done}/{len(SEARCH_TERMS)} termes)",
                              "search" if term_new == 0 else "plus",
                              count=total_new)

    return total_new, total_updated


def _scan_jobs_with_logs(db, errors: list, job_id: str) -> int:
    """Scan job postings with detailed logging."""
    from app.services.job_scraper import _search_duckduckgo, _scan_agency_website, TARGET_ROLES
    from app.models.agence import Agence
    import httpx
    import time

    agences = (
        db.query(Agence)
        .filter(Agence.siren.isnot(None))
        .filter(Agence.offres_emploi_detectees.is_(None))
        .order_by(Agence.nb_lots_geres.desc().nullslast())
        .limit(50)
        .all()
    )

    if not agences:
        _log_activity(db, job_id, 3, "Aucune agence à scanner (déjà toutes scannées)", "info")
        return 0

    _log_activity(db, job_id, 3, f"{len(agences)} agences à scanner pour offres d'emploi...", "briefcase")
    found = 0

    HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        for i, agence in enumerate(agences):
            job_findings = []

            if agence.site_web:
                job_findings = _scan_agency_website(client, agence.site_web, agence.nom, errors)

            if not job_findings:
                job_findings = _search_duckduckgo(client, agence.nom, errors)
                time.sleep(1.5)

            agence.offres_emploi_detectees = job_findings if job_findings else []
            if job_findings:
                found += 1
                roles = list(set(j.get("role", "") for j in job_findings))
                _log_activity(db, job_id, 3,
                              f"🔥 {agence.nom} recrute ! ({', '.join(roles[:2])})",
                              "fire", count=found)

            # Progress every 10 agencies
            if (i + 1) % 10 == 0:
                _log_activity(db, job_id, 3,
                              f"Scan en cours... {i+1}/{len(agences)} agences vérifiées, {found} recrutent",
                              "briefcase")

    db.commit()
    return found


@router.post("/lancer")
def lancer_scraping(db: Session = Depends(get_db)):
    """Launch full scraping pipeline SYNCHRONOUSLY.
    The frontend fires this request and doesn't wait for the response.
    Progress is tracked via polling GET /jobs."""
    import logging
    logger = logging.getLogger(__name__)

    # Auto-clean stuck jobs
    stuck_jobs = db.query(ScrapingJob).filter(
        ScrapingJob.statut.in_([JobStatut.pending, JobStatut.running])
    ).all()
    for sj in stuck_jobs:
        sj.statut = JobStatut.failed
        sj.finished_at = datetime.now(timezone.utc)
        sj.erreurs = {"info": "Auto-nettoyé (bloqué)"}
    if stuck_jobs:
        db.commit()

    job = ScrapingJob(type=JobType.manuel, statut=JobStatut.running)
    job.started_at = datetime.now(timezone.utc)
    db.add(job)
    db.commit()
    db.refresh(job)
    job_id = str(job.id)

    logger.warning(f"[Pipeline] Running synchronously for job {job_id}")

    # Run pipeline synchronously — blocks this HTTP request
    # Frontend uses fire-and-forget fetch so user isn't blocked
    _run_full_pipeline(job_id)

    # Return final state
    db.refresh(job)
    return {"id": str(job.id), "statut": job.statut.value, "nb_agences_scrappees": job.nb_agences_scrappees}


@router.get("/jobs", response_model=ScrapingJobList)
def list_jobs(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = select(ScrapingJob).order_by(ScrapingJob.created_at.desc())
    count_query = select(func.count()).select_from(ScrapingJob)
    total = db.execute(count_query).scalar()
    offset = (page - 1) * limit
    results = db.execute(query.offset(offset).limit(limit)).scalars().all()
    pages = (total + limit - 1) // limit if total > 0 else 0
    return ScrapingJobList(items=results, total=total, page=page, limit=limit, pages=pages)


@router.get("/test-thread")
def test_thread():
    """Debug endpoint — test if threads work on this host."""
    import threading, time, logging
    logger = logging.getLogger(__name__)
    results = {"started": False, "completed": False}

    def worker():
        results["started"] = True
        time.sleep(1)
        results["completed"] = True

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(timeout=5)
    return {"thread_alive": t.is_alive(), "started": results["started"], "completed": results["completed"]}


@router.get("/test-pipeline")
def test_pipeline():
    """Debug: run step 1 synchronously with the same code path as the thread."""
    db = SessionLocal()
    try:
        # Test the exact same imports and function the thread uses
        from app.services.scraping_service import _step_collect, SEARCH_TERMS, NAF_CODES, GOV_API, _upsert_agence
        from app.services.job_scraper import _search_duckduckgo, _scan_agency_website, TARGET_ROLES

        # Create a test job
        job = ScrapingJob(type=JobType.manuel, statut=JobStatut.running)
        job.started_at = datetime.now(timezone.utc)
        db.add(job)
        db.commit()
        db.refresh(job)
        job_id = str(job.id)

        # Test _log_activity
        _log_activity(db, job_id, 0, "Test: pipeline started", "info")

        # Test collect with logs
        errors = []
        new, updated = _step_collect_with_logs(db, errors, job_id)

        # Mark done
        job.statut = JobStatut.done
        job.finished_at = datetime.now(timezone.utc)
        job.nb_agences_scrappees = new + updated
        db.commit()

        return {"new": new, "updated": updated, "errors": errors[:5], "job_id": job_id, "logs": len(_activity_logs)}
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()}
    finally:
        db.close()


@router.post("/stop/{job_id}", response_model=ScrapingJobRead)
def stop_scraping(job_id: uuid.UUID, db: Session = Depends(get_db)):
    job = db.get(ScrapingJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.statut not in (JobStatut.pending, JobStatut.running):
        raise HTTPException(status_code=400, detail="Job is not running")
    job.statut = JobStatut.failed
    job.finished_at = datetime.now(timezone.utc)
    job.erreurs = {"info": "Arrêté manuellement"}
    db.commit()
    db.refresh(job)
    return job
