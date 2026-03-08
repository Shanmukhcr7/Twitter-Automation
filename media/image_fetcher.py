import os
import requests
import uuid
from PIL import Image
from io import BytesIO
from typing import Optional

from config.settings import MEDIA_DIR, UNSPLASH_KEY
from utils.logger import get_logger
from ai.ai_client import generate_image_query

logger = get_logger()

UNSPLASH_API_URL = "https://api.unsplash.com/photos/random"

def download_direct_image(image_url: str) -> Optional[str]:
    """
    Downloads an image directly from a known URL (e.g. native tweet image from pbs.twimg.com).
    Skips any search API — ideal for using the original tweet's attached media.
    """
    if not image_url:
        return None
    try:
        logger.info(f"Downloading native tweet image: {image_url[:70]}")
        headers = {"User-Agent": "Mozilla/5.0"}
        img_response = requests.get(image_url, headers=headers, timeout=15)
        img_response.raise_for_status()

        image = Image.open(BytesIO(img_response.content))
        image.verify()

        filepath = os.path.join(MEDIA_DIR, "temp.jpg")
        image = Image.open(BytesIO(img_response.content))
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        image.save(filepath, format="JPEG")

        logger.info(f"Native tweet image saved to: {filepath}")
        return filepath
    except Exception as e:
        logger.warning(f"Failed to download native tweet image: {e}")
        return None

def fetch_image(content_text: str) -> Optional[str]:
    """
    Uses AI to generate a clean search query from the provided text,
    queries the Unsplash API for a random related image, downloads, 
    verifies, and returns the path.
    """
    if not content_text:
        logger.warning("Empty content passed to image fetcher.")
        return None

    if not UNSPLASH_KEY:
        logger.error("UNSPLASH_KEY is not defined in the environment. Cannot fetch image.")
        return None

    logger.info("Generating optimal image search query via AI.")
    keyword = generate_image_query(content_text)
    
    if not keyword:
        logger.warning("AI query generation failed. Falling back to raw text truncation.")
        keyword = content_text[:50] # Fallback to first 50 chars
        
    logger.info(f"Looking for Unsplash image related to query: '{keyword}'")

    try:
        # Request a random photo matching the query
        headers = {
            "Authorization": f"Client-ID {UNSPLASH_KEY}"
        }
        params = {
            "query": keyword,
            "orientation": "landscape"
        }
        
        api_response = requests.get(UNSPLASH_API_URL, headers=headers, params=params, timeout=15)
        
        if api_response.status_code == 404:
            logger.warning(f"No Unsplash image found for strict query: '{keyword}'. Trying fallback broad query.")
            # Fallback to a broader visualization if the AI query is too specific
            params["query"] = "news trending"
            api_response = requests.get(UNSPLASH_API_URL, headers=headers, params=params, timeout=15)
            
            # If even the fallback fails, return None natively
            if api_response.status_code == 404:
                return None
            
        api_response.raise_for_status()
        
        data = api_response.json()
        
        # Grab the regular sized image URL
        image_url = data.get("urls", {}).get("regular")
        
        if not image_url:
            logger.error("Unsplash API response missing 'urls.regular' payload.")
            return None
            
        logger.debug(f"Attempting to download Unsplash image: {image_url}")
            
        # Download the actual image
        img_response = requests.get(image_url, timeout=15)
        img_response.raise_for_status()

        # Verify image using Pillow
        image = Image.open(BytesIO(img_response.content))
        image.verify() # Verify structural integrity

        # Generate a unique temp filename
        filename = "temp.jpg"
        filepath = os.path.join(MEDIA_DIR, filename)

        # Re-open image to save it
        image = Image.open(BytesIO(img_response.content))
        
        # Convert to RGB if necessary before saving as jpg
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
            
        image.save(filepath, format="JPEG")

        logger.info(f"Successfully downloaded Unsplash image to: {filepath}")
        return filepath
                
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"Unsplash API HTTP Error: {http_err} - {api_response.text if 'api_response' in locals() else ''}")
        return None
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Network error fetching image: {req_err}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing Unsplash image: {e}")
        return None
