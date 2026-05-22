from aiogram.fsm.state import State, StatesGroup


class ResumeStates(StatesGroup):
    waiting_for_resume = State()


class SearchStates(StatesGroup):
    waiting_for_position = State()
    waiting_for_area = State()
    waiting_for_salary = State()
    waiting_for_experience = State()
    waiting_for_employment = State()
    showing_results = State()
    showing_vacancy_detail = State()
