# Need Scrapper Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a web scraping + predictive insights tool targeting French real estate agencies (gestion locative & copropriété) to identify those needing workforce/logistics support for property maintenance.

**Architecture:** Python backend (FastAPI + Scrapy + Celery) with PostgreSQL/Redis, fronted by a Next.js dashboard. Three layers: scrapping engine collects data, API serves it and computes insights, dashboard displays everything with filters and exports.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Alembic, Scrapy, Playwright, Celery + Celery Beat, Redis, PostgreSQL, Next.js 14, Tailwind CSS, shadcn/ui, Recharts, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-03-16-need-scrapper-design.md`

---

## File Structure

```
need-scrapper/
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app, CORS, router includes
│   │   ├── config.py                  # Settings via pydantic-settings
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── database.py            # Engine, SessionLocal, Base
│   │   │   └── deps.py                # get_db dependency
│   │   ├── models/
│   │   │   ├── __init__.py            # Re-export all models
│   │   │   ├── agence.py
│   │   │   ├── agence_snapshot.py
│   │   │   ├── offre.py
│   │   │   ├── avis.py
│   │   │   ├── insight.py
│   │   │   └── scraping_job.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── agence.py
│   │   │   ├── agence_snapshot.py
│   │   │   ├── offre.py
│   │   │   ├── avis.py
│   │   │   ├── insight.py
│   │   │   ├── scraping_job.py
│   │   │   └── pagination.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── agences.py
│   │   │   ├── offres.py
│   │   │   ├── avis.py
│   │   │   ├── insights.py
│   │   │   ├── scraping.py
│   │   │   └── export.py
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── insight_calculator.py
│   │       └── export_service.py
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                # Test DB fixtures
│       ├── test_models.py
│       ├── test_api_agences.py
│       ├── test_api_offres.py
│       ├── test_api_avis.py
│       ├── test_api_insights.py
│       ├── test_api_scraping.py
│       ├── test_api_export.py
│       └── test_insight_calculator.py
│
├── scrapper/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── scrapy.cfg
│   ├── scrapper/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── items.py                   # Scrapy item definitions
│   │   ├── middlewares.py             # Proxy rotation, UA rotation
│   │   ├── pipelines/
│   │   │   ├── __init__.py
│   │   │   ├── cleaning.py
│   │   │   ├── snapshot.py
│   │   │   └── database.py
│   │   ├── spiders/
│   │   │   ├── __init__.py
│   │   │   ├── agence_info.py
│   │   │   ├── offre_emploi.py
│   │   │   ├── google_reviews.py
│   │   │   └── trustpilot.py
│   │   └── config/
│   │       ├── selectors.yaml
│   │       └── proxies.yaml
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   ├── celery_tasks.py
│   │   └── beat_schedule.py
│   └── tests/
│       ├── __init__.py
│       ├── test_pipelines.py
│       ├── test_spiders.py
│       └── test_celery_tasks.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   ├── components.json               # shadcn/ui config
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx               # Vue d'ensemble
│   │   │   ├── agences/
│   │   │   │   ├── page.tsx           # Liste agences
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx       # Détail agence
│   │   │   ├── offres/
│   │   │   │   └── page.tsx
│   │   │   ├── insights/
│   │   │   │   └── page.tsx
│   │   │   └── scraping/
│   │   │       └── page.tsx
│   │   ├── components/
│   │   │   ├── ui/                    # shadcn/ui components
│   │   │   ├── layout/
│   │   │   │   ├── sidebar.tsx
│   │   │   │   └── header.tsx
│   │   │   ├── charts/
│   │   │   │   ├── score-gauge.tsx
│   │   │   │   ├── trend-chart.tsx
│   │   │   │   └── sparkline.tsx
│   │   │   ├── tables/
│   │   │   │   ├── agences-table.tsx
│   │   │   │   ├── offres-table.tsx
│   │   │   │   └── jobs-table.tsx
│   │   │   └── cards/
│   │   │       ├── kpi-card.tsx
│   │   │       ├── insight-card.tsx
│   │   │       └── agence-detail-card.tsx
│   │   └── lib/
│   │       ├── api.ts                 # API client (fetch wrapper)
│   │       ├── types.ts               # TypeScript types matching backend schemas
│   │       └── utils.ts               # Helpers (formatting, colors, etc.)
│   └── public/
│       └── favicon.ico
```

---

## Chunk 1: Project Scaffolding + Database + Models

### Task 1: Docker Compose & Environment

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `.gitignore`

- [ ] **Step 1: Initialize git repo**

```bash
cd "/Users/davidkoubi/Documents/Need Scrapper"
git init
```

- [ ] **Step 2: Create .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
dist/
build/

# Node
node_modules/
.next/
out/

# Env
.env
*.env.local

# IDE
.vscode/
.idea/

# Docker
*.log

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 3: Create .env.example**

```env
# PostgreSQL
POSTGRES_USER=needscrapper
POSTGRES_PASSWORD=needscrapper
POSTGRES_DB=needscrapper
DATABASE_URL=postgresql://needscrapper:needscrapper@db:5432/needscrapper

# Redis
REDIS_URL=redis://redis:6379/0

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

- [ ] **Step 4: Create docker-compose.yml**

```yaml
services:
  db:
    image: postgres:16-alpine
    env_file: .env
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    env_file: .env
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    depends_on:
      - db
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  celery-worker:
    build: ./scrapper
    env_file: .env
    volumes:
      - ./scrapper:/app
      - ./backend:/backend
    depends_on:
      - db
      - redis
    command: celery -A tasks.celery_app worker --loglevel=info

  celery-beat:
    build: ./scrapper
    env_file: .env
    volumes:
      - ./scrapper:/app
      - ./backend:/backend
    depends_on:
      - db
      - redis
    command: celery -A tasks.celery_app beat --loglevel=info

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000

volumes:
  postgres_data:
```

- [ ] **Step 5: Commit**

```bash
git add .gitignore .env.example docker-compose.yml
git commit -m "chore: project scaffolding with docker-compose"
```

---

### Task 2: Backend Scaffolding (FastAPI + SQLAlchemy + Alembic)

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/db/__init__.py`
- Create: `backend/app/db/database.py`
- Create: `backend/app/db/deps.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`

- [ ] **Step 1: Create backend/requirements.txt**

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
alembic==1.14.1
psycopg2-binary==2.9.10
pydantic-settings==2.7.1
redis==5.2.1
openpyxl==3.1.5
python-multipart==0.0.18
```

- [ ] **Step 2: Create backend/Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: Create backend/app/config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://needscrapper:needscrapper@db:5432/needscrapper"
    redis_url: str = "redis://redis:6379/0"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    class Config:
        env_file = ".env"


settings = Settings()
```

- [ ] **Step 4: Create backend/app/db/database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass
```

- [ ] **Step 5: Create backend/app/db/deps.py**

```python
from collections.abc import Generator

from app.db.database import SessionLocal


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 6: Create backend/app/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Need Scrapper API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
```

- [ ] **Step 7: Initialize Alembic**

```bash
cd backend
pip install -r requirements.txt
alembic init alembic
```

Then edit `alembic/env.py` to use `app.db.database.Base.metadata` and `app.config.settings.database_url`.

- [ ] **Step 8: Commit**

```bash
git add backend/
git commit -m "feat: backend scaffolding with FastAPI, SQLAlchemy, Alembic"
```

---

### Task 3: Database Models

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/agence.py`
- Create: `backend/app/models/agence_snapshot.py`
- Create: `backend/app/models/offre.py`
- Create: `backend/app/models/avis.py`
- Create: `backend/app/models/insight.py`
- Create: `backend/app/models/scraping_job.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_models.py`

- [ ] **Step 1: Write test for Agence model**

```python
# backend/tests/test_models.py
import uuid
from datetime import datetime

from app.models.agence import Agence


def test_agence_creation(db_session):
    agence = Agence(
        id=uuid.uuid4(),
        nom="Foncia Paris 15",
        groupe="Foncia",
        adresse="10 rue de Vaugirard",
        ville="Paris",
        region="Île-de-France",
        code_postal="75015",
        site_web="https://foncia.com",
        nb_lots_geres=350,
        nb_collaborateurs=8,
        a_service_travaux=False,
        note_google=3.2,
        nb_avis_google=45,
        note_trustpilot=2.8,
        nb_avis_trustpilot=30,
    )
    db_session.add(agence)
    db_session.commit()

    result = db_session.get(Agence, agence.id)
    assert result.nom == "Foncia Paris 15"
    assert result.groupe == "Foncia"
    assert result.nb_lots_geres == 350
    assert result.created_at is not None
```

- [ ] **Step 2: Write conftest.py with test DB fixtures**

```python
# backend/tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base

TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
```

- [ ] **Step 3: Run test — expect FAIL (Agence model not defined)**

```bash
cd backend && python -m pytest tests/test_models.py::test_agence_creation -v
```

Expected: FAIL — `ImportError: cannot import name 'Agence'`

- [ ] **Step 4: Implement Agence model**

```python
# backend/app/models/agence.py
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Agence(Base):
    __tablename__ = "agences"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nom: Mapped[str] = mapped_column(String(255))
    groupe: Mapped[str | None] = mapped_column(String(255))
    adresse: Mapped[str | None] = mapped_column(String(500))
    ville: Mapped[str | None] = mapped_column(String(100))
    region: Mapped[str | None] = mapped_column(String(100))
    code_postal: Mapped[str | None] = mapped_column(String(10))
    site_web: Mapped[str | None] = mapped_column(String(500))
    nb_lots_geres: Mapped[int | None] = mapped_column(Integer)
    nb_collaborateurs: Mapped[int | None] = mapped_column(Integer)
    a_service_travaux: Mapped[bool] = mapped_column(Boolean, default=False)
    note_google: Mapped[float | None] = mapped_column(Float)
    nb_avis_google: Mapped[int | None] = mapped_column(Integer)
    note_trustpilot: Mapped[float | None] = mapped_column(Float)
    nb_avis_trustpilot: Mapped[int | None] = mapped_column(Integer)
    derniere_maj: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    offres = relationship("OffreEmploi", back_populates="agence")
    avis = relationship("Avis", back_populates="agence")
    insights = relationship("Insight", back_populates="agence")
    snapshots = relationship("AgenceSnapshot", back_populates="agence")
```

- [ ] **Step 5: Run test — expect PASS**

```bash
cd backend && python -m pytest tests/test_models.py::test_agence_creation -v
```

- [ ] **Step 6: Implement remaining models (AgenceSnapshot, OffreEmploi, Avis, Insight, ScrapingJob)**

```python
# backend/app/models/agence_snapshot.py
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class AgenceSnapshot(Base):
    __tablename__ = "agence_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    agence_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agences.id"))
    nb_lots_geres: Mapped[int | None] = mapped_column(Integer)
    nb_collaborateurs: Mapped[int | None] = mapped_column(Integer)
    a_service_travaux: Mapped[bool] = mapped_column(Boolean, default=False)
    note_google: Mapped[float | None] = mapped_column(Float)
    note_trustpilot: Mapped[float | None] = mapped_column(Float)
    scraping_job_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("scraping_jobs.id")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    agence = relationship("Agence", back_populates="snapshots")
    scraping_job = relationship("ScrapingJob")
