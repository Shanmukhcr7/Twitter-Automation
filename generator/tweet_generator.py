from typing import Dict
from utils.logger import get_logger
from utils.text_cleaner import truncate_text

logger = get_logger()

# Templates to ensure variety and prevent direct word-for-word copying
TEMPLATES = [
    "🔥 Trending Now\n\n{content}\n\nWhat do you think?",
    "🚨 Big news!\n\n{content}\n\nThoughts on this?",
    "Is this the next big thing? 👇\n\n{content}\n\nLet's discuss!",
    "Just in: \n\n{content}\n\nDrop your opinions below👇"
]

def format_news(item: Dict) -> str:
    """Formats a news item into a tweetable string."""
    title = item.get("title", "")
    source = item.get("source", "News")
    link = item.get("link", "")
    
    # Example: Breaking from BBC: [Title] - [Link]
    return f"From {source}: {title}\nRead more: {link}"

def format_tweet(item: Dict) -> str:
    """Formats an existing tweet into a quote/rewrite string."""
    text = item.get("text", "")
    author = item.get("author", "someone")
    
    # We strip URLs from text usually, so we quote it
    return f"As @{author} pointed out:\n\"{text}\""

from ai.ai_client import generate_text

def generate_tweet(item: Dict) -> str:
    """
    Rewrites selected content into an engaging Twitter post using AI.
    Falls back to rule-based rewriting if the AI request fails.
    """
    if not item:
        logger.warning("Empty item provided to tweet generator.")
        return ""

    logger.info("Drafting tweet base content.")

    item_type = item.get("type", "unknown")
    
    if item_type == "news":
        base_content = format_news(item)
    elif item_type == "tweet":
        base_content = format_tweet(item)
    else:
        base_content = item.get("title", item.get("text", "Interesting development taking place right now!"))

    # AI Prompt Construction
    prompt = f"""Rewrite the following content into an engaging Twitter post under 250 characters.
Make it exciting and suitable for social media.

Content:
{base_content}

Ensure:
• tweet length < 280 characters
• natural tone
• no emojis overload"""

    ai_tweet = generate_text(prompt)
    
    if ai_tweet:
        logger.info(f"✅ AI Generated tweet of length {len(ai_tweet)}.")
        return ai_tweet
    
    # --- FALLBACK ---
    logger.warning("AI formulation failed. Falling back to rule-based generation.")
    template = TEMPLATES[0]
    
    max_content_length = 280 - len(template) + len("{content}") - 10 
    truncated_content = truncate_text(base_content, max_length=max_content_length)
    
    final_tweet = template.format(content=truncated_content)
    
    logger.info(f"Fallback generated tweet of length {len(final_tweet)}.")
    return final_tweet
