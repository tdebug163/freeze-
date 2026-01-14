import os
import telebot
from telebot import types
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded
import psycopg2
from flask import Flask
from threading import Thread
import asyncio

# --- الإعدادات ---
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
API_ID = int(os.getenv("API_ID", "26569722"))
API_HASH = os.getenv("API_HASH", "90a9314c99544976451664d4c1f964fc")

bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)
user_data = {}

# إنشاء دورة (Loop) واحدة ثابتة لكل العمليات
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

@server.route("/")
def home(): return "Mikey Command Center is Alive!", 200

def save_to_db(phone, session_str):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("INSERT INTO accounts (phone, session_string) VALUES (%s, %s) ON CONFLICT (phone) DO UPDATE SET session_string = EXCLUDED.session_string", (phone, session_str))
    conn.commit()
    cur.close()
    conn.close()

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ إضافة حساب للجيش", callback_data="add"))
    bot.send_message(message.chat.id, "🚬 **مقر مايكي - جاهز للعمل**\n\nاضغط الزر وجرب الحين:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "add")
def ask_phone(call):
    msg = bot.send_message(call.message.chat.id, "📱 أرسل الرقم (مثال: +254...):")
    bot.register_next_step_handler(msg, connect_pyro)

def connect_pyro(message):
    phone = message.text.strip()
    chat_id = message.chat.id
    bot.send_message(chat_id, "⏳ جاري طلب الكود...")

    async def work():
        client = Client(f"session_{chat_id}", api_id=API_ID, api_hash=API_HASH, in_memory=True)
        try:
            await client.connect()
            code_info = await client.send_code(phone)
            user_data[chat_id] = {'client': client, 'phone': phone, 'hash': code_info.phone_code_hash}
            msg = bot.send_message(chat_id, "📩 الكود وصلك؟ أرسله الحين:")
            bot.register_next_step_handler(msg, process_code)
        except Exception as e:
            bot.send_message(chat_id, f"❌ خطأ: {str(e)}")

    loop.create_task(work())

def process_code(message):
    chat_id = message.chat.id
    code = message.text.strip()
    if chat_id not in user_data: return
    data = user_data[chat_id]

    async def sign_in():
        try:
            await data['client'].sign_in(data['phone'], data['hash'], code)
            session_str = await data['client'].export_session_string()
            save_to_db(data['phone'], session_str)
            bot.send_message(chat_id, f"✅ كفو! الحساب {data['phone']} صار في الجيب.")
        except SessionPasswordNeeded:
            msg = bot.send_message(chat_id, "🔐 الحساب محمي بكلمة سر، هاتها:")
            bot.register_next_step_handler(msg, process_password)
        except Exception as e:
            bot.send_message(chat_id, f"❌ خطأ: {str(e)}")

    loop.create_task(sign_in())

def process_password(message):
    chat_id = message.chat.id
    password = message.text.strip()
    data = user_data[chat_id]

    async def check_pass():
        try:
            await data['client'].check_password(password)
            session_str = await data['client'].export_session_string()
            save_to_db(data['phone'], session_str)
            bot.send_message(chat_id, "✅ تم بنجاح مع الباسورد!")
        except Exception as e:
            bot.send_message(chat_id, f"❌ خطأ: {str(e)}")

    loop.create_task(check_pass())

if __name__ == "__main__":
    Thread(target=lambda: server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))).start()
    # تشغيل الـ Loop في الخلفية
    Thread(target=loop.run_forever).start()
    bot.infinity_polling()
