import requests
import sqlite3
from datetime import datetime
import praw
from prawcore.exceptions import Forbidden, RequestException
from praw.exceptions import RedditAPIException
from ftfy import ftfy
from tqdm import tqdm
import time

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
                "REDDIT_CLIENT_ID not set correctly, delete credentials.txt and setup again")
        if not client_secret:
            raise ValueError(
                "REDDIT_CLIENT_SECRET not set correctly, delete credentials.txt and setup again")
        if not username:
            raise ValueError(
                "REDDIT_USERNAME not set correctly, delete credentials.txt and setup again")
        if not password:
            raise ValueError(
                "REDDIT_PASSWORD not set correctly, delete credentials.txt and setup again")

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
        self.conn = sqlite3.connect('reddit_posts.db')
        self.c = self.conn.cursor()

        # Create table if not exists
        self.c.execute('''CREATE TABLE IF NOT EXISTS posts
                          (id TEXT PRIMARY KEY,
                           subreddit TEXT,
                           title TEXT,
                           content TEXT,
                           likes INTEGER,
                           author TEXT,
                           created_utc INTEGER,
                           url TEXT)''')
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
        
        # Grammer fix for better TTS
        self.__unfiltered = ftfy(textstr)
        # Check words matched with replace words
        self.__chkWords = ("\n", '."', "UPDATE:", "AITA")
        self.__repWords = (". ", '". ', ". UPDATE:. ", "Am I the asshole")

        # Replace all occurrences of check words with replace words
        for check, replace in zip(self.__chkWords, self.__repWords):
            self.__unfiltered = self.__unfiltered.replace(check, replace)

        # Split content and filter out empty strings, then return
        return [f"{s.strip()}" for s in self.__unfiltered.split(". ") if len(s) > 1]


    def update_database(self, posts):
        """
        Update the database with Reddit posts.

        Args:
            posts (list): List of Reddit post objects.
        """
        # Initialize tqdm with the total number of posts
        progress_bar = tqdm(total=len(posts))
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
                        print(f"\n \033[1m(#)\033[0m A new entry has been added for edited content by {post.author} titled '{post.title}' posted on {post.created_utc}")
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

    def get_updated_posts(self, subreddits, threshold_likes=1000):
        """
        Get updated Reddit posts from specified subreddits.

        Args:
            subreddits (list): List of subreddit names.
            threshold_likes (int): Threshold for number of likes.

        Returns:
            list: List of Reddit post objects.
        """
        updated_posts = []
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
                headers = {"User-Agent": "YourBot/1.0"}

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
                                print(f"\n \033[1m(#)\033[0m A new update post has been found by {post_author} titled '{post_title}' posted on {post_created_utc}")

                except requests.RequestException as e:
                    # Suppress printing for 403 Forbidden errors
                    if response.status_code == 403:
                        continue
                except RedditAPIException as e:
                    print(f"\033[1m(#)\033[0m Reddit API error: {e}")

            # Close the progress bar
            progress_bar.close()

        except Exception as e:
            print(f"\n \033[1m(#)\033[0m An unexpected error occurred when looking for update content: {e}")
        
        # Implement rate limiting to avoid exceeding API limits
        finally:
            time.sleep(0.5)  # Sleep for 0.5 seconds to avoid rate limiting