BOT_NAME = "scrapper"
SPIDER_MODULES = ["scrapper.spiders"]
NEWSPIDER_MODULE = "scrapper.spiders"

ROBOTSTXT_OBEY = True

DOWNLOAD_DELAY = 3
RANDOMIZE_DOWNLOAD_DELAY = True

CONCURRENT_REQUESTS = 4
CONCURRENT_REQUESTS_PER_DOMAIN = 2

ITEM_PIPELINES = {
    "scrapper.pipelines.cleaning.CleaningPipeline": 100,
    "scrapper.pipelines.snapshot.SnapshotPipeline": 200,
    "scrapper.pipelines.database.DatabasePipeline": 300,
}

DOWNLOADER_MIDDLEWARES = {
    "scrapper.middlewares.RotateUserAgentMiddleware": 400,
    "scrapper.middlewares.ProxyRotationMiddleware": 410,
}

DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {"headless": True}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
]
