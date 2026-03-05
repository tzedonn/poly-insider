from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    telegram_bot_token: str
    telegram_chat_id: str
    poll_interval_seconds: int = 10
    min_trade_size_usd: float = 100
    cache_ttl_hours: int = 24

    @property
    def data_api_base(self) -> str:
        return "https://data-api.polymarket.com"

    @property
    def gamma_api_base(self) -> str:
        return "https://gamma-api.polymarket.com"


settings = Settings()
