# Message Filtering Bot

A Telegram userbot that filters messages from one group and forwards relevant messages to another group.

## Features

- Monitors a source Telegram group for specific messages
- Filters messages using configurable patterns
- Forwards matching messages to a destination group
- Configurable via environment variables
- Comprehensive logging and error handling

## Requirements

- Python 3.7+
- Telegram API credentials

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Telegram API Credentials

1. Go to [my.telegram.org](https://my.telegram.org/)
2. Log in with your phone number
3. Go to "API development tools"
4. Create a new application to get your `API_ID` and `API_HASH`

### 3. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration:

```env
# Telegram API Credentials
API_ID=1234567  # Replace with your API ID
API_HASH=your_api_hash_here  # Replace with your API Hash

# Chat IDs
SOURCE_CHAT_ID=-12345678  # Group to monitor
DESTINATION_CHAT_ID=-87654321  # Group to forward messages to

# Session file name (optional, defaults to 'forwarder_session')
SESSION_NAME=forwarder_session

# Message filter patterns (separate multiple patterns with semicolon)
FILTER_PATTERNS=🚨 ALERT: IMPORTANT;⚠️ WARNING: CHECK THIS;📢 NOTIFICATION: URGENT
```

#### How to Get Chat IDs

1. Add [@getmyid_bot](https://t.me/getmyid_bot) to Telegram
2. Add the bot to both your source and destination groups
3. Send a message in each group
4. The bot will reply with the chat ID

### 4. Run the Bot

```bash
python bot.py
```

The first time you run the bot, it will ask for your phone number and verification code to create a session file.

## Customization

### Filter Patterns

The bot reads filter patterns from the `FILTER_PATTERNS` variable in your `.env` file. You can define multiple patterns separated by semicolons:

```env
FILTER_PATTERNS=🚨 ALERT: IMPORTANT;⚠️ WARNING: CHECK THIS;📢 NOTIFICATION: URGENT
```

The bot automatically converts these simple text patterns into flexible regex patterns that can match variations in spacing and formatting. Just write the pattern as you expect to see it in messages, and the bot will handle the rest.

### Pattern Matching

- Patterns are case-insensitive
- Spaces in patterns are flexible (will match multiple spaces, tabs, etc.)
- Special characters are automatically escaped
- You don't need to write regex - just write the text you want to match

## Logging

The bot creates a log file named `message_filter.log` in the same directory. It logs:
- Bot startup and shutdown
- Successfully forwarded messages
- Errors and warnings
- Configuration validation
- Loaded filter patterns

## Session Management

The bot creates a session file (default: `forwarder_session.session`) to maintain login state. This file will be created automatically on first run.

**Important:** The session file contains sensitive authentication data. Make sure it's included in your `.gitignore` and not committed to version control.

## Running as a Service

For production use, consider running the bot as a systemd service or using a process manager like `supervisor` or `pm2`.

### Example systemd service

Create a file `/etc/systemd/system/message-filter.service`:

```ini
[Unit]
Description=Message Filter Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/message-filter
ExecStart=/usr/bin/python3 /path/to/message-filter/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then run:

```bash
sudo systemctl daemon-reload
sudo systemctl enable message-filter
sudo systemctl start message-filter
```

## Troubleshooting

### Common Issues

1. **Missing dependencies**: Make sure you've installed all requirements with `pip install -r requirements.txt`

2. **Invalid API credentials**: Double-check your `API_ID` and `API_HASH` from my.telegram.org

3. **Incorrect Chat IDs**: Verify the Chat IDs using the @getmyid_bot

4. **Permission issues**: Make sure the bot has been added to both groups and has permission to read messages in the source group and forward messages to the destination group

5. **Session file issues**: If you have login problems, delete the `.session` file and restart the bot

### Logs

Check the log file `message_filter.log` for detailed error messages and debugging information.

## License

This project is for personal use only. Please respect Telegram's Terms of Service when using this bot.
