from typing import List, Dict, Tuple
from config.settings import SCORING_WEIGHTS, BREAKING_KEYWORDS
from utils.logger import get_logger

logger = get_logger()

def calculate_score(item: Dict, trends: List[str]) -> Tuple[float, List[str]]:
    """
    Calculates the viral potential score of an item (tweet or news).
    score = (retweets * 2) + likes + (trend_match * 5) + (breaking_keyword * 3)
    Returns a tuple of (score, matched_trends).
    """
    score = 0.0
    matched_trends = []

    text = item.get("title", "") if item.get("type") == "news" else item.get("text", "")
    text_lower = text.lower()

    # Base engagement (mostly applies to tweets)
    retweets = float(item.get("retweets", 0))
    likes = float(item.get("likes", 0))

    score += (retweets * SCORING_WEIGHTS.get("retweets", 2.0))
    score += (likes * SCORING_WEIGHTS.get("likes", 1.0))

    # Trend match
    for trend in trends:
        # Check if trend keyword exists in text
        if trend.lower() in text_lower:
            score += SCORING_WEIGHTS.get("trend_match", 5.0)
            matched_trends.append(trend)

    # Breaking keywords match
    for keyword in BREAKING_KEYWORDS:
        if keyword in text_lower:
            score += SCORING_WEIGHTS.get("breaking_keyword", 3.0)

    # Base score for news to give them a fighting chance if no engagement stats exist
    if item.get("type") == "news" and score == 0:
        score += 10.0 # Standard baseline for news

    return score, matched_trends

from ai.ai_client import rate_virality

def detect_viral_content(aggregated_data: List[Dict], trends: List[str], target_type: str = None, top_n: int = 1) -> List[Dict]:
    """
    Evaluates a list of scraped data items and returns a list of the top `top_n` items with the highest viral scores.
    """
    if not aggregated_data:
        logger.warning("No data provided to viral detector.")
        return []
        
    # Pre-filter if a target type was specified
    if target_type == "news":
        filtered_data = [item for item in aggregated_data if item.get("type") == "news"]
    elif target_type == "tweets":
        filtered_data = [item for item in aggregated_data if item.get("type") != "news"]
    else:
        filtered_data = aggregated_data
        
    if not filtered_data:
        logger.warning(f"No data matching target_type '{target_type}' found to evaluate.")
        return []

    logger.info(f"Evaluating {len(filtered_data)} {target_type or 'all'} items heuristically against {len(trends)} trends.")

    # 1. Score heuristically
    scored_items = []
    for item in filtered_data:
        base_score, matched = calculate_score(item, trends)
        scored_items.append({
            "item": item,
            "base_score": base_score,
            "matched_trends": matched
        })

    # Sort descending by base score
    scored_items.sort(key=lambda x: x["base_score"], reverse=True)
    
    # 2. Pick top candidates to save API cost (Take top 8 to ensure we get 4 good AI scores)
    top_candidates = scored_items[:8]
    logger.info(f"Selected top {len(top_candidates)} candidates for AI viral scoring.")

    evaluated_items = []

    for candidate in top_candidates:
        item = candidate["item"]
        text = item.get("title", "") if item.get("type") == "news" else item.get("text", "")
        
        ai_score = rate_virality(text)
        
        # Fallback if AI fails
        if ai_score is None:
            logger.warning("AI viral rating failed. Falling back to heuristic baseline.")
            ai_score = candidate["base_score"] # Inject base score just for sorting purposes
            
        logger.debug(f"AI Viral Score for candidate: {ai_score}/10")
        
        item["matched_trends"] = candidate["matched_trends"]
        item["viral_score"] = ai_score
        evaluated_items.append(item)

    # Sort by AI viral score descending
    evaluated_items.sort(key=lambda x: x.get("viral_score", 0), reverse=True)
    
    # Grab the requested amount of top items
    final_selections = evaluated_items[:top_n]
    
    if final_selections:
        logger.info(f"✅ Selected top {len(final_selections)} viral content items based on AI scoring.")
    else:
        logger.warning("No items met evaluation criteria.")
        
    return final_selections
