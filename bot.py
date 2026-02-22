import re
import os
import logging
from dotenv import load_dotenv
from telethon import TelegramClient, events

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('message_filter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
api_id_str = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
source_chat_id_str = os.getenv('SOURCE_CHAT_ID')
destination_chat_id_str = os.getenv('DESTINATION_CHAT_ID')
session_name = os.getenv('SESSION_NAME', 'forwarder_session')

# Validate configuration
required_vars = {
    'API_ID': api_id_str,
    'API_HASH': api_hash,
    'SOURCE_CHAT_ID': source_chat_id_str,
    'DESTINATION_CHAT_ID': destination_chat_id_str
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

def create_regex_from_pattern(pattern: str) -> str:
    """
    Convert a simple text pattern to a flexible regex pattern.
    
    Example: "✅ CURITIBA: PASSAPORTE" becomes "✅\s+CURITIBA\s*:\s*PASSAPORTE"
    - Escapes special regex characters
    - Makes spaces flexible (\s+ or \s*)
    - Allows for variations in spacing
    """
    # Escape special regex characters except spaces
    escaped = re.escape(pattern)
    
    # Replace escaped spaces with flexible space patterns
    # \s+ means one or more spaces/tabs/newlines
    # \s* means zero or more spaces (for after colons, etc.)
    regex_pattern = escaped.replace(r'\ ', r'\s+')
    
    # Make spaces after special characters like : more flexible
    regex_pattern = re.sub(r'\\:\s\+', r'\\:\s*', regex_pattern)
    
    return regex_pattern

# Load and process filter patterns
filter_patterns_str = os.getenv('FILTER_PATTERNS', '')

if not filter_patterns_str:
    logger.warning("No FILTER_PATTERNS defined in .env file. Bot will not forward any messages.")
    PATTERNS = []
else:
    # Split patterns by semicolon and create regex patterns
    simple_patterns = [p.strip() for p in filter_patterns_str.split(';') if p.strip()]
    PATTERNS = [create_regex_from_pattern(p) for p in simple_patterns]
    logger.info(f"Loaded {len(PATTERNS)} filter patterns:")
    for i, (simple, regex) in enumerate(zip(simple_patterns, PATTERNS), 1):
        logger.info(f"  Pattern {i}: '{simple}' -> regex: {regex}")

# Create Telegram client
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

@client.on(events.NewMessage)
async def forwarder(event):
    """Forward messages matching filter patterns."""
    # 1. Check if the message is from the specific Source Group
    if event.chat_id != SOURCE_CHAT_ID:
        return

    # 2. Get message text
    text = event.text
    
    # 3. Check if text exists and matches any pattern
    if text and PATTERNS:
        for pattern in PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.info(f"Match found! Forwarding message from {SOURCE_CHAT_ID} to {DESTINATION_CHAT_ID}")
                
                try:
                    # Forward the message to the destination
                    await event.message.forward_to(DESTINATION_CHAT_ID)
                    logger.info("Message forwarded successfully")
                except Exception as e:
                    logger.error(f"Error forwarding message: {e}")
                break  # Only forward once even if multiple patterns match

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
    import asyncio
    asyncio.run(main())