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

## Deployment Guide

For optimal 24/7 uptime on a Linux server:

1. **Upload your code** to your VPS (e.g., AWS EC2, DigitalOcean Droplet, Linode).
2. **Install PM2** (Node.js process manager) to manage the Python process robustly.
   ```bash
   sudo apt update
   sudo apt install npm
   sudo npm install -g pm2
   ```
3. **Start the Scheduler with PM2**:
   Make sure you are in the bot directory, and have your virtual environment packages accessible. 
   ```bash
   pm2 start "venv/bin/python -m scheduler.task_scheduler" --name "twitter_automation_engine"
   ```
4. **Ensure Persistence Across Reboots**:
   ```bash
   pm2 startup
   pm2 save
   ```

### Alternatively using systemd:
1. Create a service file: `sudo nano /etc/systemd/system/twitterbot.service`
2. Configure:
   ```ini
   [Unit]
   Description=Twitter Viral Automation Bot
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/path/to/twitter_automation_bot
   ExecStart=/path/to/twitter_automation_bot/venv/bin/python -m scheduler.task_scheduler
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
3. Enable and start:
   ```bash
   sudo systemctl enable twitterbot
   sudo systemctl start twitterbot
   ```

## Logs & Debugging
Check the `logs/` directory for operational info (`bot_info.log`) and dedicated error traps (`bot_error.log`). Loguru automatically handles log rotation to keep storage consumption safe.
