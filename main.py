from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ContentType
from Ollama import chat_ollama
from loggin import logging_in_file
from datetime import datetime
import base64, os


API_URL = "https://api.telegram.org/bot"
BOT_TOKEN = ""


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command(commands="start"))
async def process_start_command(message: Message):
    print(message.model_dump_json(indent=4, exclude_none=True))
    await logging_in_file(
        message.from_user.id,
        message.chat.first_name,
        message.chat.username,
        "Нажал на start",
    )
    await reply_to_me(message=message)
    if message.from_user.username == "o_kak_mory":
        await message.answer(
            "Здарова, Егорка (Воздухан)! Когда с моим создателем назначишь встречу в дс?"
        )
    else:
        await message.answer(
            f"Привет, {message.from_user.first_name}!\nКак я могу тебе помочь?"
        )


@dp.message(Command(commands="help"))
async def process_help_command(message: Message):
    print(message.model_dump_json(indent=4, exclude_none=True))
    await logging_in_file(
        message.from_user.id,
        message.chat.first_name,
        message.chat.username,
        "Нажал на help",
    )
    await reply_to_me(message=message)
    await message.answer(
        "Я помогу могу помочь тебе в решении различных вопросов.\nОтправь мне текст запроса и/или изображение и я постараюсь тебе помочь!"
    )


@dp.message(F.text)
async def send_answer(message: Message):
    try:
        print(message.model_dump_json(indent=4, exclude_none=True))

        await logging_in_file(
            message.from_user.id,
            message.chat.first_name,
            message.chat.username,
            message.text,
        )
        await reply_to_me(message=message)

        await message.reply(await chat_ollama(message.text))
    except:
        await message.reply(
            "Чет не могу ничего придумать...\nСформулируй запрос по-другому."
        )


@dp.message(F.photo)
async def send_answer(message: Message):
    try:
        await bot.send_chat_action(message.chat.id, action="typing")
        print(message.model_dump_json(indent=4, exclude_none=True))

        file_id = message.photo[-1].file_id
        photo = await bot.get_file(file_id=file_id)

        temp_file_path = os.path.join("photos", f"{file_id}.jpg")

        await bot.download_file(photo.file_path, destination=temp_file_path)

        with open(temp_file_path, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode("utf-8")

        await logging_in_file(
            message.from_user.id,
            message.chat.first_name,
            message.chat.username,
            message.caption,
        )
        await reply_to_me(message=message)

        await message.reply(await chat_ollama(message.caption, img_base64))
    except Exception as e:
        print(e)
        await message.reply(
            "Чет не могу ничего придумать...\nСформулируй запрос по-другому."
        )


@dp.message()
async def send_copy(message: Message):
    try:
        await bot.send_chat_action(message.chat.id, action="typing")
        print(message.model_dump_json(indent=4, exclude_none=True))
        await logging_in_file(
            message.from_user.id,
            message.chat.first_name,
            message.chat.username,
            message.text,
        )

        await reply_to_me(message=message)

        await message.send_copy(chat_id=message.chat.id)
    except:
        await message.reply("Данный вид сообщений не поддерживается!")


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
Дата: {datetime.now()}
Пользователь: {message.from_user.first_name}, {message.from_user.username}
Текст: {text}
------------------
    """

    if photo_url:
        await bot.send_photo(chat_id=1874550541, photo=photo_url, caption=text)
    else:
        await bot.send_message(chat_id=1874550541, text=text)


if __name__ == "__main__":
    dp.run_polling(bot)
