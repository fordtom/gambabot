CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY,
    discord_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(discord_id, year)
);

CREATE TABLE IF NOT EXISTS bets (
    id INTEGER PRIMARY KEY,
    player_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    market_id TEXT NOT NULL,
    market_title TEXT,
    position TEXT NOT NULL,
    price_cents INTEGER NOT NULL,
    stake_cents INTEGER NOT NULL DEFAULT 100,
    placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    placed_year INTEGER NOT NULL,
    placed_month INTEGER NOT NULL,
    resolved_at TIMESTAMP,
    outcome TEXT,
    payout_cents INTEGER,
    FOREIGN KEY (player_id) REFERENCES players(id)
);

CREATE INDEX IF NOT EXISTS idx_bets_player ON bets(player_id);
CREATE INDEX IF NOT EXISTS idx_bets_outcome ON bets(outcome);
CREATE INDEX IF NOT EXISTS idx_players_year ON players(year);
