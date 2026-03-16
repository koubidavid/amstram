import os
import uuid
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tasks.celery_app import app

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://needscrapper:needscrapper@db:5432/needscrapper")


def get_db_session():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()


@app.task(name="tasks.run_full_scraping")
def run_full_scraping(job_id: str | None = None):
    import sys
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
    job.started_at = datetime.utcnow()
    session.commit()

    try:
        from scrapy.crawler import CrawlerProcess
        from scrapy.utils.project import get_project_settings

        process = CrawlerProcess(get_project_settings())
        process.crawl("agence_info")
        process.crawl("offre_emploi")
        process.crawl("google_reviews")
        process.crawl("trustpilot")
        process.start()

        job.statut = JobStatut.done
        job.finished_at = datetime.utcnow()
    except Exception as e:
        job.statut = JobStatut.failed
        job.finished_at = datetime.utcnow()
        job.erreurs = {"error": str(e)}
    finally:
        session.commit()
        session.close()

    return job_id


@app.task(name="tasks.run_spider")
def run_spider(spider_name: str):
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    process = CrawlerProcess(get_project_settings())
    process.crawl(spider_name)
    process.start()


@app.task(name="tasks.calculate_all_insights")
def calculate_all_insights():
    import sys
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
    twelve_months_ago = datetime.utcnow() - timedelta(days=365)

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
