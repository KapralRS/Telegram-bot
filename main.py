from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, or_f
from aiogram.types import (
    Message,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from ollama import chat_ollama
from log_in_file import logging_in_file
from get_schedule import get_schedule, get_classes_from_file
from scheduler import get_files, start_scheduler
from datetime import datetime
from dotenv import load_dotenv
import base64, os
import logging
import asyncio

logging.basicConfig(
    level=logging.INFO,
    format="[{asctime}] #{levelname:8} {filename}:{lineno} - {name} - {message}",
    style="{",
)
logger = logging.getLogger(__name__)

load_dotenv()


bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()


class States(StatesGroup):
    waiting_for_date = State()
    waiting_for_class = State()


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
            text="Здарова, Егорка (Воздухан)! Когда с моим создателем назначишь встречу в дс?",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Расписание")]]
            ),
        )
    else:
        await message.answer(
            f"Привет, {message.from_user.first_name}!\nКак я могу тебе помочь?",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Расписание")]]
            ),
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
        "Я помогу могу помочь тебе в решении различных вопросов.\nОтправь мне текст запроса и/или изображение и я постараюсь тебе помочь!",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Расписание")]]
        ),
    )


@dp.message(or_f(F.text.in_({"Расписание"}), Command(commands="schedule")))
async def send_schedule(message: Message, state: FSMContext):
    await logging_in_file(
        message.from_user.id,
        message.chat.first_name,
        message.chat.username,
        message.text,
    )
    await reply_to_me(message=message)

    dates = await get_files()

    dates_buttons = []
    for date in dates:
        dates_buttons.append([KeyboardButton(text=date)])

    await message.answer(
        "Выберите дату и смену.",
        reply_markup=ReplyKeyboardMarkup(keyboard=dates_buttons),
    )
    await state.set_state(States.waiting_for_date)


@dp.message(States.waiting_for_date)
async def process_date_input(message: Message, state: FSMContext):
    await logging_in_file(
        message.from_user.id,
        message.chat.first_name,
        message.chat.username,
        message.text,
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
                keyboard=[[KeyboardButton(text="Расписание")]]
            ),
        )
        await state.clear()
        return

    classes_buttons = []
    row = []
    for i, class_name in enumerate(classes_list):
        row.append(KeyboardButton(text=class_name))
        if (i + 1) % 3 == 0 or i == len(classes_list) - 1:
            classes_buttons.append(row)
            row = []

    await message.answer(
        f"Выберите класс.",
        reply_markup=ReplyKeyboardMarkup(keyboard=classes_buttons),
    )
    await state.set_state(States.waiting_for_class)


@dp.message(States.waiting_for_class)
async def process_clas_input(message: Message, state: FSMContext):
    await logging_in_file(
        message.from_user.id,
        message.chat.first_name,
        message.chat.username,
        message.text,
    )
    await reply_to_me(message=message)

    data = await state.get_data()
    selected_date = data.get("selected_date")

    date_for_file = selected_date.replace(" ", "_")
    schedule = get_schedule(message.text, date_for_file)

    await message.reply(
        schedule,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Расписание")]]
        ),
    )
    await state.clear()


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

        await message.reply(
            await chat_ollama(message.caption, img_base64),
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Расписание")]]
            ),
        )
    except Exception as e:
        print(e)
        await message.reply(
            "Чет не могу ничего придумать...\nСформулируй запрос по-другому.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Расписание")]]
            ),
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

        await message.send_copy(
            chat_id=message.chat.id,
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Расписание")]]
            ),
        )
    except:
        await message.reply(
            "Данный вид сообщений не поддерживается!",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Расписание")]]
            ),
        )


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


async def on_startup():
    """Действия при запуске бота"""
    logger.info("Запуск бота...")
    await start_scheduler()
    logger.info("Планировщик ежечасного скачивания активирован")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(on_startup())

    logger.info("Бот запущен и готов к работе")
    dp.run_polling(bot)