```

```python
# backend/app/models/offre.py
import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class TypePoste(str, enum.Enum):
    gestionnaire_locatif = "gestionnaire_locatif"
    assistant_gestion_locative = "assistant_gestion_locative"
    gestionnaire_copropriete = "gestionnaire_copropriete"
    assistant_copropriete = "assistant_copropriete"
    autre = "autre"


class OffreEmploi(Base):
    __tablename__ = "offres"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    agence_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agences.id"))
    titre: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    type_poste: Mapped[TypePoste] = mapped_column(Enum(TypePoste))
    url_source: Mapped[str | None] = mapped_column(String(1000))
    date_publication: Mapped[date | None] = mapped_column(Date)
    date_scrappee: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    agence = relationship("Agence", back_populates="offres")
```

```python
# backend/app/models/avis.py
import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class SourceAvis(str, enum.Enum):
    google = "google"
    trustpilot = "trustpilot"


class Avis(Base):
    __tablename__ = "avis"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    agence_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agences.id"))
    source: Mapped[SourceAvis] = mapped_column(Enum(SourceAvis))
    note: Mapped[float] = mapped_column(Float)
    texte: Mapped[str | None] = mapped_column(Text)
    mentionne_travaux: Mapped[bool] = mapped_column(Boolean, default=False)
    mentionne_reactivite: Mapped[bool] = mapped_column(Boolean, default=False)
    date_avis: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    agence = relationship("Agence", back_populates="avis")
```

```python
# backend/app/models/insight.py
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Insight(Base):
    __tablename__ = "insights"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    agence_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agences.id"))
    score_besoin: Mapped[int] = mapped_column(Integer, default=0)
    signaux: Mapped[dict | None] = mapped_column(JSON)
    ratio_lots_collab: Mapped[float | None] = mapped_column(Float)
    turnover_score: Mapped[float | None] = mapped_column(Float)
    avis_negatifs_travaux: Mapped[int | None] = mapped_column(Integer)
    croissance_parc: Mapped[float | None] = mapped_column(Float)
    has_service_travaux: Mapped[bool] = mapped_column(Boolean, default=False)
    recommandation: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    agence = relationship("Agence", back_populates="insights")
```

```python
# backend/app/models/scraping_job.py
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class JobType(str, enum.Enum):
    manuel = "manuel"
    cron = "cron"


class JobStatut(str, enum.Enum):
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"


class ScrapingJob(Base):
    __tablename__ = "scraping_jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    type: Mapped[JobType] = mapped_column(Enum(JobType))
    cron_expression: Mapped[str | None] = mapped_column(String(100))
    statut: Mapped[JobStatut] = mapped_column(Enum(JobStatut), default=JobStatut.pending)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    nb_agences_scrappees: Mapped[int] = mapped_column(Integer, default=0)
    erreurs: Mapped[dict | None] = mapped_column(JSON)
```

```python
# backend/app/models/__init__.py
from app.models.agence import Agence
from app.models.agence_snapshot import AgenceSnapshot
from app.models.avis import Avis, SourceAvis
from app.models.insight import Insight
from app.models.offre import OffreEmploi, TypePoste
from app.models.scraping_job import JobStatut, JobType, ScrapingJob

__all__ = [
    "Agence",
    "AgenceSnapshot",
    "Avis",
    "SourceAvis",
    "Insight",
    "OffreEmploi",
    "TypePoste",
    "ScrapingJob",
    "JobStatut",
    "JobType",
]
```

- [ ] **Step 7: Write tests for all models**

Add to `backend/tests/test_models.py`:

```python
def test_offre_emploi_creation(db_session):
    from app.models.agence import Agence
    from app.models.offre import OffreEmploi, TypePoste

    agence = Agence(nom="Test Agence")
    db_session.add(agence)
    db_session.flush()

    offre = OffreEmploi(
        agence_id=agence.id,
        titre="Gestionnaire Locatif H/F",
        type_poste=TypePoste.gestionnaire_locatif,
        active=True,
    )
    db_session.add(offre)
    db_session.commit()

    result = db_session.get(OffreEmploi, offre.id)
    assert result.titre == "Gestionnaire Locatif H/F"
    assert result.type_poste == TypePoste.gestionnaire_locatif
    assert result.agence_id == agence.id


def test_insight_creation(db_session):
    from app.models.agence import Agence
    from app.models.insight import Insight

    agence = Agence(nom="Test Agence")
    db_session.add(agence)
    db_session.flush()

    insight = Insight(
        agence_id=agence.id,
        score_besoin=72,
        signaux={"ratio": 25, "avis": 22, "turnover": 15, "croissance": 10},
        ratio_lots_collab=55.0,
        turnover_score=15.0,
        avis_negatifs_travaux=8,
        croissance_parc=12.5,
        has_service_travaux=False,
        recommandation="Besoin probable — plusieurs indices convergents",
    )
    db_session.add(insight)
    db_session.commit()

    result = db_session.get(Insight, insight.id)
    assert result.score_besoin == 72
    assert result.signaux["ratio"] == 25


def test_agence_snapshot_creation(db_session):
    from app.models.agence import Agence
    from app.models.agence_snapshot import AgenceSnapshot

    agence = Agence(nom="Test Agence", nb_lots_geres=200)
    db_session.add(agence)
    db_session.flush()

    snapshot = AgenceSnapshot(
        agence_id=agence.id,
        nb_lots_geres=200,
        nb_collaborateurs=5,
        a_service_travaux=False,
        note_google=3.5,
        note_trustpilot=2.9,
    )
    db_session.add(snapshot)
    db_session.commit()

    result = db_session.get(AgenceSnapshot, snapshot.id)
    assert result.nb_lots_geres == 200
    assert result.agence_id == agence.id
```

- [ ] **Step 8: Run all model tests — expect PASS**

```bash
cd backend && python -m pytest tests/test_models.py -v
```

- [ ] **Step 9: Generate initial Alembic migration**

```bash
cd backend && alembic revision --autogenerate -m "initial models"
```

- [ ] **Step 10: Commit**

```bash
git add backend/
git commit -m "feat: database models with SQLAlchemy (Agence, OffreEmploi, Avis, Insight, AgenceSnapshot, ScrapingJob)"
```

---

## Chunk 2: Pydantic Schemas + API Endpoints

### Task 4: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/pagination.py`
- Create: `backend/app/schemas/agence.py`
- Create: `backend/app/schemas/agence_snapshot.py`
- Create: `backend/app/schemas/offre.py`
- Create: `backend/app/schemas/avis.py`
- Create: `backend/app/schemas/insight.py`
- Create: `backend/app/schemas/scraping_job.py`

- [ ] **Step 1: Create pagination schema**

```python
# backend/app/schemas/pagination.py
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PaginatedResponse(BaseModel):
    total: int
    page: int
    limit: int
    pages: int
```

- [ ] **Step 2: Create all entity schemas**

```python
# backend/app/schemas/agence.py
import uuid
from datetime import datetime

from pydantic import BaseModel


class AgenceBase(BaseModel):
    nom: str
    groupe: str | None = None
    adresse: str | None = None
    ville: str | None = None
    region: str | None = None
    code_postal: str | None = None
    site_web: str | None = None
    nb_lots_geres: int | None = None
    nb_collaborateurs: int | None = None
    a_service_travaux: bool = False
    note_google: float | None = None
    nb_avis_google: int | None = None
    note_trustpilot: float | None = None
    nb_avis_trustpilot: int | None = None


class AgenceRead(AgenceBase):
    id: uuid.UUID
    derniere_maj: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgenceList(BaseModel):
    items: list[AgenceRead]
    total: int
    page: int
    limit: int
    pages: int
```

```python
# backend/app/schemas/agence_snapshot.py
import uuid
from datetime import datetime

from pydantic import BaseModel


class AgenceSnapshotRead(BaseModel):
    id: uuid.UUID
    agence_id: uuid.UUID
    nb_lots_geres: int | None = None
    nb_collaborateurs: int | None = None
    a_service_travaux: bool = False
    note_google: float | None = None
    note_trustpilot: float | None = None
    scraping_job_id: uuid.UUID | None = None
    created_at: datetime

    class Config:
        from_attributes = True
```

```python
# backend/app/schemas/offre.py
import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.models.offre import TypePoste


class OffreBase(BaseModel):
    titre: str
    description: str | None = None
    type_poste: TypePoste
    url_source: str | None = None
    date_publication: date | None = None
    active: bool = True


class OffreRead(OffreBase):
    id: uuid.UUID
    agence_id: uuid.UUID
    date_scrappee: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OffreList(BaseModel):
    items: list[OffreRead]
    total: int
    page: int
    limit: int
    pages: int
```

```python
# backend/app/schemas/avis.py
import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.models.avis import SourceAvis


class AvisRead(BaseModel):
    id: uuid.UUID
    agence_id: uuid.UUID
    source: SourceAvis
    note: float
    texte: str | None = None
    mentionne_travaux: bool = False
    mentionne_reactivite: bool = False
    date_avis: date | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class AvisList(BaseModel):
    items: list[AvisRead]
    total: int
    page: int
    limit: int
    pages: int
```

```python
# backend/app/schemas/insight.py
import uuid
from datetime import datetime

from pydantic import BaseModel


class InsightRead(BaseModel):
    id: uuid.UUID
    agence_id: uuid.UUID
    score_besoin: int
    signaux: dict | None = None
    ratio_lots_collab: float | None = None
    turnover_score: float | None = None
    avis_negatifs_travaux: int | None = None
    croissance_parc: float | None = None
    has_service_travaux: bool = False
    recommandation: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InsightList(BaseModel):
    items: list[InsightRead]
    total: int
    page: int
    limit: int
    pages: int
```

```python
# backend/app/schemas/scraping_job.py
import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.scraping_job import JobStatut, JobType


class ScrapingJobCreate(BaseModel):
    type: JobType = JobType.manuel
    cron_expression: str | None = None


class ScrapingJobRead(BaseModel):
    id: uuid.UUID
    type: JobType
    cron_expression: str | None = None
    statut: JobStatut
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    nb_agences_scrappees: int
    erreurs: dict | None = None

    class Config:
        from_attributes = True


class ScrapingJobList(BaseModel):
    items: list[ScrapingJobRead]
    total: int
    page: int
    limit: int
    pages: int
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/
git commit -m "feat: pydantic schemas for all entities with pagination"
```

---

### Task 5: Agences API Endpoint

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/agences.py`
- Modify: `backend/app/main.py` — add router
- Create: `backend/tests/test_api_agences.py`

- [ ] **Step 1: Write failing test for GET /api/agences**

```python
# backend/tests/test_api_agences.py
import uuid

from fastapi.testclient import TestClient

