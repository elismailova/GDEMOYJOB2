"""Хендлеры загрузки и обработки резюме."""
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states import ResumeStates
from bot.keyboards import Keyboards
from config import config
from services.resume_service import ResumeService

logger = logging.getLogger(__name__)
router = Router()

_ALLOWED_EXTS = {"pdf", "docx", "doc", "txt"}


@router.message(F.text == "📄 Загрузить резюме")
async def start_resume_upload(message: Message, state: FSMContext) -> None:
    await state.set_state(ResumeStates.waiting_for_resume)
    await message.answer(
        "Отправьте резюме одним из способов:\n"
        "• Прикрепите файл (PDF, DOCX, DOC, TXT, макс. 10 МБ)\n"
        "• Введите текст резюме прямо в сообщение",
        reply_markup=Keyboards.cancel(),
    )


@router.message(ResumeStates.waiting_for_resume, F.document)
async def handle_resume_file(
    message: Message, bot: Bot, session: AsyncSession, state: FSMContext
) -> None:
    doc = message.document
    filename = doc.file_name or "resume.txt"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in _ALLOWED_EXTS:
        await message.answer(
            f"Формат .{ext} не поддерживается.\n"
            "Используйте: PDF, DOCX, DOC или TXT.",
            reply_markup=Keyboards.cancel(),
        )
        return

    if doc.file_size > config.MAX_FILE_SIZE_BYTES:
        await message.answer(
            "Файл слишком большой. Максимальный размер — 10 МБ.",
            reply_markup=Keyboards.cancel(),
        )
        return

    processing_msg = await message.answer("Обрабатываю файл...")

    try:
        file = await bot.get_file(doc.file_id)
        file_bytes = await bot.download_file(file.file_path)
        raw_bytes = file_bytes.read() if hasattr(file_bytes, "read") else bytes(file_bytes)

        service = ResumeService(session)
        parsed = await service.process_file(
            telegram_id=message.from_user.id,
            file_bytes=raw_bytes,
            filename=filename,
        )
        await _send_parse_result(message, parsed)
        await state.clear()

    except ValueError as e:
        await message.answer(f"Ошибка обработки файла: {e}", reply_markup=Keyboards.cancel())
    except Exception as e:
        logger.exception("Resume file processing error: %s", e)
        await message.answer(
            "Произошла ошибка при обработке файла. Попробуйте ещё раз.",
            reply_markup=Keyboards.cancel(),
        )
    finally:
        try:
            await bot.delete_message(message.chat.id, processing_msg.message_id)
        except Exception:
            pass


@router.message(ResumeStates.waiting_for_resume, F.text)
async def handle_resume_text(
    message: Message, session: AsyncSession, state: FSMContext
) -> None:
    text = message.text.strip()
    if text in ("❌ Отмена",):
        return  # обрабатывается cancel-хендлером выше по стеку

    if len(text) < 50:
        await message.answer(
            "Текст резюме слишком короткий (менее 50 символов). "
            "Пожалуйста, введите полный текст резюме.",
            reply_markup=Keyboards.cancel(),
        )
        return

    processing_msg = await message.answer("Анализирую резюме...")

    try:
        service = ResumeService(session)
        parsed = await service.process_text(
            telegram_id=message.from_user.id,
            text=text,
        )
        await _send_parse_result(message, parsed)
        await state.clear()

    except Exception as e:
        logger.exception("Resume text processing error: %s", e)
        await message.answer(
            "Произошла ошибка. Попробуйте ещё раз.",
            reply_markup=Keyboards.cancel(),
        )
    finally:
        try:
            await message.bot.delete_message(message.chat.id, processing_msg.message_id)
        except Exception:
            pass


async def _send_parse_result(message: Message, parsed: dict) -> None:
    skills = parsed.get("skills", [])
    position = parsed.get("desired_position") or "не определена"
    level = parsed.get("experience_level") or "не определён"
    years = parsed.get("years_of_experience")
    education = parsed.get("education", [])

    years_str = f"{years} лет" if years else "не определён"

    lines = [
        "Резюме успешно загружено!\n",
        f"<b>Желаемая должность:</b> {position}",
        f"<b>Уровень:</b> {level}",
        f"<b>Опыт:</b> {years_str}",
    ]

    if education:
        lines.append(f"<b>Образование:</b> {education[0]}")

    if skills:
        skill_preview = ", ".join(skills[:15])
        if len(skills) > 15:
            skill_preview += f" и ещё {len(skills) - 15}..."
        lines.append(f"<b>Навыки ({len(skills)}):</b> {skill_preview}")
    else:
        lines.append("<b>Навыки:</b> не распознаны автоматически")

    lines.append("\nТеперь вы можете найти подходящие вакансии!")

    await message.answer(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=Keyboards.main_menu(),
    )
