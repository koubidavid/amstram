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

    def calc_avis_score(self, total_avis_negatifs: int, avis_mentionnant_travaux: int) -> int:
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

    def calc_croissance_score(self, previous_lots: int | None, current_lots: int | None) -> int:
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
