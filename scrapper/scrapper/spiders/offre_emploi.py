import os
import sys

import scrapy

from scrapper.items import OffreItem

sys.path.insert(0, "/backend")


class OffreEmploiSpider(scrapy.Spider):
    name = "offre_emploi"

    custom_settings = {
        "DOWNLOAD_DELAY": 3,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_HANDLERS": {},
        "TWISTED_REACTOR": None,
    }

    def start_requests(self):
        """Load agences with websites from the database."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models.agence import Agence

        db_url = os.getenv("DATABASE_URL", "postgresql://needscrapper:needscrapper@db:5432/needscrapper")
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()

        agences = session.query(Agence).filter(Agence.site_web.isnot(None), Agence.site_web != "").all()
        self.logger.info(f"Found {len(agences)} agences with websites to scrape for job offers")

        for agence in agences:
            url = agence.site_web
            if not url.startswith("http"):
                url = "https://" + url
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={"agence_nom": agence.nom},
                errback=self.handle_error,
            )

        session.close()

    def handle_error(self, failure):
        self.logger.warning(f"Failed to reach {failure.request.url}: {failure.value}")

    def parse(self, response):
        agence_nom = response.meta["agence_nom"]
        career_links = response.css(
            'a[href*="recrutement"], a[href*="carriere"], a[href*="careers"], '
            'a[href*="emploi"], a[href*="rejoindre"], a[href*="jobs"], '
            'a[href*="nous-rejoindre"], a[href*="offres"]'
        )
        for link in career_links:
            yield response.follow(
                link, self.parse_careers,
                meta={"agence_nom": agence_nom},
                errback=self.handle_error,
            )

    def parse_careers(self, response):
        agence_nom = response.meta["agence_nom"]
        # Try multiple common job listing selectors
        selectors = [
            ".job-listing", ".offre", ".poste", ".vacancy",
            "article", ".job-item", ".career-item", ".offer",
            '[class*="job"]', '[class*="offre"]', '[class*="poste"]',
        ]
        for sel in selectors:
            for job in response.css(sel):
                titre = job.css("h2::text, h3::text, h4::text, .titre::text, a::text").get("")
                if not titre or len(titre) < 5:
                    continue
                # Only keep relevant job titles
                if not self._is_relevant(titre):
                    continue

                item = OffreItem()
                item["agence_nom"] = agence_nom
                item["titre"] = titre.strip()
                item["description"] = job.css("p::text, .description::text").get("")
                item["url_source"] = response.url
                item["type_poste"] = self._classify_poste(titre)
                yield item

    def _is_relevant(self, titre: str) -> bool:
        titre_lower = titre.lower()
        return any(kw in titre_lower for kw in [
            "gestionnaire", "gestion locative", "copropriété",
            "syndic", "assistant", "property", "gérance",
        ])

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
