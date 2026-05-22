"""Хендлеры: /start, /help, главное меню, профиль."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.repository import UserRepo, ResumeRepo, SearchHistoryRepo
from bot.keyboards import Keyboards

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    repo = UserRepo(session)
    user, created = await repo.get_or_create(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    name = message.from_user.first_name or "Привет"
    if created:
        text = (
            f"Добро пожаловать, {name}!\n\n"
            "Я помогу подобрать вакансии на основе вашего резюме.\n\n"
            "Начните с загрузки резюме — отправьте файл (PDF, DOCX, DOC, TXT) "
            "или введите текст резюме вручную."
        )
    else:
        text = f"С возвращением, {name}! Чем могу помочь?"
    await message.answer(text, reply_markup=Keyboards.main_menu())


@router.message(Command("help"))
@router.message(F.text == "❓ Помощь")
async def cmd_help(message: Message, state: FSMContext) -> None:
    await state.clear()
    text = (
        "<b>Как использовать бота:</b>\n\n"
        "1. <b>Загрузить резюме</b> — отправьте файл или текст резюме\n"
        "2. <b>Найти вакансии</b> — бот сопоставит резюме с вакансиями HH.ru\n"
        "3. <b>Анализ навыков</b> — узнайте, каких навыков не хватает\n\n"
        "<b>Поддерживаемые форматы:</b> PDF, DOCX, DOC, TXT\n"
        "<b>Макс. размер файла:</b> 10 МБ\n\n"
        "<b>Команды:</b>\n"
        "/start — главное меню\n"
        "/help — эта справка\n"
        "/profile — мой профиль\n"
        "/cancel — отменить текущее действие"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=Keyboards.main_menu())


@router.message(Command("cancel"))
@router.message(F.text == "❌ Отмена")
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    await state.clear()
    if current:
        await message.answer("Действие отменено.", reply_markup=Keyboards.main_menu())
    else:
        await message.answer("Главное меню.", reply_markup=Keyboards.main_menu())


@router.message(Command("profile"))
@router.message(F.text == "👤 Мой профиль")
async def cmd_profile(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    user_repo = UserRepo(session)
    resume_repo = ResumeRepo(session)
    history_repo = SearchHistoryRepo(session)

    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Используйте /start для регистрации.")
        return

    resume = await resume_repo.get_latest(user.id)
    history = await history_repo.get_recent(user.id, limit=3)

    lines = [f"<b>👤 Профиль: {user.first_name or 'Без имени'}</b>"]
    lines.append(f"Telegram ID: <code>{user.telegram_id}</code>")
    lines.append(f"Дата регистрации: {user.created_at.strftime('%d.%m.%Y')}")

    if resume:
        parsed = resume.parsed_data or {}
        skills = parsed.get("skills", [])
        position = parsed.get("desired_position") or "не указана"
        lines.append(f"\n<b>📄 Резюме загружено:</b> {resume.updated_at.strftime('%d.%m.%Y')}")
        lines.append(f"Желаемая должность: {position}")
        lines.append(f"Навыки ({len(skills)}): {', '.join(skills[:10]) or 'не определены'}")
    else:
        lines.append("\n<b>📄 Резюме не загружено</b>")

    if history:
        lines.append("\n<b>🔍 Последние поиски:</b>")
        for h in history:
            params = h.query_params or {}
            pos = params.get("position", "—")
            lines.append(f"• {h.created_at.strftime('%d.%m %H:%M')} — {pos} ({h.results_count} вакансий)")

    await message.answer("\n".join(lines), parse_mode="HTML", reply_markup=Keyboards.profile_actions())


@router.callback_query(F.data == "update_resume")
async def cb_update_resume(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    from bot.states import ResumeStates
    await state.set_state(ResumeStates.waiting_for_resume)
    await callback.message.answer(
        "Отправьте новое резюме (файл или текст):",
        reply_markup=Keyboards.cancel(),
    )
