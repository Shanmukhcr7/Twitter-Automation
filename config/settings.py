import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_DIR = BASE_DIR / "media" / "temp"

# Ensure media temp directory exists
os.makedirs(MEDIA_DIR, exist_ok=True)

# Twitter API Credentials
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

# NVIDIA API Credentials
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "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")

# Unsplash API Credentials
UNSPLASH_KEY = os.getenv("UNSPLASH_KEY")

# Monitored Twitter Accounts (for scraping)
MONITORED_ACCOUNTS = [
    "IndianTechGuide",
    "ziddyyxx__03",
    "mufaddal_vohra",
    "elonmusk",
    "WIRED"
]

# Supported News RSS/URLs or general topics
NEWS_SITES_RSS = {
    "India Today": "https://www.indiatoday.in/rss/home",
    "Times of India": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "NDTV": "https://feeds.feedburner.com/ndtvnews-top-stories",
    "The Hindu": "https://www.thehindu.com/news/national/feeder/default.rss",
    "Indian Express": "https://indianexpress.com/feed/",
    "Hindustan Times": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml"
}

# Viral Scoring Weights
SCORING_WEIGHTS = {
    "retweets": 2.0,
    "likes": 1.0,
    "trend_match": 5.0,
    "breaking_keyword": 3.0
}

# Keywords that boost "breaking" score
BREAKING_KEYWORDS = [
    "breaking", "alert", "just in", "urgent", "update", "exclusive",
    "revealed", "announced", "launch", "new", "major"
]

# Scheduler Settings (in hours)
SCHEDULE_TWITTER_SCRAPE = 1
SCHEDULE_TRENDS_SCRAPE = 2
SCHEDULE_NEWS_SCRAPE = 3
