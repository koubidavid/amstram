import scrapy

from scrapper.items import OffreItem


class OffreEmploiSpider(scrapy.Spider):
    name = "offre_emploi"

    def __init__(self, agence_urls=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agence_urls = agence_urls or []

    def start_requests(self):
        for entry in self.agence_urls:
            yield scrapy.Request(
                url=entry["url"],
                callback=self.parse,
                meta={"agence_nom": entry["nom"]},
            )

    def parse(self, response):
        agence_nom = response.meta["agence_nom"]
        career_links = response.css(
            'a[href*="recrutement"], a[href*="carriere"], '
            'a[href*="emploi"], a[href*="rejoindre"]'
        )
        for link in career_links:
            yield response.follow(link, self.parse_careers, meta={"agence_nom": agence_nom})

    def parse_careers(self, response):
        agence_nom = response.meta["agence_nom"]
        for job in response.css(".job-listing, .offre, .poste"):
            item = OffreItem()
            item["agence_nom"] = agence_nom
            item["titre"] = job.css("h2::text, h3::text, .titre::text").get("")
            item["description"] = job.css(".description::text, p::text").get("")
            item["url_source"] = response.url
            item["type_poste"] = self._classify_poste(item["titre"])
            yield item

    def _classify_poste(self, titre: str) -> str:
        titre_lower = titre.lower()
        if "assistant" in titre_lower and "copropriété" in titre_lower:
            return "assistant_copropriete"
        elif "gestionnaire" in titre_lower and "copropriété" in titre_lower:
            return "gestionnaire_copropriete"
        elif "assistant" in titre_lower and "locati" in titre_lower:
            return "assistant_gestion_locative"
        elif "gestionnaire" in titre_lower and "locati" in titre_lower:
            return "gestionnaire_locatif"
        return "autre"
