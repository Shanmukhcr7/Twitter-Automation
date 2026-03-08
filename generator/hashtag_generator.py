import re
from typing import Dict, List
from utils.logger import get_logger

logger = get_logger()

def extract_keywords(text: str) -> List[str]:
    """
    Extracts potential keywords from text (words starting with capital letters, 
    or words longer than 5 chars).
    """
    # Find all words with 5+ chars
    words = re.findall(r'\b[A-Za-z]{5,}\b', text)
    # Also find capitalized words as they might be entities
    cap_words = re.findall(r'\b[A-Z][a-z]+\b', text)
    
    combined = list(set(words + cap_words))
    # Filter common stop words implicitly by keeping it simple or if we had a list
    # We'll just take the top ones prioritizing capitalized
    
    return [w.lower() for w in combined]

from ai.ai_client import generate_hashtags as ai_hashtag_gen

def generate_hashtags(item: Dict, tweet_text: str = "", max_tags: int = 4) -> str:
    """
    Automatically generates hashtags using AI based on the generated tweet text.
    Falls back to basic rule-based extraction if AI fails.
    """
    if not item:
        return ""

    logger.info("Generating hashtags for content using AI.")
    
    # Preferably use the drafted tweet, or fallback to the raw item data
    source_text = tweet_text or (item.get("title", "") if item.get("type") == "news" else item.get("text", ""))
    
    ai_tags = ai_hashtag_gen(source_text)
    
    if ai_tags:
         logger.info(f"✅ AI Generated hashtags: {ai_tags}")
         return ai_tags
         
    # --- FALLBACK ---
    logger.warning("AI hashtag generation failed. Falling back to rule-based extraction.")
    
    hashtags = set()
    matched_trends = item.get("matched_trends", [])
    for trend in matched_trends:
        clean_trend = "".join(word.capitalize() for word in trend.split())
        hashtags.add(f"#{clean_trend}")

    if item.get("type") == "news":
        source = item.get("source", "").replace(" ", "")
        if source:
            hashtags.add(f"#{source}")

    keywords = extract_keywords(source_text)
    for kw in keywords:
        if len(hashtags) >= max_tags:
            break
        if kw.isalnum():
            hashtags.add(f"#{kw.capitalize()}")

    final_tags = list(hashtags)[:max_tags]
    tag_string = " ".join(final_tags)
    
    logger.debug(f"Fallback hashtags: {tag_string}")
    return tag_string
