from datetime import datetime
import aiofiles


async def logging_in_file(id: str, first_name: str, username: str, text: str):
    try:
        async with aiofiles.open("Log.txt", mode="a") as file:
            await file.write(
                f"""
{datetime.now()}
id: {id}
Имя: {first_name}
Имя пользователя: {username}
Промт:\n{text}

------------------

"""
            )
    except Exception as e:
        print(e)
