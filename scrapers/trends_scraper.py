import requests
import json
from typing import List
from utils.logger import get_logger

logger = get_logger()

import xml.etree.ElementTree as ET

TRENDS_RSS_URL = "https://trends.google.com/trending/rss"

def scrape_trends(geo: str = 'IN', limit: int = 15) -> List[str]:
    """
    Scrapes the Google Trends RSS feed to avoid the pytrends 404 error
    and the 404 block on Cloud Datacenter IPs for the JSON endpoints.
    """
    logger.info(f"Starting Google Trends Scraping via RSS for geo: {geo}")
    
    params = {
        "geo": geo
    }
    
    # Needs a real user-agent to bypass basic blocks
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml"
    }
    
    try:
        response = requests.get(TRENDS_RSS_URL, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        trends = []
        
        for item in root.findall(".//item"):
            title = item.find("title")
            if title is not None and title.text:
                trends.append(title.text)
                
            if len(trends) >= limit:
                break
                
        logger.info(f"Successfully fetched {len(trends)} trending topics via RSS.")
        logger.debug(f"Top 5 Trends: {trends[:5]}")
        return trends
        
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Network Error fetching Google Trends RSS: {req_err}")
        return []
    except ET.ParseError as xml_err:
        logger.error(f"Failed to parse Google Trends XML: {xml_err}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in Google Trends Scraper: {e}")
        return []

if __name__ == "__main__":
    trends = scrape_trends()
    from pprint import pprint
    pprint(trends[:5])
