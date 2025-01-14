from reddit import RedditAPI  # Imports a custom module named RedditAPI for interacting with the Reddit API.
from tiktokvoice import tts, get_duration, merge_audio_files  # Imports functions for working with audio files related to TikTok voice generation.
from tqdm import tqdm  # Provides a progress bar to show the progress of iterative tasks.
from srt import gen_srt_file  # Imports a function for generating SubRip (SRT) subtitle files.
from editor import VideoEditor  # Imports a custom module for video editing tasks.
from PIL import Image, ImageDraw, ImageFont, ImageOps  # Python Imaging Library, used for image manipulation.
import requests  # Used for making HTTP requests, typically for API interactions.
import praw  # Python Reddit API Wrapper, used for interacting with the Reddit API.
import sqlite3  # Provides a lightweight disk-based database that doesn’t require a separate server process.
import argparse  # Provides facilities for parsing command-line arguments.
from datetime import datetime  # Provides classes for manipulating dates and times.
import datetime  # Provides classes for manipulating dates and times.
import subprocess  # Provides support for spawning new processes, connecting to their input/output/error pipes, and obtaining their return codes.
import os  # Provides functions for interacting with the operating system.
import sys  # Provides access to some variables used or maintained by the Python interpreter and to functions that interact strongly with the interpreter.
import time  # Provides various time-related functions.
from tabulate import tabulate # Provides utilities to create tables in the terminal space

# Clear_terminal Function
def clear_terminal():
    """Clears the terminal screen."""
    # Clear the terminal screen based on the operating system
    os.system('cls' if os.name == 'nt' else 'clear')

