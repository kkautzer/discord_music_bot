import asyncio
import discord
from discord.ext import commands
from src.cogs import Cogs

class CustomBot(commands.Bot):    
    def __init__(self):    
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="-",intents = intents)
        asyncio.run(self.add_cog(Cogs.Initialization(self)))
        asyncio.run(self.add_cog(Cogs.CurrentSongAndAlbum(self)))
        asyncio.run(self.add_cog(Cogs.VoiceAndPreviews(self)))


    def run(self, token):
        print("Starting bot...")
        super().run(token)