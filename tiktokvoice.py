# author: GiorDior aka Giorgio
# date: 12.06.2023
# topic: TikTok-Voice-TTS
# version: 1.0
# credits: https://github.com/oscie57/tiktok-voice

import os  # Provides functions for interacting with the operating system.
import time  # Provides various time-related functions.
from pydub import AudioSegment  # Library for audio manipulation.
import threading  # Provides support for threading.
import requests  # Used for making HTTP requests, typically for API interactions.
import base64  # Provides functions for encoding and decoding data using Base64 encoding.
from tqdm import tqdm  # Provides a progress bar to show the progress of iterative tasks.
import sys  # Provides access to some variables used or maintained by the Python interpreter and to functions that interact strongly with the interpreter.

COUNT = 0
VOICES = [
    # ENGLISH VOICES
    'en_au_001',                  # English AU - Female
    'en_au_002',                  # English AU - Male
    'en_uk_001',                  # English UK - Male 1
    'en_uk_003',                  # English UK - Male 2
    'en_us_001',                  # English US - Female (Int. 1)
    'en_us_002',                  # English US - Female (Int. 2)
    'en_us_006',                  # English US - Male 1
    'en_us_007',                  # English US - Male 2
    'en_us_009',                  # English US - Male 3
    'en_us_010',                  # English US - Male 4

    # OTHER
    'en_male_narration',           # narrator
    'en_male_funny',               # wacky
    'en_female_emotional',         # peaceful
]

ENDPOINTS = ['https://tiktok-tts.weilnet.workers.dev/api/generation',
             "https://tiktoktts.com/api/tiktok-tts"]
current_endpoint = 0
# in one conversion, the text can have a maximum length of 300 characters
TEXT_BYTE_LIMIT = 300

# create a list by splitting a string, every element has n chars


def split_string(string: str, chunk_size: int) -> list[str]:
    words = string.split()
    result = []
    current_chunk = ''
    for word in words:
        # Check if adding the word exceeds the chunk size
        if len(current_chunk) + len(word) + 1 <= chunk_size:
            current_chunk += ' ' + word
        else:
            if current_chunk:  # Append the current chunk if not empty
                result.append(current_chunk.strip())
            current_chunk = word
    if current_chunk:  # Append the last chunk if not empty
        result.append(current_chunk.strip())
    return result

# checking if the website that provides the service is available


def get_api_response() -> requests.Response:
    url = f'{ENDPOINTS[current_endpoint].split("/a")[0]}'
    response = requests.get(url)
    return response

# saving the audio file


def save_audio_file(base64_data: str, filename: str = "output.mp3") -> None:
    audio_bytes = base64.b64decode(base64_data)
    with open(filename, "wb") as file:
        file.write(audio_bytes)

# send POST request to get the audio data


def generate_audio(text: str, voice: str) -> bytes:
    url = f'{ENDPOINTS[current_endpoint]}'
    headers = {'Content-Type': 'application/json'}
    data = {'text': text, 'voice': voice}
    # data = {'text': text, 'voice': voice}
    response = requests.post(url, headers=headers, json=data)
    return response.content

# creates an text to speech audio file


