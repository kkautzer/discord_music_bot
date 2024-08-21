import asyncio
import subprocess
import math
import json
import time
import discord
from discord.ext import tasks, commands
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
        
    async def on_ready(self, ctx):
        await ctx.send("Bot is ready!")
    
    async def on_song_change(self, ctx):
        info = self.info
        self.current_song = info["preview-url"]
        progress_s = math.floor(info["progress"] / 1000)
        duration_s = math.floor(info["dur"] / 1000)
        progress = str(math.floor(progress_s / 60)) + ":" + str(progress_s % 60).zfill(2)
        duration = str(math.floor(duration_s / 60)) + ":" + str(duration_s % 60).zfill(2)    
        msg = (
            f'----\n**{time.ctime(time.time())}**\nNow playing \'{info["name"]}\' by {info["artists"]}' +
            f' ({progress} of {duration})\n{info["song-url"]}'    
        ) 
        await ctx.send(msg)
        
    ### ADD THE FOLLOWING LOOP TO EXECUTION FLOW
    # # # # @tasks.loop(seconds=0.1)
    # # # # async def stream_loop(self, ctx):
    # # # #     print("loop")
    # # # #     await self.update_data(self, ctx)
    # # # #     if (self.current_song != self.info["preview-url"]):
    # # # #         await self.on_song_change(self, ctx)
            
    # # # # @stream_loop.before_loop
    # # # # async def before_stream_loop(self, ctx):
    # # # #     await self.update_data(self, ctx)