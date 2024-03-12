from reddit import RedditAPI
from tiktokvoice import tts, get_duration, merge_audio_files
from tqdm import tqdm
from srt import gen_srt_file
from editor import VideoEditor
from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
import praw
import sqlite3
from datetime import datetime
import datetime
import subprocess
import os
import sys

# VARIABLES & ENABLES
subreddits = ["confession", "tifu", "LetsNotMeet", "AmItheAsshole"]  # Add your desired subreddits here to scan
enable_database_updates = 0 # Creates a database of top redit posts in the subredits defined above
enable_check_for_update_content = 0 # Check for similar content posted by users in the database (updates)
enable_video_creation = 1 # Enable automatic video creation (this is slow)

def clear_terminal():
    """Clears the terminal screen."""
    # Clear the terminal screen based on the operating system
    os.system('cls' if os.name == 'nt' else 'clear')


def setup_credentials():
    print("\nSetting up the credentials, this will only run the first time you run the program\n")
    print("You will need to create a Reddit app and get the client id and client secret\n")
    print("You will also need to enter your Reddit username and password\n")
    print("These credentials will be stored in a file called credentials.txt\n")
    print("This file will be stored locally and will only be used to authenticate with Reddit and to get the post text\n")
    print("Goto https://github.com/JaydenDownes/RSCG and follow the instructions\n")

    client_id = input("Enter the client id:\n")
    client_secret = input("Enter the client secret:\n")
    username = input("Enter the username:\n")
    password = input("Enter the password:\n")
    with open("credentials.txt", "w") as f:
        f.write(f"{client_id}\n{client_secret}\n{username}\n{password}")



if __name__ == "__main__":
    # Clear the terminal for program start
    clear_terminal()

    # Check if ffmpeg is installed
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("\033[31m\033[1m(#)\033[0m ffmpeg is not installed. Please install ffmpeg to continue.")
        exit(1)

    # Check if the credentials file exists
    if not os.path.exists("credentials.txt"):
        # print("No credentials file found, going through the setup - ")
        setup_credentials()

    # Check if the outputs folder exists
    if not os.path.exists("outputs"):
        os.mkdir("outputs")
        # print("Created inputs folder\n - This is where final videos will be saved.")
    # Check if the inputs folder exists
    if not os.path.exists("inputs"):
        os.mkdir("inputs")
        # print("Created inputs folder\n - This is where input video files will need to be stored\n - The srt and wav files will also be stored here.")
    # Check if the outputs folder exists
    if not os.path.exists("temp"):
        os.mkdir("temp")
        # print("Created temp folder\n - This is where temporary will be saved.")

    # Check if any mp4 files are present in the inputs folder
    if len([i for i in os.listdir("inputs") if i.endswith(".mp4")]) == 0:
        print("\033[31m\033[1m(#)\033[0m No input video files found in the inputs folder, Add your input video files to this folder.")
        exit(1)

    # Read the credentials from the file
    with open("credentials.txt", "r") as f:
        creds = f.readlines()

    # Try create the Reddit instance with the credentials.
    try:
        reddit = RedditAPI(
            creds[0].strip(),  # client_id
            creds[1].strip(),  # client_secret
            creds[2].strip(),  # username
            creds[3].strip())  # password
    except:
        print("\033[31m\033[1m(#)\033[0m Credentials not set correctly, delete credentials.txt and setup again.")
        exit(1)

    print("\033[1m \n", 
        "   ___ ___ ___  ___ ___ _____   ___  ___ ___   \n ", 
        " | _ \ __|   \|   \_ _|_   _| / __|/ __/ __| \n ", 
        " |   / _|| |) | |) | |  | |   \__ \ (_| (_ | \n ", 
        " |_|_\___|___/|___/___| |_|   |___/\___\___| \n ", 
        "Reddit Short-Form Content Generator V2.2 \033[0m \n ")
    
    if(enable_database_updates == 1):
        print("\n \033[1m(#)\033[0m Searching through Reddit for posts") 
        updated_posts = reddit.get_updated_posts(subreddits)
        reddit.update_database(updated_posts)

    if(enable_check_for_update_content == 1):
        print("\n \033[1m(#)\033[0m Searching through Reddit for update content, this can be slow due to API limits.") 
        reddit.check_for_similar_titles()

    if(enable_video_creation == 1):
        # Run video creation loop
        print("\033[1m(#)\033[0m Generating video content, this will take a long time")
        reddit.process_unmade_videos()