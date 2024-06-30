#todo: fix all asyncs, and make sure their are commented and compartmentalized
from discord.ext import commands, tasks
from config import CLAN_ID, ANNOUNCEMENT_CHANNEL_ID
from bungie_client import bungie_client

class ClanActivities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_clan_activities.start()

    @tasks.loop(minutes=30)
    async def check_clan_activities(self):
      await update_members_data()
      await check_special_events()

    @check_clan_activities.before_loop
    async def before_check_clan_activities(self):
        await self.bot.wait_until_ready()

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

async def setup(bot):
    await bot.add_cog(ClanActivities(bot))
