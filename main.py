import discord
from discord.ext import commands
from config import DISCORD_TOKEN
from bungie_client import setup_bungie_client

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await setup_bungie_client()
    
    # Load cogs
    await bot.load_extension('cogs.registration')
    await bot.load_extension('cogs.titles')
    await bot.load_extension('cogs.clan_activities')

bot.run(DISCORD_TOKEN)

############################OLD###############################
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from data_manager import bot_data, save_data
from config import DISCORD_TOKEN, BUNGIE_API_KEY, BUNGIE_CLIENT_ID, BUNGIE_CLIENT_SECRET
import discord
from discord.ext import commands, tasks
import asyncio
from bungio.client import Client as BungieClient
from bungio.models import BungieMembershipType, DestinyComponentType, ExactSearchRequest, DestinyActivityModeType
from datetime import datetime, timedelta

# Set up your Discord bot token and Bungie API credentials

CLAN_ID = 3787371
ANNOUNCEMENT_CHANNEL_ID = 1256662702894616671


# Initialize Discord intents
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

# Initialize Discord bot
bot = commands.Bot(command_prefix='!', intents=intents)

async def setup():
    await bungie_client.generate_auth()
    print("Bungie client authenticated")

# Initialize Bungie client
bungie_client = BungieClient(
    bungie_token=BUNGIE_API_KEY,
    bungie_client_id=BUNGIE_CLIENT_ID,
    bungie_client_secret=BUNGIE_CLIENT_SECRET
)

# Store member data
members_data = {}

# Constants
TRIALS_HASH = '3017993580'  # Character-specific hash for Trials of Osiris
WEEKLY_FLAWLESS_HASH = '1586211619'  # Hash for the weekly flawless count node
TRIALS_RESET_DAY = 4  # Friday (0 = Monday, 1 = Tuesday, ..., 6 = Sunday)

# Raid exotics dictionary
RAID_EXOTICS = {
    '2171478765': 'Eyes of Tomorrow',
    '1660030044': 'Vex Mythoclast',
    '2448907086': 'Collective Obligation',
    '4039227210': 'Heartshadow',
    '3121540812': 'One Thousand Voices',
    '2637485673': 'Anarchy',
    '1903459810': 'Conditional Finality',
    # Add more raid exotics as they are released
}

# Craftable patterns dictionary
CRAFTABLE_PATTERNS = {
    '2323544076': 'Austringer',
    '1289324202': 'Beloved',
    '1095807197': 'Calus Mini-Tool',
    '2278995296': 'Drang (Baroque)',
    '2323527788': 'Fixed Odds',
    '2715240478': 'Nezarec\'s Whisper',
    # Add more craftable weapons as they are released
}

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Connected to the following guilds:')
    for guild in bot.guilds:
        print(f'- {guild.name} (id: {guild.id})')
    print(f'Attempting to find channel with ID {ANNOUNCEMENT_CHANNEL_ID}')
    channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
    if channel:
        print(f'Successfully found channel: {channel.name}')
    else:
        print(f'Could not find channel. Available channels:')
        for guild in bot.guilds:
            for channel in guild.text_channels:
                print(f'- {channel.name} (id: {channel.id})')
    check_clan_activities.start()

@tasks.loop(minutes=30)
async def check_clan_activities():
    await update_members_data()
    await check_special_events()

