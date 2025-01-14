from moviepy.video.VideoClip import ImageClip  # Used for creating video clips from images.
from moviepy.video.tools.subtitles import SubtitlesClip  # Provides tools for creating subtitles in video clips.
from moviepy.editor import (VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip)  # Provides various video editing functionalities such as combining clips, adding text, etc.
from moviepy.video.fx.all import crop
import random  # Provides functions for generating random numbers or selecting random items from a list.
import math  # Provides mathematical functions and constants.
import os  # Provides functions for interacting with the operating system.

fstl_flag = 0 # Used to keep track of if the first subtitle has passed

def calculate_title_duration(srt_path):
    """
    Calculate the duration of the first subtitle in the SRT file.

    Args:
        srt_path (str): The path to the SRT file.

    Returns:
        float: The duration of the first subtitle in seconds.
    """
    try:
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
    except Exception as e:
        print("\033[31m\033[1m(#)\033[0m Error occurred while calculating title duration:", e)
        return None

def time_to_seconds(time_str):
    """
    Convert a time string in the format HH:MM:SS,SSS to seconds.

    Args:
        time_str (str): The time string.

    Returns:
        float: The time in seconds.
    """
    try:
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2].replace(',', '.'))  # Replace comma with dot for decimal seconds
        total_seconds = hours * 3600 + minutes * 60 + seconds
        return total_seconds
    except Exception as e:
        print("\033[31m\033[1m(#)\033[0m Error occurred while converting time to seconds:", e)
        return None

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
        try:
            # Initialize the reddit mockup image
            self.image_path = "temp/redit_mockup.png"

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
        except Exception as e:
            print("\033[31m\033[1m(#)\033[0m Error occurred while initializing VideoEditor:", e)

    def __text_generator(self, txt):
        """
        Generate a TextClip object with the specified text and style.

        Parameters:
        txt (str): The text to be displayed.

        Returns:
        TextClip: A TextClip object with the specified text and style.
        """
        # Access global variable within function
        global fstl_flag
       # print("\n \033[1m(#)\033[0m text_generator run, here is previous txt")
        #print(txt)
        if fstl_flag < 2:
            txt = " "  # Set txt to empty string to display nothing
            fstl_flag += 1  # Let the program know we are now past the first subtitle after 2 counts
            #print("\n \033[1m(#)\033[0m text Generator set fstl_flag set to 1 and txt to null, here is txt after")
            #print(txt)
        #print("\n \033[1m(#)\033[0m and now after the function")
        #print(txt)

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
        try:
            print("\033[1m(#)\033[0m Rendering video...\n")
            # Reset fstl_flag to remove first subtitle for reddit mockup
            global fstl_flag
            fstl_flag = 0
            
            # Get the actual duration of the background video
            background_duration = self.background_video.duration

            # Check if the background video duration is sufficient for the clip duration
            if background_duration < self.clip_duration:
                print("\033[31m\033[1m(#)\033[0m The background video isn't long enough for the chosen post, please choose a shorter post or use a longer background video.\n")
                print("\033[1m(#)\033[0m Background video duration:", background_duration)
                print("\033[1m(#)\033[0m Clip duration:", self.clip_duration)
                return  # Exit the method if the background video is too short

            # Randomly select a start time for the video clip
            self.start_time = random.randint(0, math.floor(background_duration - self.clip_duration))

            # Clip the video from the start time to the desired end time
            self.rendered_video = self.background_video.subclip(
                self.start_time,
                self.start_time + self.clip_duration)
            # Set the FPS to 60
            self.rendered_video = self.rendered_video.set_fps(60)
            # Set the audio of the video using the WAV file
            self.rendered_video = self.rendered_video.set_audio(
                AudioFileClip(self.wav_path))
            print("\033[1m(#)\033[0m Adding subtitles...\n")

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
            if title_duration is None:
                raise ValueError("Title duration calculation failed.")
            image_clip = image_clip.set_duration(title_duration)

            # Overlay the image onto the video
            self.result = CompositeVideoClip([self.rendered_video, image_clip.set_position(('center', 'center')), self.subtitles])

            # Save the video to the outputs folder
            self.result.write_videofile(
                output_path, fps=60, codec="libx264", bitrate="8000k", verbose="false")
            print("\033[1m(#)\033[0m Video rendered successfully!\n")
        except Exception as e:
            print("\033[31m\033[1m(#)\033[0m Error occurred while rendering video:", e)


    def aspect_converter(self, input_directory="downloads/", output_directory="inputs/", output_width=1080, output_height=1920):
        """
        Convert videos to a specified aspect ratio.

        Args:
            input_directory (str): The directory containing input video files.
            output_directory (str): The directory where output video files will be saved.
            output_width (int): The desired width of the output video.
            output_height (int): The desired height of the output video.
        """
        # Iterate over all .mp4 files in the input directory
        for filename in os.listdir(input_directory):
            if filename.endswith(".mp4"):
                input_file = os.path.join(input_directory, filename)
                
                try:
                    # Load the video clip
                    clip = VideoFileClip(input_file)
                    
                    # Calculate cropping parameters to maintain aspect ratio and center the content
                    input_aspect_ratio = clip.size[0] / clip.size[1]
                    output_aspect_ratio = output_width / output_height
                    
                    if input_aspect_ratio > output_aspect_ratio:
                        # Calculate cropping dimensions based on height
                        crop_height = clip.size[1]
                        crop_width = int(crop_height * output_aspect_ratio)
                    else:
                        # Calculate cropping dimensions based on width
                        crop_width = clip.size[0]
                        crop_height = int(crop_width / output_aspect_ratio)
                    
                    # Calculate center coordinates
                    x_center = clip.size[0] / 2
                    y_center = clip.size[1] / 2
                    
                    # Apply cropping
                    cropped_clip = crop(clip, width=crop_width, height=crop_height, x_center=x_center, y_center=y_center)
                    
                    # Resize the cropped clip to the desired output dimensions
                    resized_clip = cropped_clip.resize(width=output_width, height=output_height)
                    
                    # Output file path
                    output_file = os.path.join(output_directory, filename)
                    
                    # Write the cropped and resized video to the output file
                    resized_clip.write_videofile(output_file, codec="libx264")

                    print(f"\033[1m(#)\033[0m Cropping and resizing successful: {input_file} -> {output_file}")

                except Exception as e:
                    print(f"\033[31m\033[1m(#)\033[0m Error cropping video {input_file}: {e}")