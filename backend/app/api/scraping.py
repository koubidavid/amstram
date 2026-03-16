import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.deps import get_db
from app.models.agence import Agence
from app.models.insight import Insight
from app.models.scraping_job import JobStatut, JobType, ScrapingJob
from app.schemas.scraping_job import ScrapingJobCreate, ScrapingJobList, ScrapingJobRead

router = APIRouter(prefix="/api/scraping", tags=["scraping"])


@router.post("/lancer", response_model=ScrapingJobRead)
def lancer_scraping(db: Session = Depends(get_db)):
    """Launch scraping synchronously (~20-30s). Collects agencies + computes insights."""
    from app.services.scraping_service import run_scraping
    job = ScrapingJob(type=JobType.manuel, statut=JobStatut.pending)
    db.add(job)
    db.commit()
    db.refresh(job)

    run_scraping(db, str(job.id))
    db.refresh(job)
    return job


@router.post("/enrich-rnic")
def enrich_rnic(db: Session = Depends(get_db)):
    """Enrich agencies with RNIC data. Parses local CSV (~60-90s for 626k rows)."""
    from app.services.scraping_service import _step_enrich_rnic, _step_generate_insights
    errors = []

    db.query(Insight).delete()
    db.commit()

    matched = _step_enrich_rnic(db, errors)
    _step_generate_insights(db)

    total = db.query(Agence).count()
    with_lots = db.query(Agence).filter(Agence.nb_lots_geres.isnot(None)).count()

    return {
        "status": "done",
        "rnic_matched": matched,
        "total_agences": total,
        "agences_with_lots": with_lots,
        "errors": errors if errors else None,
    }


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


@router.post("/cron", response_model=ScrapingJobRead)
def create_cron(data: ScrapingJobCreate, db: Session = Depends(get_db)):
    job = ScrapingJob(type=JobType.cron, cron_expression=data.cron_expression, statut=JobStatut.pending)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.delete("/cron/{job_id}")
def delete_cron(job_id: uuid.UUID, db: Session = Depends(get_db)):
    job = db.get(ScrapingJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.type != JobType.cron:
        raise HTTPException(status_code=400, detail="Not a cron job")
    db.delete(job)
    db.commit()
    return {"status": "deleted"}
