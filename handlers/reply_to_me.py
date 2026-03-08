from aiogram import Bot
from aiogram.types import Message
from environs import Env

env: Env = Env()

bot = Bot(token=env("BOT_TEST_TOKEN"))


async def reply_to_me(message: Message):
    text: str = None
    photo_url: str = None

    if message.text:
        text = message.text
    elif message.photo[-1]:
        text = message.caption
        photo_url = message.photo[-1].file_id

    text = f"""
------------------
Дата: {message.date}
Пользователь: {message.chat.first_name}, {message.from_user.first_name}, {message.from_user.username}
Текст: {text}
------------------
    """

    if photo_url:
        await bot.send_photo(chat_id=env("CHAT_ID"), photo=photo_url, caption=text)
    else:
        await bot.send_message(chat_id=env("CHAT_ID"), text=text)
