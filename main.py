import sys
from utils.logger import get_logger
from scrapers.trends_scraper import scrape_trends
from scrapers.news_scraper import scrape_news
from scrapers.twitter_scraper import scrape_twitter
from detector.viral_detector import detect_viral_content
from generator.tweet_generator import generate_tweet
from generator.hashtag_generator import generate_hashtags
from media.image_fetcher import fetch_image, download_direct_image
from poster.twitter_poster import post_tweet
from utils.text_cleaner import clean_text
from utils.state_manager import filter_unposted, mark_as_posted

logger = get_logger()

# In-memory storage for scraped data by schedule
cache = {
    "trends": [],
    "news": [],
    "tweets": []
}

def job_scrape_trends():
    logger.info("Running scheduled job: Scrape Trends")
    cache["trends"] = scrape_trends()

def job_scrape_news():
    logger.info("Running scheduled job: Scrape News")
    cache["news"] = scrape_news()

def job_scrape_twitter():
    logger.info("Running scheduled job: Scrape Twitter")
    cache["tweets"] = scrape_twitter(max_tweets=5) # fetch enough for the top 4 queue

def job_scrape_and_detect(content_type: str = None, top_n: int = 4):
    """
    Scrapes the requested targets, evaluates their virality against current trends,
    and returns a list of the top `top_n` candidates.
    """
    logger.info(f"Running scheduled job: Scrape & Detect (Targeting: {content_type or 'all'}, Top N: {top_n})")
    
    # If no data exists yet, attempt to fetch it directly
    if not cache["trends"]: job_scrape_trends()

    # Filter data dynamically based on instructions from the scheduler
    if content_type == "news":
        if not cache["news"]: job_scrape_news()
        all_data = cache["news"]
    elif content_type == "tweets":
        if not cache["tweets"]: job_scrape_twitter()
        all_data = cache["tweets"]
    else:
        if not cache["news"]: job_scrape_news()
        if not cache["tweets"]: job_scrape_twitter()
        all_data = cache["news"] + cache["tweets"]
        
    if not all_data:
        logger.warning(f"No {content_type or 'scraped'} data available to evaluate.")
        return []
    
    # ✅ Filter out already-posted items BEFORE viral detection
    # This ensures the detector only picks from fresh, unposted content
    fresh_data = filter_unposted(all_data)
    if not fresh_data:
        logger.warning(f"All scraped {content_type or 'content'} has already been posted. Nothing new to evaluate.")
        return []
    
    logger.info(f"Fresh unposted pool: {len(fresh_data)} items (from {len(all_data)} scraped)")
    return detect_viral_content(fresh_data, cache["trends"], content_type, top_n=top_n)

def post_single_item(viral_item: dict) -> bool:
    """
    Executes the generative AI pipeline and Playwright workflow for a single item.
    """
    if not viral_item:
        logger.warning("Empty item provided to poster. Skipping.")
        return False

    logger.info(f"Starting generation pipeline for item: {viral_item.get('title') or viral_item.get('text')[:30]}")
    
    # Generate content with AI rules
    tweet_text = generate_tweet(viral_item)
    hashtags = generate_hashtags(viral_item, tweet_text=tweet_text)
    
    # Image: prefer the native tweet image (always accurate), fall back to Unsplash search
    native_url = viral_item.get("native_image_url")
    if native_url:
        image_path = download_direct_image(native_url)
        if image_path:
            logger.info("Using native tweet image.")
        else:
            logger.info("Native image download failed. Falling back to Unsplash.")
            source_text = viral_item.get("title") or viral_item.get("text", "")
            image_path = fetch_image(source_text)
    else:
        # For news items or tweets without media, use Unsplash
        source_text = viral_item.get("title") or viral_item.get("text", "")
        image_path = fetch_image(source_text)

    # Post
    success = post_tweet(tweet_text, hashtags, image_path)
    if success:
        logger.info("✅ Successfully posted queued item.")
        mark_as_posted(viral_item)  # Persist to JSON so it's never posted again
        return True
    else:
        logger.error("❌ Failed to post queued item.")
        return False

if __name__ == "__main__":
    logger.info("Bot started manually, running one full sequence.")
    items = job_scrape_and_detect(top_n=1)
    if items:
        post_single_item(items[0])
