import os
import sys

import scrapy
from bs4 import BeautifulSoup

from scrapper.items import AvisItem

sys.path.insert(0, "/backend")


class GoogleReviewsSpider(scrapy.Spider):
    """Scrape Google search results pages for review info (no Playwright needed)."""
    name = "google_reviews"

    custom_settings = {
        "DOWNLOAD_DELAY": 5,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_HANDLERS": {},
        "TWISTED_REACTOR": None,
    }

    def start_requests(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models.agence import Agence

        db_url = os.getenv("DATABASE_URL", "postgresql://needscrapper:needscrapper@db:5432/needscrapper")
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()

        agences = session.query(Agence).all()
        self.logger.info(f"Found {len(agences)} agences to check Google reviews for")

        for agence in agences:
            search_query = f"{agence.nom} {agence.ville or ''} avis".replace(" ", "+")
            url = f"https://www.google.com/search?q={search_query}"
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={"agence_nom": agence.nom, "agence_id": str(agence.id)},
                errback=self.handle_error,
            )

        session.close()

    def handle_error(self, failure):
        self.logger.warning(f"Failed to reach {failure.request.url}: {failure.value}")

    def parse(self, response):
        agence_nom = response.meta["agence_nom"]
        soup = BeautifulSoup(response.text, "html.parser")

        # Try to extract Google rating from search results knowledge panel
        rating_el = soup.select_one('span.Aq14fc, [data-attrid="kc:/location/location:rating"] .pihDIf')
        review_count_el = soup.select_one('span.hqzQac, [data-attrid="kc:/location/location:rating"] .mgr77e')

        if rating_el:
            try:
                note_text = rating_el.get_text(strip=True).replace(",", ".")
                note = float(note_text)

                nb_avis = 0
                if review_count_el:
                    import re
                    count_match = re.search(r"(\d[\d\s]*)", review_count_el.get_text())
                    if count_match:
                        nb_avis = int(count_match.group(1).replace(" ", ""))

                item = AvisItem()
                item["agence_nom"] = agence_nom
                item["source"] = "google"
                item["note"] = note
                item["texte"] = f"Note Google: {note}/5 ({nb_avis} avis)"
                item["date_avis"] = None
                yield item

                self.logger.info(f"[{agence_nom}] Google rating: {note}/5 ({nb_avis} avis)")
            except (ValueError, AttributeError) as e:
                self.logger.warning(f"[{agence_nom}] Could not parse Google rating: {e}")
        else:
            self.logger.info(f"[{agence_nom}] No Google rating found in search results")
