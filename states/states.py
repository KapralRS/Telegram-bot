from aiogram.fsm.state import State, StatesGroup


class States(StatesGroup):
    waiting_for_date = State()
    waiting_for_class = State()
