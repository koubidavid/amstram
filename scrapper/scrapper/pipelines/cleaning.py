TRAVAUX_KEYWORDS = [
    "travaux", "artisan", "plombier", "électricien", "devis", "facture",
    "intervention", "réparation", "suivi", "relance",
    "dégât des eaux", "sinistre", "maintenance", "entretien",
]

REACTIVITE_KEYWORDS = ["réactivité", "réactif", "relance", "suivi", "joignable"]


class CleaningPipeline:
    def process_item(self, item, spider):
        from scrapper.items import AgenceItem, AvisItem

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
