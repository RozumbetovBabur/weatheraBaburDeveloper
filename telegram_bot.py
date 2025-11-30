import os
import re
import json
import time
import requests
import unicodedata
from urllib.parse import quote_plus
from pathlib import Path
from difflib import get_close_matches
from dotenv import load_dotenv

# Load environment
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_TOKEN:
    raise SystemExit("TELEGRAM_BOT_TOKEN .env de anıqlanbaǵan")

OPENWEATHER_KEY = os.getenv('OPENWEATHER_API_KEY')
if not OPENWEATHER_KEY:
    raise SystemExit("OPENWEATHER_API_KEY .env de anıqlanbaǵan")

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
USER_CITIES_FILE = Path("user_cities.json")
REGIONS_FILE = Path("regions_lot.json")

# Normalization helpers
_NON_ALNUM_RE = re.compile(r'[^0-9a-zA-Z\u0400-\u04FF\u0600-\u06FF\s]', re.UNICODE)

REPLACEMENTS = {
    "’": "'", "ʼ": "'", "‘": "'", "´": "'", "`": "'",
    "o'": "o", "oʻ": "o", "o`": "o", "gʻ": "g", "g'": "g",
    # remove words that often appended
    " shahar": "", " shaxri": "", " shaxr": "", " tumani": "", " tuman": ""
}

