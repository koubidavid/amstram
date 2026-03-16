import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tasks.celery_app import app

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://needscrapper:needscrapper@db:5432/needscrapper")


def get_db_session():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()


def run_spider_subprocess(spider_name: str, extra_args: list[str] | None = None):
    """Run a scrapy spider in a subprocess to avoid Twisted reactor conflicts."""
    cmd = ["scrapy", "crawl", spider_name, "-s", "LOG_LEVEL=INFO"]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(
        cmd,
        cwd="/app/scrapper" if os.path.exists("/app/scrapper") else os.path.join(os.path.dirname(__file__), ".."),
        capture_output=True,
        text=True,
        timeout=3600,  # 1 hour max
        env={**os.environ, "PYTHONPATH": "/app:/backend"},
    )
    return result


@app.task(name="tasks.run_full_scraping", bind=True)
def run_full_scraping(self, job_id: str | None = None):
    sys.path.insert(0, "/backend")
    from app.models.scraping_job import ScrapingJob, JobStatut

    session = get_db_session()

    if job_id:
        job = session.get(ScrapingJob, uuid.UUID(job_id))
    else:
        job = ScrapingJob(type="manuel", statut=JobStatut.running)
        session.add(job)
        session.commit()
        job_id = str(job.id)

    job.statut = JobStatut.running
    job.started_at = datetime.now(timezone.utc)
    session.commit()

    errors = []
    total_agences = 0

    try:
        # Spider 1: Scrape agency info from PagesJaunes
        self.update_state(state="PROGRESS", meta={"step": "agence_info"})
        result = run_spider_subprocess("agence_info")
        if result.returncode != 0:
            errors.append({"spider": "agence_info", "stderr": result.stderr[-500:] if result.stderr else ""})

        # Count how many agences we have now
        from app.models.agence import Agence
        total_agences = session.query(Agence).count()

        # Spider 2: Scrape job offers from agency websites
        if total_agences > 0:
            self.update_state(state="PROGRESS", meta={"step": "offre_emploi"})
            result = run_spider_subprocess("offre_emploi")
            if result.returncode != 0:
                errors.append({"spider": "offre_emploi", "stderr": result.stderr[-500:] if result.stderr else ""})

        # Spider 3: Google Reviews
        if total_agences > 0:
            self.update_state(state="PROGRESS", meta={"step": "google_reviews"})
            result = run_spider_subprocess("google_reviews")
            if result.returncode != 0:
                errors.append({"spider": "google_reviews", "stderr": result.stderr[-500:] if result.stderr else ""})

        # Spider 4: Trustpilot
        if total_agences > 0:
            self.update_state(state="PROGRESS", meta={"step": "trustpilot"})
            result = run_spider_subprocess("trustpilot")
            if result.returncode != 0:
                errors.append({"spider": "trustpilot", "stderr": result.stderr[-500:] if result.stderr else ""})

        # Calculate insights
        if total_agences > 0:
            self.update_state(state="PROGRESS", meta={"step": "insights"})
            calculate_all_insights()

        job.statut = JobStatut.done
        job.finished_at = datetime.now(timezone.utc)
        job.nb_agences_scrappees = total_agences
        if errors:
            job.erreurs = {"spider_errors": errors}

    except Exception as e:
        job.statut = JobStatut.failed
        job.finished_at = datetime.now(timezone.utc)
        job.erreurs = {"error": str(e)}
    finally:
        session.commit()
        session.close()

    return job_id


@app.task(name="tasks.run_spider")
def run_spider(spider_name: str):
    run_spider_subprocess(spider_name)


@app.task(name="tasks.calculate_all_insights")
def calculate_all_insights():
    sys.path.insert(0, "/backend")
    from datetime import timedelta
    from sqlalchemy import func

    from app.models.agence import Agence
    from app.models.agence_snapshot import AgenceSnapshot
    from app.models.avis import Avis
    from app.models.insight import Insight
    from app.models.offre import OffreEmploi
    from app.services.insight_calculator import InsightCalculator

    session = get_db_session()
    calc = InsightCalculator()
    twelve_months_ago = datetime.now(timezone.utc) - timedelta(days=365)

    agences = session.query(Agence).all()
    for agence in agences:
        nb_lots = agence.nb_lots_geres
        nb_collab = agence.nb_collaborateurs

        total_avis_negatifs = session.query(func.count(Avis.id)).filter(
            Avis.agence_id == agence.id, Avis.note < 3
        ).scalar() or 0
        avis_mentionnant_travaux = session.query(func.count(Avis.id)).filter(
            Avis.agence_id == agence.id, Avis.note < 3, Avis.mentionne_travaux == True
        ).scalar() or 0

        nb_offres_12_mois = session.query(func.count(OffreEmploi.id)).filter(
            OffreEmploi.agence_id == agence.id,
            OffreEmploi.date_scrappee >= twelve_months_ago,
        ).scalar() or 0

        snapshots = (
            session.query(AgenceSnapshot)
            .filter(AgenceSnapshot.agence_id == agence.id)
            .order_by(AgenceSnapshot.created_at.desc())
            .limit(2)
            .all()
        )
        current_lots = snapshots[0].nb_lots_geres if len(snapshots) > 0 else None
        previous_lots = snapshots[1].nb_lots_geres if len(snapshots) > 1 else None

        has_service = agence.a_service_travaux

        result = calc.calculate(
            nb_lots=nb_lots, nb_collab=nb_collab,
            total_avis_negatifs=total_avis_negatifs,
            avis_mentionnant_travaux=avis_mentionnant_travaux,
            nb_offres_12_mois=nb_offres_12_mois,
            previous_lots=previous_lots, current_lots=current_lots,
            has_service_travaux=has_service,
        )

        insight = Insight(
            agence_id=agence.id,
            score_besoin=result["score_besoin"],
            signaux=result["signaux"],
            ratio_lots_collab=result["ratio_lots_collab"],
            turnover_score=result["turnover_score"],
            avis_negatifs_travaux=result["avis_negatifs_travaux"],
            croissance_parc=result["croissance_parc"],
            has_service_travaux=result["has_service_travaux"],
            recommandation=result["recommandation"],
        )
        session.add(insight)

    session.commit()
    session.close()
