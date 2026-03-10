import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from config.settings import NEWS_SITES_RSS
from utils.logger import get_logger
from utils.text_cleaner import clean_text

logger = get_logger()

from concurrent.futures import ThreadPoolExecutor, as_completed

def _fetch_news(site_name: str, feed_url: str, max_age_hours: int) -> List[Dict]:
    """Helper method to fetch and parse a single RSS feed."""
    results = []
    try:
        logger.debug(f"Fetching RSS feed for {site_name}: {feed_url}")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(feed_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "xml")
        items = soup.find_all("item")

        for item in items:
            title = clean_text(item.title.text if item.title else "")
            link = item.link.text if item.link else ""
            description = clean_text(item.description.text if item.description else "")
            pub_date_str = item.pubDate.text if item.pubDate else ""

            if not title or not link or not pub_date_str:
                continue
                
            date_ok = False
            if pub_date_str:
                try:
                    from email.utils import parsedate_to_datetime
                    import datetime

                    dt = parsedate_to_datetime(pub_date_str)
                    now_utc = datetime.datetime.now(datetime.timezone.utc)
                    age = (now_utc - dt).total_seconds() / 3600.0

                    if age <= max_age_hours:
                        date_ok = True
                    else:
                        logger.debug(f"Skipping news aged {age:.1f}h from {site_name}: {title[:40]}")
                except Exception as e:
                    logger.debug(f"Could not parse pubDate '{pub_date_str}' from {site_name}: {e}. Skipping.")
            else:
                logger.debug(f"No pubDate in item from {site_name}. Skipping.")

            if not date_ok:
                continue

            if title and link:
                results.append({
                    "source": site_name,
                    "title": title,
                    "link": link,
                    "description": description,
                    "type": "news"
                })

        logger.info(f"Successfully scraped {site_name}.")

    except requests.RequestException as e:
        logger.error(f"Network error scraping {site_name}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error scraping {site_name}: {e}")
        
    return results

def scrape_news(max_age_hours: int = 24) -> List[Dict]:
    """
    Scrapes headlines and links from configured RSS feeds concurrently.
    Only keeps items published within the last max_age_hours.
    Default 24h covers both morning and evening news cycles.
    """
    scraped_news = []
    logger.info(f"Starting news scraping from {len(NEWS_SITES_RSS)} RSS feeds.")

    # Fetch feeds in parallel. Using up to 10 threads to be respectful to sources.
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_site = {
            executor.submit(_fetch_news, site_name, feed_url, max_age_hours): site_name 
            for site_name, feed_url in NEWS_SITES_RSS.items()
        }
        
        for future in as_completed(future_to_site):
            site_results = future.result()
            scraped_news.extend(site_results)

    logger.info(f"Total news items scraped: {len(scraped_news)}")
    return scraped_news

if __name__ == "__main__":
    news = scrape_news()
    for n in news:
        print(f"[{n['source']}] {n['title']}")
