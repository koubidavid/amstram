import random

import yaml


class RotateUserAgentMiddleware:
    def __init__(self, user_agents):
        self.user_agents = user_agents

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.getlist("USER_AGENTS"))

    def process_request(self, request, spider):
        request.headers["User-Agent"] = random.choice(self.user_agents)


class ProxyRotationMiddleware:
    def __init__(self):
        self.proxies = []
        try:
            with open("scrapper/config/proxies.yaml") as f:
                data = yaml.safe_load(f)
                self.proxies = data.get("proxies", []) if data else []
        except FileNotFoundError:
            pass

    def process_request(self, request, spider):
        if self.proxies:
            proxy = random.choice(self.proxies)
            request.meta["proxy"] = proxy
