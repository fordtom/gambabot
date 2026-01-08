from datetime import datetime

import discord
from discord import app_commands

from services import database, resolver


async def leaderboard(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    
    year = datetime.now().year
    
    await resolver.resolve_all_bets()
    
    rankings = database.get_leaderboard(year)
    
    if not rankings:
        await interaction.followup.send(
            f"📊 **Leaderboard {year}**\n"
            f"No players registered yet.",
            ephemeral=False
        )
        return
    
    embed = discord.Embed(
        title=f"🏆 GambaBot Leaderboard {year}",
        color=discord.Color.gold()
    )
    
    lines = []
    for i, entry in enumerate(rankings[:20], 1):
        discord_id = entry["discord_id"]
        total = entry["total_cents"] / 100
        biggest = entry["biggest_win_cents"] / 100
        
        if i == 1:
            medal = "🥇"
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = f"{i}."
        
        lines.append(f"{medal} <@{discord_id}> — **${total:.2f}** (best: ${biggest:.2f})")
    
    embed.description = "\n".join(lines)
    
    if len(rankings) > 20:
        embed.set_footer(text=f"Showing top 20 of {len(rankings)} players")
    
    await interaction.followup.send(embed=embed, ephemeral=False)


def setup(tree: app_commands.CommandTree):
    @tree.command(name="leaderboard", description="View the global betting leaderboard")
    async def leaderboard_command(interaction: discord.Interaction):
        await leaderboard(interaction)
