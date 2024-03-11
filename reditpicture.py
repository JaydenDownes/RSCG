from PIL import Image, ImageDraw, ImageFont

# Function to add text to an image
def add_text_to_image(image_path, text_data):
    # Open the image
    image = Image.open(image_path)
    
    # Initialize drawing context
    draw = ImageDraw.Draw(image)
    
    # Define font styles for each piece of data
    font_styles = [
        {"font": ImageFont.truetype("Arial.ttf", size=24), "color": (255, 0, 0), "position": (10, 10)},
        {"font": ImageFont.truetype("Times New Roman.ttf", size=18), "color": (0, 255, 0), "position": (10, 50)},
        {"font": ImageFont.truetype("Courier New.ttf", size=20), "color": (0, 0, 255), "position": (10, 90)},
        {"font": ImageFont.load_default(), "color": (255, 255, 255), "position": (10, 130)},
        # Add more font styles for additional data
    ]
    
    # Add text to image
    for style, data in zip(font_styles, text_data):
        draw.text(style["position"], data, font=style["font"], fill=style["color"])
        
    # Save the modified image
    image.save("image_with_text.jpg")

# Example usage
text_data = [
    "Title: Sample Title",
    "Subreddit: Sample Subreddit",
    "Time: 2024-03-11 12:30:00",
    "ID: abc123"
    # Add more data as needed
]

add_text_to_image("blank_image.jpg", text_data)
