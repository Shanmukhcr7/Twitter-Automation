import sys
import io
from loguru import logger
from config.settings import BASE_DIR

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Remove default handler
logger.remove()

# Wrap stdout in UTF-8 so emoji/unicode (✅ ₹ etc.) never crash the logger
_utf8_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

# Add console handler
logger.add(_utf8_stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")


# Add file handler for general info
logger.add(LOG_DIR / "bot_info.log", rotation="10 MB", retention="7 days", level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}")

# Add file handler specifically for errors
logger.add(LOG_DIR / "bot_error.log", rotation="10 MB", retention="7 days", level="ERROR", format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message} | {exception}")

def get_logger():
    return logger
