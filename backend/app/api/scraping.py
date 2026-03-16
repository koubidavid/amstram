import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.scraping_job import JobStatut, JobType, ScrapingJob
from app.schemas.scraping_job import ScrapingJobCreate, ScrapingJobList, ScrapingJobRead

router = APIRouter(prefix="/api/scraping", tags=["scraping"])


@router.post("/lancer", response_model=ScrapingJobRead)
def lancer_scraping(db: Session = Depends(get_db)):
    job = ScrapingJob(type=JobType.manuel, statut=JobStatut.pending)
    db.add(job)
    db.commit()
    db.refresh(job)

    # Trigger Celery task
    try:
        from celery import Celery
        import os
        celery_app = Celery("amstram", broker=os.getenv("REDIS_URL", "redis://redis:6379/0"))
        celery_app.send_task("tasks.run_full_scraping", args=[str(job.id)])
    except Exception:
        pass  # Celery may not be available in dev/test

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


@router.post("/cron", response_model=ScrapingJobRead)
def create_cron(data: ScrapingJobCreate, db: Session = Depends(get_db)):
    job = ScrapingJob(
        type=JobType.cron,
        cron_expression=data.cron_expression,
        statut=JobStatut.pending,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.post("/stop/{job_id}", response_model=ScrapingJobRead)
def stop_scraping(job_id: uuid.UUID, db: Session = Depends(get_db)):
    from datetime import datetime

    job = db.get(ScrapingJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.statut not in (JobStatut.pending, JobStatut.running):
        raise HTTPException(status_code=400, detail="Job is not running")

    # Revoke the Celery task
    try:
        from celery import Celery
        import os
        celery_app = Celery("amstram", broker=os.getenv("REDIS_URL", "redis://redis:6379/0"))
        celery_app.control.revoke(str(job_id), terminate=True, signal="SIGTERM")
    except Exception:
        pass

    job.statut = JobStatut.failed
    job.finished_at = datetime.utcnow()
    job.erreurs = {"info": "Arrêté manuellement par l'utilisateur"}
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
