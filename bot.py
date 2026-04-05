import re
import os
import logging
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("message_filter.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
api_id_str = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
source_chat_id_str = os.getenv("SOURCE_CHAT_ID")
destination_chat_id_str = os.getenv("DESTINATION_CHAT_ID")
session_name = os.getenv("SESSION_NAME", "forwarder_session")
message_template = os.getenv("MESSAGE_TEMPLATE", "{text}")
repeat_count_str = os.getenv("ALERT_REPEAT_COUNT", "10")
repeat_interval_seconds_str = os.getenv("ALERT_REPEAT_INTERVAL_SECONDS", "2")

# Validate configuration
required_vars = {
    "API_ID": api_id_str,
    "API_HASH": api_hash,
    "SOURCE_CHAT_ID": source_chat_id_str,
    "DESTINATION_CHAT_ID": destination_chat_id_str,
}

missing_vars = [var for var, value in required_vars.items() if value is None]
if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    exit(1)

# Convert to appropriate types
try:
    API_ID: int = int(api_id_str)  # type: ignore
    API_HASH: str = api_hash  # type: ignore
    SOURCE_CHAT_ID: int = int(source_chat_id_str)  # type: ignore
    DESTINATION_CHAT_ID: int = int(destination_chat_id_str)  # type: ignore
    SESSION_NAME: str = session_name
except ValueError as e:
    logger.error(f"Error converting environment variables to correct types: {e}")
    exit(1)

try:
    ALERT_REPEAT_COUNT: int = max(1, int(repeat_count_str))
except ValueError:
    logger.warning("Invalid ALERT_REPEAT_COUNT. Falling back to 10.")
    ALERT_REPEAT_COUNT = 10

try:
    ALERT_REPEAT_INTERVAL_SECONDS: float = max(0.0, float(repeat_interval_seconds_str))
except ValueError:
    logger.warning("Invalid ALERT_REPEAT_INTERVAL_SECONDS. Falling back to 2.")
    ALERT_REPEAT_INTERVAL_SECONDS = 2.0


def create_regex_from_pattern(pattern: str) -> str:
    r"""
    Convert a simple text pattern to a flexible regex pattern.

    - Escapes special regex characters
    - Makes spaces flexible (\s+)
    - Allows optional spaces after colons (\s*)
    """
    escaped = re.escape(pattern)

    # Replace escaped spaces with flexible whitespace
    regex_pattern = escaped.replace(r"\ ", r"\s+")

    # Allow optional whitespace after colons
    regex_pattern = regex_pattern.replace(r"\:\s+", r"\:\s*")

    return regex_pattern


# Load and process filter patterns
filter_patterns_str = os.getenv("FILTER_PATTERNS", "")

if not filter_patterns_str:
    logger.warning("No FILTER_PATTERNS defined in .env file. Bot will not send any messages.")
    PATTERNS = []
else:
    # Split patterns by semicolon and create regex patterns
    simple_patterns = [p.strip() for p in filter_patterns_str.split(";") if p.strip()]
    PATTERNS = [create_regex_from_pattern(p) for p in simple_patterns]
    logger.info(f"Loaded {len(PATTERNS)} filter patterns:")
    for i, (simple, regex) in enumerate(zip(simple_patterns, PATTERNS), 1):
        logger.info(f"  Pattern {i}: '{simple}' -> regex: {regex}")

# Create Telegram client
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)


def rewrite_message(text: str) -> str:
    """Build outbound message text from a configurable template."""
    try:
        return message_template.format(
            text=text,
            source_chat_id=SOURCE_CHAT_ID,
            destination_chat_id=DESTINATION_CHAT_ID,
        )
    except KeyError as e:
        logger.error(f"Invalid placeholder in MESSAGE_TEMPLATE: {e}. Falling back to raw text.")
        return text


@client.on(events.NewMessage)
async def forwarder(event):
    """Send rewritten messages when incoming messages match configured patterns."""
    # 1. Check if the message is from the specific Source Group
    if event.chat_id != SOURCE_CHAT_ID:
        return

    # 2. Get message text
    text = event.text

    # 3. Check if text exists and matches any pattern
    if text and PATTERNS:
        for pattern in PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.info(
                    f"Match found! Sending rewritten message from {SOURCE_CHAT_ID} to {DESTINATION_CHAT_ID}"
                )

                try:
                    rewritten_text = rewrite_message(text)
                    for attempt in range(ALERT_REPEAT_COUNT):
                        await client.send_message(DESTINATION_CHAT_ID, rewritten_text)
                        if attempt < ALERT_REPEAT_COUNT - 1:
                            await asyncio.sleep(ALERT_REPEAT_INTERVAL_SECONDS)
                    logger.info(
                        f"Rewritten message sent {ALERT_REPEAT_COUNT} times "
                        f"with {ALERT_REPEAT_INTERVAL_SECONDS}s interval"
                    )
                except Exception as e:
                    logger.error(f"Error sending rewritten message: {e}")
                break


async def main():
    """Main function to start the bot."""
    logger.info("Starting message filter bot...")
    logger.info(f"Source chat ID: {SOURCE_CHAT_ID}")
    logger.info(f"Destination chat ID: {DESTINATION_CHAT_ID}")

    try:
        await client.start()
        logger.info("Bot started successfully")
        await client.run_until_disconnected()
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
