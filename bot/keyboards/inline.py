"""Все inline- и reply-клавиатуры бота."""
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from integrations.trudvsem_api import TRUDVSEM_AREAS, TRUDVSEM_EXPERIENCE, TRUDVSEM_EMPLOYMENT


class Keyboards:

    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        kb = ReplyKeyboardBuilder()
        kb.button(text="🔍 Найти вакансии")
        kb.button(text="📄 Загрузить резюме")
        kb.button(text="👤 Мой профиль")
        kb.button(text="❓ Помощь")
        kb.adjust(2)
        return kb.as_markup(resize_keyboard=True)

    @staticmethod
    def cancel() -> ReplyKeyboardMarkup:
        kb = ReplyKeyboardBuilder()
        kb.button(text="❌ Отмена")
        return kb.as_markup(resize_keyboard=True)

    @staticmethod
    def skip_or_cancel() -> ReplyKeyboardMarkup:
        kb = ReplyKeyboardBuilder()
        kb.button(text="⏭ Пропустить")
        kb.button(text="❌ Отмена")
        kb.adjust(2)
        return kb.as_markup(resize_keyboard=True)

    @staticmethod
    def remove() -> ReplyKeyboardRemove:
        return ReplyKeyboardRemove()

    @staticmethod
    def area_selection() -> ReplyKeyboardMarkup:
        kb = ReplyKeyboardBuilder()
        for name in TRUDVSEM_AREAS.keys():
            kb.button(text=name)
        kb.button(text="⏭ Пропустить")
        kb.button(text="❌ Отмена")
        kb.adjust(2)
        return kb.as_markup(resize_keyboard=True)

    @staticmethod
    def experience_selection() -> ReplyKeyboardMarkup:
        kb = ReplyKeyboardBuilder()
        for name in TRUDVSEM_EXPERIENCE.keys():
            kb.button(text=name)
        kb.button(text="⏭ Пропустить")
        kb.button(text="❌ Отмена")
        kb.adjust(2)
        return kb.as_markup(resize_keyboard=True)

    @staticmethod
    def employment_selection() -> ReplyKeyboardMarkup:
        kb = ReplyKeyboardBuilder()
        for name in TRUDVSEM_EMPLOYMENT.keys():
            kb.button(text=name)
        kb.button(text="Удалённо")
        kb.button(text="⏭ Пропустить")
        kb.button(text="❌ Отмена")
        kb.adjust(2)
        return kb.as_markup(resize_keyboard=True)

    @staticmethod
    def results_navigation(total: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        # Кнопки с номерами вакансий
        for i in range(total):
            builder.button(text=str(i + 1), callback_data=f"vac:{i}")
        builder.adjust(5)
        # Нижний ряд
        builder.row(
            InlineKeyboardButton(text="📊 Анализ навыков", callback_data="skill_gap"),
            InlineKeyboardButton(text="🔄 Новый поиск", callback_data="new_search"),
        )
        return builder.as_markup()

    @staticmethod
    def vacancy_detail(idx: int, total: int, hh_url: str) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        nav: list[InlineKeyboardButton] = []
        if idx > 0:
            nav.append(InlineKeyboardButton(text="◀ Пред.", callback_data=f"vac:{idx - 1}"))
        if idx < total - 1:
            nav.append(InlineKeyboardButton(text="След. ▶", callback_data=f"vac:{idx + 1}"))
        if nav:
            builder.row(*nav)
        builder.row(InlineKeyboardButton(text="🔍 Найти похожие на TrudVsem", url=hh_url))
        builder.row(
            InlineKeyboardButton(text="📊 Анализ навыков", callback_data="skill_gap"),
            InlineKeyboardButton(text="◀ К списку", callback_data="results_list"),
        )
        return builder.as_markup()

    @staticmethod
    def skill_gap_back() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="◀ К результатам", callback_data="results_list")
        builder.button(text="🔄 Новый поиск", callback_data="new_search")
        return builder.as_markup()

    @staticmethod
    def profile_actions() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Обновить резюме", callback_data="update_resume")
        builder.button(text="📜 История поисков", callback_data="search_history")
        return builder.as_markup()
