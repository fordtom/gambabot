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
            "❌ You're not registered for this year.", ephemeral=True
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
            ephemeral=True,
        )
        return

    total_cents = sum(b.payout_cents or 0 for b in player_bets if b.outcome == "win")
    biggest_cents = max(
        (b.payout_cents or 0 for b in player_bets if b.outcome == "win"), default=0
    )

    pending = [b for b in player_bets if b.outcome is None]
    wins = [b for b in player_bets if b.outcome == "win"]
    losses = [b for b in player_bets if b.outcome == "loss"]

    # Max return = current winnings + potential from pending bets
    pending_potential_cents = sum(
        b.stake_cents * 100 // b.price_cents for b in pending
    )
    max_return_cents = total_cents + pending_potential_cents

    embed = discord.Embed(title=f"📋 Your Bets ({year})", color=discord.Color.blue())

    embed.add_field(
        name="Summary",
        value=(
            f"Total Winnings: **${total_cents / 100:.2f}**\n"
            f"Biggest Win: **${biggest_cents / 100:.2f}**\n"
            f"Max Return: **${max_return_cents / 100:.2f}**\n"
            f"Bets Remaining: **{remaining}**"
        ),
        inline=False,
    )

    def add_chunked_fields(embed, name: str, lines: list[str]):
        """Add fields, splitting into multiple if content exceeds 1024 chars."""
        if not lines:
            return
        chunks = []
        current_chunk = []
        current_len = 0
        for line in lines:
            line_len = len(line) + 1  # +1 for newline
            if current_len + line_len > 1000:  # leave margin
                chunks.append("\n".join(current_chunk))
                current_chunk = [line]
                current_len = line_len
            else:
                current_chunk.append(line)
                current_len += line_len
        if current_chunk:
            chunks.append("\n".join(current_chunk))

        for i, chunk in enumerate(chunks):
            field_name = name if len(chunks) == 1 else f"{name} ({i + 1}/{len(chunks)})"
            embed.add_field(name=field_name, value=chunk, inline=False)

    if pending:
        pending_lines = [
            f"• ${b.stake_cents / 100:.0f} {b.position.upper()} @ ${b.price_cents / 100:.2f} - {b.market_title}"
            for b in pending
        ]
        add_chunked_fields(embed, f"⏳ Pending ({len(pending)})", pending_lines)

    if wins:
        wins_lines = [
            f"• +${b.payout_cents / 100:.2f} (${b.stake_cents / 100:.0f} {b.position.upper()} @ ${b.price_cents / 100:.2f}) - {b.market_title}"
            for b in wins
        ]
        add_chunked_fields(embed, f"✅ Wins ({len(wins)})", wins_lines)

    if losses:
        losses_lines = [
            f"• -${b.stake_cents / 100:.0f} {b.position.upper()} @ ${b.price_cents / 100:.2f} - {b.market_title}"
            for b in losses
        ]
        add_chunked_fields(embed, f"❌ Losses ({len(losses)})", losses_lines)

    await interaction.followup.send(embed=embed, ephemeral=True)


def setup(tree: app_commands.CommandTree):
    @tree.command(name="bets", description="View your bets and their status")
    async def bets_command(interaction: discord.Interaction):
        await bets(interaction)
