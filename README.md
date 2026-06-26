# Telegram Button Bot

A Telegram bot with a web dashboard for visually building and sending posts with inline keyboards (buttons) to Telegram chats and channels.

## Features

- **Visual Button Builder** — drag-and-drop row reordering, color picker, 3 button types (URL, callback, inline query)
- **Rich Text Editor** — Bold, Italic, Underline, Strike, Code, Spoiler, Blockquote, Link
- **Live Phone Preview** — iPhone-style mockup that updates in real time
- **Image Upload** — drag-and-drop with base64 encoding
- **Saved Posts & History** — localStorage persistence with import/export JSON
- **Direct Send** — pick a chat from the dropdown and send instantly
- **CLI Mode** — `python bot.py --post file.json` for headless sending
- **Chat Tracking** — auto-detects when bot is added to groups/channels

## Quick Start

1. **Clone the repo**
   ```
   git clone https://github.com/ariful47526/telegram-button-bot.git
   cd telegram-button-bot
   ```

2. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

3. **Configure environment** — copy `.env.example` to `.env` and fill in your values:
   ```
   BOT_TOKEN=your_bot_token_from_botfather
   CHAT_ID=your_chat_id
   ```

4. **Run** the server (starts both the bot and web UI):
   ```
   python server.py
   ```

5. Open **http://localhost:8000** in a browser and start building posts.

## Authentication

The web app uses **Telegram Login** for authentication. When you open the app, you'll see a "Log in with Telegram" button. Clicking it opens Telegram to verify your identity.

### Setup (one-time)

1. Open **@BotFather** on Telegram
2. Send `/setdomain`
3. Select your bot
4. Enter the domain where the app is hosted (e.g., `ariful47526.github.io` or your custom domain)

This authorizes the Telegram Login Widget on your domain. Without this step, the login button won't work.

### Running locally

If you're running the backend on `localhost:8000` and accessing the frontend via GitHub Pages, append `?api=http://localhost:8000` to the Pages URL:

```
https://ariful47526.github.io/telegram-button-bot/?api=http://localhost:8000
```

Alternatively, just open `http://localhost:8000` directly (the server serves both frontend and API).

## GitHub Pages

The frontend is also available on **GitHub Pages** at:

```
https://ariful47526.github.io/telegram-button-bot/
```

To connect it to your running backend, add `?api=BACKEND_URL` to the URL, e.g.:

```
https://ariful47526.github.io/telegram-button-bot/?api=http://localhost:8000
```

## Docker

```bash
docker build -t tg-button-bot .
docker run -p 8000:8000 -e BOT_TOKEN=your_token -e CHAT_ID=your_chat_id tg-button-bot
```

## Commands

| Command | Description |
|---|---|
| `/chats` | List all chats the bot is in |
| `/start` | Show welcome menu (bot.py only) |
| `/post` | Send a sample post (bot.py only) |
| `/send` | Send a post from JSON (bot.py only) |
| `--post` | CLI: `python bot.py --post file.json` |

## Tech Stack

- **Backend:** Python, FastAPI, python-telegram-bot, Uvicorn
- **Frontend:** Vanilla HTML/CSS/JS (single-page app)
- **Deployment:** Ready for Docker, supports webhooks
