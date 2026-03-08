from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.filters import Command, or_f, and_f
from services.log_in_file import logging_in_file
from services.scheduler import get_files
from services.get_schedule import get_classes_from_file, get_schedule
from .reply_to_me import reply_to_me
from lexicon.lexicon import LEXICON
from states.states import States
from aiogram.fsm.context import FSMContext
from aiogram import F, Router
import logging

logger = logging.getLogger(__name__)

router = Router()


@router.message(
    or_f(
        and_f(States.waiting_for_class, F.text.in_("Назад")),
        F.text.in_({"Расписание"}),
        Command(commands="schedule"),
    )
)
async def send_schedule(message: Message, state: FSMContext):
    await logging_in_file(
        id=message.from_user.id,
        first_name=message.chat.first_name,
        username=message.chat.username,
        text=message.text,
    )
    await reply_to_me(message=message)

    dates = await get_files()

    dates_buttons = []
    for date in dates:
        dates_buttons.append([KeyboardButton(text=date)])
    dates_buttons.append([KeyboardButton(text="Назад")])

    await message.answer(
        "Выберите дату и смену.",
        reply_markup=ReplyKeyboardMarkup(keyboard=dates_buttons),
    )
    await state.set_state(States.waiting_for_date)


@router.message(States.waiting_for_date)
async def process_date_input(message: Message, state: FSMContext):
    await logging_in_file(
        id=message.from_user.id,
        first_name=message.chat.first_name,
        username=message.chat.username,
        text=message.text,
    )
    await reply_to_me(message=message)

    selected_date = message.text
    await state.update_data(selected_date=selected_date)

    date_for_file = selected_date.replace(" ", "_")

    classes_list = get_classes_from_file(date_for_file)

    if not classes_list:
        await message.answer(
            "Не удалось найти классы в выбранном файле. Попробуйте другую дату.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Расписание")]], resize_keyboard=True
            ),
        )
        await state.clear()
        return

    buttons = [KeyboardButton(text=clas) for clas in classes_list]
    kb_builder = ReplyKeyboardBuilder()
    kb_builder.row(*buttons, width=5)
    kb_builder.add(KeyboardButton(text="Назад"))

    await message.answer(
        f"Выберите класс.",
        reply_markup=kb_builder.as_markup(resize_keyboard=True),
    )
    await state.set_state(States.waiting_for_class)


@router.message(States.waiting_for_class)
async def process_clas_input(message: Message, state: FSMContext):
    await logging_in_file(
        id=message.from_user.id,
        first_name=message.chat.first_name,
        username=message.chat.username,
        text=message.text,
    )
    await reply_to_me(message=message)

    data = await state.get_data()
    selected_date = data.get("selected_date")

    date_for_file = selected_date.replace(" ", "_")
    schedule = get_schedule(message.text, date_for_file)

    await message.reply(
        schedule,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Расписание")]],
            resize_keyboard=True,
        ),
    )
    await state.clear()
