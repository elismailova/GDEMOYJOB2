"""Хендлеры поиска вакансий и просмотра результатов."""
import re
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states import SearchStates
from bot.keyboards import Keyboards
from integrations.trudvsem_api import TRUDVSEM_AREAS, TRUDVSEM_EXPERIENCE, TRUDVSEM_EMPLOYMENT, TrudvsemApiClient
from services.search_service import SearchService
from services.resume_service import ResumeService

logger = logging.getLogger(__name__)
router = Router()


# ── Запуск поиска ──────────────────────────────────────────────────────────────

@router.message(F.text == "🔍 Найти вакансии")
async def start_search(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    svc = ResumeService(session)
    resume = await svc.get_resume(message.from_user.id)

    if not resume:
        await message.answer(
            "У вас нет загруженного резюме.\n"
            "Сначала загрузите резюме кнопкой «📄 Загрузить резюме».",
            reply_markup=Keyboards.main_menu(),
        )
        return

    parsed = resume.get("parsed") or {}
    position = parsed.get("desired_position") or ""
    await state.update_data(
        resume_text=resume["raw_text"],
        resume_skills=parsed.get("skills", []),
    )
    await state.set_state(SearchStates.waiting_for_position)

    hint = f"Предлагаю: «{position}»" if position else ""
    await message.answer(
        f"Введите желаемую должность для поиска.\n{hint}\n\n"
        "Или нажмите «⏭ Пропустить», чтобы использовать данные резюме.",
        reply_markup=Keyboards.skip_or_cancel(),
    )


# ── FSM: должность → город → зарплата → опыт → занятость → поиск ──────────────

@router.message(SearchStates.waiting_for_position, F.text)
async def step_position(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text == "❌ Отмена":
        await _cancel_search(message, state)
        return

    position = None if text == "⏭ Пропустить" else text
    await state.update_data(position=position)
    await state.set_state(SearchStates.waiting_for_area)
    await message.answer(
        "Выберите город / регион или пропустите:",
        reply_markup=Keyboards.area_selection(),
    )


@router.message(SearchStates.waiting_for_area, F.text)
async def step_area(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text == "❌ Отмена":
        await _cancel_search(message, state)
        return

    area = None
    if text != "⏭ Пропустить":
        area = TRUDVSEM_AREAS.get(text)

    await state.update_data(area=area, area_name=text if area else None)
    await state.set_state(SearchStates.waiting_for_salary)
    await message.answer(
        "Введите минимальный уровень зарплаты (в рублях) или пропустите:",
        reply_markup=Keyboards.skip_or_cancel(),
    )


@router.message(SearchStates.waiting_for_salary, F.text)
async def step_salary(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text == "❌ Отмена":
        await _cancel_search(message, state)
        return

    salary: int | None = None
    if text != "⏭ Пропустить":
        clean = text.replace(" ", "").replace(",", "").replace("₽", "")
        if clean.isdigit():
            salary = int(clean)
        else:
            await message.answer(
                "Введите число, например: 100000",
                reply_markup=Keyboards.skip_or_cancel(),
            )
            return

    await state.update_data(salary=salary)
    await state.set_state(SearchStates.waiting_for_experience)
    await message.answer(
        "Выберите требуемый опыт работы или пропустите:",
        reply_markup=Keyboards.experience_selection(),
    )


@router.message(SearchStates.waiting_for_experience, F.text)
async def step_experience(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text == "❌ Отмена":
        await _cancel_search(message, state)
        return

    experience = TRUDVSEM_EXPERIENCE.get(text) if text != "⏭ Пропустить" else None
    await state.update_data(experience=experience)
    await state.set_state(SearchStates.waiting_for_employment)
    await message.answer(
        "Выберите тип занятости или пропустите:",
        reply_markup=Keyboards.employment_selection(),
    )


@router.message(SearchStates.waiting_for_employment, F.text)
async def step_employment(message: Message, session: AsyncSession, state: FSMContext) -> None:
    text = message.text.strip()
    if text == "❌ Отмена":
        await _cancel_search(message, state)
        return

    employment: str | None = None
    if text != "⏭ Пропустить" and text != "Удалённо":
        employment = TRUDVSEM_EMPLOYMENT.get(text)

    await state.update_data(employment=employment)

    data = await state.get_data()
    await _run_search(message, session, state, data)


# ── Выполнение поиска ──────────────────────────────────────────────────────────

async def _run_search(
    message: Message, session: AsyncSession, state: FSMContext, data: dict
) -> None:
    searching_msg = await message.answer(
        "Ищу вакансии и анализирую соответствие...\n"
        "Это может занять 15–30 секунд.",
        reply_markup=Keyboards.remove(),
    )

    try:
        svc = SearchService(session)
        results = await svc.search(
            telegram_id=message.from_user.id,
            position=data.get("position"),
            area=data.get("area"),
            salary=data.get("salary"),
            experience=data.get("experience"),
            employment=data.get("employment"),
        )

        await state.update_data(
            search_results=results,
            resume_skills=data.get("resume_skills", []),
        )
        await state.set_state(SearchStates.showing_results)

        try:
            await message.bot.delete_message(message.chat.id, searching_msg.message_id)
        except Exception:
            pass

        if not results:
            await message.answer(
                "Подходящих вакансий не найдено.\n"
                "Попробуйте изменить критерии поиска.",
                reply_markup=Keyboards.main_menu(),
            )
            await state.clear()
            return

        await _show_results_list(message, results)

    except RuntimeError as e:
        await message.answer(str(e), reply_markup=Keyboards.main_menu())
        await state.clear()
    except Exception as e:
        logger.exception("Search error: %s", e)
        await message.answer(
            "Произошла ошибка при поиске. Попробуйте позже.",
            reply_markup=Keyboards.main_menu(),
        )
        await state.clear()


async def _show_results_list(message: Message, results: list[dict]) -> None:
    lines = [f"<b>Найдено {len(results)} вакансий</b> (топ-5 наиболее подходящих):\n"]
    for i, r in enumerate(results, 1):
        v = r["vacancy"]
        score_pct = int(r["score"] * 100)
        salary_str = TrudvsemApiClient.format_salary(v.get("salary"))
        area_name = (v.get("area") or {}).get("name", "")
        employer = (v.get("employer") or {}).get("name", "")

        lines.append(
            f"<b>{i}.</b> {v['name']}\n"
            f"    🏢 {employer}  📍 {area_name}\n"
            f"    💰 {salary_str}  ✅ {score_pct}% совпадение\n"
        )

    text = "\n".join(lines)
    if len(text) > 4096:
        text = text[:4090] + "..."

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=Keyboards.results_navigation(len(results)),
    )


# ── Просмотр конкретной вакансии ───────────────────────────────────────────────

@router.callback_query(SearchStates.showing_results, F.data.startswith("vac:"))
@router.callback_query(SearchStates.showing_vacancy_detail, F.data.startswith("vac:"))
async def cb_show_vacancy(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    idx = int(callback.data.split(":")[1])
    data = await state.get_data()
    results: list[dict] = data.get("search_results", [])

    if idx >= len(results):
        await callback.answer("Вакансия не найдена.", show_alert=True)
        return

    r = results[idx]
    v = r["vacancy"]
    score_pct = int(r["score"] * 100)
    matched = r.get("matched_skills", [])
    gap = r.get("skill_gap", [])

    salary_str = TrudvsemApiClient.format_salary(v.get("salary"))
    area = (v.get("area") or {}).get("name", "не указан")
    employer = (v.get("employer") or {}).get("name", "не указан")
    snippet = v.get("snippet", {})
    requirement = snippet.get("requirement") or ""
    responsibility = snippet.get("responsibility") or ""
    vacancy_url = v.get("alternate_url", "https://hh.ru")

    requirement = re.sub(r"<[^>]+>", "", requirement)
    responsibility = re.sub(r"<[^>]+>", "", responsibility)

    lines = [
        f"<b>{v['name']}</b>",
        f"\n🏢 {employer}",
        f"📍 {area}",
        f"💰 {salary_str}",
        f"⭐ Соответствие: <b>{score_pct}%</b>",
    ]

    if matched:
        lines.append(f"\n✅ <b>Совпадающие навыки:</b>\n{', '.join(matched[:12])}")

    if gap:
        lines.append(f"\n❌ <b>Недостающие навыки:</b>\n{', '.join(gap[:8])}")

    if requirement:
        req_short = requirement[:400] + ("..." if len(requirement) > 400 else "")
        lines.append(f"\n📋 <b>Требования:</b>\n{req_short}")

    if responsibility:
        resp_short = responsibility[:300] + ("..." if len(responsibility) > 300 else "")
        lines.append(f"\n📝 <b>Обязанности:</b>\n{resp_short}")

    text = "\n".join(lines)
    if len(text) > 4096:
        text = text[:4090] + "..."

    await state.set_state(SearchStates.showing_vacancy_detail)
    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=Keyboards.vacancy_detail(idx, len(results), vacancy_url),
    )


@router.callback_query(F.data == "results_list")
async def cb_back_to_list(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    results = data.get("search_results", [])
    await state.set_state(SearchStates.showing_results)
    if results:
        await _show_results_list(callback.message, results)
    else:
        await callback.message.answer("Результаты недоступны.", reply_markup=Keyboards.main_menu())


@router.callback_query(F.data == "skill_gap")
async def cb_skill_gap(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    results: list[dict] = data.get("search_results", [])
    resume_skills: list[str] = data.get("resume_skills", [])

    if not results:
        await callback.answer("Нет результатов поиска.", show_alert=True)
        return

    from nlp.matcher import VacancyMatcher
    matcher = VacancyMatcher()
    gap_ranked = matcher.analyze_skill_gap(resume_skills, results)

    lines = ["<b>📊 Анализ дефицита навыков</b>\n"]
    lines.append(f"Ваши навыки ({len(resume_skills)}):\n{', '.join(resume_skills[:15]) or 'не определены'}\n")

    if gap_ranked:
        lines.append("<b>Навыки, которых не хватает для топ-вакансий:</b>")
        for skill, freq in gap_ranked[:15]:
            bar = "█" * min(freq, 5)
            lines.append(f"  {bar} <b>{skill}</b> — встречается в {freq} из {len(results)} вакансий")
        lines.append(
            "\n<i>Рекомендуем начать изучение с навыков в начале списка — "
            "они наиболее востребованы среди подходящих вакансий.</i>"
        )
    else:
        lines.append("Ваши навыки хорошо покрывают требования найденных вакансий!")

    text = "\n".join(lines)
    if len(text) > 4096:
        text = text[:4090] + "..."

    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=Keyboards.skill_gap_back(),
    )


@router.callback_query(F.data == "new_search")
async def cb_new_search(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await callback.message.answer(
        "Главное меню. Начните новый поиск!",
        reply_markup=Keyboards.main_menu(),
    )


# ── Хелперы ────────────────────────────────────────────────────────────────────

async def _cancel_search(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Поиск отменён.", reply_markup=Keyboards.main_menu())
