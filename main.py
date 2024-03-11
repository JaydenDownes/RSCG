from reddit import RedditAPI
from tiktokvoice import tts, get_duration, merge_audio_files
from srt import gen_srt_file
from editor import VideoEditor
from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests
import datetime
import subprocess
import os


def setup_credentials():
    print("\n"*10, "-"*30, "\nSetting up the credentials\n")
    print("You will need to create a Reddit app and get the client id and client secret\n")
    print("You will also need to enter your Reddit username and password\n")
    print("These credentials will be stored in a file called credentials.txt\n")
    print("This file will be stored locally and will only be used to authenticate with Reddit and to get the post text\n")
    print("Goto https://github.com/Krishpkreame/RSCG and follow the instructions\n")
    print("I would recommend creating a new throwaway Reddit account\n")
    print("This will only run the first time you run the program\n")
    client_id = input("Enter the client id:\n")
    client_secret = input("Enter the client secret:\n")
    username = input("Enter the username:\n")
    password = input("Enter the password:\n")
    with open("credentials.txt", "w") as f:
        f.write(f"{client_id}\n{client_secret}\n{username}\n{password}")

# Function to add text to the image
def add_text(draw, text, position, font, size, color):
    font = ImageFont.truetype(font, size)
    draw.text(position, text, font=font, fill=color)


if __name__ == "__main__":
    # Check if ffmpeg is installed
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("\033[1m(#)\033[0m ffmpeg is not installed. Please install ffmpeg to continue.")
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

    # Check if any mp4 files are present in the inputs folder
    if len([i for i in os.listdir("inputs") if i.endswith(".mp4")]) == 0:
        print("No input video files found in the inputs folder, Add your input video files to this folder")
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
        print("\033[1m(#)\033[0m Credentials not set correctly, delete credentials.txt and setup again")
        exit(1)

    print("\033[1m \n", 
        "  ___  ___  ___ ___  \n ", 
        "| _ \/ __|/ __/ __| \n ", 
        "|   /\__ \ (_| (_ | \n ", 
        "|_|_\|___/\___\___| \n ", 
        "Reddit Short-Form Content Generator V2.0 \033[0m \n ")

    #url = input("Enter the Reddit post URL:\n")
    # Temporary Code
    #if not url:
    #    url = "https://www.reddit.com/r/confessions/comments/1bbleao/i_jaywalked_once/"
    url = "https://www.reddit.com/r/confessions/comments/1bbleao/i_jaywalked_once/"

    # Get the post from the URL
    post = reddit.get_from_url(url)

    # Split the time string and keep only the hours and minutes
    time_parts = post["time"].split(":")
    # Reconstruct the time string with only hours and minutes
    time_only_hh_mm = ":".join(time_parts[:2])

    # Print the post details
    print("\033[1m Subred:\033[0m", post["subreddit"])
    print("\033[1m ID:\033[0m", post["id"])
    print("\033[1m Title:\033[0m", post["title"])
    print("\033[1m Time:\033[0m", time_only_hh_mm)
    print("\033[1m Date posted:\033[0m", post["date_posted"])
    print("\033[1m No. of lines:\033[0m", len(post["content"]))
    print("\033[1m Likes:\033[0m", post["likes"])
    print("\033[1m Comments:\033[0m", post["comments"])
    print("\033[1m Username:\033[0m", post["username"])
    print("\033[1m Profile picture:\033[0m", post["profile_picture_url"])

    # Ask if the user wants to proceed
    #proceed = input("Do you want to proceed? (Y/n)\n")
    #if not proceed:
    #    proceed = "y"
    #if proceed.lower() != "y":
    #    print("(#) Exiting")
    #    exit(0)
    proceed = "y"

    print("\033[1m(#)\033[0m Generating Redit Post Mockup")
    # Load the image from input path
    background_image_path = "inputs/6365678-ai.png"
    background_image = Image.open(background_image_path)
    draw = ImageDraw.Draw(background_image)

    # Define font settings
    font_roboto_medium = "fonts/Roboto-Medium.ttf"
    font_roboto = "fonts/Roboto-Regular.ttf"
    font_roboto_light = "fonts/Roboto-Light.ttf"

    # Add text to the image
    add_text(draw, post["username"], (188, 78), font_roboto_medium, 24, "#000000")  # Username
    add_text(draw, post["title"], (103, 141), font_roboto, 20, "#000000")  # Title
    add_text(draw, (time_only_hh_mm + "  .  "), (104, 274), font_roboto, 13.4, "#b0b0b0")  # Time
    add_text(draw, post["date_posted"], (150, 274), font_roboto, 13.4, "#b0b0b0")  # Date
    add_text(draw, str(post["likes"]), (240, 310), font_roboto_light, 12.34, "#666666")  # Likes
    add_text(draw, str(post["comments"]), (127, 310), font_roboto_light, 12.34, "#666666")  # Comments

    profile_pic_url = post["profile_picture_url"]
    response = requests.get(profile_pic_url)
    if response.status_code == 200:
        profile_pic_path = "profile_pic.png"
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
        output_path = f"outputs/temp_redit_mockup.png"
        background_image.save(output_path)
    else:
        print("Failed to download the profile picture.")

    # Save the modified image to output path
    output_path = f"outputs/{post['id']}.png"
    background_image.save(output_path)


    # Ask if the user wants to proceed
    #proceed = input("Do you want to proceed? (Y/n)\n")
    #if not proceed:
    #    proceed = "y"
    #if proceed.lower() != "y":
    #    print("\033[1m(#)\033[0m Exiting")
    #    exit(0)
    proceed = "y"

    print("\033[1m(#)\033[0m Generating TTS")
    # Create the audio files for each sentence using the script
    script = []
    shorteneddialoguescript = []
    content = [post["title"]] + post["content"]
    new_content = [post["title"]] + post["new_content"]

    # TTS for Voice over
    for item, i in zip(content, range(0, len(content))):
        filename = f"outputs/temp_{post['id']}_{i}.mp3"
        tts(item, "en_us_007", filename, 1.15)
        dur = get_duration(filename)
        script.append((item, dur))
    print("\033[1m(#)\033[0m Created audio files for script")

    # TTS Duration for shortnened subtitles
    for item, i in zip(new_content, range(0, len(new_content))):
        filename = f"outputs/temp_{post['id']}_{i}_2.mp3"
        tts(item, "en_us_007", filename, 1.15)
        dur = get_duration(filename)
        shorteneddialoguescript.append((item, dur))
    print("\033[1m\033[1m(#)\033[0m\033[0m Got durations for shortned dialogue script")
    

    # Create the srt using the script
    srt_path = f"inputs/{post['id']}.srt"
    gen_srt_file(script, srt_path, 0.1)

    # Create TTS Duration for shortnened subtitles scrtipt
    srt_path = f"inputs/{post['id']}_2.srt"
    gen_srt_file(shorteneddialoguescript, srt_path, 0.1)

    # Merge the audio files into one
    wav_path = f"inputs/{post['id']}.wav"
    totaldur = merge_audio_files(wav_path, 0.1)
    print("\033[1m(#)\033[0m Merged audio duration:", totaldur, "seconds")

    # Create the video
    v = VideoEditor(totaldur, srt_path, wav_path, False)
    v.start_render(f"outputs/{post['id']}.mp4")
