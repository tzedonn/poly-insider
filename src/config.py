from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    telegram_bot_token: str
    telegram_chat_id: str
    poll_interval_seconds: int = 30
    min_trade_size_usd: float = 1000
    cache_ttl_hours: int = 24

    @property
    def data_api_base(self) -> str:
        return "https://data-api.polymarket.com"

    @property
    def gamma_api_base(self) -> str:
        return "https://gamma-api.polymarket.com"


settings = Settings()

EXCLUDED_SLUG_KEYWORDS = (
    "bitcoin", "btc-", "ethereum", "eth-", "solana", "sol-", "xrp",
    "nfl", "nba", "mlb", "nhl", "ufc", "mma", "boxing", "tennis",
    "golf", "pga", "soccer", "football", "basketball", "baseball",
    "hockey", "f1-", "formula-1", "nascar", "cricket", "rugby",
    "premier-league", "champions-league", "world-cup", "super-bowl",
    "stanley-cup", "world-series", "wbc-",
    "lol-", "lal-", "cbb-", "cs2-", "atp-", "epl-", "cde-",
    "presidential-nominee", "presidential-election",
    "the-masters", "crint-", "-cl-",
    "highest-temperature", "largest-company",
    "elon-musk-of-tweets",
    "fed-decision", "next-three-fed-decisions", "fed-rate-cut",
)
