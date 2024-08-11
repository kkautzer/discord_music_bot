import subprocess
import os
import discord
# from dotenv import load_dotenv

def main():
    authenticate()
    
    while(True):
        update()  
    
if __name__ == "__main__":
    main()
    
    
def authenticate():
    subprocess.call(["node", "auth.cjs"])
    
def update():
    subprocess.call(["node", "update.cjs"])