# Gambabot

Discord prediction market betting game. Players register in January, receive 16 bets + 1/month thereafter, place virtual $1 bets on Polymarket outcomes.

## Stack

- **Runtime**: Python 3.13+
- **Package manager**: `uv`
- **Framework**: discord.py 2.3+ (slash commands)
- **Database**: SQLite (`gambabot.db`)
- **HTTP**: aiohttp (Polymarket API)
- **Testing**: pytest + pytest-asyncio

## Quick Start

```bash
uv sync
cp .env.example .env  # add DISCORD_TOKEN
uv run python bot.py
```

## Project Structure

```
bot.py              # Entry point; sets up client + command tree
config.py           # Env vars (DISCORD_TOKEN, DATABASE_PATH)
models.py           # Dataclasses: Player, Bet
schema.sql          # SQLite schema
commands/           # Discord slash commands
  register.py       # /register - January-only signup
  bet.py            # /bet <url> <yes|no> - place prediction
  bets.py           # /bets - view your bets + performance
  leaderboard.py    # /leaderboard - global rankings
  rules.py          # /rules - display game rules
services/
  database.py       # SQLite CRUD operations
  polymarket.py     # Polymarket API client + URL parsing
  resolver.py       # Bet resolution logic
```

## Game Rules

- Registration: January only
- Bet allocation: 16 in January, +1 each month Feb-Dec (27 total/year)
- Bet stakes (quarterly scaling):
  - Q1 (Jan-Mar): $1
  - Q2 (Apr-Jun): $2
  - Q3 (Jul-Sep): $3
  - Q4 (Oct-Dec): $4
- Payout: `stake * 100 / price_cents` (e.g., $1 bet YES at 25¢ → win $4 if YES)
- Voided markets: Resolved as $0 loss
- Leaderboard: Ranked by total winnings, then biggest single win

## Polymarket Integration

API base: `https://gamma-api.polymarket.com`

Key endpoints:
- `/events/slug/{slug}` - event details
- `/markets?slug={slug}` - market info (prices, closed status)
- `/markets/{id}` - resolution status

URL formats accepted:
- `polymarket.com/event/{event_slug}` (single yes/no markets only)
- `polymarket.com/event/{event_slug}/{market_slug}`

## Database Schema

```sql
players(discord_id, year, registered_at)  -- composite PK
bets(id, player_id, platform, market_id, position, price_cents, stake_cents,
     placed_at, placed_year, placed_month, resolved_at, outcome, payout_cents)
```

## Development

Run bot:
```bash
uv run python bot.py
```

Run tests:
```bash
uv run pytest
```

Lint/format:
```bash
uv format
```

## Key Patterns

- **Async everywhere**: All commands, DB ops, and API calls are async
- **Ephemeral responses**: Most commands reply privately; leaderboard is public
- **Year-scoped data**: All player/bet data keyed by year
- **Resolution on demand**: `resolver.resolve_*` called before displaying bets/leaderboard
- **Parameterized queries**: All SQL uses `?` placeholders (no f-strings)

## Common Tasks

### Add a new command

1. Create `commands/yourcommand.py`
2. Define async function with `@tree.command()` decorator pattern
3. Register in `bot.py` `setup_hook()`

### Modify bet limits

Edit `services/database.py` `get_remaining_bets()`:
- January: 16 bets
- Other months: 1 bet

### Change bet stakes

Edit `services/database.py` `get_bet_stake(month)` - returns stake in cents by quarter

### Change payout formula

Edit `services/resolver.py` `resolve_bet()` - currently `stake_cents * 100 / price_cents`

## Gotchas

- Multi-outcome Polymarket events rejected; only single yes/no markets work
- `placed_month` is 1-indexed (January = 1)
- Bot must have `applications.commands` scope + guild permissions
- Leaderboard caps at 20 players due to Discord embed limits