from app.db.database import Base
from app.db.deps import get_db
from app.main import app
from tests.conftest import TestingSessionLocal, engine


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_function():
    Base.metadata.create_all(bind=engine)


def teardown_function():
    Base.metadata.drop_all(bind=engine)


def test_list_agences_empty():
    response = client.get("/api/agences")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_list_agences_with_data():
    db = TestingSessionLocal()
    from app.models.agence import Agence

    agence = Agence(id=uuid.uuid4(), nom="Foncia Paris", ville="Paris", region="Île-de-France")
    db.add(agence)
    db.commit()
    db.close()

    response = client.get("/api/agences")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["nom"] == "Foncia Paris"


def test_list_agences_filter_by_ville():
    db = TestingSessionLocal()
    from app.models.agence import Agence

    db.add(Agence(nom="A1", ville="Paris"))
    db.add(Agence(nom="A2", ville="Lyon"))
    db.commit()
    db.close()

    response = client.get("/api/agences?ville=Paris")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["ville"] == "Paris"


def test_get_agence_detail():
    db = TestingSessionLocal()
    from app.models.agence import Agence

    agence_id = uuid.uuid4()
    db.add(Agence(id=agence_id, nom="Nexity Lyon"))
    db.commit()
    db.close()

    response = client.get(f"/api/agences/{agence_id}")
    assert response.status_code == 200
    assert response.json()["nom"] == "Nexity Lyon"


def test_get_agence_not_found():
    response = client.get(f"/api/agences/{uuid.uuid4()}")
    assert response.status_code == 404
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
cd backend && python -m pytest tests/test_api_agences.py -v
```

- [ ] **Step 3: Implement agences API**

```python
# backend/app/api/agences.py
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.agence import Agence
from app.schemas.agence import AgenceList, AgenceRead

router = APIRouter(prefix="/api/agences", tags=["agences"])


@router.get("", response_model=AgenceList)
def list_agences(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    ville: str | None = None,
    region: str | None = None,
    nb_lots_min: int | None = None,
    nb_lots_max: int | None = None,
    db: Session = Depends(get_db),
):
    query = select(Agence)
    count_query = select(func.count()).select_from(Agence)

    if ville:
        query = query.where(Agence.ville == ville)
        count_query = count_query.where(Agence.ville == ville)
    if region:
        query = query.where(Agence.region == region)
        count_query = count_query.where(Agence.region == region)
    if nb_lots_min is not None:
        query = query.where(Agence.nb_lots_geres >= nb_lots_min)
        count_query = count_query.where(Agence.nb_lots_geres >= nb_lots_min)
    if nb_lots_max is not None:
        query = query.where(Agence.nb_lots_geres <= nb_lots_max)
        count_query = count_query.where(Agence.nb_lots_geres <= nb_lots_max)

    total = db.execute(count_query).scalar()
    offset = (page - 1) * limit
    results = db.execute(query.offset(offset).limit(limit)).scalars().all()
    pages = (total + limit - 1) // limit

    return AgenceList(items=results, total=total, page=page, limit=limit, pages=pages)


