#todo need to figure out the standard for making calls cuz this is still broke
from discord.ext import commands
from data_manager import bot_data
from bungie_client import bungie_client
from bungio.models import ExactSearchRequest, BungieMembershipType, DestinyComponentType
from utils.embed_creator import create_titles_embed

class Titles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='titles')
    async def titles(self, ctx):
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

async def setup(bot):
    await bot.add_cog(Titles(bot))
