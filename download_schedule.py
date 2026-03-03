# download_schedule.py
from scheduler import file_cache
from typing import List


async def get_files() -> List[str]:
    """
    Получает список доступных файлов расписания.
    Файлы автоматически обновляются каждый час.

    Returns:
        список названий файлов без расширения (например: "28 февраля 1 смена")
    """
    return await file_cache.get_files()


async def force_update_files() -> List[str]:
    """
    Принудительно обновляет файлы расписания.
    Можно использовать для админ-команд.

    Returns:
        список обновленных файлов
    """
    return await file_cache.force_update()
