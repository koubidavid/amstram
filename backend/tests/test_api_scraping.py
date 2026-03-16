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
    response = client.post("/api/scraping/cron", json={"cron_expression": "0 2 * * *"})
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "cron"
    assert data["cron_expression"] == "0 2 * * *"
    job_id = data["id"]

    response = client.delete(f"/api/scraping/cron/{job_id}")
    assert response.status_code == 200
