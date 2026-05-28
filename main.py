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
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pyrogram.errors import FloodWait, AuthKeyUnregistered, SessionRevoked
from pyrogram.enums import ChatType
from telethon.sessions import StringSession
from telethon.crypto import AuthKey

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

# --- المتغيرات ---
API_ID = 28797361  
API_HASH = "771041b32e83ab232e066b7adeee700b"  
BOT_TOKEN = "8971197244:AAEBSUdjMuKWs7U1qHfU042gGFYhbkn5HVU"  # ⚠️ لا تنسَ تغييره بالتوكن الجديد من BotFather

app = Client("manager_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

code_requests = {}

# --- دوال الأعلام وجلب النجوم ---
COUNTRY_FLAGS = {
    "+964": ("🇮🇶", "العراق"), "+966": ("🇸🇦", "السعودية"), "+971": ("🇦🇪", "الإمارات"),
    "+965": ("🇰🇼", "الكويت"), "+974": ("🇶🇦", "قطر"),
    "+973": ("🇧🇭", "البحرين"), "+968": ("🇴🇲", "عُمان"), "+20": ("🇪🇬", "مصر"),
    "+212": ("🇲🇦", "المغرب"), "+213": ("🇩🇿", "الجزائر"), "+216": ("🇹🇳", "تونس"),
    "+218": ("🇱🇾", "ليبيا"), "+249": ("🇸🇩", "السودان"), "+967": ("🇾🇪", "اليمن"),
    "+962": ("🇯🇴", "الأردن"), "+961": ("🇱🇧", "لبنان"), "+963": ("🇸🇾", "سوريا"),
    "+98": ("🇮🇷", "إيران"), "+90": ("🇹🇷", "تركيا"), "+7": ("🇷🇺", "روسيا"),
    "+1": ("🇺🇸", "أمريكا"), "+44": ("🇬🇧", "بريطانيا"), "+91": ("🇮🇳", "الهند"),
    "+92": ("🇵🇰", "باكستان"), "+93": ("🇦🇫", "أفغانستان"), "+88": ("🇧🇩", "بنجلاديش"),
    "+94": ("🇱🇰", "سريلانكا"), "+95": ("🇲🇲", "ميانمار"), "+960": ("🇲🇻", "المالديف"),
    "+62": ("🇮🇩", "إندونيسيا"), "+63": ("🇵🇭", "الفلبين"), "+66": ("🇹🇭", "تايلاند"),
    "+84": ("🇻🇳", "فيتنام"), "+86": ("🇨🇳", "الصين"), "+81": ("🇯🇵", "اليابان"),
    "+82": ("🇰🇷", "كوريا"), "+5": ("🇦🇷", "الأرجنتين"), "+55": ("🇧🇷", "البرازيل"),
    "+58": ("🇻🇪", "فنزويلا"), "+234": ("🇳🇬", "نيجيريا"), "+254": ("🇰🇪", "كينيا"),
}

def get_country_info(phone):
    if not phone: return "🏳️", "غير معروف"
    for prefix, (flag, name) in COUNTRY_FLAGS.items():
        if phone.startswith(prefix):
            return flag, name
    return "🏳️", "غير معروف"

async def get_stars_balance(client):
    try:
        from pyrogram.raw.functions.payments import GetStarsStatus
        from pyrogram.raw.types import InputPeerSelf
        res = await client.invoke(GetStarsStatus(peer=InputPeerSelf()))
        return getattr(res, "balance", 0)
    except:
        try:
            from pyrogram.raw.functions.payments import GetStarsBalance
            from pyrogram.raw.types import InputPeerSelf
            res = await client.invoke(GetStarsBalance(peer=InputPeerSelf()))
            return getattr(res, "amount", 0)
        except:
            return 0

# --- واجهة الأزرار ---
def home_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✉️ جلب الكود", callback_data="req_code"),
         InlineKeyboardButton("🕵️ كشف الحسابات", callback_data="reveal_accounts")],
        [InlineKeyboardButton("💀 إنهاء الجلسات الأخرى", callback_data="menu_terminate"),
         InlineKeyboardButton("🧹 التنظيف الشامل", callback_data="menu_clean")],
        [InlineKeyboardButton("🚪 تسجيل الخروج", callback_data="menu_logout")],
        [InlineKeyboardButton("📂 إضافة حساب", callback_data="add_account")]
    ])

