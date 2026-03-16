import os
import sys

import scrapy

from scrapper.items import AvisItem

sys.path.insert(0, "/backend")


class TrustpilotSpider(scrapy.Spider):
    name = "trustpilot"

    custom_settings = {
        "DOWNLOAD_DELAY": 3,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_HANDLERS": {},
        "TWISTED_REACTOR": None,
    }

    # Known Trustpilot slugs for major groups
    KNOWN_SLUGS = {
        "foncia": "www.foncia.com",
        "nexity": "www.nexity.fr",
        "citya": "www.citya.com",
        "oralia": "www.oralia.fr",
        "sergic": "www.sergic.com",
        "lamy": "www.lamy.fr",
    }

    def start_requests(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models.agence import Agence

        db_url = os.getenv("DATABASE_URL", "postgresql://needscrapper:needscrapper@db:5432/needscrapper")
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Get unique groups that have Trustpilot pages
        agences = session.query(Agence).filter(Agence.groupe.isnot(None), Agence.groupe != "").all()
        seen_groups = set()

        for agence in agences:
            group_key = agence.groupe.lower()
            if group_key in seen_groups:
                continue
            slug = self.KNOWN_SLUGS.get(group_key)
            if slug:
                seen_groups.add(group_key)
                url = f"https://fr.trustpilot.com/review/{slug}"
                yield scrapy.Request(
                    url=url,
                    callback=self.parse,
                    meta={"agence_nom": agence.groupe},
                    errback=self.handle_error,
                )

        # Also try searching Trustpilot for agences without known slugs
        for agence in agences:
            group_key = agence.groupe.lower()
            if group_key in seen_groups:
                continue
            if agence.site_web:
                seen_groups.add(group_key)
                # Try the website domain as Trustpilot slug
                domain = agence.site_web.replace("https://", "").replace("http://", "").rstrip("/")
                url = f"https://fr.trustpilot.com/review/{domain}"
                yield scrapy.Request(
                    url=url,
                    callback=self.parse,
                    meta={"agence_nom": agence.groupe or agence.nom},
                    errback=self.handle_error,
                )

        session.close()

    def handle_error(self, failure):
        self.logger.warning(f"Trustpilot page not found: {failure.request.url}")

    def parse(self, response):
        agence_nom = response.meta["agence_nom"]

        if response.status == 404:
            self.logger.info(f"[{agence_nom}] No Trustpilot page found")
            return

        for review in response.css('[data-service-review-card-paper="true"]'):
            note_str = review.css(
                "div[data-service-review-rating]::attr(data-service-review-rating)"
            ).get("0")
            texte = review.css(
                "p[data-service-review-text-typography]::text"
            ).get("")
            date_str = review.css("time::attr(datetime)").get("")

            item = AvisItem()
            item["agence_nom"] = agence_nom
            item["source"] = "trustpilot"
            try:
                item["note"] = float(note_str)
            except ValueError:
                item["note"] = 0.0
            item["texte"] = texte
            item["date_avis"] = date_str[:10] if date_str else None
            yield item

        # Pagination (max 3 pages)
        current_page = response.meta.get("tp_page", 1)
        if current_page < 3:
            next_link = response.css('a[name="pagination-button-next"]::attr(href)').get()
            if next_link:
                yield response.follow(
                    next_link, self.parse,
                    meta={"agence_nom": agence_nom, "tp_page": current_page + 1},
                    errback=self.handle_error,
                )
