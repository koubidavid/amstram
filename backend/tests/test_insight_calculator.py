from app.services.insight_calculator import InsightCalculator


def test_score_ratio_lots_collab_high():
    calc = InsightCalculator(median_lots_per_collab=30.0)
    score = calc.calc_ratio_score(nb_lots=500, nb_collab=10)
    assert score == 30


def test_score_ratio_lots_collab_medium():
    calc = InsightCalculator(median_lots_per_collab=30.0)
    score = calc.calc_ratio_score(nb_lots=400, nb_collab=10)
    assert score == 20


def test_score_ratio_lots_collab_low():
    calc = InsightCalculator(median_lots_per_collab=30.0)
    score = calc.calc_ratio_score(nb_lots=300, nb_collab=10)
    assert score == 0


def test_score_ratio_missing_data():
    calc = InsightCalculator(median_lots_per_collab=30.0)
    score = calc.calc_ratio_score(nb_lots=None, nb_collab=None)
    assert score == 0


def test_score_avis_negatifs():
    calc = InsightCalculator(median_lots_per_collab=30.0)
    score = calc.calc_avis_score(total_avis_negatifs=20, avis_mentionnant_travaux=10)
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
        nb_lots=500, nb_collab=10,
        total_avis_negatifs=20, avis_mentionnant_travaux=10,
        nb_offres_12_mois=4,
        previous_lots=400, current_lots=500,
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
