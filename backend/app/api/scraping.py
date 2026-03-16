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
