from flask import Flask
from telegram import (
    Bot, Update,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
import time, threading
from datetime import datetime

BOT_TOKEN = "8556881847:AAEzfOo1LKHa2EroZV9FXh1rFMosqTBQ0lc"
OWNER_ID = 6752691306
PING_TIMEOUT = 120

bot = Bot(BOT_TOKEN)
app = Flask(__name__)

subscribers = set()
last_ping = 0
light_status = "OFF"

def keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 Підписатись", callback_data="sub")],
        [InlineKeyboardButton("🔴 Відписатись", callback_data="unsub")],
        [InlineKeyboardButton("ℹ️ Статус", callback_data="status")]
    ])

@app.route("/ping", methods=["POST"])
def ping():
    global last_ping
    last_ping = time.time()
    return {"ok": True}

def broadcast(text):
    for uid in list(subscribers):
        try:
            bot.send_message(uid, text)
        except:
            pass

def monitor_light():
    global light_status
    while True:
        now = time.time()
        if light_status == "ON" and now - last_ping > PING_TIMEOUT:
            light_status = "OFF"
            broadcast("❌ Світло ВИМКНУЛИ")
        if light_status == "OFF" and now - last_ping <= PING_TIMEOUT:
            light_status = "ON"
            broadcast("✅ Світло УВІМКНУЛИ")
        time.sleep(10)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Вітаю! Отримуй сповіщення про світло.",
        reply_markup=keyboard()
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "sub":
        subscribers.add(uid)
        await q.message.reply_text("🟢 Підписка активна")
    elif q.data == "unsub":
        subscribers.discard(uid)
        await q.message.reply_text("🔴 Ви відписались")
    elif q.data == "status":
        await q.message.reply_text(
            "💡 Світло УВІМКНЕНО" if light_status == "ON" else "🌑 Світло ВИМКНЕНО"
        )

async def send_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    now = datetime.now().strftime("%d.%m %H:%M")
    broadcast(f"⚡ ОФІЦІЙНИЙ ГРАФІК\n\n{update.message.text}\n\n🕒 {now}")

def start_bot():
    tg = ApplicationBuilder().token(BOT_TOKEN).build()
    tg.add_handler(CommandHandler("start", start))
    tg.add_handler(CallbackQueryHandler(buttons))
    tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_schedule))
    tg.run_polling()

if __name__ == "__main__":
    threading.Thread(target=monitor_light, daemon=True).start()
    threading.Thread(target=start_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
