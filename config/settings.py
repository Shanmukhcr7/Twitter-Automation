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
    "WIRED",
    "AndrewYNg",
    "sama",
    "lexfridman",
    "ylecun",
    "rowancheung",
    "varunmayya",
    "demishassabis",
    "OpenAI",
    "DeepMind",
    "StanfordHAI",
    "SwiftOnSecurity",
    "TheHackersNews",
    "binitamshah",
    "LiveOverflow",
    "mikko",
    "neiltyson",
    "newscientist",
    "NatureNews",
    "BBCScienceNews",
    "ReutersScience",
    "ShaanVP",
    "SahilBloom",
    "DavidPerell",
    "codie_sanchez",
    "DickieBush",
    "paulg",
    "naval",
    "garrytan",
    "balajis",
    "patrick_oshag",
    "levelsio",
    "tibo_maker",
    "theo",
    "kentcdodds",
    "dan_abramov",
    "addyosmani",
    "rauchg",
    "leeerob",
    "paulirish",
    "getify",
    "dhh",
    "wesbos",
    "syntaxfm",
    "bradtraversy",
    "fireship_dev",
    "evan_you",
    "tjholowaychuk",
    "karpathy",
    "goodside",
    "emollick",
    "linusgsebastian",
    "mkbhd",
    "casey",
    "mrbeast",
    "mrwhosetheboss",
    "unusual_whales",
    "visualcap",
    "cb_doge",
    "AltcoinDailyio",
    "DocumentingBTC",
    "CoinDesk",
    "Cointelegraph",
    "TechCrunch",
    "verge",
    "arstechnica",
    "ProductHunt",
    "ycombinator",
    "IndieHackers",
    "NoCodeDevs",
    "startupgrind",
    "a16z",
    "navalbot"
]

# Supported News RSS/URLs or general topics
NEWS_SITES_RSS = {
    "India Today": "https://www.indiatoday.in/rss/home",
    "Times of India": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "NDTV": "https://feeds.feedburner.com/ndtvnews-top-stories",
    "The Hindu": "https://www.thehindu.com/news/national/feeder/default.rss",
    "Indian Express": "https://indianexpress.com/feed/",
    "Hindustan Times": "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
    "BBC News": "https://www.bbc.com/news",
    "Reuters": "https://www.reuters.com",
    "CNN": "https://www.cnn.com",
    "Al Jazeera": "https://www.aljazeera.com",
    "The Guardian": "https://www.theguardian.com",
    "New York Times": "https://www.nytimes.com",
    "Washington Post": "https://www.washingtonpost.com",
    "NBC News": "https://www.nbcnews.com",
    "ABC News": "https://abcnews.go.com",
    "USA Today": "https://www.usatoday.com",
    "Bloomberg": "https://www.bloomberg.com",
    "Wall Street Journal": "https://www.wsj.com",
    "Financial Times": "https://www.ft.com",
    "CNBC": "https://www.cnbc.com",
    "MarketWatch": "https://www.marketwatch.com",
    "Business Insider": "https://www.businessinsider.com",
    "Forbes": "https://www.forbes.com",
    "TechCrunch": "https://techcrunch.com",
    "The Verge": "https://www.theverge.com",
    "Wired": "https://www.wired.com",
    "Ars Technica": "https://arstechnica.com",
    "The Next Web": "https://thenextweb.com",
    "Engadget": "https://www.engadget.com",
    "VentureBeat": "https://venturebeat.com",
    "News18": "https://www.news18.com",
    "Firstpost": "https://www.firstpost.com",
    "WION": "https://www.wionews.com",
    "Nature": "https://www.nature.com/news",
    "Scientific American": "https://www.scientificamerican.com",
    "New Scientist": "https://www.newscientist.com",
    "Space.com": "https://www.space.com"
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
