from datetime import datetime

import discord
from discord import app_commands

from services import database, resolver


async def bets(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    
    year = datetime.now().year
    discord_id = str(interaction.user.id)
    
    player = database.get_player(discord_id, year)
    if not player:
        await interaction.followup.send(
            "❌ You're not registered for this year.",
            ephemeral=True
        )
        return
    
    await resolver.resolve_player_bets(player.id)
    
    player_bets = database.get_bets_for_player(player.id)
    remaining = database.get_remaining_bets(player.id)
    
    if not player_bets:
        await interaction.followup.send(
            f"📋 **Your Bets ({year})**\n"
            f"No bets placed yet.\n"
            f"Bets remaining this month: **{remaining}**",
            ephemeral=True
        )
        return
    
    total_cents = sum(b.payout_cents or 0 for b in player_bets if b.outcome == "win")
    biggest_cents = max((b.payout_cents or 0 for b in player_bets if b.outcome == "win"), default=0)
    
    pending = [b for b in player_bets if b.outcome is None]
    wins = [b for b in player_bets if b.outcome == "win"]
    losses = [b for b in player_bets if b.outcome == "loss"]
    
    embed = discord.Embed(
        title=f"📋 Your Bets ({year})",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="Summary",
        value=(
            f"Total Winnings: **${total_cents / 100:.2f}**\n"
            f"Biggest Win: **${biggest_cents / 100:.2f}**\n"
            f"Bets Remaining: **{remaining}**"
        ),
        inline=False
    )
    
    if pending:
        pending_text = "\n".join(
            f"• {b.position.upper()} @ ${b.price_cents / 100:.2f} - {b.market_title[:50]}..."
            for b in pending[:5]
        )
        if len(pending) > 5:
            pending_text += f"\n... and {len(pending) - 5} more"
        embed.add_field(name=f"⏳ Pending ({len(pending)})", value=pending_text, inline=False)
    
    if wins:
        wins_text = "\n".join(
            f"• +${b.payout_cents / 100:.2f} ({b.position.upper()} @ ${b.price_cents / 100:.2f})"
            for b in wins[:5]
        )
        if len(wins) > 5:
            wins_text += f"\n... and {len(wins) - 5} more"
        embed.add_field(name=f"✅ Wins ({len(wins)})", value=wins_text, inline=False)
    
    if losses:
        embed.add_field(name=f"❌ Losses", value=f"{len(losses)} bet(s)", inline=False)
    
    await interaction.followup.send(embed=embed, ephemeral=True)


def setup(tree: app_commands.CommandTree):
    @tree.command(name="bets", description="View your bets and their status")
    async def bets_command(interaction: discord.Interaction):
        await bets(interaction)