async def update_members_data():
    try:
        print("Attempting to get clan members...")
        clan_members = await bungie_client.api.get_members_of_group(
            group_id=CLAN_ID,
            currentpage=1,
            member_type=None  # This will get all members
        )
        print(f"Successfully retrieved clan members")
        
        # Process the clan members...
        for member in clan_members.results:
            member_id = member.destiny_user_info.membership_id
            membership_type = member.destiny_user_info.membership_type
            
            profile = await bungie_client.api.get_profile(
                membership_type=membership_type,
                destiny_membership_id=member_id,
                components=[
                    DestinyComponentType.PROFILES,
                    DestinyComponentType.CHARACTERS,
                    DestinyComponentType.RECORDS,
                    DestinyComponentType.COLLECTIBLES,
                    DestinyComponentType.METRICS,
                    DestinyComponentType.ITEM_OBJECTIVES
                ]
            )
        
        flawless_count = 0
        for character_id in profile.characters.data:
            character_stats = await bungie_client.api.get_character(
                character_id=character_id,
                destiny_membership_id=member_id,
                membership_type=membership_type,
                components=[DestinyComponentType.METRICS]
            )
            
            if TRIALS_HASH in character_stats.metrics.data.metrics:
                flawless_count += character_stats.metrics.data.metrics[TRIALS_HASH].objectives[0].progress
        
        craftable_progress = {}
        for item_hash, item_data in profile.item_components.objectives.data.items():
            if item_hash in CRAFTABLE_PATTERNS:
                craftable_progress[item_hash] = item_data[0].progress
        
        members_data[member_id] = {
            'name': member.destiny_user_info.display_name,
            'last_played': profile.profile.data.date_last_played,
            'titles': profile.records.data.records,
            'collectibles': profile.collectibles.data.collectibles,
            'catalysts': profile.records.data.catalysts,
            'raid_exotics': {hash: profile.collectibles.data.collectibles.get(int(hash), {}).get('state', 0) for hash in RAID_EXOTICS},
            'weekly_flawless': flawless_count,
            'craftable_progress': craftable_progress
        }

    except Exception as e:
        print(f"Error updating member data: {e}")
        print(f"Available methods on bungie_client: {dir(bungie_client)}")
        print(f"Available methods on bungie_client.api: {dir(bungie_client.api)}")

async def check_special_events():
    channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
    if channel is None:
        print(f"Error: Could not find channel with ID {ANNOUNCEMENT_CHANNEL_ID}")
        return
    
    for member_id, data in members_data.items():
        # Check for returning players
        if datetime.now() - data['last_played'] > timedelta(days=30):
            await channel.send(f"Welcome back, {data['name']}! It's been a while since we've seen you in the Tower.")
        
        # Check for new titles
        for record_hash, record in data['titles'].items():
            if record.completed and not record.completed_before:
                await channel.send(f"Congratulations to {data['name']} for earning a new title: {record.title_info.title_name}!")
        
        # Check for catalyst completions
        for catalyst_hash, catalyst in data['catalysts'].items():
            if catalyst.completed and not catalyst.completed_before:
                await channel.send(f"{data['name']} has completed a new catalyst!")
        
        # Check for raid exotic acquisitions
        await check_raid_exotics(channel, member_id, data['name'], data['raid_exotics'])
        
        # Check for weekly flawless
        await check_weekly_flawless(channel, member_id, data['name'], data['weekly_flawless'])
        
        # Check for completed craftable patterns
        await check_craftable_patterns(channel, member_id, data['name'], data['craftable_progress'])

async def check_raid_exotics(channel, member_id, member_name, raid_exotics):
    previous_raid_exotics = members_data.get(member_id, {}).get('raid_exotics', {})
    
    for hash, name in RAID_EXOTICS.items():
        if previous_raid_exotics.get(hash, 0) & 1 == 0 and raid_exotics.get(hash, 0) & 1 == 1:
            await channel.send(f"🎉 Congratulations to {member_name} for obtaining the raid exotic {name}! 🎉")

    members_data[member_id]['raid_exotics'] = raid_exotics

async def check_weekly_flawless(channel, member_id, member_name, current_flawless_count):
    previous_data = members_data.get(member_id, {})
    previous_flawless_count = previous_data.get('weekly_flawless', 0)
    
    if is_new_trials_week():
        if current_flawless_count > 0 and previous_flawless_count == 0:
            await channel.send(f"🏆 Congratulations to {member_name} for going flawless in Trials of Osiris this week! 🏆")
    else:
        if current_flawless_count > previous_flawless_count:
            await channel.send(f"🏆 Congratulations to {member_name} for going flawless in Trials of Osiris! 🏆")
    
    members_data[member_id]['weekly_flawless'] = current_flawless_count