# Aliases: normalized key -> canonical name (as in your regions JSON)
ALIASES = {
    "no kis": "Nukus shahar",
    "no'kis": "Nukus shahar",
    "noʼkis": "Nukus shahar",
    "nokis": "Nukus shahar",
    "nukis": "Nukus shahar",
    "nokis qalasi": "Nukus shahar",
    "Nókis qalası" : "Nukus shahar",
    "nókis qalası" : "Nukus shahar",
    "Nókis Qalası" : "Nukus shahar",
    "nókis Qalası" : "Nukus shahar",
    "Nukus shahar" : "Nukus shahar",
    "Nukus shahri" : "Nukus shahar",
    "Nukus Shahar" : "Nukus shahar",
    "nukus shahar" : "Nukus shahar",
    "No'kis shahar" : "Nukus shahar",

    "nokis rayoni": "Nukus tumani",
    "nukis rayoni": "Nukus tumani",
    "noʼkis rayoni": "Nukus tumani",
    "Nukos rayoni": "Nukus tumani",
    "nukos rayoni": "Nukus tumani",
    "Nokis rayoni": "Nukus tumani",
    "Nukis rayoni": "Nukus tumani",
    "Noʼkis rayoni": "Nukus tumani",
    "Nókis rayonı" : "Nukus tumani",
    "nókis rayonı" : "Nukus tumani",
    "Nókis Rayonı" : "Nukus tumani",
    "nókis Rayonı" : "Nukus tumani",
    "Nukus tumani" : "Nukus tumani",
    "Nukus tuman" : "Nukus tumani",
    "nukus tumani" : "Nukus tumani",
    "nukus tuman" : "Nukus tumani",

    "Amudaryo": "Amudaryo",
    "Manǵıt" : "Amudaryo",
    "manǵıt" : "Amudaryo",
    "Mang'it" : "Amudaryo",
    "mang'it" : "Amudaryo",
    "Amudarya" : "Amudaryo",
    "amudaryo" : "Amudaryo",
    "Amudaryo tumani" : "Amudaryo",
    "amudaryo tumani" : "Amudaryo",
    "amudaryo Tumani" : "Amudaryo",
    "Mang'id" : "Amudaryo",
    "mang'id" : "Amudaryo",
    "Mang'id tumani" : "Amudaryo",
    "mang'it tumani" : "Amudaryo",
    "Mang'id Tumani" : "Amudaryo",
    "Amudaryo rayonı" : "Amudaryo",
    "amudaryo rayonı" : "Amudaryo",
    "Amudaryo rayoni" : "Amudaryo",
    "Amudaryo Rayoni" : "Amudaryo",
    "Amudarya rayoni" : "Amudaryo",
    "amudarya rayoni" : "Amudaryo",
    "Mang'it qalasi" : "Amudaryo",
    "mang'it qalasi" : "Amudaryo",
    "Manǵıt qalası" : "Amudaryo",
    "manǵıt qalası" : "Amudaryo",

    "Kegeyli" : "Kegeyli",
    "Kegeyli rayoni" : "Kegeyli",
    "kegeyli rayoni" : "Kegeyli",
    "Kegeyli tumani" : "Kegeyli",
    "kegeyli tumani" : "Kegeyli",
    "Kegeyli tuman" : "Kegeyli",
    "kegeyli tuman" : "Kegeyli",
    "Xalqabat" : "Kegeyli",
    "xalqabat" : "Kegeyli",
    "Xalqabat rayoni" : "Kegeyli",
    "xalqabat rayoni" : "Kegeyli",
    "Xalqabad" : "Kegeyli",
    "xalqabad" : "Kegeyli",
    "Xalqabad rayoni" : "Kegeyli",
    "xalqabad rayoni" : "Kegeyli",
    "Xalqabat rayonı" : "Kegeyli",
    "xalqabat rayonı" : "Kegeyli",
    "Xalqabat rayon" : "Kegeyli",
    "xalqabat rayon" : "Kegeyli",
    "Qalqabat" : "Kegeyli",
    "qalqabat" : "Kegeyli",
    "Xalqabat qalasi" : "Kegeyli",
    "xalqabat qalasi" : "Kegeyli",
    "Xalqabat qala" : "Kegeyli",
    "xalqabat qala" : "Kegeyli",
    "Qalqabat rayoni" : "Kegeyli",
    "qalqabat rayoni" : "Kegeyli",
    "Qalqabat rayon" : "Kegeyli",
    "qalqabat rayon" : "Kegeyli",
    "Kegeyli qalasi" : "Kegeyli",
    "kegeyli qalasi" : 'Kegeyli',
    "Kegeyli qala" : "Kegeyli",
    "kegeyli qala" : "Kegeyli",

    "Shimbay" : "Chimboy",
    "shimbay" : "Chimboy",
    "Shimbay rayoni" : "Chimboy",
    "shimbay rayoni" : "Chimboy",
    "Chimboy" : "Chimboy",
    "Chimboy tumani" : "Chimboy",
    "chimboy tumani" : "Chimboy",
    "Chimboy tuman" : "Chimboy",
    "chimboy tuman" : "Chimboy",
    "Shımbay rayonı" : "Chimboy",
    "shımbay rayonı" : "Chimboy",
    "Shımbay rayon" : "Chimboy",
    "shımbay rayon" : "Chimboy",
    "Shımbay" : "Chimboy",
    "shımbay" : "Chimboy",
    "Shimbay qalasi" : "Chimboy",
    "shimbay qalasi" : "Chimboy",
    "Shımbay qalası" : "Chimboy",
    "Shımbay qala" : "Chimboy",
    "shımbay qala" : "Chimboy",

    "Qorao'zek" : "Qorao'zek",
    "qorao'zek" : "Qorao'zek",
    "Qorao'zak" : "Qorao'zek",
    "qorao'zak" : "Qorao'zek",
    "Qarao'zek" : "Qorao'zek",
    "qarao'zek" : "Qorao'zek",
    "Qaraozek" : "Qorao'zek",
    "qaraozek" : "Qorao'zek",
    "Qarao'zek rayoni" : "Qorao'zek",
    "qarao'zek rayoni" : "Qorao'zek",
    "Qaraózek rayonı" : "Qorao'zek",
    "qaraózek rayonı" : "Qorao'zek",
    "Qaraózek" : "Qorao'zek",
    "qaraózek" : "Qorao'zek",
    "Qarao'zek rayon" : "Qorao'zek",
    "qarao'zek rayon" : "Qorao'zek",
    "Qaraózek rayon" : "Qorao'zek",
    "qaraózek rayon" : "Qorao'zek",
    "Qaraózek qalası" : "Qorao'zek",
    "qaraóek qalası": "Qorao'zek",
    "Qarao'zek qalasi" : "Qorao'zek",
    "qarao'zek qalasi" : "Qorao'zek",
    "Karao'zek" : "Qorao'zek",
    "karao'zek" : "Qorao'zek",
    "Karao'zek rayoni" : "Qorao'zek",
    "karao'zek rayoni" : "Qorao'zek",
    "Karao'zek rayon" : "Qorao'zek",
    "karao'zek rayon" : "Qorao'zek",
    "Karaóek rayonı" : "Qorao'zek",
    "karaózek rayonı" : "Qorao'zek",
    "Karaóek rayon" : "Qorao'zek",
    "Karaózek rayon" : "Qorao'zek",

    "Taxtako'pir" : "Taxtako'pir",
    "taxtako'pit" : "Taxtako'pir",
    "Taxta" : "Taxtako'pir",
    "taxta" : "Taxtako'pir",
    "Taxtakópir" : "Taxtako'pir",
    "taxtakópir" : "Taxtako'pir",
    "Taxtako'pir rayoni" : "Taxtako'pir",
    "taxtako'pir rayoni" : "Taxtako'pir",
    "Taxtako'pir rayon" : "Taxtako'pir",
    "taxtako'pir rayon" : "Taxtako'pir",
    "Taxtakópir rayonı" : "Taxtako'pir",
    "taxtakópir rayonı" : "Taxtako'pir",
    "Taxtakópir rayon" : "Taxtako'pir",
    "taxtakópir rayon" : "Taxtako'pir",
    "Taxtako'pir qalasi'" : "Taxtako'pir",
    "taxtako'pir qalasi" : "Taxtako'pir",
    "Taxtakópir qalası" : "Taxtako'pir",
    "taxtakópir qalası" : "Taxtako'pir",
    "Taxtako'pir qala" : "Taxtako'pir",
    "taxtako'pir qala" : "Taxtako'pir",
    "Taxtakópir qala" : "Taxtako'pir",
    "taxtakópir qala" : "Taxtako'pir",
    "Taxtako'pir tumani" : "Taxtako'pir",
    "taxtako'pir tumani" : "Taxtako'pir",
    "Taxtako'pir tuman" : "Taxtako'pir",
    "taxtako'pir tuman" : "Taxtako'pir",

    "Taxiatosh" : "Taxiatosh",
    "taxiatosh" : "Taxiatosh",
    "Taxiatosh tumani" : "Taxiatosh",
    "taxiatosh tumani" : "Taxiatosh",
    "Taxiatas" : "Taxiatosh",
    "taxiatas" : "Taxiatosh",
    "Texas" : "Taxiatosh",
    "texas" : "Taxiatosh",
    "Taqiatas" : "Taxiatosh",
    "taqiatas" : "Taxiatosh",
    "Taxiatash" : "Taxiatosh",
    "taxiatash" : "Taxiatosh",
    "Taxiatas rayoni" : "Taxiatosh",
    "taxiatas rayoni" : "Taxiatosh",
    "Taxiatas rayon" : "Taxiatosh",
    "taxiatas rayon" : "Taxiatosh",
    "Taxiatas qalasi" : "Taxiatosh",
    "taxiatas qalasi" : "Taxiatosh",
    "Taxiatas qala" : "Taxiatosh",
    "taxiatas qala" : "Taxiatosh",
    "Tax" : "Taxiatosh",
    "tax" : "Taxiatosh",

    "Xo'jayli" : "Xo'jayli",
    "xo'jayli" : "Xo'jayli",
    "Xo'jayli tumani" : "Xo'jayli",
    "xo'jayli tumani" : "Xo'jayli",
    "Xo'jayli tuman" : "Xo'jayli",
    "xo'jayli tuman" : "Xo'jayli",
    "Xojeli" : "Xo'jayli",
    "xojeli" : "Xo'jayli",
    "Kojeli" : "Xo'jayli",
    "kojeli" : "Xo'jayli",
    "Xodjeli" : "Xo'jayli",
    "xodjeli" : "Xo'jayli",
    "Qojeli" : "Xo'jayli",
    "qojeli" : "Xo'jayli",
    "Xojeli rayoni" : "Xo'jayli",
    "xojeli rayoni" : "Xo'jayli",
    "Xojeli rayon" : "Xo'jayli",
    "xojeli rayon" : "Xo'jayli",
    "Kojeli rayoni" : "Xo'jayli",
    "kojeli rayoni" : "Xo'jayli",
    "Kojeli rayon" : "Xo'jayli",
    "kojeli rayon" : "Xo'jayli",
    "Xodjeli rayoni" : "Xodjeli",
    "xodjeli rayoni" : "Xodjeli",
    "Xodjeli rayon" : "Xodjeli",
    "xodjeli rayon" : "Xodjeli",
    "Xodjeli qalasi" : "Xodjeli",
    "xodjeli qalasi" : "Xodjeli",
    "Xojeli qalasi" : "Xodjeli",
    "xojeli qalasi" : "Xodjeli",


    "Sho'manoy" : "Sho'manoy",
    "sho'manoy" : "Sho'manoy",
    "Sho'manoy tumani" : "Sho'manoy",
    "sho'manoy tumani" : "Sho'manoy",
    "Sho'manoy tuman" : "Sho'manoy",
    "sho'manoy tuman" : "Sho'manoy",
    "Shomanay" : "Sho'manoy",
    "shomanay" : "Sho'manoy",
    "Shomanay rayoni" : "Sho'manoy",
    "shomanay rayoni" : "Sho'manoy",
    "Shomanay rayon" : "Sho'manoy",
    "shomanay rayon" : "Sho'manoy",
    "Shomanay qalasi" : "Sho'manoy",
    "shomanay qalasi" : "Sho'manoy",
    "Shumanay" : "Sho'manoy",
    "shumanay" : "Sho'manoy",
    "Shumanay rayoni" : "Sho'manoy",
    "shumanay rayoni" : "Sho'manoy",
    "Shumanay rayon" : "Sho'manoy",
    "shumanay rayon" : "Sho'manoy",
    "Shómanay" : "Sho'manoy",
    "shómanay" : "Sho'manoy",
    "Somanay" : "Sho'manoy",
    "samanay" : "Sho'manoy",


    "Qonliko'l" : "Qonliko'l",
    "Qonliko'l tumani" : "Qonliko'l",
    "qonliko'l tumani" : "Qonliko'l",
    "qonliko'l" : "Qonliko'l",
    "Qanliko'l" : "Qonliko'l",
    "qanliko'l" : "Qonliko'l",
    "Qanlikól" : "Qonliko'l",
    "qanlikól" : "Qonliko'l",
    "Qanlikul rayoni" : "Qonliko'l",
    "qanlikul rayoni" : "Qonliko'l",
    "Qanlikul rayon" : "Qonliko'l",
    "qanlikul rayon" : "Qonliko'l",
    "Qanlikul rayonı" : "Qonliko'l",
    "qanlikul rayonı" : "Qonliko'l",
    "Qanlikól rayonı" : "Qonliko'l",
    "qanlikól rayonı" : "Qonliko'l",
    "Kanlikul" : "Qonliko'l",
    "kanlikul" : "Qonliko'l",
    "Kanlikul rayoni" : "Qonliko'l",
    "kanlikul rayoni" : "Qonliko'l",
    "kanlikul rayon" : "Qonliko'l",
    "Kanlikul rayon" : "Qonliko'l",


    "Qo'ng'irot" : "Qo'ng'irot",
    "Qo'ng'irot tumani" : "Qo'ng'irot",
    "qo'ng'irot" : "Qo'ng'irot",
    "qo'ng'irot tumani" : "Qo'ng'irot",
    "Qo'ng'irot tuman" : "Qo'ng'irot",
    "qo'ng'irot tuman" : "Qo'ng'irot",
    "Qong'irat" : "Qo'ng'irot",
    "qing'irat" : "Qo'ng'irot",
    "Qonǵırat" : "Qo'ng'irot",
    "qonǵırat" : "Qo'ng'irot",
    "Qong'irat rayoni" : "Qo'ng'irot",
    "qong'irat rayoni" : "Qo'ng'irot",
    "Qong'irat rayon" : "Qo'ng'irot",
    "qang'irat rayon" : "Qo'ng'irot",
    "Qonǵırat rayonı" : "Qo'ng'irot",
    "qonǵırat rayonı" : "Qo'ng'irot",
    "Qonǵırat rayon" : "Qo'ng'irot",
    "qonǵırat rayon" : "Qo'ng'irot",
    "Kong'irat" : "Qo'ng'irot",
    "kong'irat" : "Qo'ng'irot",
    "Kong'irat rayoni" : "Qo'ng'irot",
    "kong'irat rayoni" : "Qo'ng'irot",
    "Kong'irat rayon" : "Qo'ng'irot",
    "kong'irat rayon" : "Qo'ng'irot",


    "Mo‘ynoq" : "Mo‘ynoq",
    "mo‘ynoq" : "Mo‘ynoq",
    "Mo‘ynoq tumani" : "Mo‘ynoq",
    "mo‘ynoq tumani" : "Mo‘ynoq",
    "Moynaq" : "Mo‘ynoq",
    "moynaq" : "Mo‘ynoq",
    "Muynaq" : "Mo‘ynoq",
    "muynaq" : "Mo‘ynoq",
    "Moynaq rayoni" : "Mo‘ynoq",
    "moynaq rayoni" : "Mo‘ynoq",
    "Moynaq rayon" : "Mo‘ynoq",
    "moynaq rayon" : "Mo‘ynoq",
    "Muynaq rayoni" : "Mo‘ynoq",
    "muynaq rayoni" : "Mo‘ynoq",
    "Moynak" : "Mo‘ynoq",
    "moynak" : "Mo‘ynoq",

    "To'rtkul" : "To'rtkul",
    "to'rtkul" : "To'rtkul",
    "To'rtko'l" : "To'rtkul",
    "to'rtko'l" : "To'rtkul",
    "Turtkul" : "To'rtkul",
    "turtkul" : "Turtkul",
    "Tórtkól" : "Turtkul",
    "tórtkól" : "Turtkul",
    "Tórtkul" : "Turtkul",
    "To'rtkul tumani" : "To'rtkul",
    "to'rtkul tumani" : "To'rtkul",
    "To'rtkul tuman" : "To'rtkul",
    "to'rtkul tuman" : "To'rtkul",
    "To'rtko'l tumani" : "To'rtkul",
    "to'rtko'l tumani" : "To'rtkul",
    "To'rtko'l rayoni" : "To'rtkul",
    "to'rtko'l rayoni" : "To'rtkul",


    "Ellikqall'a" : "Ellikqall'a",
    "ellikqall'a" : "Ellikqall'a",
    "Ellikqall'a tumani" : "Ellikqall'a",
    "ellikqall'a tumani" : "Ellikqall'a",
    "Ellikqall'a tuman" : "Ellikqall'a",
    "ellikqall'a tuman" : "Ellikqall'a",
    "Ellik" : "Ellikqall'a",
    "ellik" : "Ellikqall'a",
    "Elikqala rayoni" : "Ellikqall'a",
    "elikqala rayoni" : "Ellikqall'a",
    "Elikqala" : "Ellikqall'a",
    "elikqala" : "Ellikqall'a",
    "Ellikqalla rayon" : "Ellikqall'a",
    "ellikqalla rayon" : "Ellikqall'a",
    "boston": "Ellikqall'a",
    "bo ston": "Ellikqall'a",
    "Bostan" : "Ellikqall'a",
    "Bo'stan" : "Ellikqall'a",
    "bo'stan" : "Ellikqall'a",
    "Bo'ston tumani" : "Ellikqall'a",
    "bo'ston tumani" : "Ellikqall'a",
    "Buston" : "Ellikqall'a",
    "Boston tumani" : "Ellikqall'a",
    "boston tumani" : "Ellikqall'a",


    "Beruniy" : "Beruniy",
    "beruniy" : "Beruniy",
    "Beruniy tumani" : "Beruniy",
    "beruniy tumani" : "Beruniy",
    "Beruni" : "Beruniy",
    "Beruniy rayoni" : "Beruniy",
    "beruniy rayoni" : "Beruniy",
    "Beruniy rayon" : "Beruniy",
    "beruniy rayon" : "Beruniy",
    "Beroniy" : "Beruniy",
    "beroniy" : "Beruniy",

    "Bo'zatov": "Bo'zatov",
    "Bo'zatov tumani" : "Bo'zatov",
    "bo'zatov" : "Bo'zatov",
    "bo'zatov tumani" : "Bo'zatov",
    "Bozataw" : "Bo'zatov",
    "bozataw" : "Bo'zatov",
    "Bozataw rayoni" : "Bo'zatov",
    "bozataw rayoni" : "Bo'zatov",
    "Bozataw rayon" : "Bo'zatov",
    "bozataw rayon" : "Bo'zatov",
    "Bozatav" : "Bo'zatov",
    "bozatav" : "Bo'zatov",
    "Bo'zatov tuman" : "Bo'zatov",
    "bo'zatov tuman" : "Bo'zatov",


    "tashkent": "Toshkent shahar",
    "toshkent": "Toshkent shahar",
}

