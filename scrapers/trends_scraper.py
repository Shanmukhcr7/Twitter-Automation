import requests
import json
from typing import List
from utils.logger import get_logger

logger = get_logger()

# New stable API endpoint
TRENDS_API_URL = "https://trends.google.com/trends/api/dailytrends"

def scrape_trends(geo: str = 'IN', limit: int = 20) -> List[str]:
    """
    Directly hits the Google Trends Daily API to avoid the pytrends 404 error.
    Parses the JSON payload (stripping Google's dirty prefix characters) to extract trends.
    """
    logger.info(f"Starting Google Trends Scraping via Daily API for geo: {geo}")
    
    params = {
        "hl": "en-US",
        "tz": "330",
        "geo": geo
    }
    
    try:
        response = requests.get(TRENDS_API_URL, params=params, timeout=15)
        response.raise_for_status()
        
        # Google Trends API prefixes JSON with dirty characters ")]}'"
        # We must strip them away before parsing
        raw_text = response.text
        clean_text = raw_text.lstrip(")]}',\n")
        
        data = json.loads(clean_text)
        
        trends = []
        # Navigate the payload tree safely
        days = data.get("default", {}).get("trendingSearchesDays", [])
        
        if not days:
            logger.warning("Google Trends returned an empty days array.")
            return []
            
        # Extract from the most recent day (index 0)
        searches = days[0].get("trendingSearches", [])
        
        for search in searches:
            query = search.get("title", {}).get("query", "")
            if query:
                trends.append(query)
                
            if len(trends) >= limit:
                break
                
        logger.info(f"Successfully fetched {len(trends)} trending topics.")
        logger.debug(f"Top 5 Trends: {trends[:5]}")
        return trends
        
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Network Error fetching Google Trends: {req_err}")
        return []
    except json.JSONDecodeError as json_err:
        logger.error(f"Failed to parse Google Trends JSON: {json_err}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in Google Trends Scraper: {e}")
        return []

if __name__ == "__main__":
    trends = scrape_trends()
    from pprint import pprint
    pprint(trends[:5])
