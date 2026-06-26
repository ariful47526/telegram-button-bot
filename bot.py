import os
import json
import base64
import sys
import secrets
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

load_dotenv()
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set in .env file")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("About", callback_data="about"),
         InlineKeyboardButton("Help", callback_data="help")],
        [InlineKeyboardButton("Visit Website", url="https://example.com")],
        [InlineKeyboardButton("Share", switch_inline_query="Check out this bot!")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_html(
        "<b>Welcome to the Button Bot!</b>\n\nUse /post to send a post with buttons.",
        reply_markup=reply_markup,
    )


async def post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Option A", callback_data="opt_a"),
         InlineKeyboardButton("Option B", callback_data="opt_b")],
        [InlineKeyboardButton("Cancel", callback_data="cancel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        "<b>Important Announcement</b>\n\n"
        "<i>This is a sample post with inline buttons.</i>\n\n"
        "Please select an option below:"
    )
    await update.message.reply_html(text, reply_markup=reply_markup)


# In-memory auth code store (shared with server.py via import)
auth_codes: dict[str, str] = {}  # user_id -> code

async def auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    code = str(secrets.randbelow(900000) + 100000)
    auth_codes[str(user.id)] = code
    await update.message.reply_text(
        f"Your verification code: <code>{code}</code>\n\n"
        f"Enter this code in the web app to log in.\n\n"
        f"Code expires in 5 minutes.",
        parse_mode="HTML",
    )
    import asyncio
    asyncio.get_event_loop().call_later(300, lambda: auth_codes.pop(str(user.id), None))


async def send_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /send <json_file_path> or /send <json_string>")
        return
    input_str = " ".join(args)
    if os.path.isfile(input_str):
        with open(input_str, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        try:
            data = json.loads(input_str)
        except json.JSONDecodeError:
            await update.message.reply_text("Invalid JSON. Provide a file path or a valid JSON string.")
            return

    text = data.get("text", "")
    parse_mode = data.get("parse_mode", "HTML")
    keyboard = data.get("reply_markup", {})
    reply_markup = build_markup(keyboard)
    media = data.get("media")

    if media:
        media_bytes = base64.b64decode(media.split(",", 1)[1] if "," in media else media)
        await update.message.reply_photo(
            photo=media_bytes,
            caption=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )
    else:
        await update.message.reply_html(text, reply_markup=reply_markup)


def build_markup(keyboard_data: dict) -> InlineKeyboardMarkup | None:
    rows = keyboard_data.get("inline_keyboard", [])
    if not rows:
        return None
    keyboard = []
    for row in rows:
        buttons = []
        for btn in row:
            text = btn.get("text", "")
            if "url" in btn:
                buttons.append(InlineKeyboardButton(text, url=btn["url"]))
            elif "callback_data" in btn:
                buttons.append(InlineKeyboardButton(text, callback_data=btn["callback_data"]))
            elif "switch_inline_query" in btn:
                buttons.append(InlineKeyboardButton(text, switch_inline_query=btn["switch_inline_query"]))
        if buttons:
            keyboard.append(buttons)
    return InlineKeyboardMarkup(keyboard) if keyboard else None


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data
    responses = {
        "about": "I'm a simple Telegram bot with inline button support.",
        "help": "Commands:\n/start - Show menu\n/post - Send a post with buttons",
        "opt_a": "You selected <b>Option A</b>.",
        "opt_b": "You selected <b>Option B</b>.",
        "cancel": "Action cancelled.",
    }

    response = responses.get(data, "Unknown option.")
    if data in ("opt_a", "opt_b", "cancel"):
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_html(response)
    elif data in ("about", "help"):
        await query.message.reply_html(response)


async def send_from_file(data: dict) -> None:
    app = Application.builder().token(BOT_TOKEN).build()
    await app.initialize()
    chat_id = data.get("chat_id") or CHAT_ID
    if not chat_id:
        print("CHAT_ID not set. Set it in .env or include 'chat_id' in the JSON.")
        return

    text = data.get("text", "")
    parse_mode = data.get("parse_mode", "HTML")
    keyboard = data.get("reply_markup", {})
    reply_markup = build_markup(keyboard)
    media = data.get("media")

    if media:
        media_bytes = base64.b64decode(media.split(",", 1)[1] if "," in media else media)
        await app.bot.send_photo(
            chat_id=chat_id, photo=media_bytes,
            caption=text, parse_mode=parse_mode, reply_markup=reply_markup,
        )
    else:
        await app.bot.send_message(
            chat_id=chat_id, text=text,
            parse_mode=parse_mode, reply_markup=reply_markup,
        )
    print("Post sent successfully!")
    await app.shutdown()


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--post":
        if len(sys.argv) < 3:
            print("Usage: python bot.py --post <json_file>")
            return
        with open(sys.argv[2], "r", encoding="utf-8") as f:
            data = json.load(f)
        import asyncio
        asyncio.run(send_from_file(data))
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("auth", auth))
    app.add_handler(CommandHandler("post", post))
    app.add_handler(CommandHandler("send", send_post))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
