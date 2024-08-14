import subprocess
import math
import json
import os
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
vc = False

# CREATE COMMANDS 
@bot.command(name="current")
async def current(ctx):        
    await update_data(ctx) # update json file
    
    # format progress and duration for frontend display
    # convert milliseconds to minutes:seconds
    global info
    progress_s = math.floor(info["progress"] / 1000)
    duration_s = math.floor(info["dur"] / 1000)
    progress = str(math.floor(progress_s / 60)) + ":" + str(progress_s % 60).zfill(2)
    duration = str(math.floor(duration_s / 60)) + ":" + str(duration_s % 60).zfill(2)
    
    # develop response and send message back to discord
    response = (
                    f'Currently playing \'{info["name"]}\' by {info["artists"]}' +
                    f' ({progress} of {duration})'
                )
    await ctx.send(response)

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
    vc.play(discord.FFmpegPCMAudio(source=info["url"]))
    vc.source = discord.PCMVolumeTransformer(vc.source)
    vc.source.volume = 1.0

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
