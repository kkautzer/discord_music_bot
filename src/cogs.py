import subprocess
import discord
import json
import math
from discord.ext import commands, tasks

class Cogs:
    authorized = False
    info = {}
    current_song = None
    vc = False
    
    class Initialization(commands.Cog):
        # called when authorization to spotify acct required   
        @commands.command(name="connect")
        async def connect_acct(self, ctx):
            subprocess.call(["node", "auth.cjs"])
            Cogs.authorized = True
            await ctx.send("connected spotify account")

        async def update_data(self, ctx):
            if (not Cogs.authorized):
                await Cogs.Initialization.connect_acct(self, ctx)
            subprocess.call(["node", "update.cjs"])
            f = open("./data.json") # open json file containing current song data
            Cogs.info = json.load(f) # convert json file to python dict
            f.close() # close json file

    class VoiceAndPreviews(commands.Cog):
        ## voice commands / song preview commands
        @commands.command(name="join-voice")
        async def join_vc(self, ctx):
            print(ctx.message.guild.voice_channels)
            for channel in ctx.message.guild.voice_channels:
                if channel.name == "Music Previews":
                    print("Preview channel found!!")
                    Cogs.vc = await channel.connect()
                    return
            await ctx.send("Could not find voice channel named \'Music Previews\' in this server.")
                    
        @commands.command(name="leave-voice")
        async def leave_vc(self, ctx):
            await ctx.voice_client.disconnect()
            Cogs.vc = False
            
        @commands.command(name="play")
        async def play_current(self, ctx):
            await Cogs.Initialization.update_data(self, ctx)
            vc = Cogs.vc
            if (not vc):
                await Cogs.Initialization.join_vc(self, ctx)
            vc.play(discord.FFmpegPCMAudio(source=Cogs.info["preview-url"]))
            vc.source = discord.PCMVolumeTransformer(vc.source)
            vc.source.volume = 1.0

    class CurrentSongAndAlbum(commands.Cog):
        @commands.command(name="song")
        async def current(self,ctx):
            await Cogs.Initialization.update_data(self, ctx) # update json file
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
            await Cogs.Initialization.update_data(self, ctx)
            await ctx.send(Cogs.info["song-url"])
        @commands.command(name="alink")
        async def get_alink(self, ctx):
            await Cogs.Initialization.update_data(self, ctx)
            await ctx.send(Cogs.info["album_url"])
        @commands.command(name="released")
        async def get_release(self,ctx):
            await Cogs.Initialization.update_data(self, ctx)
            info = Cogs.info
            msg = f'\'{info["name"]}\' by {info["artists"]} was released on {info["release"]}'
            await ctx.send(msg)
        @commands.command(name="album")
        async def get_album(self,ctx):
            await Cogs.Initialization.update_data(self, ctx)
            info = Cogs.info
            msg = f'\'{info["name"]}\' by {info["artists"]} is from \'{info["album"]}\'\n{info["album_url"]}'
            await ctx.send(msg)