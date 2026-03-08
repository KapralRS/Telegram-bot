from aiogram import Router, F
from aiogram.filters import Command, or_f, and_f
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup

from services.log_in_file import logging_in_file
from .reply_to_me import reply_to_me
from lexicon.lexicon import LEXICON
from states.states import States

router = Router()


@router.message(
    or_f(and_f(States.waiting_for_date, F.text.in_("Назад")), Command(commands="start"))
)
async def process_start_command(message: Message):
    print(message.model_dump_json(indent=4, exclude_none=True))
    await logging_in_file(
        id=message.from_user.id,
        first_name=message.chat.first_name,
        username=message.chat.username,
        text="Нажал на start",
    )
    await reply_to_me(message=message)

    await message.answer(
        f"Привет, {message.from_user.first_name}!\nКак я могу тебе помочь?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Расписание")]], resize_keyboard=True
        ),
    )


@router.message(Command(commands="help"))
async def process_help_command(message: Message):
    print(message.model_dump_json(indent=4, exclude_none=True))
    await logging_in_file(
        id=message.from_user.id,
        first_name=message.chat.first_name,
        username=message.chat.username,
        text="Нажал на help",
    )
    await reply_to_me(message=message)
    await message.answer(
        LEXICON["/help"],
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Расписание")]], resize_keyboard=True
        ),
    )
