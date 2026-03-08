import aiohttp, asyncio

OLLAMA_URL = "http://localhost:11434/api/generate"


async def chat_ollama(text: str | None = None, img=None, model="gemma3:4b") -> str:
    try:
        if not text:
            text = "Опиши это изображение"

        payload = {
            "model": model,
            "prompt": text + "\n\nОтветь на русском языке.",
            "stream": False,
        }

        if img:
            payload["images"] = [img]

        async with aiohttp.ClientSession() as session:
            async with session.post(OLLAMA_URL, json=payload) as response:

                if response.status != 200:
                    return f"Ошибка в API ламы: {response.status}"

                result = await response.json()
                print(result.get("response"))
                return result.get("response")
    except asyncio.TimeoutError:
        print("Ошибка: Превышен таймаут ожидания")
        return "Проблемы с подключением, попробуйте повторить попытку позднее..."
    except aiohttp.ClientError as e:
        print(f"Ошибка соединения: {e}")
        return "Проблемы с подключением, попробуйте повторить попытку позднее..."
    except Exception as e:
        print(f"Ошибка в Ламе: {e}")
        return "Проблемы с подключением, попробуйте повторить попытку позднее..."
