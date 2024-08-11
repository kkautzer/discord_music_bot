import subprocess
import time
import os
import discord
# from dotenv import load_dotenv

def authenticate():
    subprocess.call(["node", "auth.cjs"])
    
def update():
    subprocess.call(["node", "update.cjs"])

def main():
    authenticate() # initial authentication of the program
    while(True): # infinitely updates program to get up-to-date information
        update()
        time.sleep(0.4)
        
        # transmit json data from update() call to playback in discord bot account
        # matches data from user acct as close as possible by checking for inconsistencies
            # includes >3 secs off in playback time, song skipped, or song backtracked

    
if __name__ == "__main__":
    main()