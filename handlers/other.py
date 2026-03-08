from aiogram import Router
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from services.log_in_file import logging_in_file
from handlers.reply_to_me import reply_to_me

router = Router()


@router.message()
async def process_send_copy(message: Message):
    try:
        await logging_in_file(
            id=message.from_user.id,
            first_name=message.chat.first_name,
            username=message.chat.username,
            text=message.text,
        )
        await reply_to_me(message=message)
        await message.send_copy(
            chat_id=message.chat.id,
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Расписание")]], resize_keyboard=True
            ),
        )
    except Exception as e:
        print(e)
        await message.reply(
            "Данный вид сообщений не поддерживается!",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Расписание")]], resize_keyboard=True
            ),
        )
