import requests  # Used for making HTTP requests, typically for API interactions.
import sqlite3  # Provides a lightweight disk-based database that doesn’t require a separate server process.
from datetime import datetime  # Provides classes for manipulating dates and times.
import praw  # Python Reddit API Wrapper, used for interacting with the Reddit API.
from prawcore.exceptions import Forbidden, RequestException  # Exceptions specific to the PRAW library.
from praw.exceptions import RedditAPIException  # Exceptions specific to the PRAW library.
from ftfy import ftfy  # Fixes mojibake and other glitches in Unicode text.
from tqdm import tqdm  # Provides a progress bar to show the progress of iterative tasks.
from PIL import Image, ImageDraw, ImageFont, ImageOps  # Python Imaging Library, used for image manipulation.
from tiktokvoice import tts, get_duration, merge_audio_files  # Functions for creating and manipulating audio files.
from srt import gen_srt_file  # Library for working with SubRip (SRT) subtitle files.
from editor import VideoEditor  # Custom module for video editing tasks.
import time  # Provides various time-related functions.
import re  # Provides support for regular expressions (regex).
import os  # Provides functions for interacting with the operating system.
import sys  # Provides access to some variables used or maintained by the Python interpreter and to functions that interact strongly with the interpreter.



class RedditAPI:
    def __init__(self, client_id: str = None, client_secret: str = None, username: str = None, password: str = None):
        """
        Initializes a Reddit object with the provided credentials.

        Args:
            client_id (str): The client ID for the Reddit API.
            client_secret (str): The client secret for the Reddit API.
            username (str): The username for the Reddit account.
            password (str): The password for the Reddit account.

        Raises:
            ValueError: If any of the required credentials are not provided.
        """
        # Raise error if the environment variables are not set
        if not client_id:
            raise ValueError(
                "\033[31m\033[1m(#)\033[0m REDDIT_CLIENT_ID not set correctly, delete credentials.txt and setup again.\n")
        if not client_secret:
            raise ValueError(
                "\033[31m\033[1m(#)\033[0m REDDIT_CLIENT_SECRET not set correctly, delete credentials.txt and setup again.\n")
        if not username:
            raise ValueError(
                "\033[31m\033[1m(#)\033[0m REDDIT_USERNAME not set correctly, delete credentials.txt and setup again.\n")
        if not password:
            raise ValueError(
                "\033[31m\033[1m(#)\033[0m REDDIT_PASSWORD not set correctly, delete credentials.txt and setup again.\n")

        # Create the Reddit instance
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent='RSCG',
            username=username,
            password=password)
        # Set the config to decode HTML entities
        self.reddit.config.decode_html_entities = True

        # Connect to SQLite database
        self.conn = sqlite3.connect('database.db')
        self.c = self.conn.cursor()

        # Create posts table if not exists
        self.c.execute('''CREATE TABLE IF NOT EXISTS posts
                          (id TEXT PRIMARY KEY,
                           subreddit TEXT,
                           title TEXT,
                           content TEXT,
                           likes INTEGER,
                           author TEXT,
                           created_utc INTEGER,
                           url TEXT)''')
        
        # Create 'subreddits' table
        self.c.execute('''CREATE TABLE IF NOT EXISTS subreddits (
                            id INTEGER PRIMARY KEY,
                            name TEXT UNIQUE,
                            enabled INTEGER DEFAULT 1
                        )''')

        # Create 'filters' table
        self.c.execute('''CREATE TABLE IF NOT EXISTS filters (
                            id INTEGER PRIMARY KEY,
                            word TEXT UNIQUE
                        )''')

        self.conn.commit()
    
    def __del__(self):
        # Close database connection when object is deleted
        self.conn.close()


    def __utc_to_datetimestr(self, utc: float):
        """
        Convert a UTC timestamp to a formatted string representing the corresponding datetime.

        Args:
            utc (float): The UTC timestamp to convert.

        Returns:
            str: The formatted string representing the datetime in the format "dd-mm-yyyy HH:MM:SS".
        """
        # Convert UTC timestamp to datetime object
        self.__datetime_obj = datetime.utcfromtimestamp(float(utc))
        # Convert datetime object to formatted string and return
        return self.__datetime_obj.strftime("%d-%m-%Y %H:%M:%S")
    

    def __filter_content(self, textstr: str):
        """
        Filters the content by replacing certain words and splitting it into sentences.

        Args:
            textstr (str): The input text to be filtered.

        Returns:
            list: A list of filtered sentences.
        """

        # Fetch swear words from the 'filters' table
        self.c.execute("SELECT word FROM filters")
        swear_words = [row[0] for row in self.c.fetchall()]

        # Close database connection
        self.conn.close()

        # Grammar fix for better TTS
        self.__unfiltered = ftfy(textstr)

        # Define the words to check for replacement and their corresponding replacements
        self.__chkWords = ("\n", '."', "UPDATE:", "AITA")
        self.__repWords = (". ", '". ', ". UPDATE:. ", "Am I the asshole")

        # Define a dictionary to store censored versions of swear words
        censored_swear_words = {word: word[0] + '*' * (len(word) - 2) + word[-1] for word in swear_words}

        # Replace all occurrences of check words with replace words
        for check, replace in zip(self.__chkWords, self.__repWords):
            self.__unfiltered = self.__unfiltered.replace(check, replace)

        # Replace swear words with censored versions
        for word, censored_word in censored_swear_words.items():
            self.__unfiltered = self.__unfiltered.replace(word, censored_word)

        # Replace "M" followed by 1-3 digit numbers with "Male "
        self.__unfiltered = re.sub(r'M(\d{1,3})', r'Male \1', self.__unfiltered)

        # Replace "F" followed by 1-3 digit numbers with "Female "
        self.__unfiltered = re.sub(r'F(\d{1,3})', r'Female \1', self.__unfiltered)

        # Split content and filter out empty strings, then return
        return [f"{s.strip()}" for s in self.__unfiltered.split(". ") if len(s) > 1]

    def update_database(self, posts):
        """
        Update the database with Reddit posts.

        Args:
            posts (list): List of Reddit post objects.
        """
        # Initialize tqdm with the total number of posts
        progress_bar = tqdm(total=len(posts), unit="post")
        for post in posts:
            self.c.execute("SELECT * FROM posts WHERE id=?", (post.id,))
            existing_post = self.c.fetchone()
            if existing_post:
                # Check if post content has changed
                if existing_post[3] != post.selftext or existing_post[6] != post.edited:
                    # Update existing post in database
                    self.c.execute("UPDATE posts SET content=?, likes=? WHERE id=?",
                                (post.selftext, post.score, post.id))
                    self.conn.commit()
                    self.generate_post(post.url)
                    # Check if edited content is different
                    if existing_post[3] != post.selftext:
                        # If edited content is different, create a new entry in the database
                        self.c.execute("INSERT INTO posts (id, subreddit, title, content, likes, author, created_utc, url) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                    (post.id, post.subreddit.display_name, post.title, post.selftext,
                                        post.score, post.author.name if post.author else None,
                                        post.created_utc, post.url))
                        self.conn.commit()
                        # Print statement for the new entry with edited content
                        print(f"\033[1m(#)\033[0m A new entry has been added for edited content by {post.author} titled '{post.title}' posted on {post.created_utc}.\n")
            else:
                # Add new post to database
                self.c.execute("INSERT INTO posts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (post.id, post.subreddit.display_name, post.title, post.selftext,
                                post.score, post.author.name if post.author else None,
                                post.created_utc, post.url))
                self.conn.commit()
                self.generate_post(post.url)
            # Update the progress bar
            progress_bar.update(1)
        # Close the progress bar
        progress_bar.close()

    def fetch_all_posts(self):
        """
        Fetch all posts from the database.
        """
        self.c.execute("SELECT * FROM posts")
        return self.c.fetchall()

    def generate_post(self, url):
        """
        Generate post based on URL.

        Args:
            url (str): URL of the post.
        """
        #print("Generating post for URL:", url)
        # Your implementation here

    def get_updated_posts(self, threshold_likes=1000):
        """
        Get updated Reddit posts from subreddits.

        Args:
            subreddits (list): List of subreddit names.
            threshold_likes (int): Threshold for number of likes.

        Returns:
            list: List of Reddit post objects.
        """
        updated_posts = []
        subreddits = self.view_subreddits()
        for subreddit_name in subreddits:
            subreddit = self.reddit.subreddit(subreddit_name)
            for post in subreddit.top(limit=100):  # Limit to avoid hitting API limits
                if post.score >= threshold_likes:
                    self.c.execute("SELECT * FROM posts WHERE id=?", (post.id,))
                    existing_post = self.c.fetchone()
                    if existing_post:
                        # Check if post content has changed
                        if existing_post[3] != post.selftext or existing_post[6] != post.edited:
                            updated_posts.append(post)
                    else:
                        updated_posts.append(post)
        return updated_posts

    def get_from_url(self, url: str):
        """
        Retrieves information about a Reddit post from its URL.

        Parameters:
        - url (str): The URL of the Reddit post.

        Returns:
        - dict: A dictionary containing the following information about the Reddit post:
            - subreddit (str): The name of the subreddit.
            - id (str): The ID of the post.
            - title (str): The title of the post.
            - time (str): The creation time of the post in the format "dd-mm-yyyy hh:mm:ss".
            - original_content (list): The original content of the Reddit post.
            - new_content (list): A list of strings with a maximum of three words in each string.
            - likes (int): The number of likes the post has received.
            - comments (int): The number of comments the post has received.
            - username (str): The username of the poster.
        """
        # Get post from URL
        self.post = self.reddit.submission(url=url)
        # Original content list
        original_content = self.__filter_content(self.post.selftext)
        # Split content into words
        words = self.post.selftext.split()
        # New content list: Group words into lists of strings with a maximum of three words
        new_content = [' '.join(words[i:i+3]) for i in range(0, len(words), 3)]
        
        # Print both content lists
        ##print("New Content:", new_content)
        
        # Check to make sure the user has a profile image
        try:
            # Try to get the profile picture URL
            profile_picture_url = self.post.author.icon_img
        except AttributeError:
            # Use the default profile picture URL
            profile_picture_url = "https://www.redditstatic.com/avatars/defaults/v2/avatar_default_3.png"

        # Check to make sure user has a name and isnt deleted
        try:
            # Try to get the users name
            username = self.post.author.name
        except AttributeError:
            # Use the default profile picture URL
            username = "Deleted User"

        return {
            "subreddit": self.post.subreddit.display_name,
            "id": self.post.id,
            "title": self.post.title,
            "time": self.__utc_to_datetimestr(self.post.created_utc).split()[1],  # Extracting time part only
            "date_posted": self.__utc_to_datetimestr(self.post.created_utc).split()[0],  # Extract date part
            "content": original_content,
            "new_content": new_content,
            "likes": self.post.score,
            "comments": self.post.num_comments,
            "username": username, 
            "profile_picture_url": profile_picture_url

        }
        


    def get_top_posts(self, subreddit: str, limit: int = 10):
        """
        Retrieves the top posts from a specified subreddit.

        Args:
            subreddit (str): The name of the subreddit.
            limit (int, optional): The maximum number of posts to retrieve. Defaults to 10.

        Returns:
            list: A list of dictionaries containing information about each top post.
                Each dictionary contains the following keys:
                - subreddit: The name of the subreddit.
                - id: The unique identifier of the post.
                - title: The title of the post.
                - time: The creation time of the post.
                - content: The filtered content of the post.
        """
        # Set the subreddit
        self.subreddit = self.reddit.subreddit(subreddit)

        self.final = []  # Init final list to store data
        # Get top posts from subreddit
        for iter_post in self.subreddit.top(limit=limit):
            self.final.append({
                "subreddit": iter_post.subreddit.display_name,
                "id": iter_post.id,
                "title": iter_post.title,
                "time": self.__utc_to_datetimestr(iter_post.created_utc),
                "content": self.__filter_content(iter_post.selftext)
            })
        return self.final
    
    def add_text(self, draw, text, position, font, size, color, max_width=None, max_height=None):
        """
        Adds text to the image with optional wrapping based on maximum width and height.

        Args:
            draw (ImageDraw): The ImageDraw object for drawing text on the image.
            text (str): The text to be added.
            position (tuple): The position where the text should start (x, y).
            font (str): The path to the font file.
            size (int): The font size.
            color (str): The color of the text.
            max_width (int, optional): The maximum width for the wrapped text.
            max_height (int, optional): The maximum height for the wrapped text.

        Returns:
            None
        """
        # Load the font
        font = ImageFont.truetype(font, size)

        # Check if maximum width and height are specified
        if max_width is not None and max_height is not None:
            # Split the text into words
            words = text.split()

            # Initialize variables for wrapped text
            wrapped_text = ''
            line = ''
            lines = []

            # Iterate over each word and wrap text based on max width
            for word in words:
                # Check if adding the word exceeds the max width
                if draw.textlength(line + ' ' + word, font=font) <= max_width:
                    # If not, add the word to the current line
                    line += ' ' + word if line else word
                else:
                    # If adding the word exceeds the max width, start a new line
                    lines.append(line)
                    line = word

            # Add the last line
            lines.append(line)

            # Reset text to wrapped lines
            text = '\n'.join(lines)

        # Draw the text on the image
        draw.text(position, text, font=font, fill=color)

        return

    def generateVideo(self, url):
        # Get the post from the URL
        post = self.get_from_url(url)

        # Split the time string and keep only the hours and minutes
        time_parts = post["time"].split(":")
        # Reconstruct the time string with only hours and minutes
        time_only_hh_mm = ":".join(time_parts[:2])

        # Print to termninal what content we are generating 
        print("\n \033[1m(#)\033[0m Generating video content for, " + post["username"] + " - " + post["title"] + " - " + post["date_posted"])

        # Print the post details
        #print("\n \033[1m Subred:\033[0m", post["subreddit"])
        #print("\033[1m ID:\033[0m", post["id"])
        #print("\033[1m Title:\033[0m", post["title"])
        #print("\033[1m Time:\033[0m", time_only_hh_mm)
        #print("\033[1m Date posted:\033[0m", post["date_posted"])
        #print("\033[1m No. of lines:\033[0m", len(post["content"]))
        #print("\033[1m Likes:\033[0m", post["likes"])
        #print("\033[1m Comments:\033[0m", post["comments"])
        #print("\033[1m Username:\033[0m", post["username"])
        #print("\033[1m Profile picture:\033[0m", post["profile_picture_url"])
        #print("\n")


        #print("\033[1m(#)\033[0m Generating Redit Post Mockup")
        # Load the image from input path
        background_image_path = "inputs/6365678-ai.png"
        background_image = Image.open(background_image_path)
        draw = ImageDraw.Draw(background_image)

        # Define font settings
        font_roboto_medium = "fonts/Roboto-Medium.ttf"
        font_roboto = "fonts/Roboto-Regular.ttf"
        font_roboto_light = "fonts/Roboto-Light.ttf"

        # Define maximum width and height for the title
        max_title_width = 501  # Maximum width in pixels
        max_title_height = 68  # Maximum height in pixels

        # Add text to the image
        self.add_text(draw, post["username"], (188, 78), font_roboto_medium, 24, "#000000")  # Username
        self.add_text(draw, post["title"], (103, 141), font_roboto, 20, "#000000", max_width=max_title_width, max_height=max_title_height)  # Title
        self.add_text(draw, (time_only_hh_mm + "  .  "), (104, 274), font_roboto, 13.4, "#b0b0b0")  # Time
        self.add_text(draw, post["date_posted"], (150, 274), font_roboto, 13.4, "#b0b0b0")  # Date
        self.add_text(draw, str(post["likes"]), (240, 310), font_roboto_light, 12.34, "#666666")  # Likes
        self.add_text(draw, str(post["comments"]), (127, 310), font_roboto_light, 12.34, "#666666")  # Comments

        profile_pic_url = post["profile_picture_url"]
        response = requests.get(profile_pic_url)
        if response.status_code == 200:
            profile_pic_path = "temp/profile_pic.png"
            with open(profile_pic_path, "wb") as f:
                f.write(response.content)

            # Load profile picture and mask
            profile_pic = Image.open(profile_pic_path)
            mask = Image.open('inputs/mask.png').convert('L')

            # Resize profile picture to fit the mask
            output = ImageOps.fit(profile_pic, mask.size, centering=(0.5, 0.5))
            output.putalpha(mask)

            # Paste profile picture onto the main image
            background_image.paste(output, (int(102.72), int(51.6)), output)

            # Save the modified image to output path
            output_path = f"temp/redit_mockup.png"
            background_image.save(output_path)
        else:
            print("\033[1m(#)\033[0m Failed to download the profile picture, using default.\n")
            # Save the modified image to output path without the profile picture
            output_path = f"temp/redit_mockup.png"
            background_image.save(output_path)


        # Ask if the user wants to proceed
        #proceed = input("Do you want to proceed? (Y/n)\n")
        #if not proceed:
        #    proceed = "y"
        #if proceed.lower() != "y":
        #    print("\033[1m(#)\033[0m Exiting")
        #    exit(0)
        proceed = "y"

        #print("\033[1m(#)\033[0m Generating TTS")
        # Create the audio files for each sentence using the script
        script = []
        shorteneddialoguescript = []
        content = [post["title"]] + post["content"]
        new_content = [post["title"]] + post["new_content"]

        # TTS for Voice over
        with tqdm(total=len(content), desc="Generating TTS", unit="file") as pbar:
            for item, i in zip(content, range(len(content))):
                filename = f"temp/temp_{post['id']}_{i}.mp3"
                tts(item, "en_us_006", filename, 1.15)
                dur = get_duration(filename)
                script.append((item, dur))
                pbar.update(1)

        # Clearing the progress bar from the terminal
        sys.stdout.write("\033[F")  # Move cursor up one line
        sys.stdout.write("\033[K")  # Clear line


        # Create the srt using the script
        srt_path = f"inputs/{post['id']}.srt"
        gen_srt_file(script, srt_path, 0.1)

        # Merge the audio files into one
        wav_path = f"inputs/{post['id']}.wav"
        totaldur = merge_audio_files(wav_path, 0.1)
        #print("\033[1m(#)\033[0m Merged audio duration:", totaldur, "seconds")

        # Create the video
        video_title = str(post["username"] + " - " + post["title"] + " - " + post["date_posted"])
        v = VideoEditor(totaldur, srt_path, wav_path, False)
        v.start_render(f"outputs/{video_title}.mp4")

        # Clean up the temp directory
        files_to_delete = os.listdir("temp")
        with tqdm(total=len(files_to_delete), desc="Deleting files", unit="file") as pbar:
            # Iterate over the files in the directory and delete them
            for filename in files_to_delete:
                filepath = os.path.join("temp", filename)
                try:
                    if os.path.isfile(filepath):
                        os.remove(filepath)
                        pbar.update(1)  # Update progress bar
                except Exception as e:
                    print(f"\033[31m\033[1m(#)\033[0m Error occurred while deleting {filename}: {str(e)}")
                    print("\n") # Used so the progress bar wont clear the error

        # Clearing the progress bar from the terminal
        sys.stdout.write("\033[F")  # Move cursor up one line
        sys.stdout.write("\033[K")  # Clear line
   
    def process_unmade_videos(self):
        """
        Process posts with video_made set to False.
        """
        # Fetch posts where video_made is False
        self.c.execute("SELECT id, url FROM posts WHERE video_made = 0")
        unmade_videos = self.c.fetchall()
        
        # Iterate through unmade videos and generate video with progress bar
        for post_id, post_url in tqdm(unmade_videos, desc="Generating Videos", unit="video"):
            try:
                # Call generateVideo method of the current instance
                self.generateVideo(post_url)
                
                # Update video_made to True for the processed post
                self.c.execute("UPDATE posts SET video_made = 1 WHERE id = ?", (post_id,))
                self.conn.commit()
            except Exception as e:
                print(f"\033[31m\033[1m(#)\033[0m Error generating video for post ID {post_id}: {e}\n")
                self.c.execute("UPDATE posts SET video_made = 3 WHERE id = ?", (post_id,))
                self.conn.commit()
                continue  # Move to the next iteration if an error occurs


    def retry_errors(self):
        """
        Retry generating videos for posts that previously encountered errors.
        """
        # Fetch posts where video_made is 3 (failed)
        self.c.execute("SELECT id, url FROM posts WHERE video_made = 3")
        error_videos = self.c.fetchall()
        
        # Iterate through error videos and attempt to generate video with progress bar
        for post_id, post_url in tqdm(error_videos, desc="Retrying Errors", unit="video"):
            try:
                # Call generateVideo method of the current instance
                self.generateVideo(post_url)
                
                # Update video_made to 1 for the successfully processed post
                self.c.execute("UPDATE posts SET video_made = 1 WHERE id = ?", (post_id,))
                self.conn.commit()
            except Exception as e:
                print(f"\033[31m\033[1m(#)\033[0m Error retrying video for post ID {post_id}: {e}\n")
                continue  # Move to the next iteration if an error occurs


    def check_for_similar_titles(self):
        """
        Check for new posts with similar titles by previous posters in the database.
        """
        try:
            # Fetch all authors from the database
            self.c.execute("SELECT DISTINCT author FROM posts")
            authors = self.c.fetchall()

            # Initialize tqdm with the total number of authors
            progress_bar = tqdm(authors, desc="Checking for similar titles", unit="author")

            # Iterate over each author
            for author in progress_bar:
                author = author[0]
                # Fetch all posts by the author
                self.c.execute("SELECT title FROM posts WHERE author=?", (author,))
                titles = self.c.fetchall()
                titles = [title[0] for title in titles]  # Extract titles from tuples

                # Fetch new posts by the author from Reddit API
                url = f"https://www.reddit.com/user/{author}/submitted/.json"
                headers = {"User-Agent": "ReditStoryCapture/1.0"}

                try:
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()  # Raise exception for 4XX and 5XX status codes
                    data = response.json()

                    # Parse the JSON data and process the submissions
                    for post in data["data"]["children"]:
                        post_data = post["data"]
                        post_title = post_data["title"]
                        post_id = post_data["id"]
                        post_subreddit = post_data["subreddit"]
                        post_selftext = post_data["selftext"]
                        post_score = post_data["score"]
                        post_author = post_data["author"]
                        post_created_utc = post_data["created_utc"]
                        post_url = post_data["url"]

                        if any(title.lower() in post_title.lower() for title in titles):
                            # If similar title found, check if post already exists in the database
                            self.c.execute("SELECT * FROM posts WHERE id=?", (post_id,))
                            existing_post = self.c.fetchone()
                            if not existing_post:
                                # If post doesn't exist, add it to the database
                                self.c.execute("INSERT INTO posts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                    (post_id, post_subreddit, post_title, post_selftext,
                                        post_score, post_author if post_author else None,
                                        post_created_utc, post_url))
                                self.conn.commit()
                                # Generate post for the new update
                                self.generate_post(post_url)
                                # Print statement for the new update
                                print(f"\033[1m(#)\033[0m A new update post has been found by {post_author} titled '{post_title}' posted on {post_created_utc}.\n")

                except requests.RequestException as e:
                    # Suppress printing for 403 Forbidden errors
                    if response.status_code == 403:
                        continue
                except RedditAPIException as e:
                    print(f"\033[31m\033[1m(#)\033[0m Reddit API error: {e}.\n")

            # Close the progress bar
            progress_bar.close()

        except Exception as e:
            print(f"\033[31m\033[1m(#)\033[0m An unexpected error occurred when looking for update content: {e}.\n")
        # Implement rate limiting to avoid exceeding API limits
        finally:
            time.sleep(0.5)  # Sleep for 0.5 seconds to avoid rate limiting


    def clear_database_entries(self):
        """
        Clear all entries in the database.
        """
        try:
            # Clear all entries from the 'posts' table
            self.c.execute("DELETE FROM posts")
            self.conn.commit()
            print("\033[1m(#)\033[0m All entries cleared from the database.")
        except Exception as e:
            print(f"\033[31m\033[1m(#)\033[0m Error clearing database entries: {e}\n")


    def remove_entry_by_id(self, post_id):
        """
        Remove an entry from the database by its post ID.
        """
        try:
            # Remove the entry with the specified post ID from the 'posts' table
            self.c.execute("DELETE FROM posts WHERE id = ?", (post_id,))
            self.conn.commit()
            print("\033[1m(#)\033[0m Entry with post ID", post_id, "removed from the database.")
        except Exception as e:
            print(f"\033[31m\033[1m(#)\033[0m Error removing entry with post ID {post_id}: {e}\n")

    def view_subreddits(self):
        """
        View all entries in the 'subreddits' table.
        """
        self.c.execute("SELECT * FROM subreddits")
        return self.c.fetchall()

    def add_subreddit(self, name, enabled=1):
        """
        Add a new subreddit entry to the 'subreddits' table.
        """
        try:
            self.c.execute("INSERT INTO subreddits (name, enabled) VALUES (?, ?)", (name, enabled))
            self.conn.commit()
            print("\033[1m(#)\033[0m Subreddit", name, "added to the 'subreddits' table.")
        except sqlite3.IntegrityError:
            print(f"\033[31m\033[1m(#)\033[0m Subreddit {name} already exists in the 'subreddits' table.\n")

    def remove_subreddit(self, name):
        """
        Remove a subreddit entry from the 'subreddits' table.
        """
        try:
            self.c.execute("DELETE FROM subreddits WHERE name = ?", (name,))
            self.conn.commit()
            print("\033[1m(#)\033[0m Subreddit", name, "removed from the 'subreddits' table.")
        except sqlite3.IntegrityError:
            print(f"\033[31m\033[1m(#)\033[0m Subreddit {name} does not exist in the 'subreddits' table.\n")

    def disable_subreddit(self, subreddit_name):
        """
        Disable a subreddit by setting its 'enabled' status to 0 in the database.

        Args:
            subreddit_name (str): The name of the subreddit to disable.
        """
        try:
            # Update the 'enabled' status of the specified subreddit to 0
            self.c.execute("UPDATE subreddits SET enabled = 0 WHERE subreddit = ?", (subreddit_name,))
            self.conn.commit()
            print(f"Subreddit '{subreddit_name}' disabled successfully.")
        except sqlite3.Error as e:
            print(f"Error disabling subreddit '{subreddit_name}': {e}")        


    def view_filters(self):
        """
        View all entries in the 'filters' table.
        """
        self.c.execute("SELECT * FROM filters")
        return self.c.fetchall()

    def add_filter(self, word):
        """
        Add a new word entry to the 'filters' table.
        """
        try:
            self.c.execute("INSERT INTO filters (word) VALUES (?)", (word,))
            self.conn.commit()
            print("\033[1m(#)\033[0m Filter word", word, "added to the 'filters' table.")
        except sqlite3.IntegrityError:
            print(f"\033[31m\033[1m(#)\033[0m Filter word {word} already exists in the 'filters' table.\n")

    def remove_filter(self, word):
        """
        Remove a word entry from the 'filters' table.
        """
        try:
            self.c.execute("DELETE FROM filters WHERE word = ?", (word,))
            self.conn.commit()
            print("\033[1m(#)\033[0m Filter word", word, "removed from the 'filters' table.")
        except sqlite3.IntegrityError:
            print(f"\033[31m\033[1m(#)\033[0m Filter word {word} does not exist in the 'filters' table.\n")
