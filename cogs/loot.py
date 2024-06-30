#implement fetch_loot_table and get_weapon_hash to get this working
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp

class LootCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="loot", description="Display loot table for various activities")
    async def loot(self, interaction: discord.Interaction):
        # Create the initial response with activity type selection
        await interaction.response.send_message("Select an activity type:", view=ActivityTypeView())

class ActivityTypeView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(ActivityTypeSelect())

class ActivityTypeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Raid", description="View raid loot tables"),
            discord.SelectOption(label="Dungeon", description="View dungeon loot tables"),
            discord.SelectOption(label="Other", description="View other activity loot tables")
        ]
        super().__init__(placeholder="Choose an activity type...", options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "Raid":
            await interaction.response.edit_message(content="Select a raid:", view=RaidView())
        elif self.values[0] == "Dungeon":
            await interaction.response.edit_message(content="Select a dungeon:", view=DungeonView())
        else:
            await interaction.response.edit_message(content="Select an activity:", view=OtherActivityView())

class RaidView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(RaidSelect())

class RaidSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Root of Nightmares", value="root_of_nightmares"),
            discord.SelectOption(label="King's Fall", value="kings_fall"),
            discord.SelectOption(label="Vow of the Disciple", value="vow_of_the_disciple"),
            discord.SelectOption(label="Deep Stone Crypt", value="deep_stone_crypt"),
            discord.SelectOption(label="Vault of Glass", value="vault_of_glass"),
            discord.SelectOption(label="Salvation's Edge", value="salvations_edge"),
            discord.SelectOption(label="Crota's End", value="crotas_end"),
            discord.SelectOption(label="Garden of Salvation", value="garden_of_salvation"),
            discord.SelectOption(label="Last Wish", value="last_wish"),
        ]
        super().__init__(placeholder="Choose a raid...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        loot_table = await fetch_loot_table(self.values[0], "raid")
        embed = create_loot_embed(self.values[0], loot_table)
        await interaction.edit_original_response(content=None, embed=embed, view=None)

class DungeonView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(DungeonSelect())

class DungeonSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Spire of the Watcher", value="spire_of_the_watcher"),
            discord.SelectOption(label="Duality", value="duality"),
            discord.SelectOption(label="Grasp of Avarice", value="grasp_of_avarice"),
            discord.SelectOption(label="Warlord's Ruin", value="warlords_ruin"),
            discord.SelectOption(label="Ghosts of the Deep", value="ghosts_of_the_deep"),
            discord.SelectOption(label="Prophecy", value="prophecy"),
            discord.SelectOption(label="Pit of Heresy", value="pit_of_heresy"),
            discord.SelectOption(label="Shattered Throne", value="shattered_throne"),
            # Add more dungeons as needed
        ]
        super().__init__(placeholder="Choose a dungeon...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        loot_table = await fetch_loot_table(self.values[0], "dungeon")
        embed = create_loot_embed(self.values[0], loot_table)
        await interaction.edit_original_response(content=None, embed=embed, view=None)

class OtherActivityView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(OtherActivitySelect())

class OtherActivitySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Crucible", value="crucible"),
            discord.SelectOption(label="Vanguard Ops", value="vanguard_ops"),
            discord.SelectOption(label="Gambit", value="gambit"),
            # Add more activities as needed
        ]
        super().__init__(placeholder="Choose an activity...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        loot_table = await fetch_loot_table(self.values[0], "other")
        embed = create_loot_embed(self.values[0], loot_table)
        await interaction.edit_original_response(content=None, embed=embed, view=None)

async def fetch_loot_table(activity_name: str, activity_type: str):
    # This is a placeholder function. In a real implementation, you would fetch this data
    # from an API or database. For now, we'll return some sample data.
    # Todo: Verify how the API retuns this data
    if activity_type == "raid":
        return {
            "Encounter 1": ["Weapon A", "Weapon B"],
            "Encounter 2": ["Weapon C", "Weapon D"],
            "Final Boss": ["Exotic Weapon"]
        }
    elif activity_type == "dungeon":
        return {
            "First Area": ["Weapon E", "Weapon F"],
            "Boss": ["Weapon G", "Weapon H"]
        }
    else:
        return ["Weapon I", "Weapon J", "Weapon K"]

def create_loot_embed(activity_name: str, loot_table: dict):
    embed = discord.Embed(title=f"Loot Table for {activity_name.replace('_', ' ').title()}", color=discord.Color.gold())
    
    if isinstance(loot_table, dict):  # For raids and dungeons
        for encounter, weapons in loot_table.items():
            weapon_links = [f"[{weapon}](https://www.light.gg/db/items/{get_weapon_hash(weapon)})" for weapon in weapons]
            embed.add_field(name=encounter, value="\n".join(weapon_links), inline=False)
    else:  # For other activities
        weapon_links = [f"[{weapon}](https://www.light.gg/db/items/{get_weapon_hash(weapon)})" for weapon in loot_table]
        embed.add_field(name="Weapons", value="\n".join(weapon_links), inline=False)
    
    return embed

def get_weapon_hash(weapon_name: str):
    # This function should return the actual hash for the weapon.
    # For now, we'll return a placeholder value.
    return "0"

async def setup(bot):
    await bot.add_cog(LootCog(bot))
