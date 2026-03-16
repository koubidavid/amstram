import scrapy

from scrapper.items import AvisItem


class GoogleReviewsSpider(scrapy.Spider):
    name = "google_reviews"

    def __init__(self, agence_names=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agence_names = agence_names or []

    def start_requests(self):
        for name in self.agence_names:
            search_url = f"https://www.google.com/maps/search/{name.replace(' ', '+')}"
            yield scrapy.Request(
                url=search_url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "agence_nom": name,
                },
            )

    async def parse(self, response):
        page = response.meta["playwright_page"]
        agence_nom = response.meta["agence_nom"]

        try:
            await page.wait_for_selector('[data-tab-index="1"]', timeout=5000)
            await page.click('[data-tab-index="1"]')
            await page.wait_for_timeout(2000)
        except Exception:
            await page.close()
            return

        reviews = await page.query_selector_all(".jftiEf")
        for review in reviews[:50]:
            try:
                note_el = await review.query_selector(".kvMYJc")
                note_attr = await note_el.get_attribute("aria-label") if note_el else ""
                note = float(note_attr.split("/")[0].replace(",", ".")) if "/" in note_attr else 0

                texte_el = await review.query_selector(".wiI7pd")
                texte = await texte_el.inner_text() if texte_el else ""

                item = AvisItem()
                item["agence_nom"] = agence_nom
                item["source"] = "google"
                item["note"] = note
                item["texte"] = texte
                yield item
            except Exception:
                continue

        await page.close()