def accounts_action_keyboard(owner_id, action):
    accounts = get_all_accounts(owner_id)
    buttons = [[InlineKeyboardButton("🌍 الجميع", callback_data=f"act_{action}_all")]]
    for acc_id, phone, name, stars in accounts:
        buttons.append([InlineKeyboardButton(f"{phone} | {name} | ⭐ {stars}", callback_data=f"act_{action}_{acc_id}")])
    buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_home")])
    return InlineKeyboardMarkup(buttons)

# --- أوامر البوت ---
@app.on_message(filters.command("start") & filters.private)
async def start(client, message: Message):
    await message.reply_text(
        "**🤖 أهلاً بك في بوت إدارة الحسابات الاحترافي!**\n\n"
        "يدعم إضافة الحسابات عبر (ZIP - TDATA - Session).\n"
        "يمكنك إرسال عدة ملفات دفعة واحدة وسيتم إضافتها جميعاً.\n\n"
        "**حساباتك في أمان تام.**",
        reply_markup=home_keyboard()
    )

@app.on_callback_query(filters.regex(r"^add_account$"))
async def add_account_prompt(client, callback: CallbackQuery):
    await callback.message.edit_text(
        "**📤 إرسال النسخة المُلصقة!**\n\n"
        "أرسل ملفات الـ ZIP أو الـ Session الآن:\n"
        "🔹 إذا كان TDATA: المجلد `D877F783D5D3EF8C` والملفات `key_datas` يجب أن تكون داخل الـ ZIP.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_home")]])
    )

@app.on_callback_query(filters.regex(r"^back_home$"))
async def back_home(client, callback: CallbackQuery):
    await callback.message.edit_text("**🤖 القائمة الرئيسية:**", reply_markup=home_keyboard())

@app.on_callback_query(filters.regex(r"^reveal_accounts$"))
async def reveal_accounts(client, callback: CallbackQuery):
    accounts = get_all_accounts(callback.from_user.id)
    if not accounts:
        await callback.answer("لا توجد حسابات!", show_alert=True)
        return
    
    text = "**🕵️ الحسابات المسجلة لديك:**\n\n"
    for acc_id, phone, name, stars in accounts:
        text += f"👤 الاسم: `{name}` | 📱 الرقم: `{phone}` | ⭐ النجوم: `{stars}`\n"
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back_home")]]))

# --- نظام جلب الكود ---
@app.on_callback_query(filters.regex(r"^req_code$"))
async def request_code(client, callback: CallbackQuery):
    code_requests[callback.from_user.id] = True
    await callback.message.reply_text(
        "**📥 أرسل رقم الحساب المراد جلب الكود له الآن:**\n\n*(مثال: +9647700000000)*"
    )

