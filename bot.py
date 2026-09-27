import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import json
from pathlib import Path
import os
import time

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
        await update.message.reply_text("❌ সঠিক Facebook লিঙ্ক দাও")
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

def process_facebook_report(url):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        driver.get("https://www.facebook.com/login")
        time.sleep(3)
        
        email_field = driver.find_element(By.ID, "email")
        password_field = driver.find_element(By.ID, "pass")
        
        email_field.send_keys(FACEBOOK_EMAIL)
        password_field.send_keys(FACEBOOK_PASSWORD)
        
        login_btn = driver.find_element(By.NAME, "login")
        login_btn.click()
        time.sleep(5)
        
        driver.get(url)
        time.sleep(3)
        
        try:
            three_dots = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//i[@class='x1b0d690 x1ey2e0e']"))
            )
            three_dots.click()
            time.sleep(2)
        except:
            driver.quit()
            return False
        
        try:
            report_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Report')]"))
            )
            report_option.click()
            time.sleep(2)
        except:
            driver.quit()
            return False
        
        try:
            harassment_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Harassment')]"))
            )
            harassment_btn.click()
            time.sleep(2)
        except:
            driver.quit()
            return False
        
        try:
            submit_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Submit')]"))
            )
            submit_btn.click()
            time.sleep(2)
            driver.quit()
            return True
        except:
            driver.quit()
            return False
        
    except Exception as e:
        return False

async def process_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not FACEBOOK_EMAIL or not FACEBOOK_PASSWORD:
        await update.message.reply_text("❌ Facebook লজিন Railway এ দেওয়া নেই")
        return
    
    data = load_reports()
    if not data["pending"]:
        await update.message.reply_text("📭 কোন রিপোর্ট নেই")
        return
    
    await update.message.reply_text(f"⏳ {len(data['pending'])}টি রিপোর্ট পাঠাচ্ছি...")
    
    success = 0
    failed = 0
    
    for report in data["pending"]:
        result = process_facebook_report(report["url"])
        if result:
            success += 1
            report["status"] = "completed"
        else:
            failed += 1
            report["status"] = "failed"
        time.sleep(3)
    
    data["completed"] = [r for r in data["pending"] if r["status"] == "completed"]
    data["pending"] = [r for r in data["pending"] if r["status"] == "failed"]
    save_reports(data)
    
    await update.message.reply_text(f"✅ সম্পন্ন: {success}\n❌ ব্যর্থ: {failed}")

async def clear_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = {"pending": [], "completed": []}
    save_reports(data)
    await update.message.reply_text("🗑️ সব মুছে ফেলা হয়েছে")

async def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    if not TOKEN:
        return
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_report))
    app.add_handler(CommandHandler("list", list_reports))
    app.add_handler(CommandHandler("process", process_reports))
    app.add_handler(CommandHandler("clear", clear_all))
    
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
