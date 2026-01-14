import os
import telebot
from telebot import types
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PasswordHashInvalidError
import psycopg2
from flask import Flask
from threading import Thread
import asyncio

# --- الإعدادات ---
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
API_ID = 26569722 
API_HASH = "90a9314c99544976451664d4c1f964fc"

bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)
user_states = {} # لحفظ حالة المستخدم وجلسته

# --- سيرفر الويب ---
@server.route("/")
def home(): return "Mikey is Alive!", 200

def run_web(): server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# --- قاعدة البيانات ---
def save_to_db(phone, session_str):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("INSERT INTO accounts (phone, session_string) VALUES (%s, %s) ON CONFLICT (phone) DO UPDATE SET session_string = EXCLUDED.session_string", (phone, session_str))
    conn.commit()
    cur.close()
    conn.close()

# --- واجهة البوت ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ إضافة حساب", callback_data="add"))
    bot.send_message(message.chat.id, "🔥 **مقر مايكي للعمليات** 🔥\n\nاضغط الزر لإضافة حساب للجيش:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "add")
def ask_phone(call):
    msg = bot.send_message(call.message.chat.id, "📱 أرسل الرقم مع المفتاح الدولي (مثال: +254...):")
    bot.register_next_step_handler(msg, connect_telethon)

# --- منطق Telethon ---
def connect_telethon(message):
    phone = message.text.strip()
    chat_id = message.chat.id
    bot.send_message(chat_id, f"⏳ جاري بدء الاتصال بـ {phone}...")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = TelegramClient(StringSession(), API_ID, API_HASH, loop=loop)
    
    try:
        loop.run_until_complete(client.connect())
        send_code = loop.run_until_complete(client.send_code_request(phone))
        user_states[chat_id] = {'client': client, 'phone': phone, 'hash': send_code.phone_code_hash, 'loop': loop}
        
        msg = bot.send_message(chat_id, "📩 أرسل كود التحقق الآن:")
        bot.register_next_step_handler(msg, process_code)
    except Exception as e:
        bot.send_message(chat_id, f"❌ خطأ: {e}")

def process_code(message):
    chat_id = message.chat.id
    code = message.text.strip()
    if chat_id not in user_states: return

    state = user_states[chat_id]
    client = state['client']
    loop = state['loop']

    try:
        loop.run_until_complete(client.sign_in(state['phone'], code, phone_code_hash=state['hash']))
        finish_login(message, chat_id)
    except SessionPasswordNeededError:
        msg = bot.send_message(chat_id, "🔐 الحساب محمي بكلمة سر، هاتها:")
        bot.register_next_step_handler(msg, process_password)
    except PhoneCodeInvalidError:
        msg = bot.send_message(chat_id, "❌ الكود غلط، أرسله مرة ثانية:")
        bot.register_next_step_handler(msg, process_code)
    except Exception as e:
        bot.send_message(chat_id, f"❌ خطأ: {e}")

def process_password(message):
    chat_id = message.chat.id
    password = message.text.strip()
    state = user_states[chat_id]
    client = state['client']
    loop = state['loop']

    try:
        loop.run_until_complete(client.sign_in(password=password))
        finish_login(message, chat_id)
    except PasswordHashInvalidError:
        msg = bot.send_message(chat_id, "❌ كلمة السر غلط، أرسلها صح:")
        bot.register_next_step_handler(msg, process_password)
    except Exception as e:
        bot.send_message(chat_id, f"❌ خطأ: {e}")

def finish_login(message, chat_id):
    state = user_states[chat_id]
    session_str = state['client'].session.save()
    save_to_db(state['phone'], session_str)
    bot.send_message(chat_id, f"✅ تم بنجاح! الحساب {state['phone']} صار في جيب مايكي.")
    del user_states[chat_id]

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.infinity_polling()
