import pytest
from services.database import get_bet_stake


class TestGetBetStake:
    """Test quarterly bet stake calculation."""

    @pytest.mark.parametrize(
        "month,expected_cents",
        [
            # Q1: $1
            (1, 100),
            (2, 100),
            (3, 100),
            # Q2: $2
            (4, 200),
            (5, 200),
            (6, 200),
            # Q3: $3
            (7, 300),
            (8, 300),
            (9, 300),
            # Q4: $4
            (10, 400),
            (11, 400),
            (12, 400),
        ],
    )
    def test_stake_by_month(self, month: int, expected_cents: int):
        """Stake scales quarterly: Q1=$1, Q2=$2, Q3=$3, Q4=$4."""
        assert get_bet_stake(month) == expected_cents

    def test_january_cheapest(self):
        """January bets should be the cheapest."""
        jan_stake = get_bet_stake(1)
        for month in range(2, 13):
            assert get_bet_stake(month) >= jan_stake

    def test_december_most_expensive(self):
        """December bets should be tied for most expensive (Q4)."""
        dec_stake = get_bet_stake(12)
        for month in range(1, 12):
            assert get_bet_stake(month) <= dec_stake


class TestPayoutCalculation:
    """Test payout calculation with variable stakes."""

    def test_payout_scales_with_stake(self):
        """Higher stake = higher potential payout."""
        price_cents = 25  # 25¢ price

        # $1 bet at 25¢ -> $4 payout
        stake_q1 = get_bet_stake(1)
        payout_q1 = (stake_q1 * 100) // price_cents
        assert payout_q1 == 400

        # $4 bet at 25¢ -> $16 payout
        stake_q4 = get_bet_stake(12)
        payout_q4 = (stake_q4 * 100) // price_cents
        assert payout_q4 == 1600

    def test_payout_at_even_odds(self):
        """At 50¢, payout equals 2x stake."""
        price_cents = 50
        for month in [1, 6, 9, 12]:
            stake = get_bet_stake(month)
            payout = (stake * 100) // price_cents
            assert payout == stake * 2
