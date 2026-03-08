import os
import tweepy
from typing import Optional
from config.settings import (
    TWITTER_API_KEY, TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
)
from utils.logger import get_logger

logger = get_logger()

# Global variables for the tweepy objects
api: Optional[tweepy.API] = None
client: Optional[tweepy.Client] = None

def init_twitter_client() -> bool:
    """Initialize Twitter clients (v1.1 for media, v2 for tweeting)."""
    global api, client
    
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]):
        logger.error("Twitter credentials are not fully configured in environment.")
        return False
        
    try:
        # v1.1 auth for media upload
        auth = tweepy.OAuth1UserHandler(
            TWITTER_API_KEY, TWITTER_API_SECRET,
            TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
        )
        api = tweepy.API(auth, wait_on_rate_limit=True)
        
        # Verify v1.1 credentials (fails if keys are invalid)
        api.verify_credentials()
        
        # v2 Client for posting the tweet
        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY, consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN, access_token_secret=TWITTER_ACCESS_SECRET,
            wait_on_rate_limit=True
        )
        
        logger.info("Twitter API clients initialized successfully.")
        return True
    
    except Exception as e:
        logger.error(f"Failed to authenticate with Twitter APIs: {e}")
        return False

def format_final_tweet(text: str, tags: str) -> str:
    """Ensure the text and tags fit into 280 chars."""
    status = f"{text}\n\n{tags}"
    if len(status) > 280:
        # If too long, just return the text
        if len(text) > 280:
             return text[:277] + "..."
        return text
    return status

def post_tweet(tweet_text: str, hashtags: str = "", image_path: Optional[str] = None) -> bool:
    """
    Posts a tweet, optionally with an image.
    Uses tweepy Client (v2) for the tweet and API (v1.1) for media upload.
    """
    if client is None or api is None:
        if not init_twitter_client():
            return False

    final_content = format_final_tweet(tweet_text, hashtags)
    logger.info(f"Attempting to post tweet ({len(final_content)} chars). Image: {image_path is not None}")
    
    try:
        media_id = None
        
        if image_path and os.path.exists(image_path):
            try:
                # Upload media via v1.1
                logger.debug(f"Uploading image: {image_path}")
                media = api.media_upload(image_path)
                media_id = media.media_id
                logger.info(f"Media uploaded successfully. ID: {media_id}")
            except Exception as e:
                logger.error(f"Error uploading media ({image_path}): {e}")
                # We can choose to proceed and tweet anyway without the image
                pass 
                
        # Send tweet via v2
        if media_id:
            response = client.create_tweet(text=final_content, media_ids=[media_id])
        else:
            response = client.create_tweet(text=final_content)
            
        tweet_id = response.data['id']
        logger.info(f"✅ Successfully posted tweet! ID: {tweet_id}")
        
        # Cleanup image
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
                logger.debug(f"Deleted temporary image file: {image_path}")
            except Exception as e:
                logger.error(f"Failed to delete tempoaray image {image_path}: {e}")
                
        return True
        
    except tweepy.TweepyException as e:
        logger.error(f"TweepyException during posting: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during posting: {e}")
        return False
