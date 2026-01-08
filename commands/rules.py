import discord
from discord import app_commands


RULES_TEXT = """
**📋 GambaBot Rules**

**Registration**
• Use `/register` to join — only available in January
• Once registered, you're in for the whole year

**Betting Limits**
• January: 16 bets
• February–December: 1 bet per month
• Unused bets don't roll over

**How to Place a Bet**
1. Go to [polymarket.com](https://polymarket.com)
2. Find a market and outcome you want to bet on
3. (for multiple outcome bets) Hover over the copy icon in the top right corner
4. Copy the link for the specific outcome you want to bet on
5. Use `/bet <url> <yes|no>` with that link

**Payouts**
• Each bet is $1 (virtual)
• If you win: payout = $1 ÷ price you paid
• Example: Buy YES at $0.08 → win $12.50
• Losses, voids, and timeouts pay $0

**Leaderboard**
• Ranked by total winnings
• Tiebreaker: biggest single win
• Use `/leaderboard` to view rankings
""".strip()


async def rules(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎰 GambaBot",
        description=RULES_TEXT,
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


def setup(tree: app_commands.CommandTree):
    @tree.command(name="rules", description="How to play GambaBot")
    async def rules_command(interaction: discord.Interaction):
        await rules(interaction)
