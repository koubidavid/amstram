import uuid
from datetime import datetime

from app.models.agence import Agence
from app.models.agence_snapshot import AgenceSnapshot
from app.models.offre import OffreEmploi, TypePoste
from app.models.insight import Insight


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


def test_offre_emploi_creation(db_session):
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
        recommandation="Besoin probable",
    )
    db_session.add(insight)
    db_session.commit()

    result = db_session.get(Insight, insight.id)
    assert result.score_besoin == 72
    assert result.signaux["ratio"] == 25


def test_agence_snapshot_creation(db_session):
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
