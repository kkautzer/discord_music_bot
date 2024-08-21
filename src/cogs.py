import subprocess
import discord
import json
import math
from discord.ext import commands, tasks
import time

class Cogs:
    authorized = False
    info = {}
    current_song = None
    vc = False
    stream_ctx = {}
    
    class Initialization(commands.Cog):
        @commands.Cog.listener()
        async def on_ready(self):
            self.stream_loop.start()
        
        ### ADD THE FOLLOWING LOOP TO EXECUTION FLOW
        @tasks.loop(seconds=1.0)
        async def stream_loop(self):
            if Cogs.stream_ctx: # if stream_ctx is not empty
                await self.update_data()
                if (Cogs.current_song != Cogs.info["preview-url"]):
                    await Cogs.CurrentSongAndAlbum.on_song_change(self)

        # called when authorization to spotify acct required   
        @commands.command(name="init")
        async def connect_acct(self, ctx):
            subprocess.call(["node", "auth.cjs"])
            Cogs.authorized = True
            await ctx.send(
                "Successfully connected Spotify account" +
                "\nCall '-set-stream' in the preferred channel to " +
                "set / update the stream output location or '-stop-stream' " +
                "in any channel to stop receiving live updates."
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
                    "desired channel."
                )
            except KeyError:
                await ctx.send(
                    "This server was not yet receiving live feed! Call " +
                    "'-set-stream' in the desired channel to start it."
                )
        async def update_data(self):
            if not Cogs.authorized: return
            subprocess.call(["node", "update.cjs"])
            f = open("./data.json") # open json file containing current song data
            Cogs.info = json.load(f) # convert json file to python dict
            f.close() # close json file

    class VoiceAndPreviews(commands.Cog):
        ## voice commands / song preview commands
        @commands.command(name="join-voice")
        async def join_vc(self, ctx):
            if not Cogs.authorized: 
                await ctx.send("Please authorize an account using '-init' before using commands!")
                return
            print(ctx.message.guild.voice_channels)
            for channel in ctx.message.guild.voice_channels:
                if channel.name == "Music Previews":
                    Cogs.vc = await channel.connect()
                    return
            await ctx.send("Could not find voice channel named \'Music Previews\' in this server.")
                    
        @commands.command(name="leave-voice")
        async def leave_vc(self, ctx):
            if not Cogs.authorized: 
                await ctx.send("Please authorize an account using '-init' before using commands!")
                return
            await ctx.voice_client.disconnect()
            Cogs.vc = False
        @commands.command(name="play")
        async def play_current(self, ctx):
            if not Cogs.authorized: 
                await ctx.send("Please authorize an account using '-init' before using commands!")
                return
            vc = Cogs.vc
            if (not vc):
                await Cogs.Initialization.join_vc(self, ctx)
            vc.play(discord.FFmpegPCMAudio(source=Cogs.info["preview-url"]))
            vc.source = discord.PCMVolumeTransformer(vc.source)
            vc.source.volume = 1.0

    class CurrentSongAndAlbum(commands.Cog):
        @commands.command(name="song")
        async def current(self,ctx):
            if not Cogs.authorized: 
                await ctx.send("Please authorize an account using '-init' before using commands!")
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
            if not Cogs.authorized: 
                await ctx.send("Please authorize an account using '-init' before using commands!")
                return
            await ctx.send(Cogs.info["song-url"])
        @commands.command(name="alink")
        async def get_alink(self, ctx):
            if not Cogs.authorized: 
                await ctx.send("Please authorize an account using '-init' before using commands!")
                return
            await ctx.send(Cogs.info["album_url"])
        @commands.command(name="released")
        async def get_release(self,ctx):
            if not Cogs.authorized: 
                await ctx.send("Please authorize an account using '-init' before using commands!")
                return
            info = Cogs.info
            msg = f'\'{info["name"]}\' by {info["artists"]} was released on {info["release"]}'
            await ctx.send(msg)
        @commands.command(name="album")
        async def get_album(self,ctx):
            if not Cogs.authorized: 
                await ctx.send("Please authorize an account using '-init' before using commands!")
                return
            info = Cogs.info
            msg = f'\'{info["name"]}\' by {info["artists"]} is from \'{info["album"]}\'\n{info["album_url"]}'
            await ctx.send(msg)
        
        async def on_song_change(self):
            info = Cogs.info
            Cogs.current_song = info["preview-url"]
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