# Setup Credentials Function (Sets up Reddit API access)
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
        print("\033[31m\033[1m(#)\033[0m ffmpeg is not installed. Please install ffmpeg to continue.\n")
        exit(1)

    # Check if the credentials file exists
    if not os.path.exists("credentials.txt"):
        # print("No credentials file found, going through the setup")
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
        print("\033[31m\033[1m(#)\033[0m No input video files found in the inputs folder, Add your input video files to this folder.\n")
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
        print("\033[31m\033[1m(#)\033[0m Credentials not set correctly, delete credentials.txt and setup again.\n")
        exit(1)

    # Define command-line arguments
    parser = argparse.ArgumentParser(description='ShortFormGen: Reddit Short-Form Content Generator V2.2')
    parser.add_argument('-a', '--Auto', action='store_true', help='Program will attempt to search for and generate new content every 30 minutes (can be changed in main.py)')
    parser.add_argument('-cs', '--ContentSearch', action='store_true', help='Program will only attempt to find and store new content in database')
    parser.add_argument('-ucs', '--UpdateContentSearch', action='store_true', help='Program will only attempt to find update content for videos already in the database, not new content')
    parser.add_argument('-cc', '--CreateContent', action='store_true', help='Program will generate videos for entries stored in the database that dont have a pre-existing video generated')
    parser.add_argument('-gv', '--GenerateVideo', metavar='<url>', help='Used to generate a video for a specified reddit post')
    parser.add_argument('-re', '--RetryErrors', action='store_true', help='Used to retry generating video that previously encountered errors when proccessing')
    parser.add_argument('-cd', '--ClearDatabase', action='store_true', help='Clears all videos in the database')
    parser.add_argument('-ce', '--ClearEntry', metavar='<post_id>', help='Clears entry submisison in the database')
    parser.add_argument('-vs', '--ViewSubreddits', action='store_true', help='View subreddits that will be searched by content search.')
    parser.add_argument('-as', '--AddSubreddit', metavar='<subreddit>', help='Add a subreddit that will be searched by content search.')
    parser.add_argument('-rs', '--RemoveSubreddit', metavar='<subreddit>', help='Remove a subreddit that will be searched by content search.')
    parser.add_argument('-vf', '--ViewFilter', action='store_true', help='Produces a list of words in the censored list')
    parser.add_argument('-af', '--AddFilter', metavar='<word>', help='Adds word to censored list')
    parser.add_argument('-rf', '--RemoveFilter', metavar='<word>', help='Removes word from censored list')

    # Parse command-line arguments
    args = parser.parse_args()

    print("\033[1m \n", 
        "   ___ ___ ___  ___ ___ _____   ___  ___ ___   \n ", 
        " | _ \ __|   \|   \_ _|_   _| / __|/ __/ __| \n ", 
        " |   / _|| |) | |) | |  | |   \__ \ (_| (_ | \n ", 
        " |_|_\___|___/|___/___| |_|   |___/\___\___| \n ", 
        "Reddit Short-Form Content Generator V2.2 \033[0m \n ")
        
    # If no run mode is provided, run the program in auto.
    if not any([args.ContentSearch, args.UpdateContentSearch, args.CreateContent, args.GenerateVideo, args.RetryErrors, args.ClearDatabase, args.ClearEntry, args.ViewSubreddits, args.AddSubreddit, args.RemoveSubreddit, args.ViewFilter, args.AddFilter, args.RemoveFilter]):
        # Execute Auto mode logic if no specific options are provided
        print("\033[1m(#)\033[0m Running in Auto Mode, if this was a mistake run the program using '-h' or '--help' command-line argument.\n")
        # Auto mode logic
        
        # Define the duration of the interval in seconds (30 minutes)
        interval_seconds = 30 * 60

        while True:
            # Record the start time
            start_time = time.time()

            # Auto Loop Code:
            # Check for new popular posts in subreddits
            subreddits = reddit.view_subreddits()
            updated_posts = reddit.get_updated_posts()
            reddit.update_database(updated_posts)

            # Checks for update posts by the same creators
            reddit.check_for_similar_titles()

            # Generate Videos
            reddit.process_unmade_videos() 

            # Calculate the time taken for the code execution
            time_taken = time.time() - start_time
            
            # Calculate the remaining time to make it 30 minutes
            remaining_time = interval_seconds - time_taken

            # Pause execution for the remaining time
            if remaining_time > 0:
                print(f"\033[1m(#)\033[0m Code execution took {time_taken:.2f} seconds.\n")
                print(f"\033[1m(#)\033[0mWaiting for {remaining_time:.2f} seconds.\n")
                time.sleep(remaining_time)
            else:
                print("\033[1m(#)\033[0m Code execution took longer than 30 minutes. Restarting loop immediately.\n")

        pass
    else:
        # Logic for each specific option
        if args.ContentSearch:
            # Content search logic
            print("\033[1m(#)\033[0m Searching through Reddit for posts\n") 
            subreddits = reddit.view_subreddits()
            updated_posts = reddit.get_updated_posts()
            reddit.update_database(updated_posts)
            pass

        if args.UpdateContentSearch:
            # Update content search logic
            print("\033[1m(#)\033[0m Searching through Reddit for update content, this can be slow due to API limits.\n") 
            reddit.check_for_similar_titles()
            pass

        if args.CreateContent:
            # Create content logic (run video creation loop)
            print("\033[1m(#)\033[0m Generating video content, this will take a long time.\n")
            reddit.process_unmade_videos()
            pass

        if args.GenerateVideo:
            # Generate video logic
            url = args.GenerateVideo
            # Logic for generating video for a specified Reddit post
            print(f"\033[1m(#)\033[0m Generating content for provided url ({url}), please wait..\n")
            
            reddit.generateVideo(url)
            print(f"\033[1m(#)\033[0m Finished generating content for provided url ({url}), closing program in 5 seconds\n")
            time.sleep(5)

        if args.RetryErrors:
            # Retry errors logic
            print("\033[1m(#)\033[0m Program attempting to regenerate content for previously failed entries in the database\n")
            reddit.retry_errors()
            print("\033[1m(#)\033[0m Program hyas attempted to regenerate content for previously failed entries in the database, closing in 5 seconds..\n")
            time.sleep(5)
            pass

        if args.ClearDatabase:
            # Clear database logic
            # Prompt the user for confirmation
            confirmation = input("\033[1m(#)\033[0m Are you sure you want to clear the database? (y/[n]): ").strip().lower()

            # Check user input
            if confirmation == 'y':
                # User confirmed, perform clear database logic
                print("\n\033[1m(#)\033[0m Clearing the database..\n")
                # Clear database logic
                reddit.clear_database_entries()
                print("\n\033[1m(#)\033[0m Closing program in 5 seconds..\n")
                time.sleep(5)

            else:
                # User did not confirm, do not clear the database
                print("\n\033[1m(#)\033[0m Database not cleared, exiting program in 5 seconds.\n")
                time.sleep(5)
            pass

        if args.ClearEntry:
            # Clear entry logic
            entry = args.ClearEntry

            # Prompt the user for confirmation
            confirmation = input("\n\033[1m(#)\033[0m Are you sure you want to delete the entry '{entry}' (y/[n]): ").strip().lower()

            # Check user input
            if confirmation == 'y':
                # User confirmed, deleting entry from database
                print(f"\n\033[1m(#)\033[0m Removing '{entry}' from the database..\n")
                reddit.remove_entry_by_id(entry)
                time.sleep(5)

            else:
                # User did not confirm, do not clear entry from database
                print("\n\033[1m(#)\033[0m Entry not cleared, exiting program in 5 seconds.\n")
                time.sleep(5)


        if args.ViewSubreddits:
            # View list of subreddits looked through by content search.
            print("\033[1m(#)\033[0m Below is all the currently searched Subreddits.\n")
            
            # Call the view_subreddits() function
            subreddits_entries = reddit.view_subreddits()

            # Define headers for the table
            headers = ["Subreddit", "Enabled"]

            # Print the table using tabulate
            print(tabulate(subreddits_entries, headers=headers, tablefmt="grid"))
            pass

        if args.AddSubreddit:
            # Add subreddit to content search
            subreddit = args.AddSubreddit
            # Logic for adding a Subreddit to content search
            print(f"\033[1m(#)\033[0m Adding '{subreddit}' to the content search list..\n")
            reddit.add_subreddit(subreddit)
            time.sleep(3)

        if args.RemoveSubreddit:
            # Remove subreddit to content search
            subreddit = args.RemoveSubreddit
            # Logic for removing a Subreddit from content search
            print(f"\033[1m(#)\033[0m Removing '{subreddit}' from the content search list..\n")
            reddit.remove_subreddit(subreddit)
            time.sleep(3)

        if args.ViewFilter:
            # View filter logic
            print("\033[1m(#)\033[0m Below is all the currently censored words\n")
            
            # Call the view_filters() function
            filters_entries = reddit.view_filters()

            # Define headers for the table
            headers = ["Filter"]

            # Print the table using tabulate
            print(tabulate(filters_entries, headers=headers, tablefmt="grid"))
            pass

        if args.AddFilter:
            # Add filter logic
            word = args.AddFilter
            # Logic for adding a word to the censored list
            print(f"\033[1m(#)\033[0m Adding '{word}' to the censored list..\n")
            reddit.add_filter(word)
            time.sleep(3)

        if args.RemoveFilter:
            # Remove filter logic
            word = args.RemoveFilter
            # Logic for removing a word from the censored list
            print(f"\033[1m(#)\033[0m Removing '{word}' to the censored list..\n")
            reddit.remove_filter(word)
            time.sleep(3)