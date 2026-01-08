import discord
from discord import app_commands

from config import DISCORD_TOKEN
from services import database
from commands import register, bet, bets, leaderboard


class GambaBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
    
    async def setup_hook(self):
        register.setup(self.tree)
        bet.setup(self.tree)
        bets.setup(self.tree)
        leaderboard.setup(self.tree)
        
        await self.tree.sync()
        print("Commands synced!")


def main():
    database.init_db()
    print("Database initialized.")
    
    client = GambaBot()
    
    @client.event
    async def on_ready():
        print(f"Logged in as {client.user} (ID: {client.user.id})")
        print(f"Serving {len(client.guilds)} guild(s)")
    
    client.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
