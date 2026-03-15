import requests
import json
from time import sleep
from typing import Optional
from config.settings import NVIDIA_API_KEY
from utils.logger import get_logger
from openai import OpenAI

logger = get_logger()

NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1"
MODEL_NAME = "meta/llama-3.1-405b-instruct"

ai_client = OpenAI(
    base_url=NVIDIA_API_URL,
    api_key=NVIDIA_API_KEY
) if NVIDIA_API_KEY else None

def _call_ai_api(prompt: str, system_message: str = "You are a helpful AI automation assistant.", max_tokens: int = 500, stream: bool = False, retries: int = 3) -> Optional[str]:
    """
    Core function to interact with the NVIDIA API using the OpenAI SDK.
    Handles streaming/non-streaming, retries, and rate limiting.
    """
    if not ai_client:
        logger.error("NVIDIA_API_KEY not found in environment. Client not initialized.")
        return None

    for attempt in range(1, retries + 1):
        try:
            logger.info(f"AI Request Start | Model: {MODEL_NAME} | Attempt: {attempt}")
            
            completion = ai_client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                top_p=0.7,
                max_tokens=max_tokens,
                stream=stream
            )
            
            if stream:
                full_content = ""
                for chunk in completion:
                    if not chunk.choices:
                        continue
                    if getattr(chunk.choices[0], "delta", None) and chunk.choices[0].delta.content is not None:
                        full_content += chunk.choices[0].delta.content
                
                logger.info("AI Stream Response Received.")
                return full_content.strip()

            else:
                logger.info("AI Standard Response Received.")
                return completion.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"AI Request Failure (Attempt {attempt}/{retries}): {e}")
            sleep(attempt * 2)

    logger.error("AI Request failed after all retries.")
    return None

def generate_text(prompt: str) -> Optional[str]:
    """Generates a rewrite of text based on the provided prompt."""
    return _call_ai_api(prompt, system_message="You are a social media expert writer.")

def rate_virality(text: str) -> Optional[int]:
    """Scores how viral a text might be from 1-10."""
    prompt = f"Rate the viral potential of this tweet from 1 to 10.\n\nTweet:\n{text}\n\nReturn only the number."
    response = _call_ai_api(prompt, system_message="You are a strict data analyst. Return ONLY an integer between 1 and 10 and nothing else.", max_tokens=10)
    
    if not response: return None
    
    try:
        # Clean response to ensure it's just the digit
        score_str = "".join(filter(str.isdigit, response))
        return int(score_str) if score_str else None
    except ValueError:
        logger.error(f"AI returned non-integer for virality rating: {response}")
        return None

def generate_hashtags(text: str) -> Optional[str]:
    """Generates up to 4 hashtags based on content."""
    prompt = f"Generate 4 relevant Twitter hashtags for the following post.\n\nPost:\n{text}\n\nRules:\n• only return hashtags\n• maximum 4 hashtags\n• remove duplicates\n• avoid generic hashtags like #news"
    return _call_ai_api(prompt, system_message="You are a hashtag generator. Output only space-separated hashtags.", max_tokens=50)

def generate_image_query(text: str) -> Optional[str]:
    """Converts a block of text into a precise, specific Unsplash image search query."""
    prompt = f"""Given this tweet content, create a very specific 3-5 word Unsplash image search query that precisely matches the topic visually.

Tweet:
{text}

Rules:
- Be very specific (e.g. 'Indian parliament protest crowd' not 'politics')
- No generic words like 'news', 'trending', 'social media'
- Describe a real visual scene, not abstract concepts
- Return ONLY the query phrase, nothing else"""
    return _call_ai_api(
        prompt,
        system_message="You create precise, specific search queries for stock photography. Return ONLY a 3-5 word visual search phrase. No explanation.",
        max_tokens=30
    )
