import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from config.settings import NEWS_SITES_RSS
from utils.logger import get_logger
from utils.text_cleaner import clean_text

logger = get_logger()

def scrape_news() -> List[Dict]:
    """
    Scrapes headlines and links from configured RSS feeds.
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
            for item in items[:5]:
                title = clean_text(item.title.text if item.title else "")
                link = item.link.text if item.link else ""
                description = clean_text(item.description.text if item.description else "")

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
