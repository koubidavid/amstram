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
