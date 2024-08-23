import subprocess
import discord
import json
import math
from discord.ext import commands, tasks
import time
import os

class Cogs:
    authorized = False
    info = {}
    current_song = None
    vc = {}
    stream_ctx = {}
    
    class Initialization(commands.Cog):
        @commands.Cog.listener()
        async def on_ready(self):
            self.stream_loop.start()
            print("Bot is ready!")
        
        ### ADD THE FOLLOWING LOOP TO EXECUTION FLOW
        @tasks.loop(seconds=0.4)
        async def stream_loop(self):
            await self.update_data()
                        
            # if stream_ctx not empty and current song is different than indicated
            if Cogs.stream_ctx and Cogs.info != {} and Cogs.current_song != Cogs.info["id"]:
                await Cogs.CurrentSongAndAlbum.on_song_change(self)

        # called when authorization to spotify acct required   
        @commands.command(name="init")
        async def connect_acct(self, ctx):
            try:
                subprocess.call(["node", "auth.cjs"], timeout=75)
                Cogs.authorized = True
                await ctx.send(
                    "Successfully connected Spotify account" +
                    "\nCall '-set-stream' in the preferred channel to " +
                    "set / update the stream output location or '-stop-stream' " +
                    "in any channel to stop receiving live updates."
                )
            except subprocess.TimeoutExpired:
                Cogs.authorized = False
                await ctx.send(
                    "Timeout while attempting to connect Spotify account." +
                    "Please try calling '-init' again."
                )
        @commands.command(name="set-stream")
        async def set_stream(self, ctx):
            if not Cogs.authorized: 
                await self.connect_acct(ctx)
            Cogs.stream_ctx[ctx.guild.id] = ctx
            await ctx.send("Successfully updated stream location!")
            
        @commands.command(name="stop-stream")
        async def stop_stream(self, ctx):
            if not Cogs.authorized: 
                await ctx.send("Please authorize an account using '-init' before using commands!")
                return
            try:
                del Cogs.stream_ctx[ctx.guild.id] 
                await ctx.send(
                    "Stream will no longer be sent to this server. To begin " +
                    "receiving live feed once again, call '-set-stream' in the" +
                    " desired channel."
                )
            except KeyError:
                await ctx.send(
                    "This server was not yet receiving live feed! Call " +
                    "'-set-stream' in the desired channel to start it."
                )
        async def update_data(self):
            if not Cogs.authorized: return
            try:
                subprocess.call(["node", "update.cjs"], timeout=7) # if takes longer than 15s, timeout reached
                f = open("./data/data.json", encoding="utf_16_le") # open json file containing current song data

                if (os.stat("./data/data.json").st_size == 0):
                    Cogs.info = {}
                else:
                    Cogs.info = json.load(f) # convert json file to python dict
                f.close() # close json file
            except subprocess.TimeoutExpired:
                Cogs.info = {}
                print("Timeout while attempting to update data.")
    class VoiceAndPreviews(commands.Cog):
        ## voice commands / song preview commands
        async def join_vc(self, ctx):
            if not Cogs.authorized: 
                await ctx.send("Please authorize an account using '-init' before using commands!")
                return
            for channel in ctx.message.guild.voice_channels:
                if channel.name == "Music Previews":
                    Cogs.vc[ctx.guild.id] = await channel.connect()
                    return True
            await ctx.send("Could not find voice channel named \'Music Previews\' in this server.")
            return False
                    
        @commands.command(name="leave-voice")
        async def leave_vc(self, ctx):
            if not Cogs.authorized: 
                await ctx.send("Please authorize an account using '-init' before using commands!")
                return
            if ctx.guild.id not in Cogs.vc:
                await ctx.send("Bot is not currently in a voice channel!")
                return
            await ctx.voice_client.disconnect()
            del Cogs.vc[ctx.guild.id]
        @commands.command(name="play")
        async def play_current(self, ctx):
            if not Cogs.authorized: 
                await ctx.send("Please authorize an account using '-init' before using commands!")
                return
            if Cogs.info == {}:
                await ctx.send("No song currently playing!")
                return
            
            if (ctx.guild.id not in Cogs.vc):
                if not await self.join_vc(ctx): # add this guild to vc dict
                    await ctx.send("Failed to join this server's preview channel.")
                    return
            vc = Cogs.vc[ctx.guild.id] # get channel corresponding to this guild
            if vc.is_playing():
                vc.stop()
            vc.play(discord.FFmpegPCMAudio(source=Cogs.info["preview-url"]))
            vc.source = discord.PCMVolumeTransformer(vc.source)
            vc.source.volume = 1.0
            
            await ctx.send(
                f"Now playing preview for \'{Cogs.info["name"]}\' by {Cogs.info["artists"]}...\n" +
                f"{Cogs.info["song-url"]}"
            )

    class CurrentSongAndAlbum(commands.Cog):
        @commands.command(name="song")
        async def current(self,ctx):
            if not Cogs.authorized: 
                await ctx.send("Please authorize an account using '-init' before using commands!")
                return
            if Cogs.info == {}:
                await ctx.send("No song currently playing!")
                return
            # format progress and duration for frontend display
            info = Cogs.info
            # convert milliseconds to minutes:seconds
            progress_s = math.floor(info["progress"] / 1000)
            duration_s = math.floor(info["dur"] / 1000)
            progress = str(math.floor(progress_s / 60)) + ":" + str(progress_s % 60).zfill(2)
            duration = str(math.floor(duration_s / 60)) + ":" + str(duration_s % 60).zfill(2)
            msg = (    # develop response and send message back to discord 
                        f'Currently playing \'{info["name"]}\' by {info["artists"]}' +
                        f' ({progress} of {duration})\n{info["song-url"]}'
                    )
            await ctx.send(msg)
            
        @commands.command(name="slink")
        async def get_slink(self,ctx):
            # prerequisites
            if not Cogs.authorized: 
                await ctx.send("Please authorize an account using '-init' before using commands!")
                return
            if Cogs.info == {}:
                await ctx.send("No song currently playing!")
                return
            await ctx.send(Cogs.info["song-url"])
        @commands.command(name="alink")
        async def get_alink(self, ctx):
            # prerequisites
            if not Cogs.authorized: 
                await ctx.send("Please authorize an account using '-init' before using commands!")
                return
            if Cogs.info == {}:
                await ctx.send("No song currently playing!")
                return
            await ctx.send(Cogs.info["album_url"])
        @commands.command(name="released")
        async def get_release(self,ctx):
            # prerequisites (authorized and playing a song)
            if not Cogs.authorized: 
                await ctx.send("Please authorize an account using '-init' before using commands!")
                return
            if Cogs.info == {}:
                await ctx.send("No song currently playing!")
                return
            info = Cogs.info
            msg = f'\'{info["name"]}\' by {info["artists"]} was released on {info["release"]}'
            await ctx.send(msg)
        @commands.command(name="album")
        async def get_album(self,ctx):
            # prerequisites
            if not Cogs.authorized: 
                await ctx.send("Please authorize an account using '-init' before using commands!")
                return
            if Cogs.info == {}:
                await ctx.send("No song currently playing!")
                return
            info = Cogs.info
            msg = f'\'{info["name"]}\' by {info["artists"]} is from \'{info["album"]}\'\n{info["album_url"]}'
            await ctx.send(msg)
        
        async def on_song_change(self):
            if Cogs.info == {}:
                await ctx.send("No song currently playing!")
                return
            
            info = Cogs.info
            Cogs.current_song = info["id"]
            progress_s = math.floor(info["progress"] / 1000)
            duration_s = math.floor(info["dur"] / 1000)
            progress = str(math.floor(progress_s / 60)) + ":" + str(progress_s % 60).zfill(2)
            duration = str(math.floor(duration_s / 60)) + ":" + str(duration_s % 60).zfill(2)    
            msg = (
                f'----\n**{time.ctime(time.time())}**\nNow playing \'{info["name"]}\' by {info["artists"]}' +
                f' ({progress} of {duration})\n{info["song-url"]}'    
            )
            for ctx in Cogs.stream_ctx.values():
                await ctx.send(msg)