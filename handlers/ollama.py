from aiogram import F, Router, Bot
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup

from services.log_in_file import logging_in_file
from .reply_to_me import reply_to_me
from external_services.ollama import chat_ollama

import os, base64, logging

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text)
async def send_answer(message: Message):
    try:
        print(message.model_dump_json(indent=4, exclude_none=True))

        await logging_in_file(
            id=message.from_user.id,
            first_name=message.chat.first_name,
            username=message.chat.username,
            text=message.text,
        )
        await reply_to_me(message=message)

        await message.reply(
            await chat_ollama(message.text),
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Расписание")]]
            ),
        )
    except:
        await message.reply(
            "Чет не могу ничего придумать...\nСформулируй запрос по-другому.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Расписание")]]
            ),
        )


@router.message(F.photo)
async def send_answer(message: Message, bot: Bot):
    try:
        await bot.send_chat_action(message.chat.id, action="typing")
        print(message.model_dump_json(indent=4, exclude_none=True))

        file_id = message.photo[-1].file_id
        photo = await bot.get_file(file_id=file_id)

        photos_dir = os.path.join("data", "photos")
        os.makedirs(photos_dir, exist_ok=True)

        temp_file_path = os.path.join(photos_dir, f"{file_id}.jpg")

        await bot.download_file(photo.file_path, destination=temp_file_path)

        with open(temp_file_path, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode("utf-8")

        await logging_in_file(
            id=message.from_user.id,
            first_name=message.chat.first_name,
            username=message.chat.username,
            text=message.text,
        )
        await reply_to_me(message=message)

        await message.reply(
            await chat_ollama(message.caption, img_base64),
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Расписание")]]
            ),
        )
    except Exception as e:
        logger.error(e)
        await message.reply(
            "Чет не могу ничего придумать...\nСформулируй запрос по-другому.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Расписание")]]
            ),
        )