@app.on_message(filters.text & filters.private)
async def process_code_request(client, message: Message):
    user_id = message.from_user.id
    if user_id in code_requests and code_requests[user_id]:
        del code_requests[user_id]
        target_phone = message.text.strip().replace(" ", "")
        
        accounts = get_all_accounts(user_id)
        target_acc = None
        for acc in accounts:
            if acc[1] == target_phone:  
                target_acc = get_account(acc[0])
                break
        
        if not target_acc:
            await message.reply_text("❌ هذا الرقم غير موجود في حساباتك المضافة.", reply_markup=home_keyboard())
            return

        status_msg = await message.reply_text("⏳ جاري البحث عن الكود...")
        try:
            pyro_session = target_acc[5]
            exec_client = Client(f"code_{user_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
            await exec_client.connect()
            
            code_found = None
            async for msg in exec_client.get_chat_history(777000, limit=10):
                if msg.text and ("Login code" in msg.text or "كود الدخول" in msg.text or "تسجيل الدخول" in msg.text):
                    match = re.search(r'\b(\d{5})\b', msg.text)
                    if match:
                        code_found = match.group(1)
                        break
            
            await exec_client.disconnect()
            
            if code_found:
                flag, country = get_country_info(target_phone)
                await status_msg.edit_text(
                    f"🌎 **Country:** {flag} {country}\n"
                    f"📱 **Service:** 📱\n"
                    f"🔢 **Number:** `{target_phone}`\n"
                    f"🔑 **OTP:** `{code_found}`",
                )
            else:
                await status_msg.edit_text("❌ لم أجد أي كود حالي في رسائل هذا الحساب.", reply_markup=home_keyboard())
                
        except (AuthKeyUnregistered, SessionRevoked):
            await status_msg.edit_text("❌ الجلسة باطلة أو محظورة.", reply_markup=home_keyboard())
        except Exception as e:
            await status_msg.edit_text(f"❌ خطأ: {type(e).__name__}", reply_markup=home_keyboard())

# --- قوائم الإجراءات (إنهاء جلسات / تنظيف / خروج) ---
@app.on_callback_query(filters.regex(r"^menu_(terminate|clean|logout)$"))
async def action_menus(client, callback: CallbackQuery):
    action = callback.data.split("_")[1]
    
    titles = {
        "terminate": "💀 **إنهاء الجلسات الأخرى:**\nاختر حساباً لحذف جميع جلساته (ماعدا البوت):",
        "clean": "🧹 **التنظيف الشامل:**\nاختر حساباً لحذف جميع المحادثات والقنوات منه:",
        "logout": "🚪 **تسجيل الخروج:**\nاختر حساباً لتسجيل خروج البوت منه وحذفه:"
    }
    
    await callback.message.edit_text(titles[action], reply_markup=accounts_action_keyboard(callback.from_user.id, action))

# --- محرك استخراج الجلسات ---
def get_dc_ip(dc_id):
    ips = {1: "149.154.175.53", 2: "149.154.167.51", 3: "149.154.175.100", 4: "149.154.167.90", 5: "149.154.171.5"}
    return ips.get(dc_id, "149.154.167.51")

def generate_sessions(api_id, dc_id, auth_key_bytes):
    pyro_packed = struct.pack(">B?256sQ", dc_id, False, auth_key_bytes, 9999)
    pyro_session = base64.urlsafe_b64encode(pyro_packed).decode("utf-8").rstrip("=")
    
    session = StringSession()
    session._dc_id = dc_id
    session._server_address = get_dc_ip(dc_id)
    session.port = 443
    session._auth_key = AuthKey(auth_key_bytes)
    tl_session = session.save()
    return pyro_session, tl_session

def extract_auth_pure(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            db_path = os.path.join(root, file)
            try:
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                c.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in c.fetchall()]
                
                if 'dc' in tables:
                    c.execute("SELECT dc_id, auth_key FROM dc WHERE length(auth_key) = 256 LIMIT 1")
                    row = c.fetchone()
                    if row and row[0] and row[1]: conn.close(); return row[0], row[1]
                
                if 'sessions' in tables:
                    c.execute("SELECT dc_id, auth_key FROM sessions WHERE length(auth_key) = 256 LIMIT 1")
                    row = c.fetchone()
                    if row and row[0] and row[1]: conn.close(); return row[0], row[1]
                conn.close()
            except: continue
    raise Exception("لم أجد مفتاح المصادقة في الملفات.")

def extract_string_from_txt(dir_path):
    for root, _, files in os.walk(dir_path):
        for file in files:
            if file.endswith(".txt"):
                path = os.path.join(root, file)
                with open(path, 'r') as f: content = f.read().strip()
                try:
                    data = base64.urlsafe_b64decode(content + "=" * (-len(content) % 4))
                    if len(data) == 261: return struct.unpack(">B", data[0:1])[0], data[5:261]
                except: pass
                try:
                    session = StringSession(content)
                    if session._dc_id and session._auth_key: return session._dc_id, session._auth_key.key
                except: pass
    return None, None

async def verify_and_save(owner_id, api_id, dc_id, auth_key, stype):
    pyro_session, tl_session = generate_sessions(api_id, dc_id, auth_key)
    client = Client(f"verify_{owner_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
    await client.connect()
    me = await client.get_me()
    phone = me.phone_number if me.phone_number else "Unknown"
    user_id = me.id
    first_name = me.first_name if me.first_name else "User"
    
    stars = await get_stars_balance(client)
    
    await client.disconnect()
    save_account(owner_id, phone, user_id, first_name, pyro_session, tl_session, stype, stars)
    return phone, first_name, stars

# --- استقبال الملفات (متعدد) ---
@app.on_message(filters.document & filters.private)
async def handle_files(client, message: Message):
    if not message.document.file_name.endswith((".zip", ".session", ".txt")):
        return

    status_msg = await message.reply_text("⏳ جاري المعالجة...")
    file_path = await message.download()
    extract_dir = f"tmp_{message.from_user.id}_{message.id}"
    results = []

    try:
        if message.document.file_name.endswith(".zip"):
            if os.path.exists(extract_dir): shutil.rmtree(extract_dir)
            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(file_path, 'r') as zip_ref: zip_ref.extractall(extract_dir)

            try:
                dc_id, auth_key = extract_auth_pure(extract_dir)
                phone, name, stars = await verify_and_save(message.from_user.id, API_ID, dc_id, auth_key, "TDATA/ZIP")
                results.append(f"✅ {phone} ({name}) ⭐ {stars}")
            except: pass
            
            if not results:
                dc_id, auth_key = extract_string_from_txt(extract_dir)
                if dc_id:
                    phone, name, stars = await verify_and_save(message.from_user.id, API_ID, dc_id, auth_key, "String ZIP")
                    results.append(f"✅ {phone} ({name}) ⭐ {stars}")

        elif message.document.file_name.endswith(".session"):
            try:
                dc_id, auth_key = extract_auth_pure(os.path.dirname(file_path))
                phone, name, stars = await verify_and_save(message.from_user.id, API_ID, dc_id, auth_key, "Session File")
                results.append(f"✅ {phone} ({name}) ⭐ {stars}")
            except: pass

        elif message.document.file_name.endswith(".txt"):
            with open(file_path, 'r') as f: content = f.read().strip()
            dc_id, auth_key = None, None
            try:
                data = base64.urlsafe_b64decode(content + "=" * (-len(content) % 4))
                if len(data) == 261: dc_id, auth_key = struct.unpack(">B", data[0:1])[0], data[5:261]
            except: pass
            if not dc_id:
                try:
                    session = StringSession(content)
                    if session._dc_id and session._auth_key: dc_id, auth_key = session._dc_id, session._auth_key.key
                except: pass
            
            if dc_id:
                phone, name, stars = await verify_and_save(message.from_user.id, API_ID, dc_id, auth_key, "TXT Session")
                results.append(f"✅ {phone} ({name}) ⭐ {stars}")

        if results:
            await status_msg.edit_text("**تمت الإضافة بنجاح:**\n\n" + "\n".join(results), reply_markup=home_keyboard())
        else:
            await status_msg.edit_text("❌ فشل استخراج بيانات صالحة.", reply_markup=home_keyboard())
    except Exception as e:
        await status_msg.edit_text(f"❌ خطأ: {type(e).__name__}", reply_markup=home_keyboard())
    finally:
        try:
            if os.path.exists(file_path): os.remove(file_path)
            if os.path.exists(extract_dir): shutil.rmtree(extract_dir)
        except: pass

# --- تنفيذ الأوامر الجماعية والفردية ---
@app.on_callback_query(filters.regex(r"^act_(terminate|clean|logout)_(all|\d+)$"))
async def execute_action(client, callback: CallbackQuery):
    data = callback.data.split("_")
    action = data[1]
    target = data[2]
    
    await callback.answer("⏳ جاري التنفيذ...")
    
    if target == "all":
        accounts = get_all_accounts(callback.from_user.id)
        for acc in accounts:
            await perform_action(action, acc[0], callback.from_user.id)
        await callback.message.edit_text(f"✅ **تم تنفيذ ({action}) على جميع الحسابات.**", reply_markup=home_keyboard())
    else:
        acc_id = int(target)
        msg = await perform_action(action, acc_id, callback.from_user.id)
        await callback.message.edit_text(msg, reply_markup=home_keyboard())

async def perform_action(action, acc_id, owner_id):
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
            
    except Exception as e:
        result_msg = f"❌ خطأ في `{phone}`: {type(e).__name__}"
    finally:
        if exec_client.is_connected: await exec_client.disconnect()

    return result_msg

# --- محرك التشغيل الذكي ---
async def main():
    session_file = "manager_bot.session"
    try:
        await app.start()
        print("Bot is running securely on Python 3.13+ [2026 Engine]...")
        await idle()
    except (SessionRevoked, AuthKeyUnregistered):
        print("Self-Healing: Session File Corrupted! Restarting...")
        if os.path.exists(session_file): os.remove(session_file)
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        print(f"Fatal Error: {type(e).__name__} - {e}")
    try:
        await app.stop()
    except: pass

if __name__ == "__main__":
    asyncio.run(main())