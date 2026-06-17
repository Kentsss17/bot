from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_IDS, JOB_TYPES, CAR_BRANDS, CAR_MODELS
from database import (
    get_approved_workers, create_job, assign_workers_to_job,
    get_worker_by_id
)
from keyboards import (
    job_types_kb, job_sub_kb, car_brands_kb, car_models_kb,
    workers_select_kb, job_confirm_kb, admin_menu
)

router = Router()


class JobStates(StatesGroup):
    job_type = State()
    job_sub = State()
    car_brand = State()
    car_model = State()
    car_model_text = State()
    vin = State()
    note = State()
    workers = State()
    confirm = State()


def is_admin(uid): return uid in ADMIN_IDS


# ── YANGI ISH ────────────────────────────────────────

@router.message(F.text == "📋 Yangi ish yaratish")
async def new_job_start(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id): return
    await state.clear()
    await msg.answer("🔧 <b>Ish turini tanlang:</b>", reply_markup=job_types_kb(), parse_mode="HTML")
    await state.set_state(JobStates.job_type)


@router.callback_query(JobStates.job_type, F.data.startswith("jtype_"))
async def pick_job_type(cb: CallbackQuery, state: FSMContext):
    key = cb.data.replace("jtype_", "")
    if key == "back":
        await cb.message.edit_text("🔧 <b>Ish turini tanlang:</b>", reply_markup=job_types_kb(), parse_mode="HTML")
        return
    jt = JOB_TYPES[key]
    await state.update_data(job_type_key=key, job_type_name=jt["name"])
    await cb.message.edit_text(
        f"✅ Ish turi: <b>{jt['name']}</b>\n\n📌 <b>Qo'shimcha turni tanlang:</b>",
        reply_markup=job_sub_kb(key),
        parse_mode="HTML"
    )
    await state.set_state(JobStates.job_sub)


@router.callback_query(JobStates.job_sub, F.data.startswith("jsub_"))
async def pick_job_sub(cb: CallbackQuery, state: FSMContext):
    idx = int(cb.data.replace("jsub_", ""))
    data = await state.get_data()
    key = data["job_type_key"]
    sub_name = JOB_TYPES[key]["sub"][idx]
    await state.update_data(job_sub=sub_name)
    await cb.message.edit_text(
        f"✅ {data['job_type_name']} — <b>{sub_name}</b>\n\n🚗 <b>Mashina brendini tanlang:</b>",
        reply_markup=car_brands_kb(),
        parse_mode="HTML"
    )
    await state.set_state(JobStates.car_brand)


@router.callback_query(JobStates.car_brand, F.data.startswith("brand_"))
async def pick_brand(cb: CallbackQuery, state: FSMContext):
    key = cb.data.replace("brand_", "")
    if key == "back":
        data = await state.get_data()
        await cb.message.edit_text(
            f"📌 <b>Qo'shimcha turni tanlang:</b>",
            reply_markup=job_sub_kb(data["job_type_key"]),
            parse_mode="HTML"
        )
        await state.set_state(JobStates.job_sub)
        return
    brand_name = CAR_BRANDS[key]
    await state.update_data(car_brand=brand_name)
    await cb.message.edit_text(
        f"✅ Brend: <b>{brand_name}</b>\n\n🚘 <b>Modelni tanlang:</b>",
        reply_markup=car_models_kb(brand_name),
        parse_mode="HTML"
    )
    await state.set_state(JobStates.car_model)


@router.callback_query(JobStates.car_model, F.data.startswith("model_"))
async def pick_model(cb: CallbackQuery, state: FSMContext):
    idx = int(cb.data.replace("model_", ""))
    data = await state.get_data()
    brand = data["car_brand"]
    model_name = CAR_MODELS.get(brand, ["Boshqa"])[idx]

    if model_name in ["Boshqa", "Erkin kiriting"]:
        await cb.message.edit_text("✏️ <b>Mashina modelini kiriting:</b>", parse_mode="HTML")
        await state.set_state(JobStates.car_model_text)
        return

    await state.update_data(car_model=model_name)
    await cb.message.edit_text(
        f"✅ Mashina: <b>{brand} {model_name}</b>\n\n🔑 <b>VIN kodni kiriting:</b>",
        parse_mode="HTML"
    )
    await state.set_state(JobStates.vin)


@router.message(JobStates.car_model_text)
async def model_text_input(msg: Message, state: FSMContext):
    await state.update_data(car_model=msg.text.strip())
    await msg.answer("🔑 <b>VIN kodni kiriting:</b>", parse_mode="HTML")
    await state.set_state(JobStates.vin)


