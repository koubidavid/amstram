import scrapy
import yaml

from scrapper.items import AgenceItem


class AgenceInfoSpider(scrapy.Spider):
    name = "agence_info"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            with open("scrapper/config/selectors.yaml") as f:
                self.selectors = yaml.safe_load(f)
        except FileNotFoundError:
            self.selectors = {}

    def start_requests(self):
        urls = ["https://www.fnaim.fr/annuaire"]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        sel = self.selectors.get("fnaim", {})
        for card in response.css(sel.get("agence_list", ".card")):
            item = AgenceItem()
            item["nom"] = card.css(sel.get("nom", ".title::text")).get("")
            item["adresse"] = card.css(sel.get("adresse", ".address::text")).get("")
            item["ville"] = card.css(sel.get("ville", ".city::text")).get("")
            item["site_web"] = card.css("a::attr(href)").get("")
            yield item

        next_page = response.css("a.next::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)
