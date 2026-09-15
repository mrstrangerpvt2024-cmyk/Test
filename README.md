# HTML Name & Telegram Link Telegram Bot

This version does NOT contain or hard-code any test HTML file.

## How it works
1. Upload any `.html`/`.htm` file to the bot.
2. `/setname Your Name`
3. `/setlink https://t.me/yourchannel`
4. `/generate`

The bot returns the edited HTML using the **same original filename and caption**.

## Railway
Set environment variable:
`BOT_TOKEN=your_telegram_bot_token`

Start command:
`python bot.py`

## Important
Settings are stored in memory and reset when the bot restarts.
