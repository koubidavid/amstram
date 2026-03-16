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
