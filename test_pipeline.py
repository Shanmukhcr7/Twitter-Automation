import sys
from utils.logger import get_logger
from scrapers.trends_scraper import scrape_trends
from scrapers.news_scraper import scrape_news
from scrapers.twitter_scraper import scrape_twitter
from detector.viral_detector import detect_viral_content
from generator.tweet_generator import generate_tweet
from generator.hashtag_generator import generate_hashtags
from media.image_fetcher import fetch_image
from utils.text_cleaner import clean_text

logger = get_logger()

def run_dry_test():
    """
    Runs the entire pipeline (Scrape -> Score -> Generate) without actually posting to Twitter.
    """
    logger.info("=== STARTING DRY RUN TEST ===")
    
    # 1. Scrape data
    logger.info("Step 1: Scraping Data...")
    trends = scrape_trends()
    news = scrape_news()
    tweets = scrape_twitter(max_tweets=2)
    
    all_data = news + tweets
    
    if not all_data:
        logger.error("No data could be scraped. Ensure internet connection and that snscrape is working.")
        return

    # 2. Detect Viral Content
    logger.info("\nStep 2: Detecting Viral Content...")
    viral_item = detect_viral_content(all_data, trends)
    
    if not viral_item:
        logger.warning("No viral content determined.")
        return
        
    logger.info(f"Winning Item Score: {viral_item.get('viral_score', 0)}")
    logger.info(f"Winning Item Original Text:\n{viral_item.get('title') or viral_item.get('text')[:100]}...\n")

    # 3. Generate Tweet and Hashtags
    logger.info("Step 3: Generating Content (AI)...")
    tweet_text = generate_tweet(viral_item)
    hashtags = generate_hashtags(viral_item, tweet_text=tweet_text)
    
    logger.info(f"Generated Tweet Text:\n{tweet_text}")
    logger.info(f"Generated Hashtags: {hashtags}")
    
    # 4. Fetch Image
    logger.info("\nStep 4: Fetching Image (AI Query)...")
    source_text = viral_item.get("title") or viral_item.get("text", "")
    image_path = fetch_image(source_text)
    
    if image_path:
        logger.info(f"Successfully downloaded test image to: {image_path}")
    else:
        logger.warning("Failed to download a test image.")
        
    logger.info("\n=== DRY RUN TEST COMPLETE (No actual tweets were posted) ===")
    print("\n\n" + "="*50)
    print("FINAL TWEET PREVIEW:")
    print("="*50)
    print(f"{tweet_text}\n\n{hashtags}")
    print("="*50)
    if image_path:
        print(f"[Attached Image Path: {image_path}]")
    else:
        print("[No Image Attached]")

if __name__ == "__main__":
    run_dry_test()
