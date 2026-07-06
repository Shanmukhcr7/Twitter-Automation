import time
import schedule
import pytz
from datetime import datetime
from main import job_scrape_and_detect, post_single_item, job_scrape_trends
from utils.logger import get_logger

logger = get_logger()

# India Standard Timezone
IST = pytz.timezone('Asia/Kolkata')

# Active hours: 08:00 – 23:59 IST
ACTIVE_START_HOUR = 8   # 08:00 IST
ACTIVE_END_HOUR   = 23  # up to 23:59 IST (midnight stops posting)


def is_active_hours() -> bool:
    """Returns True if current IST time is within the active posting window."""
    current_hour = datetime.now(IST).hour
    return ACTIVE_START_HOUR <= current_hour <= ACTIVE_END_HOUR


def run_cycle():
    """
    One full scrape-detect-post cycle.
    Scrapes the latest tweets (last 3 hours), picks the top-scoring fresh one, posts it.
    Also scrapes news every 12 hours at 9 AM / 9 PM IST.
    """
    now_ist = datetime.now(IST)
    current_hour = now_ist.hour
    logger.info(f"=== 3-Hour Cycle Starting | IST: {now_ist.strftime('%Y-%m-%d %H:%M:%S')} ===")

    # Guard: do nothing during quiet hours
    if not is_active_hours():
        logger.info(f"😴 Quiet hours ({now_ist.strftime('%H:%M')} IST). Skipping cycle. Resumes at 08:00 IST.")
        return

    # 1. Refresh trends periodically (every 6 hours)
    if current_hour % 6 == 0:
        job_scrape_trends()

    # 2. Post 1 tweet from the Twitter accounts (primary job, every cycle)
    logger.info("Picking best fresh tweet to post...")
    tweet_candidates = job_scrape_and_detect(content_type="tweets", top_n=1)
    if tweet_candidates:
        post_single_item(tweet_candidates[0])
    else:
        logger.warning("No fresh unposted tweets available this cycle.")

    # 3. Also post 1 news item at 9 AM / 9 PM IST (bi-daily)
    if current_hour in [9, 21]:
        logger.info("9 AM / 9 PM IST — also posting one news item.")
        news_candidates = job_scrape_and_detect(content_type="news", top_n=1)
        if news_candidates:
            post_single_item(news_candidates[0])
        else:
            logger.warning("No fresh unposted news available for this news slot.")

    logger.info("=== Cycle complete. Next run in 3 hours. ===")


def start_scheduler():
    logger.info("Initializing scheduler — 1 tweet every 3 hours (08:00–23:59 IST).")

    # Schedule a cycle every 3 hours
    schedule.every(3).hours.do(run_cycle)

    # Run immediately on startup (first post right away)
    logger.info("Running initial cycle on startup...")
    run_cycle()

    logger.info("Scheduler running. Press Ctrl+C to stop.")
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
