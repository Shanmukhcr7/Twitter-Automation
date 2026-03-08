import os
import json
import time
from typing import Optional
from playwright.sync_api import sync_playwright, TimeoutError
from config.settings import (
    TWITTER_ACCESS_TOKEN 
    # We repurpose TWITTER_ACCESS_TOKEN in .env to hold the 'auth_token' cookie 
    # value since it is already secret and safely passed to Docker.
)
from utils.logger import get_logger

logger = get_logger()

def check_auth_token_configured() -> bool:
    if not TWITTER_ACCESS_TOKEN or len(TWITTER_ACCESS_TOKEN) < 20:
        logger.error("TWITTER_ACCESS_TOKEN in .env must be set to your Twitter 'auth_token' cookie value for Playwright.")
        return False
    return True

def format_final_tweet(text: str, tags: str) -> str:
    """Ensure the text and tags fit into Twitter's approximate limits."""
    status = f"{text}\n\n{tags}"
    if len(status) > 280:
        if len(text) > 280:
             return text[:277] + "..."
        return text
    return status

def post_tweet(tweet_text: str, hashtags: str = "", image_path: Optional[str] = None) -> bool:
    """
    Posts a tweet, optionally with an image, using Playwright Browser Automation.
    Bypasses API paywalls by simulating a logged-in user session.
    """
    if not check_auth_token_configured():
        return False

    final_content = format_final_tweet(tweet_text, hashtags)
    logger.info(f"Attempting to post tweet ({len(final_content)} chars) via Playwright. Image: {image_path is not None}")
    
    success = False
    
    with sync_playwright() as p:
        # Launch Chromium (Headless for Docker/Server environments)
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        
        # Create a new context and instantly inject the authentication cookie
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Injects the critical 'auth_token' cookie which bypasses the login screen entirely
        context.add_cookies([{
            "name": "auth_token",
            "value": TWITTER_ACCESS_TOKEN, 
            "domain": ".x.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "sameSite": "None"
        }])
        
        page = context.new_page()

        try:
            # Navigate directly to the compose route
            logger.debug("Navigating to x.com compose page...")
            page.goto("https://x.com/compose/tweet", timeout=30000)
            
            # Wait for the draft editor text box to appear securely
            logger.debug("Waiting for the compose text box...")
            editor_selector = '[data-testid="tweetTextarea_0"]'
            page.wait_for_selector(editor_selector, state="visible", timeout=15000)
            
            # Type the tweet text
            logger.debug("Typing tweet content...")
            page.locator(editor_selector).fill(final_content)
            time.sleep(1) # Humanize the execution slightly
            
            # Upload Image if provided
            if image_path and os.path.exists(image_path):
                logger.debug(f"Uploading image: {image_path}")
                file_input_selector = 'input[data-testid="fileInput"]'
                # The file input is often hidden, so we attach the file directly to the DOM node
                page.set_input_files(file_input_selector, image_path)
                
                # Wait for the image preview to successfully render to ensure it is fully uploaded
                logger.debug("Waiting for media attachment to process...")
                page.wait_for_selector('[data-testid="attachments"]', state="visible", timeout=20000)
                time.sleep(2)
                
            # Click the Post button
            logger.debug("Clicking the Post button...")
            post_button_selector = '[data-testid="tweetButton"]'
            page.wait_for_selector(post_button_selector, state="visible")
            page.locator(post_button_selector).click()
            
            # Wait a few seconds to ensure the POST request fires before the browser closes
            time.sleep(5)
            logger.info("✅ Successfully posted tweet via Browser Automation!")
            success = True
            
        except TimeoutError as e:
            logger.error("Playwright Timeout: The page took too long to load or an element was missing. Is the auth_token cookie valid?")
            success = False
        except Exception as e:
            logger.error(f"Unexpected Playwright error during posting: {e}")
            success = False
        finally:
            browser.close()
            
            # Cleanup temporary image file
            if image_path and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    logger.debug(f"Deleted temporary image file: {image_path}")
                except Exception as e:
                    logger.error(f"Failed to delete tempoaray image {image_path}: {e}")
                    
    return success
