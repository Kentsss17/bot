from aiogram import Router, F
from aiogram.types import Message

from config import ADMIN_IDS
from database import get_statistics

router = Router()


@router.message(F.text == "📊 Statistika")
async def show_stats(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    s = await get_statistics()

    top5_text = ""
    for i, row in enumerate(s["top5"], 1):
        top5_text += f"  {i}. {row[0]} | {row[1] or '—'} | ✅{row[2]} 🔄{row[3]}\n"
    if not top5_text:
        top5_text = "  Hali ma'lumot yo'q\n"

    text = (
        f"📊 <b>Statistika</b>\n\n"
        f"📅 <b>Bugun:</b>\n"
        f"  • Yangi ishlar: <b>{s['today_created']}</b>\n"
        f"  • Bajarilgan: <b>{s['today_done']}</b>\n\n"
        f"📆 <b>Bu oy:</b>\n"
        f"  • Bajarilgan: <b>{s['month_done']}</b>\n\n"
        f"📈 <b>Jami:</b>\n"
        f"  • Bajarilgan ishlar: <b>{s['total_done']}</b>\n"
        f"  • Faol (ochiq) ishlar: <b>{s['active_jobs']}</b>\n"
        f"  ⏳ Kutilmoqda: <b>{s['pending_count']}</b> ta ariza\n\n"
        f"🏆 <b>Top-5 ishchilar:</b>\n{top5_text}"
    )
    await msg.answer(text, parse_mode="HTML")


@router.message(F.text == "⚙️ Sozlamalar")
async def settings(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    from config import ADMIN_IDS as AIDS
    await msg.answer(
        f"⚙️ <b>Sozlamalar</b>\n\n"
        f"🤖 Bot: @ishchitabib_bot\n"
        f"👤 Admin IDlar:\n"
        + "\n".join([f"  • <code>{aid}</code>" for aid in AIDS]) +
        f"\n\n💡 ID olish uchun: @userinfobot",
        parse_mode="HTML"
    )
