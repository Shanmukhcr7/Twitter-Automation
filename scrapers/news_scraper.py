import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from config.settings import NEWS_SITES_RSS
from utils.logger import get_logger
from utils.text_cleaner import clean_text

logger = get_logger()

def scrape_news(max_age_hours: int = 24) -> List[Dict]:
    """
    Scrapes headlines and links from configured RSS feeds.
    Only keeps items published within the last max_age_hours.
    Default 24h covers both morning and evening news cycles.
    """
    scraped_news = []
    logger.info("Starting news scraping from RSS feeds.")

    for site_name, feed_url in NEWS_SITES_RSS.items():
        try:
            logger.debug(f"Fetching RSS feed for {site_name}: {feed_url}")
            # Add a generic user agent
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = requests.get(feed_url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "xml")
            items = soup.find_all("item")

            # Limit to top 5 per site to avoid overwhelming
            for item in items:
                title = clean_text(item.title.text if item.title else "")
                link = item.link.text if item.link else ""
                description = clean_text(item.description.text if item.description else "")
                pub_date_str = item.pubDate.text if item.pubDate else ""

                if not title or not link or not pub_date_str:
                    continue
                    
                # Parse the RSS pubDate and enforce freshness
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
                    scraped_news.append({
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

    logger.info(f"Total news items scraped: {len(scraped_news)}")
    return scraped_news

if __name__ == "__main__":
    news = scrape_news()
    for n in news:
        print(f"[{n['source']}] {n['title']}")
