from __future__ import annotations

from pydantic import BaseModel


class Trade(BaseModel):
    proxyWallet: str
    side: str
    size: float
    price: float
    timestamp: int
    title: str
    slug: str
    eventSlug: str
    outcome: str
    outcomeIndex: int
    transactionHash: str
    name: str = ""
    pseudonym: str = ""
    bio: str = ""
    profileImage: str = ""

    @property
    def usdc_value(self) -> float:
        return self.size * self.price


class Position(BaseModel):
    proxyWallet: str
    size: float
    avgPrice: float
    initialValue: float
    currentValue: float
    title: str
    slug: str
    eventSlug: str
    eventId: str = ""
    outcome: str
    outcomeIndex: int
    curPrice: float = 0.0
    endDate: str = ""


class TradedResponse(BaseModel):
    user: str
    traded: int


class WalletAnalysis(BaseModel):
    address: str
    positions: list[Position]
    market_count: int
    first_seen: int | None = None
    profile_name: str = ""
    profile_bio: str = ""
    profile_image: str = ""
