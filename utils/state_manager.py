import os
import json
import hashlib
from datetime import datetime, timezone
from utils.logger import get_logger

logger = get_logger()

# Store history in a data/ directory in the project root
STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "posted_history.json")
MAX_HISTORY = 200  # Rolling window to prevent unlimited growth


def _load_state() -> dict:
    """Load the posted history from disk. Returns an empty state dict if missing."""
    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load state file: {e}")
    return {"posted_ids": []}


def _save_state(state: dict):
    """Persist state to disk."""
    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"Could not save state file: {e}")


def _make_id(item: dict) -> str:
    """Create a stable fingerprint for a content item using its URL or text."""
    # Prefer URL as it's definitive. Fall back to hashing the text.
    identifier = item.get("url") or item.get("link") or item.get("text", "") or item.get("title", "")
    return hashlib.md5(identifier.strip().lower().encode()).hexdigest()


def is_already_posted(item: dict) -> bool:
    """Returns True if this item has already been posted."""
    item_id = _make_id(item)
    state = _load_state()
    return item_id in state.get("posted_ids", [])


def mark_as_posted(item: dict):
    """Records the item as posted in the persistent state."""
    item_id = _make_id(item)
    state = _load_state()
    
    posted_ids = state.get("posted_ids", [])
    
    if item_id not in posted_ids:
        posted_ids.append(item_id)
        # Rolling window - remove oldest if over limit
        if len(posted_ids) > MAX_HISTORY:
            posted_ids = posted_ids[-MAX_HISTORY:]
        
        state["posted_ids"] = posted_ids
        state["last_updated"] = datetime.now(timezone.utc).isoformat()
        _save_state(state)
        logger.debug(f"Marked item as posted. History size: {len(posted_ids)}")


def filter_unposted(items: list) -> list:
    """Filters a list of items, keeping only those not yet posted."""
    state = _load_state()
    posted_ids = set(state.get("posted_ids", []))
    
    fresh = [item for item in items if _make_id(item) not in posted_ids]
    filtered_count = len(items) - len(fresh)
    
    if filtered_count > 0:
        logger.info(f"Filtered out {filtered_count} already-posted items. {len(fresh)} fresh items remain.")
    
    return fresh
