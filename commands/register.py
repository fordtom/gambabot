from datetime import datetime

import discord
from discord import app_commands

from services import database


async def register(interaction: discord.Interaction):
    now = datetime.now()
    year = now.year
    
    if now.month != 1:
        await interaction.response.send_message(
            f"❌ Registration is only open in January. Come back next year!",
            ephemeral=True
        )
        return
    
    discord_id = str(interaction.user.id)
    existing = database.get_player(discord_id, year)
    
    if existing:
        await interaction.response.send_message(
            f"✅ You're already registered for {year}!",
            ephemeral=True
        )
        return
    
    database.register_player(discord_id, year)
    
    await interaction.response.send_message(
        f"🎰 **Welcome to GambaBot {year}!**\n"
        f"You have **16 bets** to place this month.\n"
        f"After January, you get **1 bet per month**.\n"
        f"Use `/bet <url> <yes|no>` to place your bets!",
        ephemeral=True
    )


def setup(tree: app_commands.CommandTree):
    @tree.command(name="register", description="Join this year's betting game (January only)")
    async def register_command(interaction: discord.Interaction):
        await register(interaction)
