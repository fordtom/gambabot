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

    # Build table rows
    rows = []
    for i, entry in enumerate(rankings[:20], 1):
        discord_id = entry["discord_id"]
        total = entry["total_cents"] / 100
        biggest = entry["biggest_win_cents"] / 100
        remaining = entry["remaining_bets"]
        max_return = entry["max_return_cents"] / 100
        pending = entry["pending_count"]

        if i == 1:
            medal = "🥇"
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = f"`{i}.`"

        rows.append({
            "medal": medal,
            "discord_id": discord_id,
            "total": total,
            "biggest": biggest,
            "remaining": remaining,
            "max_return": max_return,
            "pending": pending
        })

    # Format each player on one line with stats
    lines = []
    for row in rows:
        # Winnings | Best Win | Bets Remaining | Max Possible Return
        line = (
            f"{row['medal']} <@{row['discord_id']}> — "
            f"**${row['total']:.2f}**  ⸱  "
            f"best ${row['biggest']:.2f}  ⸱  "
            f"{row['remaining']} left  ⸱  "
            f"max ${row['max_return']:.2f}"
        )
        lines.append(line)

    embed.description = "\n".join(lines)

    footer_text = ""
    if len(rankings) > 20:
        footer_text = f"Showing top 20 of {len(rankings)} players"

    embed.set_footer(text=footer_text if footer_text else None)

    await interaction.followup.send(embed=embed, ephemeral=False)


def setup(tree: app_commands.CommandTree):
    @tree.command(name="leaderboard", description="View the global betting leaderboard")
    async def leaderboard_command(interaction: discord.Interaction):
        await leaderboard(interaction)
