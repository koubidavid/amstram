import scrapy

from scrapper.items import AvisItem


class TrustpilotSpider(scrapy.Spider):
    name = "trustpilot"

    def __init__(self, company_slugs=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.company_slugs = company_slugs or []

    def start_requests(self):
        for entry in self.company_slugs:
            url = f"https://fr.trustpilot.com/review/{entry['slug']}"
            yield scrapy.Request(url=url, callback=self.parse, meta={"agence_nom": entry["nom"]})

    def parse(self, response):
        agence_nom = response.meta["agence_nom"]

        for review in response.css('[data-service-review-card-paper="true"]'):
            note_str = review.css("div[data-service-review-rating]::attr(data-service-review-rating)").get("0")
            texte = review.css("p[data-service-review-text-typography]::text").get("")
            date_str = review.css("time::attr(datetime)").get("")

            item = AvisItem()
            item["agence_nom"] = agence_nom
            item["source"] = "trustpilot"
            item["note"] = float(note_str)
            item["texte"] = texte
            item["date_avis"] = date_str[:10] if date_str else None
            yield item

        next_page = response.css('a[name="pagination-button-next"]::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse, meta={"agence_nom": agence_nom})
