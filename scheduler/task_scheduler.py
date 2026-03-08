import time
import schedule
import pytz
from datetime import datetime
from config.settings import SCHEDULE_TWITTER_SCRAPE, SCHEDULE_TRENDS_SCRAPE, SCHEDULE_NEWS_SCRAPE
from main import job_scrape_trends, job_scrape_news, job_scrape_twitter, job_evaluate_and_post
from utils.logger import get_logger

logger = get_logger()

# Setup India Standard Timezone
IST = pytz.timezone('Asia/Kolkata')

def dispatch_hourly_job():
    """
    Master dispatcher that fires at the top of every hour.
    Checks the current IST time to decide what sequence to run.
    """
    now_ist = datetime.now(IST)
    current_hour = now_ist.hour
    logger.info(f"Hourly Dispatcher woke up. Current IST time: {now_ist.strftime('%Y-%m-%d %H:%M:%S')}")

    # Every hour we need trends data to be somewhat fresh
    if current_hour % SCHEDULE_TRENDS_SCRAPE == 0:
        job_scrape_trends()
        
    # Check for 9 AM (09:00) or 9 PM (21:00) IST
    if current_hour == 9 or current_hour == 21:
        logger.info(f"Triggering NEWS ONLY sequence for strictly {current_hour}:00 IST schedule.")
        job_scrape_news()
        job_evaluate_and_post(content_type="news")
    else:
        logger.info(f"Triggering TWITTER ONLY sequence for normal hourly schedule.")
        job_scrape_twitter()
        job_evaluate_and_post(content_type="tweets")

def start_scheduler():
    logger.info("Initializing timezone-aware task scheduler (IST)...")

    # Schedule the master dispatcher to run at the start of every hour (e.g. 09:00, 10:00, 11:00)
    schedule.every().hour.at(":00").do(dispatch_hourly_job)

    logger.info("Scheduler started. Waiting for the next hour mark. Press Ctrl+C to exit.")
    
    # We optionally trigger one run immediately upon starting up to ensure the cache isn't entirely idle
    dispatch_hourly_job()

    try:
        while True:
            schedule.run_pending()
            time.sleep(30) # Wait 30 seconds between checks
    except KeyboardInterrupt:
        logger.info("Scheduler stopped manually.")
    except Exception as e:
        logger.error(f"Scheduler encountered an error: {e}")

if __name__ == "__main__":
    start_scheduler()
