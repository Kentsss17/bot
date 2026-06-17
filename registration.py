from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart

from config import ADMIN_IDS
from database import add_worker, get_worker_by_tg, update_worker_status, get_worker_by_id
from keyboards import phone_kb, confirm_kb, approve_worker_kb, worker_menu, admin_menu

router = Router()


class RegStates(StatesGroup):
    name = State()
    age = State()
    phone = State()
    confirm = State()


@router.message(CommandStart())
async def start(msg: Message, state: FSMContext, bot=None):
    await state.clear()
    uid = msg.from_user.id

    if uid in ADMIN_IDS:
        await msg.answer(
            "👨‍💼 <b>Admin paneliga xush kelibsiz!</b>",
            reply_markup=admin_menu(),
            parse_mode="HTML"
        )
        return

    worker = await get_worker_by_tg(uid)
    if worker:
        if worker["status"] == "approved":
            await msg.answer(
                f"👷 Xush kelibsiz, <b>{worker['full_name']}</b>!",
                reply_markup=worker_menu(),
                parse_mode="HTML"
            )
        elif worker["status"] == "pending":
            await msg.answer("⏳ Arizangiz ko'rib chiqilmoqda. Iltimos kuting...")
        elif worker["status"] == "rejected":
            await msg.answer("❌ Arizangiz rad etilgan. Qo'shimcha ma'lumot uchun admin bilan bog'laning.")
        return

    await msg.answer(
        "👋 <b>Elektro Tabib</b> botiga xush kelibsiz!\n\n"
        "Ro'yxatdan o'tish uchun to'liq ismingizni yuboring:",
        parse_mode="HTML"
    )
    await state.set_state(RegStates.name)


@router.message(RegStates.name)
async def reg_name(msg: Message, state: FSMContext):
    if len(msg.text.strip()) < 2:
        await msg.answer("❗ Ism kamida 2 ta belgi bo'lishi kerak. Qayta kiriting:")
        return
    await state.update_data(name=msg.text.strip())
    await msg.answer("🎂 Yoshingizni kiriting (son bilan):")
    await state.set_state(RegStates.age)


@router.message(RegStates.age)
async def reg_age(msg: Message, state: FSMContext):
    try:
        age = int(msg.text.strip())
        if not (14 <= age <= 80):
            raise ValueError
    except ValueError:
        await msg.answer("❗ Yosh 14–80 oralig'ida bo'lishi kerak. Qayta kiriting:")
        return
    await state.update_data(age=age)
    await msg.answer(
        "📱 Telefon raqamingizni yuboring:",
        reply_markup=phone_kb()
    )
    await state.set_state(RegStates.phone)


@router.message(RegStates.phone, F.contact)
async def reg_phone_contact(msg: Message, state: FSMContext):
    phone = msg.contact.phone_number
    await state.update_data(phone=phone)
    await _show_confirm(msg, state)


@router.message(RegStates.phone, F.text)
async def reg_phone_text(msg: Message, state: FSMContext):
    phone = msg.text.strip()
    await state.update_data(phone=phone)
    await _show_confirm(msg, state)


async def _show_confirm(msg: Message, state: FSMContext):
    data = await state.get_data()
    text = (
        f"📋 <b>Ma'lumotlaringiz:</b>\n\n"
        f"👤 Ism: <b>{data['name']}</b>\n"
        f"🎂 Yosh: <b>{data['age']}</b>\n"
        f"📱 Telefon: <b>{data['phone']}</b>\n\n"
        f"Tasdiqlaysizmi?"
    )
    await msg.answer(text, reply_markup=confirm_kb(), parse_mode="HTML")
    await state.set_state(RegStates.confirm)


@router.message(RegStates.confirm, F.text == "✅ Tasdiqlash")
async def reg_confirm(msg: Message, state: FSMContext, bot):
    data = await state.get_data()
    uid = msg.from_user.id

    await add_worker(
        telegram_id=uid,
        full_name=data["name"],
        phone=data["phone"],
        age=data["age"],
        status="pending"
    )

    worker = await get_worker_by_tg(uid)

    await msg.answer(
        "✅ Arizangiz yuborildi! Adminlar ko'rib chiqgach xabar beramiz.",
        reply_markup=__import__('keyboards').remove_kb()
    )
    await state.clear()

    # Adminlarga xabar
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"🆕 <b>Yangi ariza!</b>\n\n"
                f"👤 Ism: <b>{data['name']}</b>\n"
                f"🎂 Yosh: <b>{data['age']}</b>\n"
                f"📱 Telefon: <b>{data['phone']}</b>\n"
                f"🆔 Telegram ID: <code>{uid}</code>",
                reply_markup=approve_worker_kb(worker["id"]),
                parse_mode="HTML"
            )
        except Exception:
            pass


@router.message(RegStates.confirm, F.text == "🔄 Qayta boshlash")
async def reg_restart(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("🔄 Qayta boshlandi. Ismingizni yuboring:")
    await state.set_state(RegStates.name)


# ── ADMIN ariza tasdiqlash ────────────────────────────

@router.callback_query(F.data.startswith("approve_"))
async def approve_worker(cb: CallbackQuery, bot):
    worker_id = int(cb.data.split("_")[1])
    worker = await get_worker_by_id(worker_id)
    if not worker:
        await cb.answer("Ishchi topilmadi!")
        return

    await update_worker_status(worker_id, "approved")
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.edit_text(
        cb.message.text + "\n\n✅ <b>Qabul qilindi</b>",
        parse_mode="HTML"
    )
    await cb.answer("✅ Qabul qilindi!")

    if worker["telegram_id"]:
        try:
            await bot.send_message(
                worker["telegram_id"],
                "🎉 <b>Tabriklaymiz!</b>\n\nArizangiz tasdiqlandi. Endi botdan foydalanishingiz mumkin.",
                reply_markup=worker_menu(),
                parse_mode="HTML"
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("reject_") & ~F.data.startswith("reject_job_"))
async def reject_worker(cb: CallbackQuery, bot):
    worker_id = int(cb.data.split("_")[1])
    worker = await get_worker_by_id(worker_id)
    if not worker:
        await cb.answer("Ishchi topilmadi!")
        return

    await update_worker_status(worker_id, "rejected")
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.edit_text(
        cb.message.text + "\n\n❌ <b>Rad etildi</b>",
        parse_mode="HTML"
    )
    await cb.answer("❌ Rad etildi!")

    if worker["telegram_id"]:
        try:
            await bot.send_message(
                worker["telegram_id"],
                "❌ Arizangiz rad etildi. Qo'shimcha ma'lumot uchun admin bilan bog'laning."
            )
        except Exception:
            pass
