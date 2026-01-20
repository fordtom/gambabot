-- Migration: Add stake_cents column to bets table
-- All existing bets were $1 stakes, so default to 100 cents

ALTER TABLE bets ADD COLUMN stake_cents INTEGER NOT NULL DEFAULT 100;
