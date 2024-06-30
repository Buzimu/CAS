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
