import requests
import json
from time import sleep
from typing import Optional
from config.settings import NVIDIA_API_KEY
from utils.logger import get_logger

logger = get_logger()

NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL_NAME = "qwen/qwen3.5-122b-a10b"

def _call_ai_api(prompt: str, system_message: str = "You are a helpful AI automation assistant.", max_tokens: int = 500, stream: bool = False, retries: int = 3) -> Optional[str]:
    """
    Core function to interact with the NVIDIA API.
    Handles streaming/non-streaming, retries, and rate limiting.
    """
    if not NVIDIA_API_KEY:
        logger.error("NVIDIA_API_KEY not found in environment.")
        return None

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": max_tokens,
        "stream": stream
    }

    for attempt in range(1, retries + 1):
        try:
            logger.info(f"AI Request Start | Model: {MODEL_NAME} | Attempt: {attempt}")
            
            # Use streaming parsing if requested
            if stream:
                response = requests.post(NVIDIA_API_URL, headers=headers, json=payload, stream=True, timeout=30)
                response.raise_for_status()
                
                full_content = ""
                for line in response.iter_lines():
                    if line:
                        line_text = line.decode('utf-8')
                        if line_text.startswith("data: ") and line_text != "data: [DONE]":
                            data = json.loads(line_text[6:])
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    full_content += delta['content']
                
                logger.info("AI Stream Response Received.")
                return full_content.strip()

            else:
                # Non-streaming parsing
                response = requests.post(NVIDIA_API_URL, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                logger.info("AI Standard Response Received.")
                return data['choices'][0]['message']['content'].strip()

        except requests.exceptions.HTTPError as http_err:
            logger.error(f"AI API HTTP Error (Attempt {attempt}/{retries}): {http_err} - {response.text}")
            if response.status_code == 429: # Rate limit
                sleep_time = attempt * 2
                logger.warning(f"Rate limited. Sleeping {sleep_time}s.")
                sleep(sleep_time)
            elif response.status_code >= 500:
                sleep(attempt)
            else:
                break # Client error, no retry
                
        except Exception as e:
            logger.error(f"AI Request Failure (Attempt {attempt}/{retries}): {e}")
            sleep(attempt)

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
    """Converts a block of text into a concise image search query."""
    prompt = f"Convert the following tweet into a short image search query.\n\nTweet:\n{text}\n\nReturn only the search phrase."
    return _call_ai_api(prompt, system_message="You extract high-quality, short search queries for stock images. Output only the short query string.", max_tokens=20)
