#todo: change this so that we just check if the name is valid and add it to the save file. Gathering info can be handled by the update players. Maybe we can call that function 
from discord.ext import commands
from data_manager import bot_data, save_data

class Registration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='register')
    async def register(self, ctx):      
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
      

async def setup(bot):
    await bot.add_cog(Registration(bot))
