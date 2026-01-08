from typing import Optional

from models import Bet, MarketInfo
from services import database, polymarket


async def get_market_info(url: str) -> Optional[MarketInfo]:
    event_slug, market_slug = polymarket.parse_polymarket_url(url)

    if market_slug:
        return await polymarket.get_market_info(market_slug)

    if event_slug:
        # Event-only URL; try to resolve to single yes/no market
        resolved_slug = await polymarket.get_event_market_slug(event_slug)
        if resolved_slug:
            return await polymarket.get_market_info(resolved_slug)

    return None


async def resolve_bet(bet: Bet) -> bool:
    if bet.outcome is not None:
        return False
    
    if bet.platform == "polymarket":
        resolution = await polymarket.check_resolution(bet.market_id)
    else:
        return False
    
    if resolution is None:
        return False
    
    if resolution == "void":
        database.resolve_bet(bet.id, "loss", 0)
        return True
    
    user_won = (bet.position == resolution)
    
    if user_won:
        payout_cents = (100 * 100) // bet.price_cents
        database.resolve_bet(bet.id, "win", payout_cents)
    else:
        database.resolve_bet(bet.id, "loss", 0)
    
    return True


async def resolve_player_bets(player_id: int) -> int:
    bets = database.get_bets_for_player(player_id)
    resolved_count = 0
    
    for bet in bets:
        if bet.outcome is None:
            if await resolve_bet(bet):
                resolved_count += 1
    
    return resolved_count


async def resolve_all_bets() -> int:
    unresolved = database.get_all_unresolved_bets()
    resolved_count = 0
    
    for bet in unresolved:
        if await resolve_bet(bet):
            resolved_count += 1
    
    return resolved_count