def is_new_trials_week():
    current_time = datetime.utcnow()
    days_since_reset = (current_time.weekday() - TRIALS_RESET_DAY) % 7
    last_reset = current_time - timedelta(days=days_since_reset, hours=current_time.hour, minutes=current_time.minute, seconds=current_time.second)
    
    previous_check_time = getattr(is_new_trials_week, 'last_check_time', None)
    is_new_trials_week.last_check_time = current_time
    
    return previous_check_time is None or previous_check_time < last_reset

async def check_craftable_patterns(channel, member_id, member_name, current_progress):
    previous_data = members_data.get(member_id, {})
    previous_progress = previous_data.get('craftable_progress', {})
    
    for pattern_hash, progress in current_progress.items():
        previous_pattern_progress = previous_progress.get(pattern_hash, 0)
        
        if progress == 100 and previous_pattern_progress < 100:
            weapon_name = CRAFTABLE_PATTERNS.get(pattern_hash, 'Unknown Weapon')
            await channel.send(f"🛠️ Congratulations to {member_name} for completing the pattern for {weapon_name}! It can now be crafted! 🛠️")

    members_data[member_id]['craftable_progress'] = current_progress

    try:
        user_id = str(ctx.author.id)
        if user_id not in bot_data["users"]:
            await ctx.send("You haven't registered your Bungie name yet. Please use !register first.")
            return
        
        bungie_name = bot_data["users"][user_id]["bungie_name"]
        display_name, bungie_code = bungie_name.split('#')
        
        print(f"Fetching titles for: {display_name}#{bungie_code}")
        
        # Create the ExactSearchRequest object
        search_request = ExactSearchRequest(
            display_name=display_name,
            display_name_code=int(bungie_code)
        )
        
        # Search for the player
        search_result = await bungie_client.api.search_destiny_player_by_bungie_name(
            data=search_request,
            membership_type=BungieMembershipType.ALL
        )
        
        if not search_result:
            await ctx.send(f"No player found with username {bungie_name}")
            return
        
        player = search_result[0]
        
        # Get the player's profile, including records (titles)
        profile = await bungie_client.api.get_profile(
            membership_type=player.membership_type,
            destiny_membership_id=player.membership_id,
            components=[DestinyComponentType.RECORDS]
        )
        
        records = profile.records.data.records
        
        in_progress_titles = []
        achieved_titles = []
        
        for record_hash, record in records.items():
            # Check if this record is a title
            if record.title_info:
                if record.completed:
                    gilding_count = record.gilding_tracker.number_of_gildings if record.gilding_tracker else 0
                    achieved_titles.append(f"{record.title_info.title_name} (Gilded {gilding_count}x)")
                else:
                    # Calculate completion percentage
                    total_objectives = len(record.objectives)
                    completed_objectives = sum(1 for obj in record.objectives if obj.complete)
                    completion_percentage = (completed_objectives / total_objectives) * 100
                    in_progress_titles.append(f"{record.title_info.title_name}: {completion_percentage:.2f}% complete")
        
        embed = discord.Embed(title=f"Titles for {player.bungie_global_display_name}", color=0x00ff00)
        
        if achieved_titles:
            embed.add_field(name="Achieved Titles", value="\n".join(achieved_titles), inline=False)
        
        if in_progress_titles:
            embed.add_field(name="In-Progress Titles", value="\n".join(in_progress_titles), inline=False)
        
        if not achieved_titles and not in_progress_titles:
            embed.description = "No titles found for this player."
        
        await ctx.send(embed=embed)
        
    except ValueError:
        await ctx.send("Invalid username format. Please use the format 'Name#1234'.")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")
        print(f"Full error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

@bot.command(name='register')
async def register(ctx):
    def check(m):
        return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)

    try:
        await ctx.send("I've sent you a DM to register your Bungie name.")
        await ctx.author.send("Please enter your Bungie name (including the #xxxx at the end):")
        
        msg = await bot.wait_for('message', check=check, timeout=60.0)
        bungie_name = msg.content.strip()
        
        if '#' not in bungie_name:
            await ctx.author.send("Invalid format. Please include the # and numbers at the end of your Bungie name.")
            return

        # Store the Bungie name
        bot_data["users"][str(ctx.author.id)] = {"bungie_name": bungie_name}
        save_data(bot_data)
        
        await ctx.author.send(f"Thank you! Your Bungie name ({bungie_name}) has been registered.")
    
    except asyncio.TimeoutError:
        await ctx.author.send("Registration timed out. Please try again.")
    except Exception as e:
        await ctx.author.send(f"An error occurred during registration: {str(e)}")
        print(f"Registration error: {e}")


    try:
        user_id = str(ctx.author.id)
        if user_id not in bot_data["users"]:
            await ctx.send("You haven't registered your Bungie name yet. Please use !register first.")
            return
        
        bungie_name = bot_data["users"][user_id]["bungie_name"]
        display_name, bungie_code = bungie_name.split('#')
        
        print(f"Fetching titles for: {display_name}#{bungie_code}")
        
        # Create the ExactSearchRequest object
        search_request = ExactSearchRequest(
            display_name=display_name,
            display_name_code=int(bungie_code)
        )
        
        # Search for the player
        search_result = await bungie_client.api.search_destiny_player_by_bungie_name(
            data=search_request,
            membership_type=BungieMembershipType.ALL
        )
        
        if not search_result:
            await ctx.send(f"No player found with username {bungie_name}")
            return
        
        player = search_result[0]
        
        # Get the player's profile, including records (titles)
        profile = await bungie_client.api.get_profile(
            membership_type=player.membership_type,
            destiny_membership_id=player.membership_id,
            components=[DestinyComponentType.RECORDS, DestinyComponentType.PROFILE_RECORDS]
        )
        
        # Access records from profile_records
        records = profile.profile_records.data.records
        
        in_progress_titles = []
        achieved_titles = []
        
        for record_hash, record in records.items():
            # Check if this record is a title
            if hasattr(record, 'title_info') and record.title_info:
                if record.state & 64:  # 64 is the flag for "Record Redeemed"
                    gilding_count = record.gilding_tracker.number_of_gildings if record.gilding_tracker else 0
                    achieved_titles.append(f"{record.title_info.title_name} (Gilded {gilding_count}x)")
                else:
                    # Calculate completion percentage
                    total_objectives = len(record.objectives)
                    completed_objectives = sum(1 for obj in record.objectives if obj.complete)
                    completion_percentage = (completed_objectives / total_objectives) * 100
                    in_progress_titles.append(f"{record.title_info.title_name}: {completion_percentage:.2f}% complete")
        
        embed = discord.Embed(title=f"Titles for {player.bungie_global_display_name}", color=0x00ff00)
        
        if achieved_titles:
            embed.add_field(name="Achieved Titles", value="\n".join(achieved_titles), inline=False)
        
        if in_progress_titles:
            embed.add_field(name="In-Progress Titles", value="\n".join(in_progress_titles), inline=False)
        
        if not achieved_titles and not in_progress_titles:
            embed.description = "No titles found for this player."
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")
        print(f"Full error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")




    try:
        user_id = str(ctx.author.id)
        if user_id not in bot_data["users"]:
            await ctx.send("You haven't registered your Bungie name yet. Please use !register first.")
            return
        
        bungie_name = bot_data["users"][user_id]["bungie_name"]
        display_name, bungie_code = bungie_name.split('#')
        
        print(f"Fetching titles for: {display_name}#{bungie_code}")
        
        # Create the ExactSearchRequest object
        search_request = ExactSearchRequest(
            display_name=display_name,
            display_name_code=int(bungie_code)
        )
        
        # Search for the player
        search_result = await bungie_client.api.search_destiny_player_by_bungie_name(
            data=search_request,
            membership_type=BungieMembershipType.ALL
        )
        
        if not search_result:
            await ctx.send(f"No player found with username {bungie_name}")
            return
        
        player = search_result[0]
        
        # Get the player's profile, including records (titles)
        profile = await bungie_client.api.get_profile(
            membership_type=player.membership_type,
            destiny_membership_id=player.membership_id,
            components=[DestinyComponentType.RECORDS]
        )
        
        # Access records from profile_records
        records = profile.profile_records.data.records
        
        in_progress_titles = []
        achieved_titles = []
        
        for record_hash, record in records.items():
            # Check if this record is a title
            if hasattr(record, 'title_info') and record.title_info:
                if record.state & 64:  # 64 is the flag for "Record Redeemed"
                    gilding_count = record.gilding_tracker.number_of_gildings if record.gilding_tracker else 0
                    achieved_titles.append(f"{record.title_info.title_name} (Gilded {gilding_count}x)")
                else:
                    # Calculate completion percentage
                    total_objectives = len(record.objectives)
                    completed_objectives = sum(1 for obj in record.objectives if obj.complete)
                    completion_percentage = (completed_objectives / total_objectives) * 100 if total_objectives > 0 else 0
                    in_progress_titles.append(f"{record.title_info.title_name}: {completion_percentage:.2f}% complete")
        
        embed = discord.Embed(title=f"Titles for {player.bungie_global_display_name}", color=0x00ff00)
        
        if achieved_titles:
            embed.add_field(name="Achieved Titles", value="\n".join(achieved_titles), inline=False)
        
        if in_progress_titles:
            embed.add_field(name="In-Progress Titles", value="\n".join(in_progress_titles), inline=False)
        
        if not achieved_titles and not in_progress_titles:
            embed.description = "No titles found for this player."
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")
        print(f"Full error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

@bot.command(name='titles')
async def titles(ctx):
    try:
        user_id = str(ctx.author.id)
        if user_id not in bot_data["users"]:
            await ctx.send("You haven't registered your Bungie name yet. Please use !register first.")
            return
        
        bungie_name = bot_data["users"][user_id]["bungie_name"]
        display_name, bungie_code = bungie_name.split('#')
        
        print(f"Fetching titles for: {display_name}#{bungie_code}")
        
        # Create the ExactSearchRequest object
        search_request = ExactSearchRequest(
            display_name=display_name,
            display_name_code=int(bungie_code)
        )
        
        # Search for the player
        search_result = await bungie_client.api.search_destiny_player_by_bungie_name(
            data=search_request,
            membership_type=BungieMembershipType.ALL
        )
        
        if not search_result:
            await ctx.send(f"No player found with username {bungie_name}")
            return
        
        player = search_result[0]
        
        # Get the player's profile, including records (titles)
        profile = await bungie_client.api.get_profile(
            membership_type=player.membership_type,
            destiny_membership_id=player.membership_id,
            components=[DestinyComponentType.RECORDS, DestinyComponentType.PROFILE_RECORDS]
        )
        
        # Access records from profile_records
        records = profile.profile_records.data.records
        
        in_progress_titles = []
        achieved_titles = []
        
        for record_hash, record in records.items():
            # Check if this record is a title
            if hasattr(record, 'title_info') and record.title_info:
                if record.state & 64:  # 64 is the flag for "Record Redeemed"
                    gilding_count = record.gilding_tracker.number_of_gildings if record.gilding_tracker else 0
                    achieved_titles.append(f"{record.title_info.title_name} (Gilded {gilding_count}x)")
                else:
                    # Calculate completion percentage
                    total_objectives = len(record.objectives)
                    completed_objectives = sum(1 for obj in record.objectives if obj.complete)
                    completion_percentage = (completed_objectives / total_objectives) * 100 if total_objectives > 0 else 0
                    in_progress_titles.append(f"{record.title_info.title_name}: {completion_percentage:.2f}% complete")
        
        embed = discord.Embed(title=f"Titles for {player.bungie_global_display_name}", color=0x00ff00)
        
        if achieved_titles:
            embed.add_field(name="Achieved Titles", value="\n".join(achieved_titles), inline=False)
        
        if in_progress_titles:
            embed.add_field(name="In-Progress Titles", value="\n".join(in_progress_titles), inline=False)
        
        if not achieved_titles and not in_progress_titles:
            embed.description = "No titles found for this player."
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")
        print(f"Full error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

bot.run(DISCORD_TOKEN)
