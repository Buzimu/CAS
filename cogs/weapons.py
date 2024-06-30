from discord import app_commands
from discord.ext import commands
import discord
from bungie_client import bungie_client
from data_manager import bot_data

class Weapons(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="weapons", description="Show top weapons, optionally filtered by activity")
    @app_commands.describe(activity="The activity to filter weapons by")
    @app_commands.autocomplete(activity=activity_autocomplete)
    async def weapons(self, interaction: discord.Interaction, activity: str = None):
        user_id = str(interaction.user.id)
        if user_id not in bot_data["users"]:
            await interaction.response.send_message("You haven't registered your Bungie name yet. Please use !register first.")
            return

        bungie_name = bot_data["users"][user_id]["bungie_name"]
        
        # Fetch weapons data from Bungie API
        weapons_data = await fetch_weapons_data(bungie_name, activity)
        
        # Create and send embed with weapons data
        embed = create_weapons_embed(weapons_data, activity)
        await interaction.response.send_message(embed=embed)

async def activity_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    activities = ["Crucible", "Gambit", "Strikes", "Raid", "Dungeon", "Patrol", "Trials"]
    return [
        app_commands.Choice(name=activity, value=activity)
        for activity in activities if current.lower() in activity.lower()
    ]

async def fetch_weapons_data(bungie_name, activity=None):
    # Use bungie_client to fetch weapons data
    # This is a placeholder - you'll need to implement the actual API call
    # Return format should be a list of dictionaries, each containing weapon name and kills
    return [
        {"name": "The Last Word", "kills": 1000},
        {"name": "Felwinter's Lie", "kills": 800},
        {"name": "Ace of Spades", "kills": 600},
    ]

def create_weapons_embed(weapons_data, activity=None):
    title = f"Top Weapons{f' in {activity}' if activity else ''}"
    embed = discord.Embed(title=title, color=discord.Color.blue())
    for weapon in weapons_data[:10]:  # Top 10 weapons
        embed.add_field(name=weapon["name"], value=f"Kills: {weapon['kills']}", inline=False)
    return embed

async def setup(bot):
    await bot.add_cog(Weapons(bot))
