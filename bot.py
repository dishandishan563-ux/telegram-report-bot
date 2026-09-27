import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import json
from pathlib import Path
import os
import asyncio

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

CONFIG_FILE = "reports.json"
FACEBOOK_EMAIL = os.getenv("FB_EMAIL", "")
FACEBOOK_PASSWORD = os.getenv("FB_PASSWORD", "")

def load_reports():
    if Path(CONFIG_FILE).exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"pending": [], "completed": []}

def save_reports(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚨 ফেসবুক রিপোর্ট বট\n\n"
        "/add <লিঙ্ক> - রিপোর্ট যোগ করো\n"
        "/list - সব রিপোর্ট দেখো\n"
        "/process - রিপোর্ট পাঠাও\n"
        "/clear - সব মুছো"
    )

async def add_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("ব্যবহার: /add https://facebook.com/...")
        return
    
    url = context.args[0]
    
    if "facebook.com" not in url and "fb.com" not in url:
        await update.message.reply_text("❌ Facebook লিঙ্ক দাও")
        return
    
    data = load_reports()
    data["pending"].append({"url": url, "status": "waiting"})
    save_reports(data)
    
    await update.message.reply_text(f"✅ যোগ করা হয়েছে:\n{url}")

async def list_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_reports()
    if not data["pending"]:
        await update.message.reply_text("📭 কোন রিপোর্ট নেই")
        return
    
    msg = "📋 পেন্ডিং রিপোর্ট:\n\n"
    for i, r in enumerate(data["pending"], 1):
        msg += f"{i}. {r['url']}\n   স্ট্যাটাস: {r['status']}\n\n"
    await update.message.reply_text(msg)

async def process_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_reports()
    if not data["pending"]:
        await update.message.reply_text("📭 কোন রিপোর্ট নেই")
        return
    
    await update.message.reply_text(f"⏳ {len(data['pending'])}টি রিপোর্ট সংরক্ষিত আছে")
    await update.message.reply_text("⚠️ নোট: Selenium এখন Railway এ কাজ করছে না। ম্যানুয়ালি Facebook এ গিয়ে রিপোর্ট করতে হবে।")

async def clear_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = {"pending": [], "completed": []}
    save_reports(data)
    await update.message.reply_text("🗑️ সব মুছে ফেলা হয়েছে")

async def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    if not TOKEN:
        logger.error("TELEGRAM_TOKEN not found!")
        return
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_report))
    app.add_handler(CommandHandler("list", list_reports))
    app.add_handler(CommandHandler("process", process_reports))
    app.add_handler(CommandHandler("clear", clear_all))
    
    await app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    asyncio.run(main())
