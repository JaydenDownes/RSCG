<a name="top"></a>

<h1 align="center">
Reddit Short-Form Content Generator 
</h1>

<br/>

> [!IMPORTANT]
> This software is currently under active development and may contain bugs or other issues. It is provided without warranty of any kind. By using this software, you acknowledge and accept that your use is at your own risk, and the developers are not liable for any damages or consequences arising from its use.

Reddit Short-Form Content Generator is a powerful yet user-friendly software designed to streamline the creation of short-form content for social media platforms. It automates the generation of videos using text-to-speech (TTS) technology and Moviepy, allowing users to quickly and easily produce engaging content. With features for automating the uploading process and creating mockups, RSCG simplifies content creation for users of all skill levels. Eventually, this project aims to be accessible to end-users with no prior coding experience. Join us on this journey as we continue to enhance and improve Short-Form Content generation for creators everywhere.


## How to setup:

### Step 1: Download RSCG and all dependencies

1. Download Python for you computer
2. Download RSCG by using git clone or clicking on the green **Code** button and clicking **Download Zip**
3. Extract and open the folder in any terminal app
4. Run ```pip install -r requirements.txt```
5. **FFMPEG** is an important requirement needed to render the final video, follow setup [here](https://gist.github.com/barbietunnie/47a3de3de3274956617ce092a3bc03a1). Downloading on windows will also require 7Zip to unpack the file, which can be downloaded from [here](https://www.7-zip.org/download.html).
6. **ImageMagick** is another requirement, which can be downloaded [here](https://imagemagick.org/script/download.php#windows) for windows. For other operating systems visit [here](https://imagemagick.org/script/download.php).


### Step 2: Obtaining Reddit API Credentials

1. Go to [Reddit](https://www.reddit.com/) and log in (I would recommend creating a throwaway account)
2. Navigate to [Reddit Apps](https://www.reddit.com/prefs/apps).
3. Scroll down to the "Developed Applications" section and click on the "Create App" button.
4. Fill out the required fields:
   - **Name**: Choose a name for your application.
   - **App type**: Select "Script".
   - **About URL**: You can leave this blank.
   - **Redirect URI**: Enter `http://localhost:8080`.
5. Click on the "Create app" button.
6. After creating the app, you'll see your **client ID** and **client secret**. Keep these safe; you'll need them to authenticate your application.

### Step 3: Run RSCG script

1. After downloading RSCG open the folder in any terminal
2. **Run** `python main.py`. - (try `python3 main.py` if it doesnt work)
3. On first run it will run through setup where you put in the credentials you got from Step 2 (Setup once the first time you run it)
4. You will need to put a mp4 video that will be used as a background video into the **inputs** folder, the longer the video the better.
5. After setting up you can enter any reddit link into the program and it will create a tiktok style video in the **outputs** folder


### Command Line Parameters (optional)
##### Content Generation Options:
Command | Details
--- | ---
`-a` or `-Auto` | Program will attempt to search for and generate new content every 30 minutes (can be changed in main.py)
`-cs` or `-ContentSearch` | Program will only attempt to find and store new content in database
`-ucs` or `-UpdateContentSearch` | Program will only attempt to find update content for videos already in the database, not new content.
`-cc <url>` or `-CreateContent <url>` | Program will generate videos for entries stored in the database that dont have a pre-exisitng video generated.
`-gv <url>` or `-GenerateVideo <url>` | used to generate video for a specified reddit post.
`-re` or `-RetryErrors` | used to retry generating video that previously encountered errors when proccessing
&nbsp; | &nbsp;


##### Database Options:
Command | Details
--- | ---
`-cd` or `-ClearDatabase` | Clears all videos in the database
`-ce` or `-ClearEntry` | Clears entry submisison in the database
`-vs` or `-viewsubreddits` | View subreddits that will be searched by content search.
`-as <subreddit>` or `-addsubreddit <subreddit>` | Add a subreddit that will be searched by content search..
`-rs <subreddit>` or `-removefilter <subreddit>` | Remove a subreddit that will be searched by content search.
`-vf` or `-viewfilter` | Produces a list of words in the censored list.
`-af <word>` or `-addfilter <word>` | Adds word to censored list.
`-rf <word>` or `-removefilter <word>` | Removes word from censored list.
