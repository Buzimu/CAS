import discord

def create_titles_embed(player_name, achieved_titles, in_progress_titles):
    embed = discord.Embed(title=f"Titles for {player_name}", color=0x00ff00)
    
    if achieved_titles:
        embed.add_field(name="Achieved Titles", value="\n".join(achieved_titles), inline=False)
    
    if in_progress_titles:
        embed.add_field(name="In-Progress Titles", value="\n".join(in_progress_titles), inline=False)
    
    if not achieved_titles and not in_progress_titles:
        embed.description = "No titles found for this player."
    
    return embed
