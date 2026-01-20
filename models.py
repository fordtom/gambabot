from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Player:
    id: int
    discord_id: str
    year: int
    registered_at: datetime


@dataclass
class Bet:
    id: int
    player_id: int
    platform: str
    market_id: str
    market_title: Optional[str]
    position: str
    price_cents: int
    stake_cents: int
    placed_at: datetime
    placed_year: int
    placed_month: int
    resolved_at: Optional[datetime]
    outcome: Optional[str]
    payout_cents: Optional[int]


@dataclass
class MarketInfo:
    platform: str
    market_id: str
    title: str
    yes_cents: int
    no_cents: int
    resolved: bool
    resolution: Optional[str]
