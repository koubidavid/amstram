import json
import os
import re
import sys

import scrapy

from scrapper.items import AgenceItem

sys.path.insert(0, "/backend")


class AgenceInfoSpider(scrapy.Spider):
    """Scrape French property management agencies from the official government API."""
    name = "agence_info"

    # NAF codes for property management
    # 6831Z = Agences immobilières
    # 6832A = Administration d'immeubles et autres biens immobiliers (gestion locative/syndic)
    NAF_CODES = ["68.31Z", "68.32A"]

    SEARCH_TERMS = [
        "gestion locative",
        "syndic copropriete",
        "gestion immobiliere",
        "administrateur biens",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "DOWNLOAD_HANDLERS": {},
        "TWISTED_REACTOR": None,
        "HTTPERROR_ALLOWED_CODES": [404],
    }

    def start_requests(self):
        # Use the official French government API (recherche-entreprises.api.gouv.fr)
        # This is a free, public API — no authentication needed, no blocking
        for term in self.SEARCH_TERMS:
            for page in range(1, 11):  # 10 pages x 25 results = 250 per term
                url = (
                    f"https://recherche-entreprises.api.gouv.fr/search"
                    f"?q={term}&page={page}&per_page=25"
                    f"&activite_principale=68.32A,68.31Z"
                    f"&etat_administratif=A"  # Only active companies
                )
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_api,
                    meta={"term": term, "page": page},
                )

    def parse_api(self, response):
        term = response.meta["term"]
        page = response.meta["page"]

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON from API for term={term} page={page}")
            return

        results = data.get("results", [])
        self.logger.info(f"[{term}] Page {page}: {len(results)} results (total: {data.get('total_results', '?')})")

        for entry in results:
            item = self._extract_from_api(entry)
            if item:
                yield item

    def _extract_from_api(self, entry):
        try:
            nom = entry.get("nom_complet", "")
            if not nom or len(nom) < 3:
                return None

            # Get the main establishment (siege)
            siege = entry.get("siege", {})
            if not siege:
                return None

            adresse = siege.get("adresse", "")
            code_postal = siege.get("code_postal", "")
            ville = siege.get("libelle_commune", "")
            region = siege.get("libelle_region", "") or self._region_from_cp(code_postal)

            # Check if it's relevant
            activite = siege.get("activite_principale", "")
            libelle_activite = siege.get("libelle_activite_principale", "").lower()

            is_relevant = any(kw in libelle_activite for kw in [
                "administration", "immeubles", "immobilier", "agences",
            ]) or activite in ["68.32A", "68.31Z"]

            if not is_relevant:
                return None

            # Detect group
            groupe = self._detect_groupe(nom)

            # Estimate company size from tranche_effectif_salarie
            tranche = entry.get("tranche_effectif_salarie", "") or siege.get("tranche_effectif_salarie", "")
            nb_collaborateurs = self._estimate_employees(tranche)

            # Detect service travaux from activity description
            nature = entry.get("nature_juridique", "")
            a_service_travaux = "travaux" in nom.lower()

            item = AgenceItem()
            item["nom"] = nom.title()
            item["groupe"] = groupe
            item["adresse"] = adresse
            item["ville"] = ville.title() if ville else ""
            item["region"] = region
            item["code_postal"] = code_postal
            item["site_web"] = ""  # API doesn't provide websites
            item["a_service_travaux"] = a_service_travaux
            item["nb_lots_geres"] = None
            item["nb_collaborateurs"] = nb_collaborateurs
            return item

        except Exception as e:
            self.logger.warning(f"Error extracting entry: {e}")
            return None

    def _detect_groupe(self, nom: str) -> str:
        nom_lower = nom.lower()
        groups = {
            "foncia": "Foncia", "nexity": "Nexity", "citya": "Citya",
            "oralia": "Oralia", "immo de france": "Immo de France",
            "sergic": "Sergic", "lamy": "Lamy", "laforêt": "Laforêt",
            "century 21": "Century 21", "guy hoquet": "Guy Hoquet",
            "square habitat": "Square Habitat", "gestrim": "Gestrim",
            "icade": "Icade", "kaufman": "Kaufman & Broad",
        }
        for key, value in groups.items():
            if key in nom_lower:
                return value
        return ""

    def _estimate_employees(self, tranche: str) -> int | None:
        """Convert INSEE employee range code to an estimate."""
        mapping = {
            "00": 0, "01": 1, "02": 4, "03": 8, "11": 15,
            "12": 30, "21": 75, "22": 150, "31": 350, "32": 750,
            "41": 1500, "42": 3500, "51": 7500, "52": 9999,
        }
        return mapping.get(tranche)

    def _region_from_cp(self, cp: str) -> str:
        if not cp or len(cp) < 2:
            return ""
        dept = cp[:2]
        regions = {
            "75": "Île-de-France", "77": "Île-de-France", "78": "Île-de-France",
            "91": "Île-de-France", "92": "Île-de-France", "93": "Île-de-France",
            "94": "Île-de-France", "95": "Île-de-France",
            "13": "PACA", "83": "PACA", "06": "PACA", "84": "PACA",
            "69": "Auvergne-Rhône-Alpes", "38": "Auvergne-Rhône-Alpes",
            "42": "Auvergne-Rhône-Alpes", "63": "Auvergne-Rhône-Alpes",
            "31": "Occitanie", "34": "Occitanie", "30": "Occitanie", "66": "Occitanie",
            "33": "Nouvelle-Aquitaine", "87": "Nouvelle-Aquitaine",
            "44": "Pays de la Loire", "49": "Pays de la Loire",
            "35": "Bretagne", "29": "Bretagne", "56": "Bretagne",
            "59": "Hauts-de-France", "62": "Hauts-de-France", "80": "Hauts-de-France",
            "67": "Grand Est", "57": "Grand Est", "51": "Grand Est",
            "25": "Bourgogne-Franche-Comté", "21": "Bourgogne-Franche-Comté",
            "76": "Normandie", "14": "Normandie",
            "37": "Centre-Val de Loire", "45": "Centre-Val de Loire",
        }
        return regions.get(dept, "")
