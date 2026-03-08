import sys
from utils.logger import get_logger
from scrapers.trends_scraper import scrape_trends
from scrapers.news_scraper import scrape_news
from scrapers.twitter_scraper import scrape_twitter
from detector.viral_detector import detect_viral_content
from generator.tweet_generator import generate_tweet
from generator.hashtag_generator import generate_hashtags
from media.image_fetcher import fetch_image
from poster.twitter_poster import post_tweet
from utils.text_cleaner import clean_text

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
    cache["tweets"] = scrape_twitter(max_tweets=2) # keep lightweight

def job_evaluate_and_post(content_type: str = None):
    logger.info(f"Running scheduled job: Evaluate & Post (Targeting: {content_type or 'all'})")
    
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
        return
    
    viral_item = detect_viral_content(all_data, cache["trends"], content_type)
    
    if not viral_item:
        logger.warning("No viral content could be determined right now. Skipping post.")
        return

    # Check against a minimum score threshold (optional, set to 0 to always post the best one found)
    if viral_item.get('viral_score', 0) < 5.0 and viral_item.get('type') != 'news':
        logger.info("Highest scoring item didn't meet threshold. Waiting for next cycle.")
        return

    logger.info("Starting generation pipeline for viral item.")
    
    # Generate content with AI rules
    tweet_text = generate_tweet(viral_item)
    hashtags = generate_hashtags(viral_item, tweet_text=tweet_text)
    
    # Fetch image with AI query formulation
    source_text = viral_item.get("title") or viral_item.get("text", "")
    image_path = fetch_image(source_text)

    # Post
    success = post_tweet(tweet_text, hashtags, image_path)
    if success:
        logger.info("Successfully posted scheduled tweet.")
        # Clear out the item to avoid reposting (mock clearing by emptying cache or just let it overwrite next cycle)
        # In a real DB we'd track posted URLs
    else:
        logger.error("Failed to post scheduled tweet.")

if __name__ == "__main__":
    logger.info("Bot started manually, running one full sequence.")
    job_evaluate_and_post()
