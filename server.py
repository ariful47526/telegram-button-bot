import os, pathlib
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set in .env file")

bot_chats: dict[int, dict] = {}

async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.my_chat_member:
        chat = update.my_chat_member.chat
        bot_chats[chat.id] = {"id": chat.id, "title": chat.title or chat.effective_name or f"Chat {chat.id}", "type": chat.type}
        logger.info(f"Bot added to chat: {chat.title or chat.id} ({chat.type})")

async def list_chats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not bot_chats:
        await update.message.reply_text("No chats found. Add me to a group or channel first.")
        return
    lines = ["<b>Bot is in these chats:</b>\n"]
    for cid, c in bot_chats.items():
        lines.append(f"• {c['title']} (<code>{cid}</code>) - {c['type']}")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")

# ---- FastAPI ----

@asynccontextmanager
async def lifespan(app: FastAPI):
    bot_task = asyncio.create_task(run_bot())
    yield
    bot_task.cancel()
    try: await bot_task
    except: pass

app = FastAPI(title="TG Post Bot API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

SCRIPT_DIR = pathlib.Path(__file__).parent

@app.get("/")
async def root():
    return HTMLResponse((SCRIPT_DIR / "index.html").read_text(encoding="utf-8"))

async def run_bot():
    app_bot = Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("chats", list_chats_cmd))
    app_bot.add_handler(MessageHandler(filters.StatusUpdate.MY_CHAT_MEMBER, track_chats))
    await app_bot.initialize()
    await app_bot.start()
    logger.info("Bot started polling")
    await app_bot.updater.start_polling()
    while True:
        await asyncio.sleep(3600)

class SendRequest(BaseModel):
    chat_id: str
    text: str
    parse_mode: str = "HTML"
    reply_markup: dict | None = None
    media: str | None = None

@app.get("/api/chats")
async def get_chats():
    return {"ok": True, "chats": list(bot_chats.values())}

@app.post("/api/send")
async def send_post(req: SendRequest):
    try:
        app_bot = Application.builder().token(BOT_TOKEN).build()
        await app_bot.initialize()
        chat_id = int(req.chat_id) if req.chat_id.lstrip("-").isdigit() else req.chat_id
        keyboard = None
        if req.reply_markup and req.reply_markup.get("inline_keyboard"):
            k_rows = []
            for row in req.reply_markup["inline_keyboard"]:
                btns = []
                for b in row:
                    if "url" in b: btns.append(InlineKeyboardButton(b["text"], url=b["url"]))
                    elif "callback_data" in b: btns.append(InlineKeyboardButton(b["text"], callback_data=b["callback_data"]))
                    elif "switch_inline_query" in b: btns.append(InlineKeyboardButton(b["text"], switch_inline_query=b["switch_inline_query"]))
                if btns: k_rows.append(btns)
            if k_rows: keyboard = InlineKeyboardMarkup(k_rows)

        if req.media:
            import base64
            media_bytes = base64.b64decode(req.media.split(",", 1)[1] if "," in req.media else req.media)
            msg = await app_bot.bot.send_photo(chat_id=chat_id, photo=media_bytes, caption=req.text, parse_mode=req.parse_mode, reply_markup=keyboard)
        else:
            msg = await app_bot.bot.send_message(chat_id=chat_id, text=req.text, parse_mode=req.parse_mode, reply_markup=keyboard)
        await app_bot.shutdown()
        return {"ok": True, "message_id": msg.message_id}
    except Exception as e:
        raise HTTPException(500, str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
