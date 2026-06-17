from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_IDS, SPECIALIZATIONS
from database import (
    get_all_workers, get_worker_by_id, add_worker,
    update_worker_field, deactivate_worker,
    count_done_jobs_for_worker, count_active_jobs_for_worker
)
from keyboards import (
    workers_list_kb, worker_detail_kb, worker_edit_kb,
    specialization_kb, delete_confirm_kb, admin_menu
)

router = Router()


def is_admin(uid): return uid in ADMIN_IDS


class AddWorkerStates(StatesGroup):
    name = State()
    phone = State()
    age = State()
    spec = State()
    tg_id = State()


class EditWorkerStates(StatesGroup):
    field = State()
    value = State()


class LinkTgStates(StatesGroup):
    tg_id = State()


# ── WORKERS BOSHQARUVI ───────────────────────────────

@router.message(F.text == "👷 Ishchilar boshqaruvi")
async def workers_menu(msg: Message):
    if not is_admin(msg.from_user.id): return
    workers = await get_all_workers()
    await msg.answer(
        f"👷 <b>Ishchilar ro'yxati</b> ({len(workers)} ta):",
        reply_markup=workers_list_kb(workers),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "workers_back")
async def workers_back(cb: CallbackQuery):
    workers = await get_all_workers()
    await cb.message.edit_text(
        f"👷 <b>Ishchilar ro'yxati</b> ({len(workers)} ta):",
        reply_markup=workers_list_kb(workers),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("wview_"))
async def worker_view(cb: CallbackQuery):
    wid = int(cb.data.replace("wview_", ""))
    w = await get_worker_by_id(wid)
    if not w:
        await cb.answer("Ishchi topilmadi!")
        return
    done = await count_done_jobs_for_worker(wid)
    active = await count_active_jobs_for_worker(wid)
    text = (
        f"👷 <b>{w['full_name']}</b>\n\n"
        f"📱 Telefon: {w['phone'] or '—'}\n"
        f"🎂 Yosh: {w['age'] or '—'}\n"
        f"🔧 Mutaxassislik: {w['specialization'] or '—'}\n"
        f"🆔 Telegram ID: {w['telegram_id'] or '—'}\n"
        f"📊 Status: {'✅ Faol' if w['status'] == 'approved' else w['status']}\n\n"
        f"✅ Bajarilgan ishlar: <b>{done}</b>\n"
        f"🔄 Faol ishlar: <b>{active}</b>"
    )
    await cb.message.edit_text(text, reply_markup=worker_detail_kb(wid), parse_mode="HTML")


# ── QO'SHISH ─────────────────────────────────────────

@router.callback_query(F.data == "worker_add")
async def worker_add_start(cb: CallbackQuery, state: FSMContext):
    await cb.message.answer("👤 <b>Ishchi ismi va familiyasini kiriting:</b>", parse_mode="HTML")
    await state.set_state(AddWorkerStates.name)
    await cb.answer()


@router.message(AddWorkerStates.name)
async def add_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text.strip())
    await msg.answer("📱 <b>Telefon raqamini kiriting:</b>", parse_mode="HTML")
    await state.set_state(AddWorkerStates.phone)


@router.message(AddWorkerStates.phone)
async def add_phone(msg: Message, state: FSMContext):
    await state.update_data(phone=msg.text.strip())
    await msg.answer("🎂 <b>Yoshini kiriting</b> (ixtiyoriy, o'tkazish uchun — yuboring):", parse_mode="HTML")
    await state.set_state(AddWorkerStates.age)


@router.message(AddWorkerStates.age)
async def add_age(msg: Message, state: FSMContext):
    txt = msg.text.strip()
    age = None
    if txt.isdigit():
        age = int(txt)
    await state.update_data(age=age)
    await msg.answer(
        "🔧 <b>Mutaxassislikni tanlang:</b>",
        reply_markup=specialization_kb(),
        parse_mode="HTML"
    )
    await state.set_state(AddWorkerStates.spec)


@router.callback_query(AddWorkerStates.spec, F.data.startswith("newspec_"))
async def add_spec(cb: CallbackQuery, state: FSMContext):
    idx = int(cb.data.replace("newspec_", ""))
    spec = SPECIALIZATIONS[idx]
    await state.update_data(spec=spec)
    await cb.message.edit_text(
        f"✅ Mutaxassislik: <b>{spec}</b>\n\n"
        f"🆔 <b>Telegram ID kiriting</b> (ixtiyoriy, o'tkazish uchun <b>-</b> yuboring):",
        parse_mode="HTML"
    )
    await state.set_state(AddWorkerStates.tg_id)