@router.message(JobStates.vin)
async def pick_vin(msg: Message, state: FSMContext):
    vin = msg.text.strip().upper()
    if len(vin) < 3:
        await msg.answer("❗ VIN kod kamida 3 ta belgi. Qayta kiriting:")
        return
    await state.update_data(vin=vin)
    await msg.answer(
        "📝 <b>Qo'shimcha izoh kiriting:</b>\n"
        "<i>(Izoh yo'q bo'lsa — <b>-</b> yuboring)</i>",
        parse_mode="HTML"
    )
    await state.set_state(JobStates.note)


@router.message(JobStates.note)
async def pick_note(msg: Message, state: FSMContext):
    await state.update_data(note=msg.text.strip())
    workers = await get_approved_workers()
    if not workers:
        await msg.answer("❗ Tasdiqlangan ishchilar yo'q. Avval ishchi qo'shing.")
        await state.clear()
        return
    await state.update_data(selected_workers=[])
    await msg.answer(
        "👷 <b>Ishchilarni tanlang:</b>\n<i>(Bir nechta tanlash mumkin)</i>",
        reply_markup=workers_select_kb(workers, []),
        parse_mode="HTML"
    )
    await state.set_state(JobStates.workers)


@router.callback_query(JobStates.workers, F.data.startswith("wsel_"))
async def select_worker(cb: CallbackQuery, state: FSMContext):
    key = cb.data.replace("wsel_", "")
    if key == "confirm":
        data = await state.get_data()
        sel = data.get("selected_workers", [])
        if not sel:
            await cb.answer("❗ Kamida 1 ta ishchi tanlang!", show_alert=True)
            return
        await _show_job_confirm(cb.message, data)
        await state.set_state(JobStates.confirm)
        return

    worker_id = int(key)
    data = await state.get_data()
    sel = data.get("selected_workers", [])
    if worker_id in sel:
        sel.remove(worker_id)
    else:
        sel.append(worker_id)
    await state.update_data(selected_workers=sel)
    workers = await get_approved_workers()
    await cb.message.edit_reply_markup(reply_markup=workers_select_kb(workers, sel))
    await cb.answer()


async def _show_job_confirm(msg: Message, data: dict):
    sel_ids = data.get("selected_workers", [])
    worker_names = []
    for wid in sel_ids:
        w = await get_worker_by_id(wid)
        if w:
            worker_names.append(w["full_name"])

    text = (
        f"📋 <b>Ish ma'lumotlari:</b>\n\n"
        f"🔧 Tur: <b>{data['job_type_name']}</b>\n"
        f"📌 Qo'shimcha: <b>{data['job_sub']}</b>\n"
        f"🚗 Mashina: <b>{data['car_brand']} {data['car_model']}</b>\n"
        f"🔑 VIN: <code>{data['vin']}</code>\n"
        f"📝 Izoh: <b>{data['note']}</b>\n"
        f"👷 Ishchilar: <b>{', '.join(worker_names)}</b>\n\n"
        f"Tasdiqlaysizmi?"
    )
    await msg.answer(text, reply_markup=job_confirm_kb(), parse_mode="HTML")


@router.callback_query(JobStates.confirm, F.data == "job_send")
async def send_job(cb: CallbackQuery, state: FSMContext, bot):
    data = await state.get_data()
    from datetime import datetime
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    job_id = await create_job(
        job_type=data["job_type_name"],
        job_sub=data["job_sub"],
        car_brand=data["car_brand"],
        car_model=data["car_model"],
        vin_code=data["vin"],
        note=data["note"],
        created_by=cb.from_user.id,
    )
    sel_ids = data.get("selected_workers", [])
    await assign_workers_to_job(job_id, sel_ids)

    await cb.message.edit_text("✅ <b>Ish muvaffaqiyatli yaratildi!</b>", parse_mode="HTML")
    await cb.answer("✅ Yuborildi!")
    await state.clear()

    # Ishchilarga xabar
    for wid in sel_ids:
        w = await get_worker_by_id(wid)
        if w and w["telegram_id"]:
            try:
                await bot.send_message(
                    w["telegram_id"],
                    f"🆕 <b>Yangi ish tayinlandi!</b>\n\n"
                    f"🔧 Tur: <b>{data['job_type_name']}</b>\n"
                    f"📌 Qo'shimcha: <b>{data['job_sub']}</b>\n"
                    f"🚗 Mashina: <b>{data['car_brand']} {data['car_model']}</b>\n"
                    f"🔑 VIN: <code>{data['vin']}</code>\n"
                    f"📅 Sana: {now}",
                    parse_mode="HTML"
                )
            except Exception:
                pass


@router.callback_query(JobStates.confirm, F.data == "job_cancel")
async def cancel_job(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("❌ Ish yaratish bekor qilindi.")
    await cb.answer()
