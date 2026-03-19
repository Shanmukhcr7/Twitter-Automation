import requests
import time
import random as _random
from bs4 import BeautifulSoup
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from config.settings import MONITORED_ACCOUNTS
from utils.logger import get_logger
from utils.text_cleaner import clean_text

logger = get_logger()

# ── Candidate Nitter instances to probe at startup ───────────────────────────
# The scraper tests EACH of these at startup from the server's own IP and builds
# a runtime list of instances that actually return real RSS XML (not HTML captcha).
# Cloud/datacenter IPs are often blocked by Nitter instances silently (HTTP 200
# but serving an HTML captcha page). The health check detects this automatically.
# Add new candidates here freely — they get validated before use.
ALL_CANDIDATE_INSTANCES = [
    "https://nitter.net",
    "https://xcancel.com",
    "https://nitter.perennialte.ch",
    "https://nitter.tiekoetter.com",
    "https://nitter.privacyredirect.com",
    "https://nitter.projectsegfau.lt",
    "https://nitter.kylrth.com",
    "https://nitter.poast.org",
    "https://nitter.catsarch.com",
    "https://nitter.mint.lgbt",
    "https://nitter.1d4.us",
    "https://nitter.weiler.rocks",
    "https://nitter.unixfox.eu",
    "https://nitter.mstdn.social",
    "https://nitter.foss.wtf",
    "https://nitter.esmailelbob.xyz",
    "https://nitter.lunar.icu",
    "https://nitter.privacydev.net",
]

# Runtime list — populated by _discover_working_instances() on first call
_WORKING_INSTANCES: List[str] = []

# Account used for health checks (small, low-traffic account)
_TEST_ACCOUNT = "jack"


def _check_instance(instance: str) -> bool:
    """Returns True if the instance serves real RSS (not HTML captcha) from this server IP."""
    try:
        url = f"{instance}/{_TEST_ACCOUNT}/rss"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; RSS/2.0)"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return False
        ct = r.headers.get("Content-Type", "")
        text = r.text
        return (
            "xml" in ct or "rss" in ct
            or text.strip().startswith("<?xml")
            or "<rss" in text[:300]
            or "<channel>" in text[:500]
        )
    except Exception:
        return False


def _discover_working_instances() -> List[str]:
    """
    Health-checks all candidate instances IN PARALLEL from this server's own IP.
    Builds a runtime list of instances that serve real RSS XML (not captcha/HTML blocks).
    Called once on first scrape_twitter() call; results cached for the process lifetime.
    """
    global _WORKING_INSTANCES
    logger.info(
        f"Running Nitter health check from this server IP "
        f"({len(ALL_CANDIDATE_INSTANCES)} candidates)..."
    )

    working = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_check_instance, inst): inst for inst in ALL_CANDIDATE_INSTANCES}
        for future in as_completed(futures):
            inst = futures[future]
            try:
                if future.result():
                    working.append(inst)
                    logger.info(f"  [OK]  {inst}")
                else:
                    logger.debug(f"  [NO]  {inst}")
            except Exception as e:
                logger.debug(f"  [ERR] {inst}: {e}")

    if not working:
        logger.error("No working Nitter instances found from this server! Twitter scraping will be skipped.")
    else:
        logger.info(f"Health check done. {len(working)}/{len(ALL_CANDIDATE_INSTANCES)} instances OK from this IP.")

    _WORKING_INSTANCES = working
    return working


def _scrape_account(account: str, max_age_hours: int) -> List[Dict]:
    """Scrapes a single Twitter account using the runtime-validated Nitter instance list."""
    results = []
    logger.debug(f"Scraping tweets for account: @{account}")
    success = False

    if not _WORKING_INSTANCES:
        logger.warning(f"No working Nitter instances available. Skipping @{account}.")
        return []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    }

    # Small random jitter to spread concurrent requests
    time.sleep(_random.uniform(0.3, 1.5))

    for instance in _WORKING_INSTANCES:
        rss_url = f"{instance}/{account}/rss"
        try:
            logger.debug(f"Trying: {rss_url}")
            response = requests.get(rss_url, headers=headers, timeout=15)

            if response.status_code != 200:
                logger.debug(f"{instance} returned {response.status_code}. Trying next...")
                continue

            # Double-check the response is actually RSS (instances can go stale mid-run)
            ct = response.headers.get("Content-Type", "")
            text = response.text
            is_real_rss = (
                "xml" in ct or "rss" in ct
                or text.strip().startswith("<?xml")
                or "<rss" in text[:300]
                or "<channel>" in text[:500]
            )
            if not is_real_rss:
                logger.debug(f"{instance} returned HTML captcha mid-run. Trying next...")
                continue

            soup = BeautifulSoup(response.content, "lxml-xml")
            items = soup.find_all("item")

            if not items:
                logger.debug(f"No RSS items for @{account} on {instance}. Trying next...")
                continue

            for item in items:
                raw_html = item.description.text if item.description else ""
                text_content = clean_text(raw_html)
                link = item.link.text if item.link else ""
                pub_date_str = item.pubDate.text if item.pubDate else ""

                native_image_url = None
                try:
                    desc_soup = BeautifulSoup(raw_html, "html.parser")
                    img_tag = desc_soup.find("img", src=lambda s: s and s.startswith("https://"))
                    if img_tag:
                        native_image_url = img_tag["src"]
                        logger.debug(f"Extracted tweet image: {native_image_url[:60]}")
                except Exception:
                    pass

                if not text_content:
                    continue

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
                            logger.debug(f"Skipping tweet aged {age_hours:.1f}h (max {max_age_hours}h): {text_content[:30]}")
                    except Exception as e:
                        logger.debug(f"Could not parse pubDate '{pub_date_str}': {e}")
                else:
                    logger.debug("No pubDate — skipping to avoid stale content.")

                if not date_ok:
                    continue

                results.append({
                    "source": f"@{account}",
                    "author": account,
                    "text": text_content,
                    "likes": 50,
                    "retweets": 10,
                    "url": link,
                    "native_image_url": native_image_url,
                    "type": "tweet"
                })

            logger.info(f"Successfully scraped @{account} via {instance}.")
            success = True
            break

        except requests.RequestException as e:
            logger.debug(f"Connection error on {instance}: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error parsing RSS from {instance}: {e}")
            continue

    if not success:
        logger.warning(f"Failed to scrape @{account} across all working Nitter instances.")

    return results


def scrape_twitter(max_tweets: int = 5, max_age_hours: int = 2) -> List[Dict]:
    """
    Scrapes recent tweets from configured accounts using Nitter RSS feeds.

    On first call, runs a server-side health check to discover which Nitter
    instances actually work from this server's IP (many block datacenter IPs
    silently with fake HTTP 200 + HTML captcha responses). Only validated
    instances are used for scraping. Results cached for the process lifetime.
    """
    # Lazy: run health check exactly once per process
    if not _WORKING_INSTANCES:
        _discover_working_instances()

    if not _WORKING_INSTANCES:
        logger.error("No working Nitter instances. Skipping Twitter scraping for this cycle.")
        return []

    scraped_tweets = []
    working_names = [i.replace("https://", "") for i in _WORKING_INSTANCES]
    logger.info(
        f"Scraping {len(MONITORED_ACCOUNTS)} accounts via {len(_WORKING_INSTANCES)} "
        f"validated instance(s): {working_names}"
    )

    # Scale workers to the number of working instances (max 5 to avoid rate-limiting)
    max_workers = max(1, min(len(_WORKING_INSTANCES) * 2, 5))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
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
        print(f"[{t['source']}] {t['text'][:80]}...")
