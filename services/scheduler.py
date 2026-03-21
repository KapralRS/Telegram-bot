import aiohttp
import aiofiles
import os
import re
from pathlib import Path
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup
from typing import List, Dict
from datetime import datetime, timedelta
import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class ScheduleDownloader:
    """Класс для скачивания файлов расписания"""

    def __init__(self, save_dir: str = "/tmp/schedule_files"):
        self.save_dir = save_dir
        self.downloaded_files = []
        self.last_download_time = None
        self.is_downloading = False
        Path(save_dir).mkdir(parents=True, exist_ok=True)

    async def download_schedule_files(self) -> List[str]:
        """
        Скачивает файлы расписания с сайта школы.
        """
        if self.is_downloading:
            logger.info("Скачивание уже выполняется, пропускаем...")
            return self.downloaded_files

        self.is_downloading = True
        try:
            logger.info(
                f"Начинаю скачивание файлов в {datetime.now().strftime('%H:%M:%S')}..."
            )

            base_url = "https://sh40-cherepovec-r19.gosweb.gosuslugi.ru"
            page_url = f"{base_url}/roditelyam-i-uchenikam/izmeneniya-v-raspisanii/"

            downloaded_files = []
            seen_urls = set()

            async with aiohttp.ClientSession() as session:
                async with session.get(page_url) as response:
                    if response.status != 200:
                        logger.error(f"Ошибка загрузки страницы: {response.status}")
                        return self.downloaded_files

                    html = await response.text()

                soup = BeautifulSoup(html, "html.parser")
                file_block = soup.find("div", class_="tpl-block-2973-list")

                if not file_block:
                    logger.error("Блок с файлами не найден")
                    return self.downloaded_files

                file_objects = file_block.find_all("div", class_="object-item")
                file_info_map: Dict[str, dict] = {}

                for obj in file_objects:
                    link = obj.find("a", href=True)
                    if not link or not link["href"].endswith(".xls"):
                        continue

                    href = link["href"]
                    full_url = urljoin(base_url, href)

                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)

                    filename = unquote(href.split("/")[-1])

                    # Ищем русское название
                    russian_name = None
                    span = obj.find("span")
                    if span and span.text.strip():
                        russian_name = span.text.strip()
                    else:
                        text = obj.get_text(strip=True)
                        if text and not text.endswith(".xls"):
                            russian_name = text

                    if russian_name:
                        russian_name = re.sub(r"[^\w\s-]", "", russian_name)
                        russian_name = re.sub(r"[-\s]+", "_", russian_name)
                        russian_name = russian_name.strip("_")

                    if not russian_name:
                        russian_name = filename.replace(".xls", "").replace("_", " ")

                    file_info_map[full_url] = {
                        "url": full_url,
                        "filename": filename,
                        "russian_name": russian_name,
                        "saved_name": f"{russian_name}.xls",
                    }

                logger.info(f"Найдено уникальных файлов: {len(file_info_map)}")

                # Скачиваем файлы
                new_files_count = 0
                for file_info in file_info_map.values():
                    try:
                        save_path = os.path.join(self.save_dir, file_info["saved_name"])

                        # Проверяем, нужно ли обновить файл
                        need_download = False
                        if not os.path.exists(save_path):
                            need_download = True
                            logger.info(f"Новый файл: {file_info['saved_name']}")
                        else:
                            # Проверяем возраст файла (если старше 1 дня - обновляем)
                            file_time = datetime.fromtimestamp(
                                os.path.getmtime(save_path)
                            )
                            if datetime.now() - file_time > timedelta(days=1):
                                need_download = True
                                logger.info(
                                    f"Обновление файла: {file_info['saved_name']} (старше 1 дня)"
                                )

                        if need_download:
                            async with session.get(file_info["url"]) as response:
                                if response.status == 200:
                                    async with aiofiles.open(save_path, "wb") as f:
                                        await f.write(await response.read())

                                    new_files_count += 1
                                    logger.info(f"Скачан: {file_info['saved_name']}")
                                else:
                                    logger.error(
                                        f"Ошибка скачивания {file_info['filename']}: {response.status}"
                                    )

                        downloaded_files.append(file_info["saved_name"])

                    except Exception as e:
                        logger.error(
                            f"Ошибка при обработке {file_info['filename']}: {e}"
                        )
                        continue

            self.last_download_time = datetime.now()
            self.downloaded_files = downloaded_files

            if new_files_count > 0:
                logger.info(
                    f"Скачивание завершено. Новых файлов: {new_files_count}, всего: {len(downloaded_files)}"
                )
            else:
                logger.info(
                    f"Скачивание завершено. Новых файлов нет. Всего: {len(downloaded_files)}"
                )

            return downloaded_files

        finally:
            self.is_downloading = False

    async def get_file_list_for_display(self) -> List[str]:
        """
        Возвращает список файлов для отображения пользователям.
        """
        if not self.downloaded_files:
            await self.download_schedule_files()

        # Преобразуем названия для отображения
        return [f.replace(".xls", "").replace("_", " ") for f in self.downloaded_files]


class HourlyScheduleScheduler:
    """Планировщик для скачивания файлов каждый час"""

    def __init__(self, downloader: ScheduleDownloader):
        self.downloader = downloader
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    def start(self):
        """Запускает планировщик"""
        if self.is_running:
            logger.warning("Планировщик уже запущен")
            return

        # Добавляем задачу на каждый час
        self.scheduler.add_job(
            self._hourly_download,
            CronTrigger(minute=0),  # Запуск в 00 минут каждого часа
            id="hourly_schedule_download",
            replace_existing=True,
        )

        # Также запускаем сразу при старте
        self.scheduler.add_job(
            self._initial_download,
            trigger="date",
            run_date=datetime.now(),
            id="initial_download",
        )

        self.scheduler.start()
        self.is_running = True
        logger.info(
            "Планировщик запущен. Скачивание будет происходить в начале каждого часа (в 00 минут)"
        )

    async def _hourly_download(self):
        """Задача для ежечасного скачивания"""
        logger.info(f"Запуск планового скачивания в {datetime.now().strftime('%H:%M')}")
        await self.downloader.download_schedule_files()

    async def _initial_download(self):
        """Первоначальное скачивание при запуске"""
        logger.info("Первоначальное скачивание при запуске")
        await self.downloader.download_schedule_files()

    def shutdown(self):
        """Останавливает планировщик"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Планировщик остановлен")


downloader = ScheduleDownloader()
scheduler = HourlyScheduleScheduler(downloader)


async def get_files() -> List[str]:
    """
    Получает список доступных файлов расписания.
    Файлы обновляются автоматически каждый час.
    """
    return await downloader.get_file_list_for_display()


async def start_scheduler():
    """Запускает планировщик (вызывается при старте бота)"""
    scheduler.start()


async def force_update() -> List[str]:
    """Принудительно обновляет файлы"""
    logger.info("Принудительное обновление файлов")
    await downloader.download_schedule_files()
    return await downloader.get_file_list_for_display()
