from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import Base, engine
from app.models import *  # noqa: F401,F403 — import all models so Base.metadata knows about them

# Create all tables on startup
Base.metadata.create_all(bind=engine)

# Safe migration: add missing columns (no Alembic)
with engine.connect() as conn:
    from sqlalchemy import text, inspect as sa_inspect
    inspector = sa_inspect(engine)
    for table_name, columns_to_add in [
        ("scraping_jobs", [("progression", "JSON")]),
    ]:
        if table_name in inspector.get_table_names():
            existing = {c["name"] for c in inspector.get_columns(table_name)}
            for col_name, col_type in columns_to_add:
                if col_name not in existing:
                    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
                    conn.commit()

app = FastAPI(title="Amstram — Opportunity Finder API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.agences import router as agences_router
from app.api.offres import router as offres_router
from app.api.avis import router as avis_router
from app.api.insights import router as insights_router
from app.api.scraping import router as scraping_router
from app.api.export import router as export_router
from app.api.predictions import router as predictions_router

app.include_router(agences_router)
app.include_router(offres_router)
app.include_router(avis_router)
app.include_router(insights_router)
app.include_router(scraping_router)
app.include_router(export_router)
app.include_router(predictions_router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/admin/reset-db")
def reset_db():
    """Drop and recreate all tables. Use with caution."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return {"status": "tables recreated"}
