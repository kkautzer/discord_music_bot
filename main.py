import os
import discord
from dotenv import load_dotenv    
from src.bot import CustomBot

# setup & initialize bot
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
intents = discord.Intents.default()
intents.message_content = True
bot = CustomBot()

bot.run(TOKEN)