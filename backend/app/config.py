from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://needscrapper:needscrapper@db:5432/needscrapper"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    model_config = {"env_file": ".env"}


settings = Settings()
