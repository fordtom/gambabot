import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from models import Player, Bet
from config import DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    schema_path = Path(__file__).parent.parent / "schema.sql"
    with open(schema_path) as f:
        schema = f.read()

    conn = get_connection()
    conn.executescript(schema)
    conn.commit()
    conn.close()


def get_bet_stake(month: int) -> int:
    """Returns bet stake in cents based on month (1-indexed).

    Q1 (Jan-Mar): $1, Q2 (Apr-Jun): $2, Q3 (Jul-Sep): $3, Q4 (Oct-Dec): $4
    """
    if month <= 3:
        return 100
    elif month <= 6:
        return 200
    elif month <= 9:
        return 300
    else:
        return 400


def get_player(discord_id: str, year: int) -> Optional[Player]:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM players WHERE discord_id = ? AND year = ?", (discord_id, year)
    ).fetchone()
    conn.close()

    if row:
        return Player(
            id=row["id"],
            discord_id=row["discord_id"],
            year=row["year"],
            registered_at=datetime.fromisoformat(row["registered_at"]),
        )
    return None


def register_player(discord_id: str, year: int) -> Player:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO players (discord_id, year) VALUES (?, ?)", (discord_id, year)
    )
    player_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return Player(
        id=player_id, discord_id=discord_id, year=year, registered_at=datetime.now()
    )


def get_bets_for_player(player_id: int) -> list[Bet]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM bets WHERE player_id = ? ORDER BY placed_at DESC", (player_id,)
    ).fetchall()
    conn.close()

    return [_row_to_bet(row) for row in rows]


def has_bet_on_market(player_id: int, market_id: str) -> bool:
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM bets WHERE player_id = ? AND market_id = ? LIMIT 1",
        (player_id, market_id),
    ).fetchone()
    conn.close()
    return row is not None


def get_bets_used_in_month(player_id: int, year: int, month: int) -> int:
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) as count FROM bets WHERE player_id = ? AND placed_year = ? AND placed_month = ?",
        (player_id, year, month),
    ).fetchone()
    conn.close()
    return row["count"]


def get_bets_used_in_january(player_id: int) -> int:
    return get_bets_used_in_month(player_id, datetime.now().year, 1)


def get_remaining_bets(player_id: int) -> int:
    now = datetime.now()
    month = now.month

    if month == 1:
        used = get_bets_used_in_january(player_id)
        return max(0, 16 - used)
    else:
        used = get_bets_used_in_month(player_id, now.year, month)
        return max(0, 1 - used)


def create_bet(
    player_id: int,
    platform: str,
    market_id: str,
    market_title: str,
    position: str,
    price_cents: int,
) -> Bet:
    now = datetime.now()
    stake_cents = get_bet_stake(now.month)

    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO bets
           (player_id, platform, market_id, market_title, position, price_cents, stake_cents, placed_year, placed_month)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            player_id,
            platform,
            market_id,
            market_title,
            position,
            price_cents,
            stake_cents,
            now.year,
            now.month,
        ),
    )
    bet_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return Bet(
        id=bet_id,
        player_id=player_id,
        platform=platform,
        market_id=market_id,
        market_title=market_title,
        position=position,
        price_cents=price_cents,
        stake_cents=stake_cents,
        placed_at=now,
        placed_year=now.year,
        placed_month=now.month,
        resolved_at=None,
        outcome=None,
        payout_cents=None,
    )


def resolve_bet(bet_id: int, outcome: str, payout_cents: int):
    conn = get_connection()
    conn.execute(
        "UPDATE bets SET outcome = ?, payout_cents = ?, resolved_at = ? WHERE id = ?",
        (outcome, payout_cents, datetime.now().isoformat(), bet_id),
    )
    conn.commit()
    conn.close()


def get_all_unresolved_bets() -> list[Bet]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM bets WHERE outcome IS NULL").fetchall()
    conn.close()
    return [_row_to_bet(row) for row in rows]


def get_leaderboard(year: int) -> list[dict]:
    now = datetime.now()
    current_month = now.month

    conn = get_connection()
    rows = conn.execute(
        """
        SELECT
            p.id as player_id,
            p.discord_id,
            COALESCE(SUM(CASE WHEN b.outcome = 'win' THEN b.payout_cents ELSE 0 END), 0) as total_cents,
            COALESCE(MAX(CASE WHEN b.outcome = 'win' THEN b.payout_cents ELSE 0 END), 0) as biggest_win_cents,
            COALESCE(SUM(CASE WHEN b.outcome IS NULL THEN b.stake_cents * 100 / b.price_cents ELSE 0 END), 0) as pending_potential_cents,
            COUNT(CASE WHEN b.outcome IS NULL THEN 1 END) as pending_count,
            COUNT(CASE WHEN b.placed_year = ? AND b.placed_month = ? THEN 1 END) as bets_this_month
        FROM players p
        LEFT JOIN bets b ON p.id = b.player_id
        WHERE p.year = ?
        GROUP BY p.id, p.discord_id
        ORDER BY total_cents DESC, biggest_win_cents DESC
        """,
        (year, current_month, year),
    ).fetchall()
    conn.close()

    # Calculate remaining bets based on current month
    if current_month == 1:
        max_bets = 16
    else:
        max_bets = 1

    return [
        {
            "discord_id": row["discord_id"],
            "total_cents": row["total_cents"],
            "biggest_win_cents": row["biggest_win_cents"],
            "pending_count": row["pending_count"],
            "max_return_cents": row["total_cents"] + row["pending_potential_cents"],
            "remaining_bets": max(0, max_bets - row["bets_this_month"]),
        }
        for row in rows
    ]


def _row_to_bet(row: sqlite3.Row) -> Bet:
    return Bet(
        id=row["id"],
        player_id=row["player_id"],
        platform=row["platform"],
        market_id=row["market_id"],
        market_title=row["market_title"],
        position=row["position"],
        price_cents=row["price_cents"],
        stake_cents=row["stake_cents"],
        placed_at=datetime.fromisoformat(row["placed_at"]),
        placed_year=row["placed_year"],
        placed_month=row["placed_month"],
        resolved_at=datetime.fromisoformat(row["resolved_at"])
        if row["resolved_at"]
        else None,
        outcome=row["outcome"],
        payout_cents=row["payout_cents"],
    )
