import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scrapper.items import AgenceItem, AvisItem
from scrapper.pipelines.cleaning import CleaningPipeline


def test_cleaning_normalizes_agence_name():
    pipeline = CleaningPipeline()
    item = AgenceItem(nom="  FONCIA  paris 15  ", ville="  Paris ")
    result = pipeline.process_item(item, None)
    assert result["nom"] == "Foncia Paris 15"
    assert result["ville"] == "Paris"


def test_cleaning_detects_travaux_keywords():
    pipeline = CleaningPipeline()
    item = AvisItem(
        agence_nom="Test", source="google", note=2.0,
        texte="Les travaux n'avancent pas, impossible de joindre l'artisan",
    )
    result = pipeline.process_item(item, None)
    assert result.get("mentionne_travaux") is True


def test_cleaning_detects_reactivite_keywords():
    pipeline = CleaningPipeline()
    item = AvisItem(
        agence_nom="Test", source="google", note=1.0,
        texte="Aucune réactivité, pas de suivi des relances",
    )
    result = pipeline.process_item(item, None)
    assert result.get("mentionne_reactivite") is True


def test_cleaning_no_keywords():
    pipeline = CleaningPipeline()
    item = AvisItem(
        agence_nom="Test", source="google", note=5.0,
        texte="Très bonne agence, personnel agréable",
    )
    result = pipeline.process_item(item, None)
    assert result.get("mentionne_travaux") is False
    assert result.get("mentionne_reactivite") is False
