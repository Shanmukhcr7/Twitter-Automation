import time
import schedule
import pytz
from datetime import datetime
from config.settings import SCHEDULE_TWITTER_SCRAPE, SCHEDULE_TRENDS_SCRAPE, SCHEDULE_NEWS_SCRAPE
from main import job_scrape_trends, job_scrape_news, job_scrape_twitter, job_scrape_and_detect, post_single_item
from utils.logger import get_logger

logger = get_logger()

# Setup India Standard Timezone
IST = pytz.timezone('Asia/Kolkata')

# Sub-Interval Posting Queues (in-memory, refreshed hourly)
TWEET_QUEUE = []
NEWS_QUEUE = []


def fill_queues(current_hour: int):
    """
    Scrapes fresh content and replenishes in-memory posting queues.
    Called at startup (regardless of minute) and at the top of every hour.
    """
    logger.info(f"Filling queues from fresh scrape (hour={current_hour})...")

    # Trends are refreshed per configured interval
    if current_hour % SCHEDULE_TRENDS_SCRAPE == 0:
        job_scrape_trends()

    # Tweets are refreshed per configured interval
    if current_hour % SCHEDULE_TWITTER_SCRAPE == 0:
        job_scrape_twitter()

    # News are refreshed per configured interval
    if current_hour % SCHEDULE_NEWS_SCRAPE == 0:
        job_scrape_news()

    # Tweets: Pick Top 4 newly scraped to fill the posting queue
    new_tweets = job_scrape_and_detect(content_type="tweets", top_n=4)
    if new_tweets:
        TWEET_QUEUE.extend(new_tweets)
        logger.info(f"Added {len(new_tweets)} tweets to TWEET_QUEUE. Total: {len(TWEET_QUEUE)}")
    else:
        logger.warning("No fresh tweets found to fill the queue this cycle.")

    # News: Pick Top 4 only at 9am / 9pm IST (bi-daily)
    if current_hour in [9, 21]:
        new_news = job_scrape_and_detect(content_type="news", top_n=4)
        if new_news:
            NEWS_QUEUE.extend(new_news)
            logger.info(f"Added {len(new_news)} news items to NEWS_QUEUE. Total: {len(NEWS_QUEUE)}")


def dispatch_15min_job():
    """
    Sub-Interval dispatcher that fires every 15 minutes (:00, :15, :30, :45).
    - Refills queues at the top of every hour.
    - Pops and posts exactly 1 Tweet every 15 minutes.
    - Pops and posts exactly 1 News item every 3 hours at the top of the hour.
    """
    now_ist = datetime.now(IST)
    current_hour = now_ist.hour
    current_minute = now_ist.minute
    logger.info(f"Sub-Interval Dispatcher woke up. Current IST time: {now_ist.strftime('%Y-%m-%d %H:%M:%S')}")



    # Top of the hour: refill the queues with fresh content
    if current_minute < 15:
        logger.info("Top of the hour — refreshing queues.")
        fill_queues(current_hour)

    # 1. Pop and post exactly 1 Tweet (every 15 minutes)
    if len(TWEET_QUEUE) > 0:
        logger.info(f"Popping 1 TWEET from queue. ({len(TWEET_QUEUE)} remaining)")
        tweet_candidate = TWEET_QUEUE.pop(0)
        post_single_item(tweet_candidate)
    else:
        logger.info("TWEET_QUEUE is empty. Waiting for next hourly scrape.")

    # 2. Pop and post exactly 1 News item (every 3 hours at the top of the hour)
    if current_hour % 3 == 0 and current_minute < 15:
        if len(NEWS_QUEUE) > 0:
            logger.info(f"Popping 1 NEWS from queue. ({len(NEWS_QUEUE)} remaining)")
            news_candidate = NEWS_QUEUE.pop(0)
            post_single_item(news_candidate)
        else:
            logger.info("NEWS_QUEUE is empty. Expected if outside 9am/9pm scrape windows.")


def start_scheduler():
    logger.info("Initializing timezone-aware task scheduler (IST)...")

    # Schedule the master dispatcher to run every 15 minutes
    schedule.every().hour.at(":00").do(dispatch_15min_job)
    schedule.every().hour.at(":15").do(dispatch_15min_job)
    schedule.every().hour.at(":30").do(dispatch_15min_job)
    schedule.every().hour.at(":45").do(dispatch_15min_job)

    logger.info("Scheduler started. Waiting for the next 15-minute mark. Press Ctrl+C to exit.")

    # Always pre-fill queues at startup regardless of current minute, then dispatch once
    now_ist = datetime.now(IST)
    logger.info("Performing initial queue fill on startup...")
    fill_queues(now_ist.hour)
    dispatch_15min_job()

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped manually.")
    except Exception as e:
        logger.error(f"Scheduler encountered an error: {e}")


if __name__ == "__main__":
    start_scheduler()
