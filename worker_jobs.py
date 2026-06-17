from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from config import ADMIN_IDS
from database import (
    get_worker_by_tg, get_jobs_for_worker,
    get_job_by_id, get_jw_by_id, update_jw_status, get_worker_by_id
)
from keyboards import job_action_kb, worker_menu

router = Router()


class RejectJobStates(StatesGroup):
    reason = State()


@router.message(F.text == "📋 Mening ishlarim")
async def my_jobs(msg: Message):
    worker = await get_worker_by_tg(msg.from_user.id)
    if not worker or worker["status"] != "approved":
        return

    jobs = await get_jobs_for_worker(worker["id"])
    if not jobs:
        await msg.answer("📭 Hozircha tayinlangan ishingiz yo'q.")
        return

    await msg.answer(f"📋 <b>Sizning ishlaringiz</b> ({len(jobs)} ta):", parse_mode="HTML")

    for j in jobs:
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        text = (
            f"🚗 <b>{j['car_brand']} {j['car_model']}</b>\n"
            f"🔧 {j['job_type']}\n"
            f"📌 {j['job_sub']}\n"
            f"🔑 VIN: <code>{j['vin_code']}</code>\n"
            f"📝 {j['note']}\n"
            f"📅 {j['created_at'][:16] if j['created_at'] else now}"
        )
        await msg.answer(text, reply_markup=job_action_kb(j["jw_id"]), parse_mode="HTML")


@router.callback_query(F.data.startswith("done_"))
async def job_done(cb: CallbackQuery, bot):
    jw_id = int(cb.data.replace("done_", ""))
    jw = await get_jw_by_id(jw_id)
    if not jw:
        await cb.answer("Topilmadi!")
        return

    job = await get_job_by_id(jw["job_id"])
    worker = await get_worker_by_id(jw["worker_id"])
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    await update_jw_status(jw_id, "Bajarildi")
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.edit_text(
        cb.message.text + "\n\n✅ <b>Bajarildi!</b>",
        parse_mode="HTML"
    )
    await cb.answer("✅ Bajarildi deb belgilandi!")

    # Adminlarga xabar
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"✅ <b>Ish bajarildi!</b>\n\n"
                f"👷 Ishchi: <b>{worker['full_name']}</b>\n"
                f"🔧 Ish turi: <b>{job['job_type']}</b>\n"
                f"📌 Qo'shimcha: <b>{job['job_sub']}</b>\n"
                f"🚗 Mashina: <b>{job['car_brand']} {job['car_model']}</b>\n"
                f"🔑 VIN kod: <code>{job['vin_code']}</code>\n"
                f"🕐 Vaqt: {now}",
                parse_mode="HTML"
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("reject_job_"))
async def job_reject_start(cb: CallbackQuery, state: FSMContext):
    jw_id = int(cb.data.replace("reject_job_", ""))
    await state.update_data(reject_jw_id=jw_id)
    await cb.message.answer("❌ <b>Rad etish sababini kiriting:</b>", parse_mode="HTML")
    await state.set_state(RejectJobStates.reason)
    await cb.answer()


@router.message(RejectJobStates.reason)
async def job_reject_reason(msg: Message, state: FSMContext):
    data = await state.get_data()
    jw_id = data["reject_jw_id"]

    await update_jw_status(jw_id, "Rad etildi", reject_reason=msg.text.strip())
    await msg.answer("✅ Ish rad etildi va sabab saqlandi.")
    await state.clear()
