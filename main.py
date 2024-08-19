import subprocess
import math
import json
import os
import time
import discord
from discord.ext import commands
from dotenv import load_dotenv    

authorized = False;    

async def update_data(ctx):
    global authorized
    if (not authorized):
        await connect_acct(ctx)

    subprocess.call(["node", "update.cjs"])
    f = open("./data.json") # open json file containing current song data
    global info
    info = json.load(f) # convert json file to python dict
    f.close() # close json file
   
# setup & initialize bot
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="--", intents=intents)
client = discord.Client(intents=intents)
info = {}
current_song = None
vc = False



## CREATE CUSTOM EVENT HANDLER LOOP
@bot.command(name="start")
async def event_loop(ctx):
    while(True):  
        await update_data(ctx)
        global info
        global current_song
        if (current_song != info["preview-url"]):
            await on_song_change(ctx)
    
@bot.event
async def on_song_change(ctx):
    global info
    global current_song
    current_song = info["preview-url"]
   
    progress_s = math.floor(info["progress"] / 1000)
    duration_s = math.floor(info["dur"] / 1000)
    progress = str(math.floor(progress_s / 60)) + ":" + str(progress_s % 60).zfill(2)
    duration = str(math.floor(duration_s / 60)) + ":" + str(duration_s % 60).zfill(2)

   
    msg = (
        f'Now playing \'{info["name"]}\' by {info["artists"]}' +
        f' ({progress} of {duration})\n{info["song-url"]}'    
    ) 
    await ctx.send(msg)    

# CREATE COMMANDS 
@bot.command(name="song")
async def current(ctx):        
    await update_data(ctx) # update json file
    
    # format progress and duration for frontend display
    global info
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
    
@bot.command(name="slink")
async def get_slink(ctx):
    await update_data(ctx)
    global info    
    await ctx.send(info["song-url"])
@bot.command(name="alink")
async def get_alink(ctx):
    await update_data(ctx)
    global info
    await ctx.send(info["album_url"])
@bot.command(name="released")
async def get_release(ctx):
    await update_data(ctx)
    global info
    msg = f'\'{info["name"]}\' by {info["artists"]} was released on {info["release"]}'
    await ctx.send(msg)
@bot.command(name="album")
async def get_album(ctx):
    await update_data(ctx)
    global info
    msg = f'\'{info["name"]}\' by {info["artists"]} is from \'{info["album"]}\'\n{info["album_url"]}'
    await ctx.send(msg)
## voice commands / song preview commands
@bot.command(name="join-voice")
async def join_vc(ctx):
    voice = bot.get_channel(int(os.getenv("VC_ID")))
    global vc
    vc = await voice.connect() 
@bot.command(name="leave-voice")
async def leave_vc(ctx):
    await ctx.voice_client.disconnect()
    global vc
    vc = False
@bot.command(name="play")
async def play_current(ctx):
    await update_data(ctx)
    global vc
    if (not vc):
        await join_vc(ctx)
    global info
    vc.play(discord.FFmpegPCMAudio(source=info["preview-url"]))
    vc.source = discord.PCMVolumeTransformer(vc.source)
    vc.source.volume = 1.0
    
# called when authorization to spotify acct required   
@bot.command(name="connect")
async def connect_acct(ctx):
    subprocess.call(["node", "auth.cjs"])
    global authorized
    authorized = True
    await ctx.send("connected spotify account")
    
    
bot.run(TOKEN)


## code not reached (bot.run already performs infinite loop)
# # while(True): # infinitely updates program to get up-to-date information
# #     update_data()
# #     print("updated data!")
    
    # transmit json data from update() call to playback in discord bot account
    # matches data from user acct as close as possible by checking for inconsistencies
    #     includes >3 secs off in playback time, song skipped, or song backtracked
    
    # # time.sleep(0.4)
