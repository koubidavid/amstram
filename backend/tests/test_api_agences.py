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