# Load regions JSON
try:
    with open(REGIONS_FILE, "r", encoding="utf-8") as f:
        REGIONS_DATA = json.load(f)
except Exception as e:
    print("regions_lot.json ashıwda qáte:", e)
    REGIONS_DATA = {}

# Build flat list of entries and compute strong normalized form
def strip_diacritics(s: str) -> str:
    nk = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nk if not unicodedata.combining(c))

def normalize_text_strong(s: str) -> str:
    if not s:
        return ''
    s = s.strip().lower()
    # replacements
    for k, v in REPLACEMENTS.items():
        s = s.replace(k, v)
    s = strip_diacritics(s)
    s = _NON_ALNUM_RE.sub(' ', s)
    s = ' '.join(s.split())
    # some translit fixes
    s = s.replace('tashkent', 'toshkent')
    return s

# Flatten regions into list of dicts: name, region, lat, lon, norm
_REGIONS_FLAT = []
for region, arr in REGIONS_DATA.items():
    for it in arr:
        name = it.get('name') or ''
        lat = it.get('lat')
        lon = it.get('lon')
        norm = normalize_text_strong(name)
        _REGIONS_FLAT.append({'name': name, 'region': region, 'lat': lat, 'lon': lon, 'norm': norm})
print(f"Loaded {_REGIONS_FLAT.__len__()} region entries from {REGIONS_FILE if REGIONS_FILE.exists() else 'no file'}")

