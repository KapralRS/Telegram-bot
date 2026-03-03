from datetime import datetime
import aiofiles
import logging

logging.basicConfig(level=logging.INFO)


async def logging_in_file(id: str, first_name: str, username: str, text: str):
    try:
        async with aiofiles.open("Log.txt", mode="a") as file:
            await file.write(
                f"\n{datetime.now()} id: {id} Имя: {first_name} Имя пользователя: {username} Промт: {text}"
            )
    except Exception as e:
        print(e)
