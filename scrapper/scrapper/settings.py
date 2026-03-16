BOT_NAME = "scrapper"
SPIDER_MODULES = ["scrapper.spiders"]
NEWSPIDER_MODULE = "scrapper.spiders"

ROBOTSTXT_OBEY = False  # Many sites block scraping via robots.txt

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

# No Playwright by default — spiders override if needed
# DOWNLOAD_HANDLERS and TWISTED_REACTOR are set per-spider

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]

LOG_LEVEL = "INFO"
