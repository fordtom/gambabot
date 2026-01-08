import json
import math
import re
from typing import Optional

import aiohttp

from models import MarketInfo

GAMMA_API = "https://gamma-api.polymarket.com"


def parse_polymarket_url(url: str) -> tuple[Optional[str], Optional[str]]:
    """Parse a Polymarket URL, returning (event_slug, market_slug).

    For event/market URLs: returns (event_slug, market_slug)
    For event-only URLs: returns (event_slug, None)
    For market URLs: returns (None, market_slug)
    """
    # Full event/market URL: polymarket.com/event/{event}/{market}
    match = re.search(r"polymarket\.com/event/([^/]+)/([^/?#]+)", url)
    if match:
        return (match.group(1), match.group(2))

    # Event-only URL: polymarket.com/event/{event}
    match = re.search(r"polymarket\.com/event/([^/?#]+)", url)
    if match:
        return (match.group(1), None)

    # Direct market URL: polymarket.com/market/{market}
    match = re.search(r"polymarket\.com/market/([^/?#]+)", url)
    if match:
        return (None, match.group(1))

    return (None, None)


async def get_event_market_slug(event_slug: str) -> Optional[str]:
    """Fetch event by slug, return market slug if it's a simple yes/no event."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{GAMMA_API}/events/slug/{event_slug}") as resp:
            if resp.status != 200:
                return None
            data = await resp.json()

    if not data:
        return None

    markets = data.get("markets", [])
    if len(markets) != 1:
        # Multi-outcome event; user must specify which market
        return None

    market = markets[0]
    outcomes = market.get("outcomes")
    if outcomes:
        if isinstance(outcomes, str):
            outcomes = json.loads(outcomes)
        # Only simple yes/no markets
        if outcomes != ["Yes", "No"]:
            return None

    return market.get("slug")


async def get_market_info(market_slug: str) -> Optional[MarketInfo]:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{GAMMA_API}/markets?slug={market_slug}") as resp:
            if resp.status != 200:
                return None
            data = await resp.json()

            if not data or not isinstance(data, list) or len(data) == 0:
                return None

            return _parse_market_data(data[0])


async def check_resolution(market_id: str) -> Optional[str]:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{GAMMA_API}/markets/{market_id}") as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
    
    if not data:
        return None
    
    resolution_status = data.get("umaResolutionStatus")
    if resolution_status != "resolved":
        return None
    
    outcome_prices = data.get("outcomePrices")
    if not outcome_prices:
        return "void"
    
    try:
        if isinstance(outcome_prices, str):
            outcome_prices = json.loads(outcome_prices)
        
        yes_price = float(outcome_prices[0])
        no_price = float(outcome_prices[1])
        
        if yes_price > no_price:
            return "yes"
        elif no_price > yes_price:
            return "no"
        else:
            return "void"
    except (ValueError, IndexError, TypeError):
        return "void"


def _parse_market_data(market: dict) -> Optional[MarketInfo]:
    market_id = market.get("id")
    if not market_id:
        return None
    
    title = market.get("question") or market.get("title")
    if not title:
        return None
    
    outcome_prices = market.get("outcomePrices")
    if not outcome_prices:
        return None
    
    try:
        if isinstance(outcome_prices, str):
            outcome_prices = json.loads(outcome_prices)
        
        yes_price = float(outcome_prices[0])
        no_price = float(outcome_prices[1])
        
        yes_cents = math.ceil(yes_price * 100)
        no_cents = math.ceil(no_price * 100)
    except (ValueError, IndexError, TypeError):
        return None
    
    if yes_cents <= 0 or no_cents <= 0:
        return None
    
    closed = market.get("closed", False)
    
    resolution = None
    if closed:
        if yes_cents >= 99:
            resolution = "yes"
        elif yes_cents <= 1:
            resolution = "no"
    
    return MarketInfo(
        platform="polymarket",
        market_id=market_id,
        title=title,
        yes_cents=yes_cents,
        no_cents=no_cents,
        resolved=closed,
        resolution=resolution
    )
