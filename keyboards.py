from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from config import JOB_TYPES, CAR_BRANDS, CAR_MODELS, SPECIALIZATIONS


# ── ADMIN ─────────────────────────────────────────────

def admin_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📋 Yangi ish yaratish")],
        [KeyboardButton(text="👷 Ishchilar boshqaruvi")],
        [KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="⚙️ Sozlamalar")],
    ], resize_keyboard=True)


# ── WORKER ────────────────────────────────────────────

def worker_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📋 Mening ishlarim")],
    ], resize_keyboard=True)


# ── REGISTRATION ──────────────────────────────────────

def phone_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📱 Telefon raqamimni yuborish", request_contact=True)]
    ], resize_keyboard=True, one_time_keyboard=True)


def confirm_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✅ Tasdiqlash")],
        [KeyboardButton(text="🔄 Qayta boshlash")],
    ], resize_keyboard=True)


def remove_kb():
    from aiogram.types import ReplyKeyboardRemove
    return ReplyKeyboardRemove()


# ── ADMIN — ariza ────────────────────────────────────

def approve_worker_kb(worker_id):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Qabul", callback_data=f"approve_{worker_id}"),
        InlineKeyboardButton(text="❌ Rad", callback_data=f"reject_{worker_id}"),
    ]])


# ── JOB TYPES ────────────────────────────────────────

def job_types_kb():
    buttons = []
    for key, val in JOB_TYPES.items():
        buttons.append([InlineKeyboardButton(text=val["name"], callback_data=f"jtype_{key}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def job_sub_kb(job_type_key):
    subs = JOB_TYPES[job_type_key]["sub"]
    buttons = [[InlineKeyboardButton(text=s, callback_data=f"jsub_{i}")] for i, s in enumerate(subs)]
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="jtype_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def car_brands_kb():
    buttons = []
    row = []
    for key, val in CAR_BRANDS.items():
        row.append(InlineKeyboardButton(text=val, callback_data=f"brand_{key}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def car_models_kb(brand):
    models = CAR_MODELS.get(brand, ["Boshqa"])
    buttons = [[InlineKeyboardButton(text=m, callback_data=f"model_{i}")] for i, m in enumerate(models)]
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="brand_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def workers_select_kb(workers, selected_ids):
    buttons = []
    for w in workers:
        check = "✅" if w["id"] in selected_ids else "◻️"
        spec = w["specialization"] or ""
        buttons.append([InlineKeyboardButton(
            text=f"{check} {w['full_name']} | {spec}",
            callback_data=f"wsel_{w['id']}"
        )])
    count = len(selected_ids)
    buttons.append([InlineKeyboardButton(
        text=f"✔️ Tasdiqlash ({count} ta tanlandi)",
        callback_data="wsel_confirm"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def job_confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🚀 Ishni yuborish", callback_data="job_send"),
        InlineKeyboardButton(text="❌ Bekor", callback_data="job_cancel"),
    ]])


# ── WORKER JOBS ──────────────────────────────────────

def job_action_kb(jw_id):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Bajarildi", callback_data=f"done_{jw_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_job_{jw_id}"),
    ]])


# ── WORKERS LIST ─────────────────────────────────────

def workers_list_kb(workers):
    buttons = [[InlineKeyboardButton(
        text=f"👷 {w['full_name']}",
        callback_data=f"wview_{w['id']}"
    )] for w in workers]
    buttons.append([InlineKeyboardButton(text="➕ Yangi ishchi qo'shish", callback_data="worker_add")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def worker_detail_kb(worker_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"wedit_{worker_id}")],
        [InlineKeyboardButton(text="🔗 Telegram ID birlashtirish", callback_data=f"wlink_{worker_id}")],
        [InlineKeyboardButton(text="🗑️ O'chirish", callback_data=f"wdel_{worker_id}")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="workers_back")],
    ])


def worker_edit_kb(worker_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Ism", callback_data=f"wef_{worker_id}_full_name"),
         InlineKeyboardButton(text="📱 Telefon", callback_data=f"wef_{worker_id}_phone")],
        [InlineKeyboardButton(text="🎂 Yosh", callback_data=f"wef_{worker_id}_age"),
         InlineKeyboardButton(text="🔧 Mutaxassislik", callback_data=f"wef_{worker_id}_specialization")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"wview_{worker_id}")],
    ])


def specialization_kb(worker_id=None):
    buttons = []
    row = []
    for i, s in enumerate(SPECIALIZATIONS):
        cb = f"wspec_{worker_id}_{i}" if worker_id else f"newspec_{i}"
        row.append(InlineKeyboardButton(text=s, callback_data=cb))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def delete_confirm_kb(worker_id):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"wdel_confirm_{worker_id}"),
        InlineKeyboardButton(text="❌ Yo'q", callback_data=f"wview_{worker_id}"),
    ]])
