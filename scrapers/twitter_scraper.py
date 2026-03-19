import requests
import random
from bs4 import BeautifulSoup
from typing import List, Dict
from config.settings import MONITORED_ACCOUNTS
from utils.logger import get_logger
from utils.text_cleaner import clean_text

logger = get_logger()

# Nitter instances (validated 2026-03-19 for REAL RSS output, not just HTTP 200)
# Many instances return HTTP 200 but serve HTML captcha pages. The scraper now
# validates content-type/content to detect and skip these fake-200 responses.
NITTER_INSTANCES = [
    "https://nitter.net",              # Primary: real RSS confirmed
    "https://xcancel.com",             # Fallback: real RSS confirmed (some accounts 400)
    # Candidates below: may be blocked by captcha on cloud IPs - keep for retry attempts
    "https://nitter.tiekoetter.com",
    "https://nitter.privacyredirect.com",
    "https://nitter.projectsegfau.lt",
    "https://nitter.kylrth.com",
]

from concurrent.futures import ThreadPoolExecutor, as_completed

def _scrape_account(account: str, max_age_hours: int) -> List[Dict]:
    """Helper method to scrape a single Twitter account using Nitter instances."""
    results = []
    logger.debug(f"Scraping tweets for account: @{account}")
    success = False

    # Headers to simulate a real browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # Shallow copy and shuffle instances to distribute load and handle potential blocks
    instances = list(NITTER_INSTANCES)
    random.shuffle(instances)

    for instance in instances:
        rss_url = f"{instance}/{account}/rss"

        try:
            logger.debug(f"Trying Nitter instance: {rss_url}")
            response = requests.get(rss_url, headers=headers, timeout=12)

            # If rate-limited or instance down, try the next one
            if response.status_code != 200:
                logger.debug(f"Instance {instance} returned status {response.status_code}. Trying next...")
                continue

            # CRITICAL: Many Nitter instances respond with HTTP 200 but serve an HTML
            # captcha/auth page instead of RSS XML when they block datacenter IPs.
            # We must validate the response is actually RSS before parsing it.
            content_type = response.headers.get("Content-Type", "")
            response_text = response.text
            is_real_rss = (
                "xml" in content_type or "rss" in content_type
                or response_text.strip().startswith("<?xml")
                or "<rss" in response_text[:300]
                or "<channel>" in response_text[:500]
            )
            if not is_real_rss:
                logger.debug(f"Instance {instance} returned HTML (captcha/auth page) instead of RSS. Trying next...")
                continue

            soup = BeautifulSoup(response.content, "lxml-xml")
            items = soup.find_all("item")

            if not items:
                logger.debug(f"No items in RSS for @{account} on {instance}. Trying next...")
                continue

            for item in items:
                raw_html = item.description.text if item.description else ""
                text = clean_text(raw_html)
                link = item.link.text if item.link else ""
                pub_date_str = item.pubDate.text if item.pubDate else ""

                # Extract native tweet image directly from Nitter's embedded HTML.
                # Nitter puts tweet images as <img src="https://pbs.twimg.com/..."> in the description.
                native_image_url = None
                try:
                    desc_soup = BeautifulSoup(raw_html, "html.parser")
                    img_tag = desc_soup.find("img", src=lambda s: s and s.startswith("https://"))
                    if img_tag:
                        native_image_url = img_tag["src"]
                        logger.debug(f"Extracted native tweet image: {native_image_url[:60]}")
                except Exception:
                    pass

                if not text:
                    continue

                # Enforce freshness using pubDate timestamp
                date_ok = False
                if pub_date_str:
                    try:
                        from email.utils import parsedate_to_datetime
                        import datetime as dt_module

                        parsed_dt = parsedate_to_datetime(pub_date_str)
                        now_utc = dt_module.datetime.now(dt_module.timezone.utc)
                        age_hours = (now_utc - parsed_dt).total_seconds() / 3600.0

                        if age_hours <= max_age_hours:
                            date_ok = True
                        else:
                            logger.debug(f"Skipping tweet aged {age_hours:.1f}h (max: {max_age_hours}h): {text[:30]}")
                    except Exception as e:
                        logger.debug(f"Could not parse pubDate '{pub_date_str}': {e}. Skipping item.")
                else:
                    logger.debug("No pubDate found in RSS item. Skipping to avoid stale content.")

                if not date_ok:
                    continue

                # Nitter RSS feed won't expose accurate likes/retweets unfortunately, 
                # but we can grab the text and link effectively.
                results.append({
                    "source": f"@{account}",
                    "author": account,
                    "text": text,
                    "likes": 50, # Mock baseline engagement for scoring
                    "retweets": 10, # Mock baseline engagement for scoring
                    "url": link,
                    "native_image_url": native_image_url,  # Direct tweet image if available
                    "type": "tweet"
                })

            logger.info(f"Successfully scraped @{account} using {instance}.")
            success = True
            break # Move to the next account once successful

        except requests.RequestException as e:
            logger.debug(f"Failed to connect to {instance}: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error parsing RSS from {instance}: {e}")
            continue

    if not success:
        logger.warning(f"Failed to scrape @{account} across all mapped Nitter instances.")
        
    return results

def scrape_twitter(max_tweets: int = 5, max_age_hours: int = 2) -> List[Dict]:
    """
    Scrapes recent tweets from configured accounts concurrently using Nitter RSS feeds.
    Checks the `pubDate` to only return content strictly published within the last `max_age_hours` 
    to prevent fetching duplicate old content across scheduling cycles.
    """
    scraped_tweets = []
    logger.info(f"Starting Twitter scraping using Nitter instances for {len(MONITORED_ACCOUNTS)} accounts concurrently.")

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_account = {
            executor.submit(_scrape_account, account, max_age_hours): account
            for account in MONITORED_ACCOUNTS
        }
        
        for future in as_completed(future_to_account):
            account_results = future.result()
            scraped_tweets.extend(account_results)

    logger.info(f"Total tweets scraped: {len(scraped_tweets)}")
    return scraped_tweets

if __name__ == "__main__":
    tweets = scrape_twitter(2)
    for t in tweets:
        print(f"[{t['source']}] {t['text'][:50]}...")
