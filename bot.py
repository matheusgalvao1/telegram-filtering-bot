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
        logging.FileHandler('passport_alerts.log'),
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

# Regex Pattern:
# Matches "✅ CURITIBA: PASSAPORTE" or "✅ FLORIAN[ÓO]POLIS: PASSAPORTE"
PATTERN = r"✅\s*(CURITIBA|FLORIAN[ÓO]POLIS)\s*:\s*PASSAPORTE"

# Create Telegram client
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

@client.on(events.NewMessage)
async def forwarder(event):
    """Forward messages matching passport alert pattern."""
    # 1. Check if the message is from the specific Source Group
    if event.chat_id != SOURCE_CHAT_ID:
        return

    # 2. Get message text
    text = event.text
    
    # 3. Check if text exists and matches pattern
    if text and re.search(PATTERN, text, re.IGNORECASE):
        logger.info(f"Match found! Forwarding message from {SOURCE_CHAT_ID} to {DESTINATION_CHAT_ID}")
        
        try:
            # Forward the message to the destination
            await event.message.forward_to(DESTINATION_CHAT_ID)
            logger.info("Message forwarded successfully")
        except Exception as e:
            logger.error(f"Error forwarding message: {e}")

async def main():
    """Main function to start the bot."""
    logger.info("Starting passport alerts bot...")
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