# User store helpers (store object: {telegram_id: {"city":..., "lat":..., "lon":...}})
def load_user_store():
    try:
        if USER_CITIES_FILE.exists():
            with open(USER_CITIES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print("load_user_store error:", e)
    return {}

def save_user_store(d):
    try:
        with open(USER_CITIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("save_user_store error:", e)

def save_user_city(telegram_id, city_name, lat=None, lon=None):
    d = load_user_store()
    d[str(telegram_id)] = {"city": city_name, "lat": lat, "lon": lon}
    save_user_store(d)

# Matching function — returns item dict or None
def find_city_item(query, cutoff=0.6):
    if not query:
        return None
    qn = normalize_text_strong(query)

    # 0) alias direct
    if qn in ALIASES:
        canonical = ALIASES[qn]
        # find in regions flat
        for it in _REGIONS_FLAT:
            if normalize_text_strong(it['name']) == normalize_text_strong(canonical) or it['name'] == canonical:
                return {'method': 'alias', 'item': it}
        # synthetic item if not present
        return {'method': 'alias', 'item': {'name': canonical, 'region': None, 'lat': None, 'lon': None}}

    # 1) exact normalized
    for it in _REGIONS_FLAT:
        if it.get('norm') == qn:
            return {'method': 'exact', 'item': it}

    # 2) substring / token containment (all tokens in name)
    q_tokens = qn.split()
    for it in _REGIONS_FLAT:
        name_norm = it.get('norm','')
        if all(tok in name_norm for tok in q_tokens):
            return {'method': 'substring', 'item': it}

    # 3) fuzzy
    names = [it['norm'] for it in _REGIONS_FLAT if it.get('norm')]
    matches = get_close_matches(qn, names, n=6, cutoff=cutoff)
    if matches:
        best = matches[0]
        for it in _REGIONS_FLAT:
            if it.get('norm') == best:
                return {'method': 'fuzzy', 'item': it, 'match': best}

    # 4) token overlap scoring
    best = None; best_score = 0
    qset = set(q_tokens)
    for it in _REGIONS_FLAT:
        name_tokens = set(it.get('norm','').split())
        score = len(qset & name_tokens)
        if score > best_score:
            best_score = score; best = it
    if best_score > 0:
        return {'method': 'token', 'item': best, 'score': best_score}

    return None

# Telegram helpers
def send_message(chat_id, text):
    payload = {"chat_id": chat_id, "text": text}
    try:
        r = requests.post(f"{TELEGRAM_API}/sendMessage", json=payload, timeout=10)
        return r.json()
    except Exception as e:
        print("send_message error:", e)
        return None

# OpenWeather fetch helpers
def fetch_weather_by_name(name):
    enc = quote_plus(name)
    url = f"http://api.openweathermap.org/data/2.5/weather?q={enc}&appid={OPENWEATHER_KEY}&units=metric&lang=uz"
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            return True, r.json()
        return False, f"{r.status_code}: {r.text}"
    except Exception as e:
        return False, str(e)

def fetch_weather_by_coords(lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_KEY}&units=metric&lang=uz"
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            return True, r.json()
        return False, f"{r.status_code}: {r.text}"
    except Exception as e:
        return False, str(e)

def format_weather(data):
    data = data if isinstance(data, dict) else {}
    # If wrapper {source,data: {...}} used previously, try to extract
    if 'data' in data and isinstance(data['data'], dict):
        data = data['data']
    name = data.get('name') or data.get('sys', {}).get('country', '') or ''
    weather = (data.get('weather') or [{}])[0]
    main = data.get('main', {})
    lines = []
    if name:
        lines.append(f"📍 {name}")
    if weather.get('description'):
        lines.append(f"🌥 Jaǵday: {weather.get('description').capitalize()}")
    t = main.get('temp')
    if t is not None:
        lines.append(f"🌡 Temperatura: {t}°C (min {main.get('temp_min')} / max {main.get('temp_max')})")
    if main.get('humidity') is not None:
        lines.append(f"💧 Ízǵarlıǵı: {main.get('humidity')}%")
    if main.get('pressure') is not None:
        lines.append(f"🔵 Basım: {main.get('pressure')} hPa")
    return "\n".join(lines) if lines else "Hawa-rayı maǵlıwmatları tabılmadı."

# Message processing
def process_message(message):
    chat_id = message['chat']['id']
    telegram_id = message.get('from', {}).get('id')
    text = (message.get('text') or "").strip()
    if not text:
        send_message(chat_id, "Iltimas tekst jiberiń.")
        return

    if text == '/start':
        send_message(chat_id,
            "Assalomu alaykum! Hawa rayı Botına xosh keldińiz.\n\n"
            "Buyrıqlar:\n"
            "/setcity Qala yamasa rayon atın saqlaw ushın (/setcity Nókis qalası)\n"
            "/weather — Saqlanǵan qala hám rayon boylab hawa-rayı malıwmatı alıq (/weather Nókis qalası)\n"
            "/weather — Egerde Qala yamasa rayon atı saqlanbaǵan bolsa (/weather Nókis qalası) dep jazıń sonda malıwmatlar shıǵadı\n")
        return

    if text.startswith('/setcity'):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            send_message(chat_id, "Iltimas qala yamas rayon atınıń jazıń: /setcity Kegeyli")
            return
        raw = parts[1].strip()
        res = find_city_item(raw)
        if not res:
            # fallback: save raw input as city name (no coords)
            save_user_city(telegram_id, raw, None, None)
            send_message(chat_id, f"(Saqlanǵan - biraq JSON dizimde tabılmadı) {raw}")
            return
        item = res['item']
        name = item.get('name')
        lat = item.get('lat'); lon = item.get('lon')
        save_user_city(telegram_id, name, lat, lon)
        send_message(chat_id, f"Sizdiń qala yamasa rayonıńız saqlandı: {name} (Usıl: {res.get('method')})")
        return

    if text.startswith('/weather'):
        parts = text.split(maxsplit=1)
        if len(parts) == 1:
            # get from local store
            store = load_user_store()
            info = store.get(str(telegram_id))
            if not info:
                send_message(chat_id, "Aldın /setcity menen qalanı belgileń yamasa /weather qala atın jazıń.")
                return
            city_name = info.get('city'); lat = info.get('lat'); lon = info.get('lon')
        else:
            raw = parts[1].strip()
            res = find_city_item(raw)
            if not res:
                # fallback to direct search by raw string
                city_name = raw; lat = lon = None
            else:
                item = res['item']
                city_name = item.get('name'); lat = item.get('lat'); lon = item.get('lon')

        # prefer coords if available
        if lat is not None and lon is not None:
            ok, data = fetch_weather_by_coords(lat, lon)
        else:
            ok, data = fetch_weather_by_name(city_name)

        if not ok:
            send_message(chat_id, f"Hawa-rayı alıwda qátelik: {data}")
            return
        msg = format_weather(data)
        send_message(chat_id, msg)
        return

    # unknown
    send_message(chat_id, "Siz qáte kiritińiz. /start buyruǵın kiritiń qaytan urınıp kóriń.")

# Long-polling
def main_loop():
    offset = None
    print("Bot jumısqa tústi. Long-Polling baslandı...")
    while True:
        params = {"timeout": 30}
        if offset:
            params['offset'] = offset
        try:
            r = requests.get(f"{TELEGRAM_API}/getUpdates", params=params, timeout=35)
            res = r.json()
            if not res.get('ok'):
                time.sleep(2)
                continue
            updates = res.get('result', [])
            for u in updates:
                offset = u['update_id'] + 1
                if 'message' in u:
                    process_message(u['message'])
        except Exception as e:
            print("Polling error:", e)
            time.sleep(5)

if __name__ == "__main__":
    main_loop()
