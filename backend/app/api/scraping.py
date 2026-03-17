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


def _update_progress(db, job_id: str, step_index: int, detail: str = ""):
    """Update job progression with current step and ETA."""
    import time
    job = db.get(ScrapingJob, uuid.UUID(job_id))
    if not job:
        return

    total_steps = len(PIPELINE_STEPS)
    current = PIPELINE_STEPS[step_index]

    # Estimate remaining time
    remaining_min = sum(s["estimate_min"] for s in PIPELINE_STEPS[step_index:])

    job.progression = {
        "step": step_index + 1,
        "total_steps": total_steps,
        "step_key": current["key"],
        "step_label": current["label"],
        "detail": detail,
        "percent": round((step_index / total_steps) * 100),
        "eta_minutes": round(remaining_min, 1),
        "eta_display": f"~{int(remaining_min)} min" if remaining_min >= 1 else "< 1 min",
    }
    db.commit()


def _run_full_pipeline(job_id: str):
    """Run the complete pipeline: collect + RNIC + Pappers + jobs + insights."""
    import logging
    logger = logging.getLogger(__name__)

    from app.services.scraping_service import run_scraping, _step_enrich_rnic, _step_enrich_pappers, _step_generate_insights
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

        # Step 1: Collect from API
        _update_progress(db, job_id, 0, "Requêtes API recherche-entreprises.gouv.fr...")
        run_scraping(db, job_id)
        nb = db.query(Agence).count()
        logger.info(f"[Pipeline] Step 1 done: {nb} agences collected")

        errors = []

        # Step 2: Enrich with RNIC
        _update_progress(db, job_id, 1, f"{nb} agences à enrichir avec le RNIC...")
        _step_enrich_rnic(db, errors)
        logger.info(f"[Pipeline] Step 2 done: RNIC enrichment")

        # Step 3: Enrich with Pappers
        _update_progress(db, job_id, 2, "Récupération dirigeants et CA via Pappers...")
        _step_enrich_pappers(db, errors)
        logger.info(f"[Pipeline] Step 3 done: Pappers enrichment")

        # Step 4: Scan for job postings
        _update_progress(db, job_id, 3, "Scan DuckDuckGo + sites agences pour offres d'emploi...")
        found = scan_agency_jobs(db, errors)
        logger.info(f"[Pipeline] Step 4 done: {found} agencies with job postings")

        # Step 5: Recalculate insights
        _update_progress(db, job_id, 4, "Recalcul des scores avec toutes les données...")
        db.query(Insight).delete()
        db.commit()
        _step_generate_insights(db)
        logger.info(f"[Pipeline] Step 5 done: insights generated")

        # Finalize
        job = db.get(ScrapingJob, uuid.UUID(job_id))
        if job:
            job.nb_agences_scrappees = db.query(Agence).count()
            job.progression = {
                "step": len(PIPELINE_STEPS),
                "total_steps": len(PIPELINE_STEPS),
                "step_key": "done",
                "step_label": "Terminé",
                "detail": f"{job.nb_agences_scrappees} agences, {found} avec offres d'emploi",
                "percent": 100,
                "eta_minutes": 0,
                "eta_display": "Terminé",
            }
            if errors:
                job.erreurs = {"warnings": errors}
            db.commit()

        logger.info(f"[Pipeline] Job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"[Pipeline] Job {job_id} failed: {e}")
        job = db.get(ScrapingJob, uuid.UUID(job_id))
        if job:
            job.statut = JobStatut.failed
            job.finished_at = datetime.now(timezone.utc)
            job.erreurs = {"error": str(e)}
            db.commit()
    finally:
        db.close()


@router.post("/lancer", response_model=ScrapingJobRead)
def lancer_scraping(db: Session = Depends(get_db)):
    """Launch full scraping pipeline.
    Runs synchronously — the frontend polls /jobs for status."""
    import threading
    import logging
    logger = logging.getLogger(__name__)

    job = ScrapingJob(type=JobType.manuel, statut=JobStatut.pending)
    db.add(job)
    db.commit()
    db.refresh(job)

    job_id = str(job.id)

    def _run_in_thread():
        try:
            logger.warning(f"[Pipeline] Thread started for job {job_id}")
            _run_full_pipeline(job_id)
            logger.warning(f"[Pipeline] Thread completed for job {job_id}")
        except Exception as e:
            logger.error(f"[Pipeline] Thread crashed: {e}", exc_info=True)

    t = threading.Thread(target=_run_in_thread, daemon=True)
    t.start()
    logger.warning(f"[Pipeline] Thread launched: alive={t.is_alive()}")

    return job


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
        logger.warning("[test-thread] Worker started!")
        time.sleep(1)
        results["completed"] = True
        logger.warning("[test-thread] Worker completed!")

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(timeout=5)
    return {
        "thread_alive": t.is_alive(),
        "started": results["started"],
        "completed": results["completed"],
    }


@router.get("/test-pipeline")
def test_pipeline():
    """Debug: run just step 1 (collect) synchronously and return result."""
    import logging
    logger = logging.getLogger(__name__)
    db = SessionLocal()
    try:
        from app.services.scraping_service import _step_collect
        errors = []
        logger.warning("[test-pipeline] Starting collect...")
        new, updated = _step_collect(db, errors)
        logger.warning(f"[test-pipeline] Done: new={new} updated={updated} errors={len(errors)}")
        return {"new": new, "updated": updated, "errors": errors[:5]}
    except Exception as e:
        logger.error(f"[test-pipeline] Failed: {e}", exc_info=True)
        return {"error": str(e)}
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
