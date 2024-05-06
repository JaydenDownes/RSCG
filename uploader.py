import random
import time
from playwright.sync_api import sync_playwright

def upload_video(username, password, video_path, caption):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_default_timeout(720000)  # Set a longer timeout (e.g., 60 seconds)

        page.goto('https://www.tiktok.com/login/phone-or-email/email?redirect_url=https%3A%2F%2Fwww.tiktok.com%2Fcreator-center%2Fupload&enter_method=redirect&enter_from=creator-center')

        # Fill in login credentials
        page.fill('input[name="username"]', username)
        page.fill('input[type="password"]', password)

        # Click on the login button
        login_button = page.wait_for_selector('button[data-e2e="login-button"]')
        login_button.click()    
        
        # Wait for the upload button to be available
        upload_button = page.wait_for_selector('button[aria-label="Select file"]')

        # Click on the file selection button to upload the video
        upload_button.click()

        # Set the input file
        page.set_input_files('input[type=file]', video_path)

        # Wait for the caption field to appear and fill it
        caption_field = page.wait_for_selector('div[aria-autocomplete="list"][contenteditable="true"]')
        type_caption(caption_field, caption)

        # Wait for the "Post" button to become clickable
        post_button = page.wait_for_selector('button:not([disabled]) .css-1z070dx:has-text("Post")')
        post_button.click()

        # Wait for navigation after posting
        page.wait_for_navigation()

        browser.close()

def type_caption(element, text):
    for char in text:
        element.type(char)
        time.sleep(random.uniform(0.1, 0.3))  # Random delay between 0.1 and 0.3 seconds


# Example usage
username = "r3dd1tst0rytime"
password = "TypoAdmin415718$"
video_path = "outputs\Deleted User - I lied about my height for most of high school - 05-08-2018.mp4"
caption = "Check out this awesome video!"

upload_video(username, password, video_path, caption)
