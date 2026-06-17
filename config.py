import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_IDS = [6563439963, 7831366060, 7689533732]

DB_PATH = "elektro_tabib.db"

# Ish turlari
JOB_TYPES = {
    "moy": {
        "name": "🛢 Moy almashtirish",
        "sub": ["To'liq (Old + Orqa)", "Old ko'prik", "Orqa ko'prik", "Reduktor", "Farqlovchi"]
    },
    "xadavoy": {
        "name": "🔩 Xadavoy tuzatish",
        "sub": ["Amortizator", "Rulman", "SHRUS", "Tormoz kolodkasi", "Tormoz diski", "Boshqa"]
    },
    "motor": {
        "name": "⚙️ Motor / Reduktor",
        "sub": ["Motor ta'mirlash", "Reduktor ta'mirlash", "Motor almashtirish", "Reduktor almashtirish"]
    },
    "batareya": {
        "name": "🔋 Batareya ishlari",
        "sub": ["Diagnostika", "Balanslashtirish", "Hujayra almashtirish", "BMS ta'mirlash", "To'liq almashtirish"]
    },
    "inverter": {
        "name": "⚡ Inverter / Elektronika",
        "sub": ["Inverter ta'mirlash", "OBC ta'mirlash", "DC-DC ta'mirlash", "ECU ta'mirlash", "Sensor almashtirish"]
    },
    "kuzov": {
        "name": "🚗 Kuzov / Bamper",
        "sub": ["Bamper", "Qanotlar", "Bo'yash", "Shisha", "Boshqa"]
    },
    "boshqa": {
        "name": "🔧 Boshqa ish",
        "sub": ["Konditsioner", "Salon", "Faralar", "Audio/Video", "Boshqa"]
    },
}

# Mashina brendlari
CAR_BRANDS = {
    "byd": "BYD",
    "zeekr": "Zeekr",
    "liAuto": "Li Auto",
    "voyah": "Voyah",
    "changan": "Changan",
    "bmw": "BMW",
    "tesla": "Tesla",
    "boshqa": "Boshqa"
}

# BYD modellari
CAR_MODELS = {
    "BYD": ["Atto 3", "Han", "Tang", "Seal", "Dolphin", "Song Plus", "Yuan Plus", "Boshqa"],
    "Zeekr": ["001", "007", "009", "X", "Boshqa"],
    "Li Auto": ["L6", "L7", "L8", "L9", "Mega", "Boshqa"],
    "Voyah": ["Free", "Dream", "Boshqa"],
    "Changan": ["Deepal S7", "Deepal L7", "Uni-K", "Uni-V", "Boshqa"],
    "BMW": ["i3", "i4", "i5", "i7", "iX", "Boshqa"],
    "Tesla": ["Model 3", "Model Y", "Model S", "Model X", "Boshqa"],
    "Boshqa": ["Erkin kiriting"],
}

# Mutaxassisliklar
SPECIALIZATIONS = [
    "Moy ustasi",
    "Elektrik",
    "Kuzovchi",
    "Akkumulyator ustasi",
    "Elektronik",
    "Mexanik",
    "Boshqa"
]
