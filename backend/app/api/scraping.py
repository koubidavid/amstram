"""Scraping API — one button does everything."""
import asyncio
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

# Track running task so we can check status
_running_task: asyncio.Task | None = None


def _run_full_pipeline(job_id: str):
    """Run the complete pipeline: collect + RNIC + insights."""
    from app.services.scraping_service import run_scraping, _step_enrich_rnic, _step_generate_insights
    from app.models.insight import Insight

    db = SessionLocal()
    try:
        # Step 1: Collect from API + generate initial insights
        run_scraping(db, job_id)

        # Step 2: Enrich with RNIC (local file)
        errors = []
        db.query(Insight).delete()
        db.commit()
        _step_enrich_rnic(db, errors)

        # Step 3: Recalculate insights with RNIC data
        _step_generate_insights(db)

        # Update job with final counts
        from app.models.agence import Agence
        job = db.get(ScrapingJob, uuid.UUID(job_id))
        if job:
            job.nb_agences_scrappees = db.query(Agence).count()
            rnic_count = db.query(Agence).filter(Agence.nb_lots_geres.isnot(None)).count()
            if errors:
                job.erreurs = {"rnic_warnings": errors}
            db.commit()
    finally:
        db.close()


@router.post("/lancer", response_model=ScrapingJobRead)
async def lancer_scraping(db: Session = Depends(get_db)):
    """Launch full scraping pipeline in background.
    Collects agencies + enriches with RNIC + computes insights."""
    global _running_task

    job = ScrapingJob(type=JobType.manuel, statut=JobStatut.pending)
    db.add(job)
    db.commit()
    db.refresh(job)

    job_id = str(job.id)

    # Run in background via asyncio + thread executor
    loop = asyncio.get_event_loop()
    _running_task = loop.run_in_executor(None, _run_full_pipeline, job_id)

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
