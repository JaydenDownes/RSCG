from moviepy.video.VideoClip import ImageClip
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
import random
import math
import os

def calculate_title_duration(srt_path):
    """
    Calculate the duration of the first subtitle in the SRT file.

    Args:
        srt_path (str): The path to the SRT file.

    Returns:
        float: The duration of the first subtitle in seconds.
    """
    with open(srt_path, 'r') as file:
        lines = file.readlines()
    
    # Find the start and end times of the first subtitle
    start_time_str, end_time_str = lines[1].split(' --> ')
    
    # Convert start and end times to seconds
    start_time = time_to_seconds(start_time_str.strip())
    end_time = time_to_seconds(end_time_str.strip())
    
    # Calculate duration
    duration = end_time - start_time
    
    return duration

def time_to_seconds(time_str):
    """
    Convert a time string in the format HH:MM:SS,SSS to seconds.

    Args:
        time_str (str): The time string.

    Returns:
        float: The time in seconds.
    """
    parts = time_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2].replace(',', '.'))  # Replace comma with dot for decimal seconds
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds

class VideoEditor:
    def __init__(self, clip_duration, srt_path, wav_path, image_path, animate_text=True):
        """
        Initialize the Editor object.

        Args:
            reddit_id (str): The ID of the Reddit post.
            clip_duration (int): The duration of the video clip in seconds.
            srt_path (str): The path to the SRT file.
            wav_path (str): The path to the WAV file.
            image_path (str): The path to the picture to include in the video.

        Attributes:
            reddit_id (str): The ID of the Reddit post.
            clip_duration (int): The duration of the video clip in seconds.
            srt_path (str): The path to the SRT file.
            wav_path (str): The path to the WAV file.
            image_path (str): The path to the picture to include in the video.
            bg_path (list): A list of background video paths.
            background_video (VideoFileClip): The background video clip.
        """
        # Initialize the reddit mockup image
        self.image_path = "outputs/temp_redit_mockup.png"

        # The Y coordinate of the text.
        self.y_cord = 1080
        # Whether to animate the text or not.
        self.animate_text = animate_text
        # The intended duration of the video clip in seconds.
        self.clip_duration = clip_duration
        # The path to the WAV and SRT file.
        self.srt_path = srt_path
        self.wav_path = wav_path
        # A list of background videos
        self.bg_path = [
            f for f in os.listdir("inputs") if f.endswith('.mp4')]
        # Randomly select a background video to use later
        self.bg_path = random.choice(self.bg_path)
        self.background_video = VideoFileClip(
            os.path.join("inputs", self.bg_path))

    def __text_generator(self, txt):
        """
        Generate a TextClip object with the specified text and style.

        Parameters:
        txt (str): The text to be displayed.

        Returns:
        TextClip: A TextClip object with the specified text and style.
        """
        

        # Reset the Y coordinate of the text to below the screen
        self.y_cord = 1080
        # Return a TextClip object with the specified text and style
        # stroke_color='black', stroke_width=1.8,
        return TextClip(
            txt,
            font='Tahoma-Bold', fontsize=39,
            color='white', method='caption', size=(550, None))


    def start_render(self, output_path="outputs/output.mp4"):
        """
        Starts the rendering process by creating a video clip with subtitles.

        Args:
            output_path (str): The path to save the rendered video file. Default is "outputs/output.mp4".

        Returns:
            None
        """
        print("\033[1m(#)\033[0m Rendering video...")
        # The maximum time to start the video clip from. (Otherwise the clip will cut to black)
        self.upperlimit_time = (
            self.background_video.duration -
            math.ceil(10*self.clip_duration) / 10
        )
        if self.upperlimit_time < 0:
            print("\033[1m(#)\033[0m The background video isn't long enough for the chosen post.")
            print("\033[1m(#)\033[0m Please choose a shorter post or use a longer background video.")
            self.upperlimit_time = 0
            print("\033[1m(#)\033[0m Background video duration:", self.background_video.duration)
            print("\033[1m(#)\033[0m Clip duration:", self.clip_duration)

        # Randomly select a start time for the video clip
        self.start_time = random.randint(0, math.floor(self.upperlimit_time))

        # Clip the video from the start time to the desired end time
        self.rendered_video = self.background_video.subclip(
            self.start_time,
            self.start_time + self.clip_duration)
        # Set the FPS to 60
        self.rendered_video = self.rendered_video.set_fps(60)
        # Set the audio of the video using the WAV file
        self.rendered_video = self.rendered_video.set_audio(
            AudioFileClip(self.wav_path))
        print("\033[1m(#)\033[0m Adding subtitles...")

        # Create a SubtitlesClip object using the SRT file, and decide whether to animate
        self.subtitles = SubtitlesClip(
            self.srt_path,
            self.__text_generator).set_position(('center', 550))

        # Load the image clip
        image_clip = ImageClip(self.image_path)
        
        # Resize the image to fit the width of the background video
        bg_width = self.background_video.size[0]
        image_clip = image_clip.resize(width=bg_width)

        # Set the duration for how long the image should appear (same as title duration)
        title_duration = calculate_title_duration(self.srt_path)
        image_clip = image_clip.set_duration(title_duration)

        # Overlay the image onto the video
        self.result = CompositeVideoClip([self.rendered_video, image_clip.set_position(('center', 'center')), self.subtitles])

        # Save the video to the outputs folder
        self.result.write_videofile(
            output_path, fps=60, codec="libx264", bitrate="8000k")
        print("\033[1m(#)\033[0m Video rendered successfully!")