from datetime import datetime
from typing import Literal

import discord
from discord import app_commands

from services import database, resolver


async def bet(interaction: discord.Interaction, url: str, position: Literal["yes", "no"]):
    await interaction.response.defer(thinking=True)
    
    now = datetime.now()
    year = now.year
    discord_id = str(interaction.user.id)
    
    player = database.get_player(discord_id, year)
    if not player:
        await interaction.followup.send(
            "❌ You're not registered for this year. Use `/register` first (January only).",
            ephemeral=True
        )
        return
    
    remaining = database.get_remaining_bets(player.id)
    if remaining <= 0:
        month_name = now.strftime("%B")
        await interaction.followup.send(
            f"❌ You have no bets remaining for {month_name}.",
            ephemeral=True
        )
        return
    
    market = await resolver.get_market_info(url)
    if not market:
        await interaction.followup.send(
            "❌ Couldn't find that market. Check the URL and try again.\n"
            "Use a Polymarket link like: `polymarket.com/event/{event}/{market}`",
            ephemeral=True
        )
        return
    
    if database.has_bet_on_market(player.id, market.market_id):
        await interaction.followup.send(
            "❌ You've already placed a bet on this market.",
            ephemeral=True
        )
        return
    
    if market.resolved:
        await interaction.followup.send(
            "❌ This market has already resolved. Pick an open market.",
            ephemeral=True
        )
        return
    
    price_cents = market.yes_cents if position == "yes" else market.no_cents
    
    if price_cents <= 0:
        await interaction.followup.send(
            "❌ Invalid price from market. Try again later.",
            ephemeral=True
        )
        return
    
    payout_cents = (100 * 100) // price_cents
    
    database.create_bet(
        player_id=player.id,
        platform=market.platform,
        market_id=market.market_id,
        market_title=market.title[:200],
        position=position,
        price_cents=price_cents
    )
    
    await interaction.followup.send(
        f"✅ **Bet placed!**\n"
        f"**{market.title[:100]}**\n"
        f"Position: **{position.upper()}** @ ${price_cents / 100:.2f}\n"
        f"Potential payout: **${payout_cents / 100:.2f}**\n"
        f"Bets remaining: **{remaining - 1}**",
        ephemeral=True
    )


def setup(tree: app_commands.CommandTree):
    @tree.command(name="bet", description="Place a bet on a prediction market")
    @app_commands.describe(
        url="Link to a Polymarket market outcome (copy button in top right)",
        position="Bet YES or NO on this market"
    )
    async def bet_command(
        interaction: discord.Interaction,
        url: str,
        position: Literal["yes", "no"]
    ):
        await bet(interaction, url, position)