@router.message(AddWorkerStates.tg_id)
async def add_tg_id(msg: Message, state: FSMContext, bot):
    txt = msg.text.strip()
    tg_id = None
    if txt.isdigit():
        tg_id = int(txt)
    data = await state.get_data()
    await add_worker(
        telegram_id=tg_id,
        full_name=data["name"],
        phone=data["phone"],
        age=data.get("age"),
        specialization=data.get("spec"),
        status="approved"
    )
    await msg.answer(
        f"✅ <b>{data['name']}</b> ishchi sifatida qo'shildi!",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )
    await state.clear()

    if tg_id:
        try:
            await bot.send_message(
                tg_id,
                "🎉 <b>Xush kelibsiz!</b>\n\nAdmin sizni ishchi sifatida qo'shdi. Botdan foydalanishingiz mumkin.",
                reply_markup=__import__('keyboards').worker_menu(),
                parse_mode="HTML"
            )
        except Exception:
            pass


# ── TAHRIRLASH ────────────────────────────────────────

@router.callback_query(F.data.startswith("wedit_"))
async def worker_edit(cb: CallbackQuery):
    wid = int(cb.data.replace("wedit_", ""))
    await cb.message.edit_text(
        "✏️ <b>Qaysi maydonni tahrirlaysiz?</b>",
        reply_markup=worker_edit_kb(wid),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("wef_"))
async def worker_edit_field(cb: CallbackQuery, state: FSMContext):
    parts = cb.data.split("_")
    wid = int(parts[1])
    field = parts[2]

    if field == "specialization":
        await cb.message.edit_text(
            "🔧 <b>Yangi mutaxassislikni tanlang:</b>",
            reply_markup=specialization_kb(wid),
            parse_mode="HTML"
        )
        return

    field_names = {
        "full_name": "ismi va familiyasi",
        "phone": "telefon raqami",
        "age": "yoshi",
        "telegram_id": "Telegram ID"
    }
    await state.update_data(edit_worker_id=wid, edit_field=field)
    await cb.message.answer(
        f"✏️ <b>Yangi {field_names.get(field, field)}ni kiriting:</b>",
        parse_mode="HTML"
    )
    await state.set_state(EditWorkerStates.value)
    await cb.answer()


@router.callback_query(F.data.startswith("wspec_"))
async def worker_edit_spec(cb: CallbackQuery):
    parts = cb.data.split("_")
    wid = int(parts[1])
    idx = int(parts[2])
    spec = SPECIALIZATIONS[idx]
    await update_worker_field(wid, "specialization", spec)
    await cb.message.edit_text(f"✅ Mutaxassislik yangilandi: <b>{spec}</b>", parse_mode="HTML")
    await cb.answer("✅ Saqlandi!")


@router.message(EditWorkerStates.value)
async def save_edit(msg: Message, state: FSMContext):
    data = await state.get_data()
    wid = data["edit_worker_id"]
    field = data["edit_field"]
    value = msg.text.strip()
    if field == "age" and value.isdigit():
        value = int(value)
    if field == "telegram_id" and value.isdigit():
        value = int(value)
    await update_worker_field(wid, field, value)
    await msg.answer("✅ Ma'lumot yangilandi!")
    await state.clear()


# ── TELEGRAM ID BIRLASHTIRISH ─────────────────────────

@router.callback_query(F.data.startswith("wlink_"))
async def link_tg(cb: CallbackQuery, state: FSMContext):
    wid = int(cb.data.replace("wlink_", ""))
    await state.update_data(link_worker_id=wid)
    await cb.message.answer(
        "🆔 <b>Telegram ID ni kiriting:</b>\n"
        "<i>(@userinfobot orqali olishingiz mumkin)</i>",
        parse_mode="HTML"
    )
    await state.set_state(LinkTgStates.tg_id)
    await cb.answer()


@router.message(LinkTgStates.tg_id)
async def save_tg_link(msg: Message, state: FSMContext):
    data = await state.get_data()
    wid = data["link_worker_id"]
    tg_id = msg.text.strip()
    if not tg_id.lstrip("-").isdigit():
        await msg.answer("❗ Noto'g'ri ID format. Raqam kiriting:")
        return
    await update_worker_field(wid, "telegram_id", int(tg_id))
    await msg.answer("✅ Telegram ID birlashtirildi!")
    await state.clear()


# ── O'CHIRISH ─────────────────────────────────────────

@router.callback_query(F.data.startswith("wdel_") & ~F.data.startswith("wdel_confirm_"))
async def worker_del_confirm(cb: CallbackQuery):
    wid = int(cb.data.replace("wdel_", ""))
    w = await get_worker_by_id(wid)
    await cb.message.edit_text(
        f"🗑️ <b>{w['full_name']}</b>ni o'chirishni tasdiqlaysizmi?",
        reply_markup=delete_confirm_kb(wid),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("wdel_confirm_"))
async def worker_del_do(cb: CallbackQuery):
    wid = int(cb.data.replace("wdel_confirm_", ""))
    w = await get_worker_by_id(wid)
    await deactivate_worker(wid)
    await cb.message.edit_text(f"🗑️ <b>{w['full_name']}</b> o'chirildi.", parse_mode="HTML")
    await cb.answer("✅ O'chirildi!")
