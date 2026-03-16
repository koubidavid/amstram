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

def test_list_offres_empty():
    response = client.get("/api/offres")
    assert response.status_code == 200
    assert response.json()["total"] == 0

def test_list_offres_with_data():
    db = TestingSessionLocal()
    from app.models.agence import Agence
    from app.models.offre import OffreEmploi, TypePoste
    agence = Agence(nom="Test")
    db.add(agence)
    db.flush()
    db.add(OffreEmploi(agence_id=agence.id, titre="Gestionnaire", type_poste=TypePoste.gestionnaire_locatif))
    db.commit()
    db.close()

    response = client.get("/api/offres")
    assert response.status_code == 200
    assert response.json()["total"] == 1
