# Twitter Viral Content Automation Engine

A fully automated, modular, and production-ready Python system designed to discover trending content, evaluate its viral potential, rewrite it, attach relevant imagery, and automatically post it to Twitter/X.

## Project Overview

The engine relies on scraping and free tools to minimize API costs. It continuously monitors:
- Top headlines from trusted news sites via RSS.
- High-engagement accounts on Twitter via `snscrape`.
- Real-time trending searches in Google Trends via `pytrends`.

It then assigns a **viral score** to each piece of collected content based on custom metrics (likes, retweets, trending keyword matches, breaking news labels). The top-performing content is rewritten into an engaging tweet format, enriched with dynamically synthesized hashtags and a relevant image from DuckDuckGo, before being published via the Twitter API.

## Architecture Framework

```text
twitter_automation_bot/
├── config/
│   └── settings.py          # Centralized configuration (weights, accounts, schedules)
├── scrapers/
│   ├── news_scraper.py      # RSS feed parsing via BeautifulSoup
│   ├── twitter_scraper.py   # CLI wrapper for snscrape
│   └── trends_scraper.py    # pytrends integration
├── detector/
│   └── viral_detector.py    # Scoring algorithm logic
├── generator/
│   ├── tweet_generator.py   # Content rewriting templates
│   └── hashtag_generator.py # Keyword and trend synthesis
├── media/
│   └── image_fetcher.py     # duckduckgo-search and Pillow verification
├── poster/
│   └── twitter_poster.py    # Tweepy v1.1 and v2 integration
├── scheduler/
│   └── task_scheduler.py    # schedule library chron jobs
├── utils/
│   ├── text_cleaner.py      # HTML/whitespace processing
│   └── logger.py            # Loguru configuration
├── logs/                    # Generated at runtime
├── media/temp/              # Image download cache
├── .env.example             # Environment template
├── constraints.txt          # (Optional) specific library pins if needed
├── main.py                  # Orchestrator
└── README.md
```

## Installation Instructions

1. **Clone the repository** (if hosted via git):
   ```bash
   git clone <repository_url>
   cd twitter_automation_bot
   ```

2. **Set up a Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: Ensure `snscrape` is globally installed or accessible in your PATH environment if the python module wrapper requires the CLI.*

## Environment Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Open `.env` and configure your standard Twitter Developer API credentials:
   ```env
   TWITTER_API_KEY=your_api_key
   TWITTER_API_SECRET=your_api_secret
   TWITTER_ACCESS_TOKEN=your_access_token
   TWITTER_ACCESS_SECRET=your_access_secret
   ```
   Your Twitter Developer application requires **Elevated Access** or properly scoped **OAuth 1.0a / OAuth 2.0** permissions (Read and Write) to execute media uploads and create tweets.

## Running the Bot

### Immediate Single Execution
To test the pipeline sequentially just once:
```bash
python main.py
```

### Running the Scheduler
To start the daemon that monitors, evaluates, and posts based on intervals:
```bash
python -m scheduler.task_scheduler
```

## Deployment Guide (Self-Hosted via Coolify / Docker)

For optimal 24/7 uptime on your Hostinger KVM VPS, this project is fully Dockerized for easy deployment on [Coolify](https://coolify.io).

1. **Upload your code** to your private GitHub repository.
2. **Access Coolify**: Open your Coolify dashboard and click **Create** -> **Project** -> **Add New Resource**.
3. **Connect GitHub**: Select your GitHub repository.
4. **Deploy via Docker**: 
   - Coolify will automatically detect the `Dockerfile` (or you can use the `docker-compose.yml` integration) and build the Python 3.10 environment.
5. **Environment Variables**:
   Under the **Environment Variables** tab in your newly created Coolify application, securely paste EVERY API key from your local `.env` file (e.g., `TWITTER_API_KEY`, `NVIDIA_API_KEY`, `UNSPLASH_KEY`).
6. **Start the Service**:
   Click **Deploy**. Coolify will compile the container and spin up the bot as a background worker. Thanks to Docker, it will automatically restart upon server reboots or application crashes forever!

## Logs & Debugging
Check the `logs/` directory for operational info (`bot_info.log`) and dedicated error traps (`bot_error.log`). Loguru automatically handles log rotation. If running inside Coolify, you can simply view the live terminal output natively inside your Coolify dashboard.
