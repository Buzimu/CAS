#implement fetch_loot_table and get_weapon_hash to get this working
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from bungie_client import bungie_client
from config import BUNGIE_API_KEY

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
    # We'll use the Bungie API to fetch this data
    # This requires multiple API calls and data processing

    if activity_type == "raid" or activity_type == "dungeon":
        # Fetch activity definition
        activity_def = await get_activity_definition(activity_name)
        if not activity_def:
            return None

        # Fetch rewards for each encounter
        loot_table = {}
        for phase in activity_def.get('phases', []):
            encounter_name = phase.get('name', 'Unknown Encounter')
            reward_items = await get_activity_rewards(activity_def['hash'], phase.get('phaseHash'))
            loot_table[encounter_name] = reward_items

    else:  # Other activities (crucible, vanguard, etc.)
        # Fetch activity rewards
        activity_def = await get_activity_definition(activity_name)
        if not activity_def:
            return None

        reward_items = await get_activity_rewards(activity_def['hash'])
        loot_table = reward_items

    return loot_table

async def get_activity_definition(activity_name: str):
    # Fetch activity definition from Bungie API
    try:
        response = await bungie_client.api.search_destiny_entity('DestinyActivityDefinition', activity_name)
        if response and response.results:
            return response.results[0].hash
    except Exception as e:
        print(f"Error fetching activity definition: {e}")
    return None

async def get_activity_rewards(activity_hash: int, phase_hash: int = None):
    # Fetch rewards for a specific activity (and phase, if applicable)
    try:
        response = await bungie_client.api.get_destiny_entity('DestinyActivityDefinition', activity_hash)
        if response and response.response:
            activity_def = response.response
            if phase_hash:
                phase_rewards = activity_def.get('phases', {}).get(phase_hash, {}).get('rewards', [])
            else:
                phase_rewards = activity_def.get('rewards', [])

            reward_items = []
            for reward in phase_rewards:
                item_def = await get_item_definition(reward['itemHash'])
                if item_def and item_def['itemType'] == 3:  # 3 is the item type for weapons
                    reward_items.append({
                        'name': item_def['displayProperties']['name'],
                        'hash': item_def['hash']
                    })
            return reward_items
    except Exception as e:
        print(f"Error fetching activity rewards: {e}")
    return []

async def get_item_definition(item_hash: int):
    # Fetch item definition from Bungie API
    try:
        response = await bungie_client.api.get_destiny_entity('DestinyInventoryItemDefinition', item_hash)
        if response and response.response:
            return response.response
    except Exception as e:
        print(f"Error fetching item definition: {e}")
    return None

def get_weapon_hash(weapon_name: str):
    # This function is now unnecessary as we're fetching real hashes
    # from the Bungie API in the fetch_loot_table function
    pass

def create_loot_embed(activity_name: str, loot_table: dict):
    embed = discord.Embed(title=f"Loot Table for {activity_name.replace('_', ' ').title()}", color=discord.Color.gold())
    
    if isinstance(loot_table, dict):  # For raids and dungeons
        for encounter, weapons in loot_table.items():
            weapon_links = [f"[{weapon['name']}](https://www.light.gg/db/items/{weapon['hash']})" for weapon in weapons]
            embed.add_field(name=encounter, value="\n".join(weapon_links) or "No weapons", inline=False)
    else:  # For other activities
        weapon_links = [f"[{weapon['name']}](https://www.light.gg/db/items/{weapon['hash']})" for weapon in loot_table]
        embed.add_field(name="Weapons", value="\n".join(weapon_links) or "No weapons", inline=False)
    
    return embed



async def setup(bot):
    await bot.add_cog(LootCog(bot))