def tts(text: str, voice: str = "none", filename: str = "output.wav", speed: int = 1.0, play_sound: bool = False) -> None:
    # checking if the website is available
    global current_endpoint, COUNT
    # print("\033[1m(#)\033[0m Generating TTS")
    # Define a maximum number of retries
    max_retries = 3

    # Retry loop
    for attempt in range(max_retries):
        try:
            # Check if the API is available
            if get_api_response().status_code == 200:
                # print("tts online", COUNT)
                COUNT += 1
                break  # Exit the retry loop if successful
            else:
                # Switch to the alternate endpoint if the first one fails
                current_endpoint = (current_endpoint + 1) % 2
                if get_api_response().status_code == 200:
                    # print("tts online", COUNT)
                    COUNT += 1
                    break  # Exit the retry loop if successful
                else:
                    print("\033[1m(#)\033[0m Service not available, retrying...\n")
        except Exception as e:
            print("\033[1m(#)\033[0m Error occurred while checking API availability:", str(e))

        # Wait for a short duration before retrying
        time.sleep(5)

    else:
        # If all retries fail, print an error message and return
        print("\033[1m(#)\033[0m Maximum retries reached, unable to access the service.\n")
        return

    # The rest of the function remains unchanged
    # checking if arguments are valid
    if voice == "none":
        print("\033[1m(#)\033[0m No voice has been selected.\n")
        return

    if not voice in VOICES:
        print("\033[1m(#)\033[0m Voice does not exist.\n")
        return

    if len(text) == 0:
        print("\033[1m(#)\033[0m Insert a valid text.\n")
        return

    # creating the audio file
    try:
        if len(text) < TEXT_BYTE_LIMIT:
            audio = generate_audio((text), voice)
            if current_endpoint == 0:
                audio_base64_data = str(audio).split('"')[5]
            else:
                audio_base64_data = str(audio).split('"')[3].split(",")[1]

            if audio_base64_data == "error":
                print("\033[1m(#)\033[0m This voice is unavailable right now. \n")
                return

        else:
            # Split longer text into smaller parts
            text_parts = split_string(text, 299)
            audio_base64_data = [None] * len(text_parts)

            # Define a thread function to generate audio for each text part
            def generate_audio_thread(text_part, index):
                audio = generate_audio(text_part, voice)
                if current_endpoint == 0:
                    base64_data = str(audio).split('"')[5]
                else:
                    base64_data = str(audio).split('"')[3].split(",")[1]

                if audio_base64_data == "error":
                    print("\033[1m(#)\033[0m This voice is unavailable right now. \n")
                    return "error"

                audio_base64_data[index] = base64_data

            threads = []
            for index, text_part in enumerate(text_parts):
                # Create and start a new thread for each text part
                thread = threading.Thread(
                    target=generate_audio_thread, args=(text_part, index))
                thread.start()
                threads.append(thread)

            # Wait for all threads to complete
            for thread in tqdm(threads, desc="Generating Audio"):
                thread.join()

            # Concatenate the base64 data in the correct order
            audio_base64_data = "".join(audio_base64_data)

        save_audio_file(audio_base64_data, filename)
        #print(f"'{filename}' saved.")

        if speed != 1.0:
            audio = AudioSegment.from_file(filename, format="mp3")
            final = audio.speedup(playback_speed=speed)
            final.export(filename, format="mp3")

        if play_sound:
            print("\033[1m(#)\033[0m Wont be playing sound, as it is not supported in this environment. \n")

    except Exception as e:
        print("\033[1m(#)\033[0m Error occurred while generating audio:", str(e))


def get_duration(filename: str) -> float:
    """
    Calculate the duration of an audio file in seconds.

    Args:
        filename (str): The path to the audio file.

    Returns:
        float: The duration of the audio file in seconds.

    Raises:
        FileNotFoundError: If the audio file is not found.

    """
    try:
        audio = AudioSegment.from_file(filename, format=filename.split(".")[1])
        duration_seconds = len(audio) / 1000
        return round(duration_seconds, 2)
    except FileNotFoundError as e:
        return 0


def merge_audio_files(output_file: str, delay: float = 0.1) -> float:
    """
    Merge multiple mp3 audio files into a single audio file with a small delay between each file.

    Args:
        delay (int): The delay in milliseconds between each audio file. Default is 100 milliseconds.

    Returns:
        float: The duration of the merged audio in seconds.
    """
    # Get all mp3 files in the temp directory
    mp3_files = [file for file in os.listdir(
        "temp") if file.endswith(".mp3")]

    # Sort the files in number order
    mp3_files.sort(key=lambda x: int(x.split("_")[2].split(".")[0]))

    # Create an empty AudioSegment object
    merged_audio = AudioSegment.silent(duration=0)

   # Iterate over the mp3 files and append them to the merged_audio with a small delay
    with tqdm(total=len(mp3_files), desc="Merging Audio") as pbar:
        for i, file in enumerate(mp3_files):
            audio = AudioSegment.from_file(os.path.join("temp", file), format="mp3")
            if i == 0:
                merged_audio += audio
            else:
                merged_audio += AudioSegment.silent(duration=(delay * 1000)) + audio
            pbar.update(1)

    # Clearing the progress bar from the terminal
    sys.stdout.write("\033[F")  # Move cursor up one line
    sys.stdout.write("\033[K")  # Clear line

    # Export the merged audio as a single mp3 file
    merged_audio.export(output_file, format="wav")

    # Remove all the mp3 files from the temp directory
    with tqdm(total=len(mp3_files), desc="Removing MP3 files") as pbar:
        for file in mp3_files:
            os.remove(os.path.join("temp", file))
            pbar.update(1)

    # Clearing the progress bar from the terminal
    sys.stdout.write("\033[F")  # Move cursor up one line
    sys.stdout.write("\033[K")  # Clear line

    # Return the duration of the merged audio in seconds
    return len(merged_audio) / 1000