@router.get("/{agence_id}/snapshots")
def list_agence_snapshots(
    agence_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    from app.models.agence_snapshot import AgenceSnapshot

    query = select(AgenceSnapshot).where(AgenceSnapshot.agence_id == agence_id).order_by(AgenceSnapshot.created_at.desc())
    count_query = select(func.count()).select_from(AgenceSnapshot).where(AgenceSnapshot.agence_id == agence_id)

    total = db.execute(count_query).scalar()
    offset = (page - 1) * limit
    results = db.execute(query.offset(offset).limit(limit)).scalars().all()
    pages = (total + limit - 1) // limit

    return {"items": results, "total": total, "page": page, "limit": limit, "pages": pages}


@router.get("/{agence_id}", response_model=AgenceRead)
def get_agence(agence_id: uuid.UUID, db: Session = Depends(get_db)):
    agence = db.get(Agence, agence_id)
    if not agence:
        raise HTTPException(status_code=404, detail="Agence not found")
    return agence
```

- [ ] **Step 4: Register router in main.py**

Add to `backend/app/main.py`:

```python
from app.api.agences import router as agences_router

app.include_router(agences_router)
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
cd backend && python -m pytest tests/test_api_agences.py -v
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/ backend/tests/test_api_agences.py backend/app/main.py
git commit -m "feat: GET /api/agences with filters and pagination"
```

---

### Task 6: Offres, Avis, Insights, Scraping, Export API Endpoints

**Files:**
- Create: `backend/app/api/offres.py`
- Create: `backend/app/api/avis.py`
- Create: `backend/app/api/insights.py`
- Create: `backend/app/api/scraping.py`
- Create: `backend/app/api/export.py`
- Create: `backend/app/services/export_service.py`
- Modify: `backend/app/main.py` — add all routers
- Create: `backend/tests/test_api_offres.py`
- Create: `backend/tests/test_api_insights.py`
- Create: `backend/tests/test_api_scraping.py`
- Create: `backend/tests/test_api_export.py`

This task follows the same TDD pattern as Task 5 for each endpoint. Key endpoints:

- [ ] **Step 1: Write failing tests for offres API**

Test `GET /api/offres` with filters (type_poste, region, date), `GET /api/agences/{id}/offres`.

- [ ] **Step 2: Implement offres API**

```python
# backend/app/api/offres.py
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.agence import Agence
from app.models.offre import OffreEmploi, TypePoste
from app.schemas.offre import OffreList

router = APIRouter(prefix="/api", tags=["offres"])


@router.get("/offres", response_model=OffreList)
def list_offres(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    type_poste: TypePoste | None = None,
    region: str | None = None,
    active: bool | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
):
    query = select(OffreEmploi)
    count_query = select(func.count()).select_from(OffreEmploi)

    if type_poste:
        query = query.where(OffreEmploi.type_poste == type_poste)
        count_query = count_query.where(OffreEmploi.type_poste == type_poste)
    if active is not None:
        query = query.where(OffreEmploi.active == active)
        count_query = count_query.where(OffreEmploi.active == active)
    if region:
        query = query.join(Agence).where(Agence.region == region)
        count_query = count_query.join(Agence).where(Agence.region == region)
    if date_from:
        query = query.where(OffreEmploi.date_publication >= date_from)
        count_query = count_query.where(OffreEmploi.date_publication >= date_from)
    if date_to:
        query = query.where(OffreEmploi.date_publication <= date_to)
        count_query = count_query.where(OffreEmploi.date_publication <= date_to)

    total = db.execute(count_query).scalar()
    offset = (page - 1) * limit
    results = db.execute(query.offset(offset).limit(limit)).scalars().all()
    pages = (total + limit - 1) // limit

    return OffreList(items=results, total=total, page=page, limit=limit, pages=pages)


@router.get("/agences/{agence_id}/offres", response_model=OffreList)
def list_agence_offres(
    agence_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = select(OffreEmploi).where(OffreEmploi.agence_id == agence_id)
    count_query = (
        select(func.count())
        .select_from(OffreEmploi)
        .where(OffreEmploi.agence_id == agence_id)
    )

    total = db.execute(count_query).scalar()
    offset = (page - 1) * limit
    results = db.execute(query.offset(offset).limit(limit)).scalars().all()
    pages = (total + limit - 1) // limit

    return OffreList(items=results, total=total, page=page, limit=limit, pages=pages)
```

- [ ] **Step 3: Run offres tests — expect PASS**
- [ ] **Step 4: Commit offres API**

- [ ] **Step 5: Write failing tests + implement avis API**

```python
# backend/app/api/avis.py
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.avis import Avis, SourceAvis
from app.schemas.avis import AvisList

router = APIRouter(prefix="/api", tags=["avis"])


@router.get("/agences/{agence_id}/avis", response_model=AvisList)
def list_agence_avis(
    agence_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    source: SourceAvis | None = None,
    note_max: float | None = None,
    db: Session = Depends(get_db),
):
    query = select(Avis).where(Avis.agence_id == agence_id)
    count_query = select(func.count()).select_from(Avis).where(Avis.agence_id == agence_id)

    if source:
        query = query.where(Avis.source == source)
        count_query = count_query.where(Avis.source == source)
    if note_max is not None:
        query = query.where(Avis.note <= note_max)
        count_query = count_query.where(Avis.note <= note_max)

    total = db.execute(count_query).scalar()
    offset = (page - 1) * limit
    results = db.execute(query.order_by(Avis.date_avis.desc()).offset(offset).limit(limit)).scalars().all()
    pages = (total + limit - 1) // limit

    return AvisList(items=results, total=total, page=page, limit=limit, pages=pages)
```

```python
# backend/tests/test_api_avis.py
import uuid

from fastapi.testclient import TestClient

from app.db.database import Base
from app.db.deps import get_db
from app.main import app
from tests.conftest import TestingSessionLocal, engine


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_function():
    Base.metadata.create_all(bind=engine)


def teardown_function():
    Base.metadata.drop_all(bind=engine)


def test_list_avis_for_agence():
    db = TestingSessionLocal()
    from app.models.agence import Agence
    from app.models.avis import Avis

    agence_id = uuid.uuid4()
    db.add(Agence(id=agence_id, nom="Test"))
    db.add(Avis(agence_id=agence_id, source="google", note=2.0, texte="Mauvais suivi travaux"))
    db.add(Avis(agence_id=agence_id, source="trustpilot", note=4.0, texte="Bien"))
    db.commit()
    db.close()

    response = client.get(f"/api/agences/{agence_id}/avis")
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_filter_avis_by_source():
    db = TestingSessionLocal()
    from app.models.agence import Agence
    from app.models.avis import Avis

    agence_id = uuid.uuid4()
    db.add(Agence(id=agence_id, nom="Test"))
    db.add(Avis(agence_id=agence_id, source="google", note=2.0))
    db.add(Avis(agence_id=agence_id, source="trustpilot", note=4.0))
    db.commit()
    db.close()

    response = client.get(f"/api/agences/{agence_id}/avis?source=google")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_filter_avis_by_note_max():
    db = TestingSessionLocal()
    from app.models.agence import Agence
    from app.models.avis import Avis

    agence_id = uuid.uuid4()
    db.add(Agence(id=agence_id, nom="Test"))
    db.add(Avis(agence_id=agence_id, source="google", note=2.0))
    db.add(Avis(agence_id=agence_id, source="google", note=4.0))
    db.commit()
    db.close()

    response = client.get(f"/api/agences/{agence_id}/avis?note_max=3")
    assert response.status_code == 200
    assert response.json()["total"] == 1
```

- [ ] **Step 6: Commit avis API**

- [ ] **Step 7: Write failing tests + implement insights API**

```python
# backend/app/api/insights.py
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.insight import Insight
from app.schemas.insight import InsightList, InsightRead

router = APIRouter(prefix="/api", tags=["insights"])


@router.get("/insights", response_model=InsightList)
def list_insights(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    score_min: int | None = None,
    db: Session = Depends(get_db),
):
    # Get latest insight per agence (subquery for max created_at per agence)
    latest_subq = (
        select(Insight.agence_id, func.max(Insight.created_at).label("max_date"))
        .group_by(Insight.agence_id)
        .subquery()
    )
    query = (
        select(Insight)
        .join(latest_subq, (Insight.agence_id == latest_subq.c.agence_id) & (Insight.created_at == latest_subq.c.max_date))
        .order_by(Insight.score_besoin.desc())
    )
    count_query = select(func.count()).select_from(query.subquery())

    if score_min is not None:
        query = query.where(Insight.score_besoin >= score_min)

    total = db.execute(count_query).scalar()
    offset = (page - 1) * limit
    results = db.execute(query.offset(offset).limit(limit)).scalars().all()
    pages = (total + limit - 1) // limit

    return InsightList(items=results, total=total, page=page, limit=limit, pages=pages)


@router.get("/agences/{agence_id}/insights/historique", response_model=list[InsightRead])
def get_agence_insights_history(
    agence_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    results = (
        db.execute(
            select(Insight)
            .where(Insight.agence_id == agence_id)
            .order_by(Insight.created_at.asc())
        )
        .scalars()
        .all()
    )
    return results
```

- [ ] **Step 8: Commit insights API**

- [ ] **Step 9: Write failing tests + implement scraping API**

```python
# backend/app/api/scraping.py
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

    # Trigger Celery task asynchronously
    try:
        from tasks.celery_tasks import run_full_scraping
        run_full_scraping.delay(str(job.id))
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
    pages = (total + limit - 1) // limit

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

    # Register with Celery Beat dynamically
    try:
        from tasks.beat_schedule import register_cron
        register_cron(str(job.id), data.cron_expression)
    except Exception:
        pass

    return job


@router.delete("/cron/{job_id}")
def delete_cron(job_id: uuid.UUID, db: Session = Depends(get_db)):
    job = db.get(ScrapingJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.type != JobType.cron:
        raise HTTPException(status_code=400, detail="Not a cron job")

    # Unregister from Celery Beat
    try:
        from tasks.beat_schedule import unregister_cron
        unregister_cron(str(job.id))
    except Exception:
        pass

    db.delete(job)
    db.commit()
    return {"status": "deleted"}
```

```python
# backend/tests/test_api_scraping.py
from fastapi.testclient import TestClient

from app.db.database import Base
from app.db.deps import get_db
from app.main import app
from tests.conftest import TestingSessionLocal, engine


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_function():
    Base.metadata.create_all(bind=engine)


def teardown_function():
    Base.metadata.drop_all(bind=engine)


def test_lancer_scraping():
    response = client.post("/api/scraping/lancer")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "manuel"
    assert data["statut"] == "pending"


def test_list_jobs_empty():
    response = client.get("/api/scraping/jobs")
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_create_and_delete_cron():
    # Create
    response = client.post("/api/scraping/cron", json={"cron_expression": "0 2 * * *"})
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "cron"
    assert data["cron_expression"] == "0 2 * * *"
    job_id = data["id"]

    # Delete
    response = client.delete(f"/api/scraping/cron/{job_id}")
    assert response.status_code == 200
```

- [ ] **Step 10: Commit scraping API**

- [ ] **Step 11: Write failing tests + implement export API**

```python
# backend/app/services/export_service.py
import csv
import io

import openpyxl
from sqlalchemy.orm import Session

from app.models.agence import Agence
from app.models.insight import Insight
from app.models.offre import OffreEmploi


def _write_excel(headers: list[str], rows: list[list]) -> io.BytesIO:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def _write_csv(headers: list[str], rows: list[list]) -> io.StringIO:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    output.seek(0)
    return output


def export_agences(db: Session, format: str) -> io.BytesIO | io.StringIO:
    agences = db.query(Agence).all()
    headers = ["Nom", "Groupe", "Ville", "Région", "Lots gérés", "Collaborateurs",
               "Service travaux", "Note Google", "Note Trustpilot"]
    rows = [[a.nom, a.groupe, a.ville, a.region, a.nb_lots_geres,
             a.nb_collaborateurs, a.a_service_travaux, a.note_google,
             a.note_trustpilot] for a in agences]
    return _write_excel(headers, rows) if format == "excel" else _write_csv(headers, rows)


def export_offres(db: Session, format: str) -> io.BytesIO | io.StringIO:
    offres = db.query(OffreEmploi).all()
    headers = ["Titre", "Type poste", "Agence ID", "Date publication", "Active", "URL"]
    rows = [[o.titre, o.type_poste.value, str(o.agence_id), str(o.date_publication),
             o.active, o.url_source] for o in offres]
    return _write_excel(headers, rows) if format == "excel" else _write_csv(headers, rows)


def export_insights(db: Session, format: str) -> io.BytesIO | io.StringIO:
    insights = db.query(Insight).all()
    headers = ["Agence ID", "Score", "Ratio lots/collab", "Turnover", "Avis négatifs",
               "Croissance parc", "Service travaux", "Recommandation"]
    rows = [[str(i.agence_id), i.score_besoin, i.ratio_lots_collab, i.turnover_score,
             i.avis_negatifs_travaux, i.croissance_parc, i.has_service_travaux,
             i.recommandation] for i in insights]
    return _write_excel(headers, rows) if format == "excel" else _write_csv(headers, rows)
```

```python
# backend/app/api/export.py
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.services.export_service import export_agences, export_insights, export_offres

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/agences/{format}")
def export_agences_route(format: str, db: Session = Depends(get_db)):
    if format not in ("csv", "excel"):
        return {"error": "Format must be 'csv' or 'excel'"}
    data = export_agences(db, format)
    media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == "excel" else "text/csv"
    ext = "xlsx" if format == "excel" else "csv"
    return StreamingResponse(data, media_type=media, headers={"Content-Disposition": f"attachment; filename=agences.{ext}"})


@router.get("/offres/{format}")
def export_offres_route(format: str, db: Session = Depends(get_db)):
    if format not in ("csv", "excel"):
        return {"error": "Format must be 'csv' or 'excel'"}
    data = export_offres(db, format)
    media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == "excel" else "text/csv"
    ext = "xlsx" if format == "excel" else "csv"
    return StreamingResponse(data, media_type=media, headers={"Content-Disposition": f"attachment; filename=offres.{ext}"})


@router.get("/insights/{format}")
def export_insights_route(format: str, db: Session = Depends(get_db)):
    if format not in ("csv", "excel"):
        return {"error": "Format must be 'csv' or 'excel'"}
    data = export_insights(db, format)
    media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == "excel" else "text/csv"
    ext = "xlsx" if format == "excel" else "csv"
    return StreamingResponse(data, media_type=media, headers={"Content-Disposition": f"attachment; filename=insights.{ext}"})
```

```python
# backend/tests/test_api_export.py
import uuid

from fastapi.testclient import TestClient

from app.db.database import Base
from app.db.deps import get_db
from app.main import app
from tests.conftest import TestingSessionLocal, engine


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_function():
    Base.metadata.create_all(bind=engine)


def teardown_function():
    Base.metadata.drop_all(bind=engine)


def test_export_agences_csv():
    db = TestingSessionLocal()
    from app.models.agence import Agence
    db.add(Agence(nom="Test Export", ville="Paris"))
    db.commit()
    db.close()

    response = client.get("/api/export/agences/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "Test Export" in response.text


def test_export_agences_excel():
    response = client.get("/api/export/agences/excel")
    assert response.status_code == 200


def test_export_offres_csv():
    response = client.get("/api/export/offres/csv")
    assert response.status_code == 200


def test_export_insights_csv():
    response = client.get("/api/export/insights/csv")
    assert response.status_code == 200
```

- [ ] **Step 12: Commit export API**

- [ ] **Step 13: Register all routers in main.py and run full test suite**

```bash
cd backend && python -m pytest tests/ -v
```

- [ ] **Step 14: Commit**

```bash
git add backend/
git commit -m "feat: complete REST API (offres, avis, insights, scraping, export)"
```

---

## Chunk 3: Insight Calculator

### Task 7: Insight Calculator Service

**Files:**
- Create: `backend/app/services/insight_calculator.py`
- Create: `backend/tests/test_insight_calculator.py`

- [ ] **Step 1: Write failing test for score calculation**

```python
# backend/tests/test_insight_calculator.py
from app.services.insight_calculator import InsightCalculator


def test_score_ratio_lots_collab_high():
    """Agence with 50 lots per collab vs median of 30 → high ratio score."""
    calc = InsightCalculator(median_lots_per_collab=30.0)
    score = calc.calc_ratio_score(nb_lots=500, nb_collab=10)
    # 50/30 = 1.67 => >median+50% => 30 pts
    assert score == 30


def test_score_ratio_lots_collab_medium():
    calc = InsightCalculator(median_lots_per_collab=30.0)
    score = calc.calc_ratio_score(nb_lots=400, nb_collab=10)
    # 40/30 = 1.33 => >median+25% => 20 pts
    assert score == 20


def test_score_ratio_lots_collab_low():
    calc = InsightCalculator(median_lots_per_collab=30.0)
    score = calc.calc_ratio_score(nb_lots=300, nb_collab=10)
    # 30/30 = 1.0 => at median => 0 pts
    assert score == 0


def test_score_ratio_missing_data():
    calc = InsightCalculator(median_lots_per_collab=30.0)
    score = calc.calc_ratio_score(nb_lots=None, nb_collab=None)
    assert score == 0


def test_score_avis_negatifs():
    calc = InsightCalculator(median_lots_per_collab=30.0)
    score = calc.calc_avis_score(total_avis_negatifs=20, avis_mentionnant_travaux=10)
    # 50% mention travaux => 25 * 0.5 = 12.5 => 13 pts
    assert score == 13


def test_score_turnover():
    calc = InsightCalculator(median_lots_per_collab=30.0)
    assert calc.calc_turnover_score(nb_offres_12_mois=4) == 20
    assert calc.calc_turnover_score(nb_offres_12_mois=3) == 15
    assert calc.calc_turnover_score(nb_offres_12_mois=1) == 5
    assert calc.calc_turnover_score(nb_offres_12_mois=0) == 0


def test_score_croissance():
    calc = InsightCalculator(median_lots_per_collab=30.0)
    assert calc.calc_croissance_score(previous_lots=100, current_lots=115) == 15
    assert calc.calc_croissance_score(previous_lots=100, current_lots=105) == 8
    assert calc.calc_croissance_score(previous_lots=100, current_lots=100) == 0


def test_score_service_travaux():
    calc = InsightCalculator(median_lots_per_collab=30.0)
    assert calc.calc_service_travaux_score(has_service=False) == 10
    assert calc.calc_service_travaux_score(has_service=True) == 0


def test_full_score_calculation():
    calc = InsightCalculator(median_lots_per_collab=30.0)
    result = calc.calculate(
        nb_lots=500,
        nb_collab=10,
        total_avis_negatifs=20,
        avis_mentionnant_travaux=10,
        nb_offres_12_mois=4,
        previous_lots=400,
        current_lots=500,
        has_service_travaux=False,
    )
    assert result["score_besoin"] > 50
    assert "recommandation" in result
    assert "signaux" in result


def test_recommandation_text():
    calc = InsightCalculator(median_lots_per_collab=30.0)
    assert "Forte probabilité" in calc.get_recommandation(80)
    assert "Besoin probable" in calc.get_recommandation(60)
    assert "À surveiller" in calc.get_recommandation(30)
    assert "Pas de besoin" in calc.get_recommandation(10)
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
cd backend && python -m pytest tests/test_insight_calculator.py -v
```

- [ ] **Step 3: Implement InsightCalculator**

```python
# backend/app/services/insight_calculator.py
import math


class InsightCalculator:
    KEYWORDS = [
        "travaux", "artisan", "plombier", "électricien", "devis", "facture",
        "intervention", "réparation", "suivi", "relance", "réactivité",
        "dégât des eaux", "sinistre", "maintenance", "entretien",
    ]

    def __init__(self, median_lots_per_collab: float = 30.0):
        self.median = median_lots_per_collab

    def calc_ratio_score(self, nb_lots: int | None, nb_collab: int | None) -> int:
        if not nb_lots or not nb_collab or nb_collab == 0:
            return 0
        ratio = nb_lots / nb_collab
        if ratio >= self.median * 1.5:
            return 30
        elif ratio >= self.median * 1.25:
            return 20
        elif ratio >= self.median * 1.1:
            return 10
        return 0

    def calc_avis_score(
        self, total_avis_negatifs: int, avis_mentionnant_travaux: int
    ) -> int:
        if total_avis_negatifs == 0:
            return 0
        pct = avis_mentionnant_travaux / total_avis_negatifs
        return min(25, math.ceil(25 * pct))

    def calc_turnover_score(self, nb_offres_12_mois: int) -> int:
        if nb_offres_12_mois > 3:
            return 20
        elif nb_offres_12_mois == 3:
            return 15
        elif nb_offres_12_mois == 2:
            return 10
        elif nb_offres_12_mois == 1:
            return 5
        return 0

    def calc_croissance_score(
        self, previous_lots: int | None, current_lots: int | None
    ) -> int:
        if not previous_lots or not current_lots or previous_lots == 0:
            return 0
        growth = (current_lots - previous_lots) / previous_lots
        if growth >= 0.10:
            return 15
        elif growth >= 0.05:
            return 8
        return 0

    def calc_service_travaux_score(self, has_service: bool) -> int:
        return 0 if has_service else 10

    def get_recommandation(self, score: int) -> str:
        if score > 75:
            return "Forte probabilité de besoin — agence sous-dimensionnée avec signaux multiples"
        elif score > 50:
            return "Besoin probable — plusieurs indices convergents"
        elif score > 25:
            return "À surveiller — quelques signaux détectés"
        return "Pas de besoin identifié actuellement"

    def calculate(
        self,
        nb_lots: int | None,
        nb_collab: int | None,
        total_avis_negatifs: int,
        avis_mentionnant_travaux: int,
        nb_offres_12_mois: int,
        previous_lots: int | None,
        current_lots: int | None,
        has_service_travaux: bool,
    ) -> dict:
        ratio = self.calc_ratio_score(nb_lots, nb_collab)
        avis = self.calc_avis_score(total_avis_negatifs, avis_mentionnant_travaux)
        turnover = self.calc_turnover_score(nb_offres_12_mois)
        croissance = self.calc_croissance_score(previous_lots, current_lots)
        service = self.calc_service_travaux_score(has_service_travaux)

        score = ratio + avis + turnover + croissance + service

        return {
            "score_besoin": score,
            "signaux": {
                "ratio_lots_collab": ratio,
                "avis_negatifs_travaux": avis,
                "turnover": turnover,
                "croissance_parc": croissance,
                "absence_service_travaux": service,
            },
            "ratio_lots_collab": (nb_lots / nb_collab) if nb_lots and nb_collab else None,
            "turnover_score": float(nb_offres_12_mois),
            "avis_negatifs_travaux": avis_mentionnant_travaux,
            "croissance_parc": (
                ((current_lots - previous_lots) / previous_lots * 100)
                if previous_lots and current_lots
                else None
            ),
            "has_service_travaux": has_service_travaux,
            "recommandation": self.get_recommandation(score),
        }
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
cd backend && python -m pytest tests/test_insight_calculator.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/insight_calculator.py backend/tests/test_insight_calculator.py
git commit -m "feat: insight calculator with 5 weighted signals and recommendations"
```

---

## Chunk 4: Scrapping Engine

### Task 8: Scrapy Project Scaffolding

**Files:**
- Create: `scrapper/requirements.txt`
- Create: `scrapper/Dockerfile`
- Create: `scrapper/scrapy.cfg`
- Create: `scrapper/scrapper/__init__.py`
- Create: `scrapper/scrapper/settings.py`
- Create: `scrapper/scrapper/items.py`
- Create: `scrapper/scrapper/middlewares.py`
- Create: `scrapper/scrapper/config/selectors.yaml`
- Create: `scrapper/scrapper/config/proxies.yaml`

- [ ] **Step 1: Create scrapper/scrapy.cfg**

```ini
# scrapper/scrapy.cfg
[settings]
default = scrapper.settings

[deploy]
project = scrapper
```

- [ ] **Step 2: Create scrapper/requirements.txt**

```
scrapy==2.12.0
playwright==1.49.1
scrapy-playwright==0.0.43
beautifulsoup4==4.12.3
sqlalchemy==2.0.36
psycopg2-binary==2.9.10
celery[redis]==5.4.0
pyyaml==6.0.2
```

- [ ] **Step 2: Create scrapper/Dockerfile**

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium && playwright install-deps chromium

COPY . .

ENV PYTHONPATH=/app:/backend

CMD ["celery", "-A", "tasks.celery_app", "worker", "--loglevel=info"]
```

- [ ] **Step 3: Create scrapper/scrapper/items.py**

```python
import scrapy


class AgenceItem(scrapy.Item):
    nom = scrapy.Field()
    groupe = scrapy.Field()
    adresse = scrapy.Field()
    ville = scrapy.Field()
    region = scrapy.Field()
    code_postal = scrapy.Field()
    site_web = scrapy.Field()
    nb_lots_geres = scrapy.Field()
    nb_collaborateurs = scrapy.Field()
    a_service_travaux = scrapy.Field()


class OffreItem(scrapy.Item):
    agence_nom = scrapy.Field()
    titre = scrapy.Field()
    description = scrapy.Field()
    type_poste = scrapy.Field()
    url_source = scrapy.Field()
    date_publication = scrapy.Field()


class AvisItem(scrapy.Item):
    agence_nom = scrapy.Field()
    source = scrapy.Field()  # "google" or "trustpilot"
    note = scrapy.Field()
    texte = scrapy.Field()
    date_avis = scrapy.Field()
```

- [ ] **Step 4: Create scrapper/scrapper/settings.py**

```python
BOT_NAME = "scrapper"
SPIDER_MODULES = ["scrapper.spiders"]
NEWSPIDER_MODULE = "scrapper.spiders"

ROBOTSTXT_OBEY = True

DOWNLOAD_DELAY = 3
RANDOMIZE_DOWNLOAD_DELAY = True

CONCURRENT_REQUESTS = 4
CONCURRENT_REQUESTS_PER_DOMAIN = 2

ITEM_PIPELINES = {
    "scrapper.pipelines.cleaning.CleaningPipeline": 100,
    "scrapper.pipelines.snapshot.SnapshotPipeline": 200,
    "scrapper.pipelines.database.DatabasePipeline": 300,
}

DOWNLOADER_MIDDLEWARES = {
    "scrapper.middlewares.RotateUserAgentMiddleware": 400,
    "scrapper.middlewares.ProxyRotationMiddleware": 410,
}

DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {"headless": True}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
]
```

- [ ] **Step 5: Create scrapper/scrapper/middlewares.py**

```python
import random

import yaml


class RotateUserAgentMiddleware:
    def __init__(self, user_agents):
        self.user_agents = user_agents

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.getlist("USER_AGENTS"))

    def process_request(self, request, spider):
        request.headers["User-Agent"] = random.choice(self.user_agents)


class ProxyRotationMiddleware:
    def __init__(self):
        self.proxies = []
        try:
            with open("scrapper/config/proxies.yaml") as f:
                data = yaml.safe_load(f)
                self.proxies = data.get("proxies", [])
        except FileNotFoundError:
            pass

    def process_request(self, request, spider):
        if self.proxies:
            proxy = random.choice(self.proxies)
            request.meta["proxy"] = proxy
```

- [ ] **Step 6: Create config files**

```yaml
# scrapper/scrapper/config/selectors.yaml
# CSS/XPath selectors per site — update without code changes
fnaim:
  agence_list: ".annuaire-results .card"
  nom: ".card-title::text"
  adresse: ".card-address::text"
  ville: ".card-city::text"

foncia:
  careers_list: ".job-listing"
  titre: ".job-title::text"
  description: ".job-description::text"
```

```yaml
# scrapper/scrapper/config/proxies.yaml
# Add proxies here — one per line
proxies: []
#  - http://user:pass@proxy1:8080
#  - http://user:pass@proxy2:8080
```

- [ ] **Step 7: Commit**

```bash
git add scrapper/
git commit -m "feat: scrapy project scaffolding with items, middlewares, config"
```

---

### Task 9: Pipelines (Cleaning, Snapshot, Database)

**Files:**
- Create: `scrapper/scrapper/pipelines/__init__.py`
- Create: `scrapper/scrapper/pipelines/cleaning.py`
- Create: `scrapper/scrapper/pipelines/snapshot.py`
- Create: `scrapper/scrapper/pipelines/database.py`
- Create: `scrapper/tests/test_pipelines.py`

- [ ] **Step 1: Write failing test for cleaning pipeline**

```python
# scrapper/tests/test_pipelines.py
from scrapper.items import AgenceItem, AvisItem
from scrapper.pipelines.cleaning import CleaningPipeline

TRAVAUX_KEYWORDS = [
    "travaux", "artisan", "plombier", "électricien", "devis", "facture",
    "intervention", "réparation", "suivi", "relance", "réactivité",
    "dégât des eaux", "sinistre", "maintenance", "entretien",
]


def test_cleaning_normalizes_agence_name():
    pipeline = CleaningPipeline()
    item = AgenceItem(nom="  FONCIA  paris 15  ", ville="  Paris ")
    result = pipeline.process_item(item, None)
    assert result["nom"] == "Foncia Paris 15"
    assert result["ville"] == "Paris"


def test_cleaning_detects_travaux_keywords():
    pipeline = CleaningPipeline()
    item = AvisItem(
        agence_nom="Test",
        source="google",
        note=2.0,
        texte="Les travaux n'avancent pas, impossible de joindre l'artisan",
    )
    result = pipeline.process_item(item, None)
    assert result.get("mentionne_travaux") is True


def test_cleaning_detects_reactivite_keywords():
    pipeline = CleaningPipeline()
    item = AvisItem(
        agence_nom="Test",
        source="google",
        note=1.0,
        texte="Aucune réactivité, pas de suivi des relances",
    )
    result = pipeline.process_item(item, None)
    assert result.get("mentionne_reactivite") is True
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
cd scrapper && python -m pytest tests/test_pipelines.py -v
```

- [ ] **Step 3: Implement CleaningPipeline**

```python
# scrapper/scrapper/pipelines/cleaning.py
import re

from scrapper.items import AgenceItem, AvisItem

TRAVAUX_KEYWORDS = [
    "travaux", "artisan", "plombier", "électricien", "devis", "facture",
    "intervention", "réparation", "suivi", "relance",
    "dégât des eaux", "sinistre", "maintenance", "entretien",
]

REACTIVITE_KEYWORDS = ["réactivité", "réactif", "relance", "suivi", "joignable"]


class CleaningPipeline:
    def process_item(self, item, spider):
        if isinstance(item, AgenceItem):
            return self._clean_agence(item)
        elif isinstance(item, AvisItem):
            return self._clean_avis(item)
        return item

    def _clean_agence(self, item):
        if item.get("nom"):
            item["nom"] = " ".join(item["nom"].strip().split()).title()
        if item.get("ville"):
            item["ville"] = item["ville"].strip().title()
        if item.get("region"):
            item["region"] = item["region"].strip()
        return item

    def _clean_avis(self, item):
        texte = (item.get("texte") or "").lower()
        item["mentionne_travaux"] = any(kw in texte for kw in TRAVAUX_KEYWORDS)
        item["mentionne_reactivite"] = any(kw in texte for kw in REACTIVITE_KEYWORDS)
        return item
```

- [ ] **Step 4: Run test — expect PASS**
- [ ] **Step 5: Implement SnapshotPipeline and DatabasePipeline**

```python
# scrapper/scrapper/pipelines/snapshot.py
from scrapper.items import AgenceItem


class SnapshotPipeline:
    """Marks agence items for snapshot creation in the database pipeline."""

    def process_item(self, item, spider):
        if isinstance(item, AgenceItem):
            item["_create_snapshot"] = True
        return item
```

```python
# scrapper/scrapper/pipelines/database.py
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://needscrapper:needscrapper@db:5432/needscrapper"
)


class DatabasePipeline:
    def open_spider(self, spider):
        engine = create_engine(DATABASE_URL)
        self.Session = sessionmaker(bind=engine)

    def process_item(self, item, spider):
        # Import here to avoid circular imports at module level
        from scrapper.items import AgenceItem, AvisItem, OffreItem

        session = self.Session()
        try:
            if isinstance(item, AgenceItem):
                self._upsert_agence(session, item)
            elif isinstance(item, OffreItem):
                self._insert_offre(session, item)
            elif isinstance(item, AvisItem):
                self._insert_avis(session, item)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
        return item

    def _upsert_agence(self, session, item):
        from datetime import datetime
        import sys
        sys.path.insert(0, "/backend")
        from app.models.agence import Agence
        from app.models.agence_snapshot import AgenceSnapshot

        agence = session.query(Agence).filter(Agence.nom == item["nom"]).first()
        if agence:
            for field in ["groupe", "adresse", "ville", "region", "code_postal",
                          "site_web", "nb_lots_geres", "nb_collaborateurs", "a_service_travaux"]:
                if item.get(field) is not None:
                    setattr(agence, field, item[field])
            agence.derniere_maj = datetime.utcnow()
        else:
            agence = Agence(
                nom=item["nom"],
                groupe=item.get("groupe"),
                adresse=item.get("adresse"),
                ville=item.get("ville"),
                region=item.get("region"),
                code_postal=item.get("code_postal"),
                site_web=item.get("site_web"),
                nb_lots_geres=item.get("nb_lots_geres"),
                nb_collaborateurs=item.get("nb_collaborateurs"),
                a_service_travaux=item.get("a_service_travaux", False),
                derniere_maj=datetime.utcnow(),
            )
            session.add(agence)
            session.flush()

        # Create snapshot if flagged
        if item.get("_create_snapshot"):
            snapshot = AgenceSnapshot(
                agence_id=agence.id,
                nb_lots_geres=agence.nb_lots_geres,
                nb_collaborateurs=agence.nb_collaborateurs,
                a_service_travaux=agence.a_service_travaux,
                note_google=agence.note_google,
                note_trustpilot=agence.note_trustpilot,
            )
            session.add(snapshot)

    def _insert_offre(self, session, item):
        import sys
        sys.path.insert(0, "/backend")
        from app.models.agence import Agence
        from app.models.offre import OffreEmploi

        agence = session.query(Agence).filter(Agence.nom == item["agence_nom"]).first()
        if not agence:
            return

        offre = OffreEmploi(
            agence_id=agence.id,
            titre=item["titre"],
            description=item.get("description"),
            type_poste=item.get("type_poste", "autre"),
            url_source=item.get("url_source"),
            date_publication=item.get("date_publication"),
            active=True,
        )
        session.add(offre)

    def _insert_avis(self, session, item):
        import sys
        sys.path.insert(0, "/backend")
        from app.models.agence import Agence
        from app.models.avis import Avis

        agence = session.query(Agence).filter(Agence.nom == item["agence_nom"]).first()
        if not agence:
            return

        avis = Avis(
            agence_id=agence.id,
            source=item["source"],
            note=item["note"],
            texte=item.get("texte"),
            mentionne_travaux=item.get("mentionne_travaux", False),
            mentionne_reactivite=item.get("mentionne_reactivite", False),
            date_avis=item.get("date_avis"),
        )
        session.add(avis)
```

- [ ] **Step 6: Commit**

```bash
git add scrapper/
git commit -m "feat: scrapy pipelines (cleaning, snapshot, database)"
```

---

### Task 10: Spiders

**Files:**
- Create: `scrapper/scrapper/spiders/__init__.py`
- Create: `scrapper/scrapper/spiders/agence_info.py`
- Create: `scrapper/scrapper/spiders/offre_emploi.py`
- Create: `scrapper/scrapper/spiders/google_reviews.py`
- Create: `scrapper/scrapper/spiders/trustpilot.py`

- [ ] **Step 1: Implement AgenceInfoSpider**

```python
# scrapper/scrapper/spiders/agence_info.py
import scrapy
import yaml

from scrapper.items import AgenceItem


class AgenceInfoSpider(scrapy.Spider):
    name = "agence_info"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with open("scrapper/config/selectors.yaml") as f:
            self.selectors = yaml.safe_load(f)

    def start_requests(self):
        # FNAIM directory as starting point
        urls = [
            "https://www.fnaim.fr/annuaire",
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        sel = self.selectors.get("fnaim", {})
        for card in response.css(sel.get("agence_list", ".card")):
            item = AgenceItem()
            item["nom"] = card.css(sel.get("nom", ".title::text")).get("")
            item["adresse"] = card.css(sel.get("adresse", ".address::text")).get("")
            item["ville"] = card.css(sel.get("ville", ".city::text")).get("")
            item["site_web"] = card.css("a::attr(href)").get("")
            yield item

        # Follow pagination
        next_page = response.css("a.next::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)
```

- [ ] **Step 2: Implement OffreEmploiSpider**

```python
# scrapper/scrapper/spiders/offre_emploi.py
import scrapy

from scrapper.items import OffreItem


class OffreEmploiSpider(scrapy.Spider):
    name = "offre_emploi"

    def __init__(self, agence_urls=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agence_urls = agence_urls or []

    def start_requests(self):
        for entry in self.agence_urls:
            yield scrapy.Request(
                url=entry["url"],
                callback=self.parse,
                meta={"agence_nom": entry["nom"]},
            )

    def parse(self, response):
        agence_nom = response.meta["agence_nom"]

        # Look for common career page patterns
        career_links = response.css(
            'a[href*="recrutement"], a[href*="carriere"], '
            'a[href*="emploi"], a[href*="rejoindre"]'
        )
        for link in career_links:
            yield response.follow(
                link, self.parse_careers, meta={"agence_nom": agence_nom}
            )

    def parse_careers(self, response):
        agence_nom = response.meta["agence_nom"]
        # Extract job listings — selectors vary per site
        for job in response.css(".job-listing, .offre, .poste"):
            item = OffreItem()
            item["agence_nom"] = agence_nom
            item["titre"] = job.css("h2::text, h3::text, .titre::text").get("")
            item["description"] = job.css(".description::text, p::text").get("")
            item["url_source"] = response.url
            item["type_poste"] = self._classify_poste(item["titre"])
            yield item

    def _classify_poste(self, titre: str) -> str:
        titre_lower = titre.lower()
        if "assistant" in titre_lower and "copropriété" in titre_lower:
            return "assistant_copropriete"
        elif "gestionnaire" in titre_lower and "copropriété" in titre_lower:
            return "gestionnaire_copropriete"
        elif "assistant" in titre_lower and "locati" in titre_lower:
            return "assistant_gestion_locative"
        elif "gestionnaire" in titre_lower and "locati" in titre_lower:
            return "gestionnaire_locatif"
        return "autre"
```

- [ ] **Step 3: Implement GoogleReviewsSpider** (uses Playwright for JS rendering)

```python
# scrapper/scrapper/spiders/google_reviews.py
import scrapy

from scrapper.items import AvisItem


class GoogleReviewsSpider(scrapy.Spider):
    name = "google_reviews"

    def __init__(self, agence_names=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agence_names = agence_names or []

    def start_requests(self):
        for name in self.agence_names:
            search_url = f"https://www.google.com/maps/search/{name.replace(' ', '+')}"
            yield scrapy.Request(
                url=search_url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "agence_nom": name,
                },
            )

    async def parse(self, response):
        page = response.meta["playwright_page"]
        agence_nom = response.meta["agence_nom"]

        # Click on reviews tab and scroll to load
        try:
            await page.wait_for_selector('[data-tab-index="1"]', timeout=5000)
            await page.click('[data-tab-index="1"]')
            await page.wait_for_timeout(2000)
        except Exception:
            await page.close()
            return

        # Extract reviews
        reviews = await page.query_selector_all(".jftiEf")
        for review in reviews[:50]:  # Limit to 50 reviews
            try:
                note_el = await review.query_selector(".kvMYJc")
                note_attr = await note_el.get_attribute("aria-label") if note_el else ""
                note = float(note_attr.split("/")[0].replace(",", ".")) if "/" in note_attr else 0

                texte_el = await review.query_selector(".wiI7pd")
                texte = await texte_el.inner_text() if texte_el else ""

                item = AvisItem()
                item["agence_nom"] = agence_nom
                item["source"] = "google"
                item["note"] = note
                item["texte"] = texte
                yield item
            except Exception:
                continue

        await page.close()
```

- [ ] **Step 4: Implement TrustpilotSpider**

```python
# scrapper/scrapper/spiders/trustpilot.py
import scrapy

from scrapper.items import AvisItem


class TrustpilotSpider(scrapy.Spider):
    name = "trustpilot"

    def __init__(self, company_slugs=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.company_slugs = company_slugs or []

    def start_requests(self):
        for entry in self.company_slugs:
            url = f"https://fr.trustpilot.com/review/{entry['slug']}"
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={"agence_nom": entry["nom"]},
            )

    def parse(self, response):
        agence_nom = response.meta["agence_nom"]

        for review in response.css('[data-service-review-card-paper="true"]'):
            note_str = review.css("div[data-service-review-rating]::attr(data-service-review-rating)").get("0")
            texte = review.css("p[data-service-review-text-typography]::text").get("")
            date_str = review.css("time::attr(datetime)").get("")

            item = AvisItem()
            item["agence_nom"] = agence_nom
            item["source"] = "trustpilot"
            item["note"] = float(note_str)
            item["texte"] = texte
            item["date_avis"] = date_str[:10] if date_str else None
            yield item

        # Pagination
        next_page = response.css('a[name="pagination-button-next"]::attr(href)').get()
        if next_page:
            yield response.follow(
                next_page, self.parse, meta={"agence_nom": agence_nom}
            )
```

- [ ] **Step 5: Commit**

```bash
git add scrapper/scrapper/spiders/
git commit -m "feat: 4 scrapy spiders (agence_info, offre_emploi, google_reviews, trustpilot)"
```

---

### Task 11: Celery Tasks & Beat Schedule

**Files:**
- Create: `scrapper/tasks/__init__.py`
- Create: `scrapper/tasks/celery_app.py`
- Create: `scrapper/tasks/celery_tasks.py`
- Create: `scrapper/tasks/beat_schedule.py`

- [ ] **Step 1: Create Celery app**

```python
# scrapper/tasks/celery_app.py
import os

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = Celery("need_scrapper", broker=REDIS_URL, backend=REDIS_URL)
app.config_from_object("tasks.beat_schedule")
app.autodiscover_tasks(["tasks"])
```

- [ ] **Step 2: Create Celery tasks**

```python
# scrapper/tasks/celery_tasks.py
import os
import uuid
from datetime import datetime

from celery import chain
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tasks.celery_app import app

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://needscrapper:needscrapper@db:5432/needscrapper"
)


def get_db_session():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()


@app.task(name="tasks.run_full_scraping")
def run_full_scraping(job_id: str | None = None):
    """Run all spiders sequentially."""
    session = get_db_session()

    # Import here to avoid circular imports
    import sys
    sys.path.insert(0, "/backend")
    from app.models.scraping_job import ScrapingJob, JobStatut

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
    """Run a single spider."""
    process = CrawlerProcess(get_project_settings())
    process.crawl(spider_name)
    process.start()


@app.task(name="tasks.calculate_all_insights")
def calculate_all_insights():
    """Recalculate insights for all agencies after scraping."""
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

    agences = session.query(Agence).all()
    twelve_months_ago = datetime.utcnow() - timedelta(days=365)

    for agence in agences:
        # Signal 1: ratio lots/collab — use current agence data
        nb_lots = agence.nb_lots_geres
        nb_collab = agence.nb_collaborateurs

        # Signal 2: avis negatifs travaux
        total_avis_negatifs = session.query(func.count(Avis.id)).filter(
            Avis.agence_id == agence.id, Avis.note < 3
        ).scalar() or 0
        avis_mentionnant_travaux = session.query(func.count(Avis.id)).filter(
            Avis.agence_id == agence.id, Avis.note < 3, Avis.mentionne_travaux == True
        ).scalar() or 0

        # Signal 3: turnover — count offres in last 12 months
        nb_offres_12_mois = session.query(func.count(OffreEmploi.id)).filter(
            OffreEmploi.agence_id == agence.id,
            OffreEmploi.date_scrappee >= twelve_months_ago,
        ).scalar() or 0

        # Signal 4: croissance parc — compare last 2 snapshots
        snapshots = (
            session.query(AgenceSnapshot)
            .filter(AgenceSnapshot.agence_id == agence.id)
            .order_by(AgenceSnapshot.created_at.desc())
            .limit(2)
            .all()
        )
        current_lots = snapshots[0].nb_lots_geres if len(snapshots) > 0 else None
        previous_lots = snapshots[1].nb_lots_geres if len(snapshots) > 1 else None

        # Signal 5: service travaux
        has_service = agence.a_service_travaux

        # Calculate
        result = calc.calculate(
            nb_lots=nb_lots,
            nb_collab=nb_collab,
            total_avis_negatifs=total_avis_negatifs,
            avis_mentionnant_travaux=avis_mentionnant_travaux,
            nb_offres_12_mois=nb_offres_12_mois,
            previous_lots=previous_lots,
            current_lots=current_lots,
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
```

- [ ] **Step 3: Create beat schedule**

```python
# scrapper/tasks/beat_schedule.py
# Celery Beat configuration with dynamic cron support
import json
import os

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CRON_REGISTRY_KEY = "needscrapper:cron_registry"

beat_schedule = {}
beat_schedule_filename = "celerybeat-schedule"
timezone = "Europe/Paris"


def _get_redis():
    return redis.from_url(REDIS_URL)


def register_cron(job_id: str, cron_expression: str):
    """Register a cron job in Redis for Celery Beat to pick up."""
    r = _get_redis()
    parts = cron_expression.split()
    if len(parts) != 5:
        raise ValueError("Invalid cron expression, expected 5 parts: min hour day month dow")
    r.hset(CRON_REGISTRY_KEY, job_id, json.dumps({
        "minute": parts[0], "hour": parts[1],
        "day_of_month": parts[2], "month_of_year": parts[3],
        "day_of_week": parts[4],
    }))


def unregister_cron(job_id: str):
    """Remove a cron job from Redis."""
    r = _get_redis()
    r.hdel(CRON_REGISTRY_KEY, job_id)


def load_dynamic_schedules():
    """Load all registered crons from Redis into beat_schedule."""
    from celery.schedules import crontab
    r = _get_redis()
    crons = r.hgetall(CRON_REGISTRY_KEY)
    for job_id, schedule_json in crons.items():
        schedule = json.loads(schedule_json)
        beat_schedule[f"cron-{job_id.decode()}"] = {
            "task": "tasks.run_full_scraping",
            "schedule": crontab(**schedule),
            "args": [job_id.decode()],
        }


# Load on import
try:
    load_dynamic_schedules()
except Exception:
    pass  # Redis may not be available at import time
```

- [ ] **Step 4: Commit**

```bash
git add scrapper/tasks/
git commit -m "feat: celery tasks for scraping orchestration and beat schedule"
```

---

## Chunk 5: Frontend Dashboard

### Task 12: Next.js Scaffolding

**Files:**
- Create: `frontend/` (via create-next-app)

- [ ] **Step 1: Create Next.js project**

```bash
cd "/Users/davidkoubi/Documents/Need Scrapper"
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --no-turbopack
```

- [ ] **Step 2: Install dependencies**

```bash
cd frontend
npm install recharts lucide-react
npx shadcn@latest init
npx shadcn@latest add button card table input select badge tabs toast dialog dropdown-menu separator sheet
```

- [ ] **Step 3: Create API client**

```typescript
// frontend/src/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  // Agences
  getAgences: (params?: string) => fetchApi<AgenceList>(`/api/agences?${params || ""}`),
  getAgence: (id: string) => fetchApi<Agence>(`/api/agences/${id}`),
  getAgenceAvis: (id: string) => fetchApi<AvisList>(`/api/agences/${id}/avis`),
  getAgenceOffres: (id: string) => fetchApi<OffreList>(`/api/agences/${id}/offres`),
  getAgenceInsightsHistorique: (id: string) => fetchApi<InsightRead[]>(`/api/agences/${id}/insights/historique`),

  // Offres
  getOffres: (params?: string) => fetchApi<OffreList>(`/api/offres?${params || ""}`),

  // Insights
  getInsights: (params?: string) => fetchApi<InsightList>(`/api/insights?${params || ""}`),

  // Scraping
  lancerScraping: () => fetchApi<ScrapingJobRead>("/api/scraping/lancer", { method: "POST" }),
  getScrapingJobs: () => fetchApi<ScrapingJobList>("/api/scraping/jobs"),
  createCron: (cron: string) =>
    fetchApi<ScrapingJobRead>("/api/scraping/cron", {
      method: "POST",
      body: JSON.stringify({ cron_expression: cron }),
    }),
  deleteCron: (id: string) => fetchApi<void>(`/api/scraping/cron/${id}`, { method: "DELETE" }),

  // Export
  exportAgences: (format: string) => `${API_BASE}/api/export/agences/${format}`,
  exportOffres: (format: string) => `${API_BASE}/api/export/offres/${format}`,
  exportInsights: (format: string) => `${API_BASE}/api/export/insights/${format}`,
};
```

- [ ] **Step 4: Create types**

```typescript
// frontend/src/lib/types.ts
export interface Agence {
  id: string;
  nom: string;
  groupe: string | null;
  adresse: string | null;
  ville: string | null;
  region: string | null;
  code_postal: string | null;
  site_web: string | null;
  nb_lots_geres: number | null;
  nb_collaborateurs: number | null;
  a_service_travaux: boolean;
  note_google: number | null;
  nb_avis_google: number | null;
  note_trustpilot: number | null;
  nb_avis_trustpilot: number | null;
  derniere_maj: string | null;
  created_at: string;
  updated_at: string;
}

export interface AgenceList {
  items: Agence[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface OffreEmploi {
  id: string;
  agence_id: string;
  titre: string;
  description: string | null;
  type_poste: string;
  url_source: string | null;
  date_publication: string | null;
  date_scrappee: string;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface OffreList {
  items: OffreEmploi[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface AvisRead {
  id: string;
  agence_id: string;
  source: "google" | "trustpilot";
  note: number;
  texte: string | null;
  mentionne_travaux: boolean;
  mentionne_reactivite: boolean;
  date_avis: string | null;
  created_at: string;
}

export interface AvisList {
  items: AvisRead[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface InsightRead {
  id: string;
  agence_id: string;
  score_besoin: number;
  signaux: Record<string, number> | null;
  ratio_lots_collab: number | null;
  turnover_score: number | null;
  avis_negatifs_travaux: number | null;
  croissance_parc: number | null;
  has_service_travaux: boolean;
  recommandation: string | null;
  created_at: string;
  updated_at: string;
}

export interface InsightList {
  items: InsightRead[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface ScrapingJobRead {
  id: string;
  type: "manuel" | "cron";
  cron_expression: string | null;
  statut: "pending" | "running" | "done" | "failed";
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  nb_agences_scrappees: number;
  erreurs: Record<string, string> | null;
}

export interface ScrapingJobList {
  items: ScrapingJobRead[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/
git commit -m "feat: next.js scaffolding with shadcn/ui, API client, types"
```

---

### Task 13: Layout & Navigation

**Files:**
- Create: `frontend/src/components/layout/sidebar.tsx`
- Create: `frontend/src/components/layout/header.tsx`
- Modify: `frontend/src/app/layout.tsx`

- [ ] **Step 1: Create sidebar**

```tsx
// frontend/src/components/layout/sidebar.tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Building2,
  BriefcaseBusiness,
  Brain,
  LayoutDashboard,
  ScanSearch,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Vue d'ensemble", href: "/", icon: LayoutDashboard },
  { name: "Agences", href: "/agences", icon: Building2 },
  { name: "Offres d'emploi", href: "/offres", icon: BriefcaseBusiness },
  { name: "Insights", href: "/insights", icon: Brain },
  { name: "Scraping", href: "/scraping", icon: ScanSearch },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-64 flex-col border-r bg-card px-4 py-6">
      <div className="mb-8 px-2">
        <h1 className="text-xl font-bold">Need Scrapper</h1>
        <p className="text-sm text-muted-foreground">Gestion locative & copro</p>
      </div>
      <nav className="flex flex-1 flex-col gap-1">
        {navigation.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
              pathname === item.href
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            )}
          >
            <item.icon className="h-4 w-4" />
            {item.name}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
```

- [ ] **Step 2: Update layout.tsx**

```tsx
// frontend/src/app/layout.tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/sidebar";
import { Toaster } from "@/components/ui/toaster";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Need Scrapper",
  description: "Scrapping & insights pour agences immobilières",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body className={inter.className}>
        <div className="flex h-screen">
          <Sidebar />
          <main className="flex-1 overflow-auto bg-background p-8">
            {children}
          </main>
        </div>
        <Toaster />
      </body>
    </html>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/layout/ frontend/src/app/layout.tsx
git commit -m "feat: dashboard layout with sidebar navigation"
```

---

### Task 14: Dashboard Overview Page

**Files:**
- Create: `frontend/src/components/cards/kpi-card.tsx`
- Create: `frontend/src/components/charts/sparkline.tsx`
- Modify: `frontend/src/app/page.tsx`

- [ ] **Step 1: Create KPI card component**

```tsx
// frontend/src/components/cards/kpi-card.tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { type LucideIcon } from "lucide-react";

interface KpiCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon: LucideIcon;
  trend?: number;
}

export function KpiCard({ title, value, description, icon: Icon, trend }: KpiCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground">{description}</p>
        )}
        {trend !== undefined && (
          <p className={`text-xs ${trend >= 0 ? "text-green-600" : "text-red-600"}`}>
            {trend >= 0 ? "+" : ""}{trend}% vs dernier scrapping
          </p>
        )}
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 2: Create overview page**

```tsx
// frontend/src/app/page.tsx
"use client";

import { useEffect, useState } from "react";
import { Building2, BriefcaseBusiness, Brain, AlertTriangle } from "lucide-react";
import { KpiCard } from "@/components/cards/kpi-card";
import { api } from "@/lib/api";

export default function DashboardPage() {
  const [stats, setStats] = useState({
    totalAgences: 0,
    offresActives: 0,
    insightsHigh: 0,
  });

  useEffect(() => {
    async function loadStats() {
      try {
        const [agences, offres, insightsHigh] = await Promise.all([
          api.getAgences("limit=1"),
          api.getOffres("active=true&limit=1"),
          api.getInsights("score_min=50&limit=1"),
        ]);
        setStats({
          totalAgences: agences.total,
          offresActives: offres.total,
          insightsHigh: insightsHigh.total,
        });
      } catch (e) {
        console.error("Failed to load stats", e);
      }
    }
    loadStats();
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Vue d'ensemble</h2>
        <p className="text-muted-foreground">
          Tableau de bord Need Scrapper
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          title="Agences scrappées"
          value={stats.totalAgences}
          icon={Building2}
        />
        <KpiCard
          title="Offres actives"
          value={stats.offresActives}
          icon={BriefcaseBusiness}
        />
        <KpiCard
          title="Insights score > 50"
          value={stats.insightsHigh}
          icon={Brain}
        />
        <KpiCard
          title="Besoins détectés"
          value={stats.insightsHigh}
          description="Agences avec score élevé"
          icon={AlertTriangle}
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/
git commit -m "feat: dashboard overview page with KPI cards"
```

---

### Task 15: Agences Page (List + Detail)

**Files:**
- Create: `frontend/src/components/tables/agences-table.tsx`
- Create: `frontend/src/app/agences/page.tsx`
- Create: `frontend/src/app/agences/[id]/page.tsx`
- Create: `frontend/src/components/cards/agence-detail-card.tsx`
- Create: `frontend/src/components/charts/score-gauge.tsx`

- [ ] **Step 1: Create agences data table**

Implement with shadcn/ui `Table` component, columns: Nom, Ville, Région, Lots gérés, Collaborateurs, Note Google, Score besoin. Sortable + filterable. Pagination.

- [ ] **Step 2: Create agences list page**

Page with filters sidebar (ville, région, score range) + AgencesTable.

- [ ] **Step 3: Create score gauge component**

```tsx
// frontend/src/components/charts/score-gauge.tsx
interface ScoreGaugeProps {
  score: number;
  size?: "sm" | "md" | "lg";
}

export function ScoreGauge({ score, size = "md" }: ScoreGaugeProps) {
  const getColor = (s: number) => {
    if (s > 75) return "text-red-500";
    if (s > 50) return "text-orange-500";
    if (s > 25) return "text-yellow-500";
    return "text-green-500";
  };

  const dimensions = { sm: "h-12 w-12 text-sm", md: "h-16 w-16 text-lg", lg: "h-24 w-24 text-2xl" };

  return (
    <div className={`flex items-center justify-center rounded-full border-4 ${getColor(score)} ${dimensions[size]} font-bold`}>
      {score}
    </div>
  );
}
```

- [ ] **Step 4: Create agence detail page** with tabs (Infos, Avis, Offres, Insights)
- [ ] **Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat: agences list page with filters and detail page with tabs"
```

---

### Task 16: Offres, Insights, Scraping Pages

**Files:**
- Create: `frontend/src/components/tables/offres-table.tsx`
- Create: `frontend/src/app/offres/page.tsx`
- Create: `frontend/src/components/cards/insight-card.tsx`
- Create: `frontend/src/components/charts/trend-chart.tsx`
- Create: `frontend/src/app/insights/page.tsx`
- Create: `frontend/src/components/tables/jobs-table.tsx`
- Create: `frontend/src/app/scraping/page.tsx`

- [ ] **Step 1: Create offres page** — Table with filters (type_poste, région, active/inactive), export button
- [ ] **Step 2: Commit offres page**

- [ ] **Step 3: Create insight card component**

```tsx
// frontend/src/components/cards/insight-card.tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScoreGauge } from "@/components/charts/score-gauge";
import type { InsightRead } from "@/lib/types";

interface InsightCardProps {
  insight: InsightRead;
  agenceNom: string;
}

export function InsightCard({ insight, agenceNom }: InsightCardProps) {
  const getBadgeVariant = (score: number) => {
    if (score > 75) return "destructive";
    if (score > 50) return "default";
    if (score > 25) return "secondary";
    return "outline";
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="text-base">{agenceNom}</CardTitle>
          <Badge variant={getBadgeVariant(insight.score_besoin)}>
            {insight.recommandation}
          </Badge>
        </div>
        <ScoreGauge score={insight.score_besoin} />
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>Ratio lots/collab: <strong>{insight.ratio_lots_collab?.toFixed(1) || "N/A"}</strong></div>
          <div>Turnover: <strong>{insight.turnover_score || 0} offres</strong></div>
          <div>Avis négatifs travaux: <strong>{insight.avis_negatifs_travaux || 0}</strong></div>
          <div>Croissance parc: <strong>{insight.croissance_parc?.toFixed(1) || 0}%</strong></div>
          <div>Service travaux: <strong>{insight.has_service_travaux ? "Oui" : "Non"}</strong></div>
        </div>
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 4: Create insights page** — Grid of InsightCards, sorted by score descending, with filters
- [ ] **Step 5: Commit insights page**

- [ ] **Step 6: Create trend chart component** (Recharts LineChart for score evolution)

```tsx
// frontend/src/components/charts/trend-chart.tsx
"use client";

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface TrendChartProps {
  data: { date: string; score: number }[];
}

export function TrendChart({ data }: TrendChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis domain={[0, 100]} />
        <Tooltip />
        <Line type="monotone" dataKey="score" stroke="hsl(var(--primary))" strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

- [ ] **Step 7: Create scraping page** — Launch button, cron config dialog, jobs table with status badges
- [ ] **Step 8: Commit scraping page**

- [ ] **Step 9: Create frontend Dockerfile**

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]
```

- [ ] **Step 10: Final commit**

```bash
git add frontend/
git commit -m "feat: complete dashboard (offres, insights, scraping pages + charts)"
```

---

## Chunk 6: Integration & Polish

### Task 17: Docker Compose Integration Test

- [ ] **Step 1: Copy .env.example to .env**

```bash
cp .env.example .env
```

- [ ] **Step 2: Build and start all services**

```bash
docker compose up --build -d
```

- [ ] **Step 3: Run Alembic migrations**

```bash
docker compose exec backend alembic upgrade head
```

- [ ] **Step 4: Verify API health**

```bash
curl http://localhost:8000/api/health
# Expected: {"status":"ok"}
```

- [ ] **Step 5: Verify frontend loads**

Open http://localhost:3000 — should see dashboard with sidebar and KPI cards (all 0).

- [ ] **Step 6: Verify Swagger docs**

Open http://localhost:8000/docs — should see all API endpoints documented.

- [ ] **Step 7: Run backend tests**

```bash
docker compose exec backend python -m pytest tests/ -v
```

- [ ] **Step 8: Commit any fixes**

```bash
git add .
git commit -m "fix: integration fixes for docker-compose deployment"
```

---

### Task 18: End-to-End Smoke Test

- [ ] **Step 1: Manually insert test data via API**

```bash
# Create a test agence via API or direct DB insert
docker compose exec backend python -c "
from app.db.database import SessionLocal
from app.models.agence import Agence
import uuid

db = SessionLocal()
a = Agence(id=uuid.uuid4(), nom='Test Foncia Paris', groupe='Foncia', ville='Paris', region='Île-de-France', nb_lots_geres=400, nb_collaborateurs=8, a_service_travaux=False, note_google=3.1, nb_avis_google=50)
db.add(a)
db.commit()
print(f'Created agence: {a.id}')
"
```

- [ ] **Step 2: Verify data appears in dashboard**

Open http://localhost:3000/agences — should see "Test Foncia Paris" in the table.

- [ ] **Step 3: Test export**

```bash
curl -o test_export.xlsx http://localhost:8000/api/export/agences/excel
# Should download an Excel file
```

- [ ] **Step 4: Test scraping launch**

```bash
curl -X POST http://localhost:8000/api/scraping/lancer
# Should return a ScrapingJob with statut "pending"
```

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "chore: end-to-end smoke test verified"
```
