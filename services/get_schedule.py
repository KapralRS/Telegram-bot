import pandas as pd
import re
import os
from pathlib import Path
from typing import List


def load_schedule(file_path):
    """Загружает расписание из Excel-файла."""
    try:
        df = pd.read_excel(file_path, sheet_name=0, header=None)
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return None
    return df.values


def find_classes(header_row):
    """Находит классы в строке заголовков (индекс 2) по шаблону цифра+буква."""
    class_pattern = re.compile(r"^\d+[a-zA-Zа-яА-Я]?$")
    classes = {}
    for col in range(3, len(header_row)):
        val = header_row[col]
        if pd.notna(val):
            s = str(val).strip()
            if s and s not in ("№", "Время") and class_pattern.match(s):
                classes[s] = col
    return classes


def get_classes_from_file(date_file: str) -> List[str]:
    """
    Получает список классов из файла расписания по дате.

    Args:
        date_file: название файла с датой (например, "28_февраля")

    Returns:
        список классов, найденных в файле
    """
    file_path = Path("data\schedule_files") / f"{date_file}.xls"
    if not file_path.exists():
        # Пробуем без расширения .xls
        file_path = Path("data\schedule_files") / date_file
        if not file_path.exists():
            return []

    data = load_schedule(file_path)
    if data is None:
        return []

    header_row = data[2]  # строка с классами (индекс 2)
    classes_dict = find_classes(header_row)

    # Возвращаем отсортированный список классов
    return sorted(
        classes_dict.keys(),
        key=lambda x: (
            int(re.match(r"\d+", x).group()) if re.match(r"\d+", x) else 0,
            x,
        ),
    )


def is_likely_teacher(text):
    """Проверяет, похожа ли строка на имя учителя (содержит точку или двоеточие)."""
    if not isinstance(text, str):
        return False
    if ":" in text:
        return True
    if "." in text:
        parts = text.split(".")
        if len(parts) >= 2 and all(len(p.strip()) > 0 for p in parts if p):
            return True
    return False


def parse_teacher_info(cell):
    """Разбирает ячейку с учителем: если это учитель, возвращает (имя, подгруппа), иначе (None, None)."""
    if pd.isna(cell):
        return None, None
    text = str(cell).strip()
    if text == "/" or text == "":
        return None, None
    if ":" in text:
        parts = text.split(":", 1)
        return parts[0].strip(), parts[1].strip()
    if is_likely_teacher(text):
        return text, ""
    return None, None


def format_cabinet(cab):
    """Преобразует номер кабинета в читаемый вид, убирая .0, если это целое число."""
    if pd.isna(cab):
        return ""
    s = str(cab).strip()
    try:
        if "." in s:
            f = float(s)
            if f.is_integer():
                return str(int(f))
    except:
        pass
    return s


def get_schedule_text(data, class_name, start_col, end_col):
    """
    Возвращает строку с расписанием для указанного класса.
    """
    lines = []
    lines.append(f"        📋 РАСПИСАНИЕ {class_name.upper()} КЛАССА")
    lines.append("\n" + "-" * 60)

    # Собираем строки с номерами уроков (поддерживаем уроки с 1 по 13)
    lesson_rows = []
    lesson_numbers = []

    for r in range(3, len(data)):
        val = data[r, 1]  # столбец B - номер урока
        if pd.notna(val):
            try:
                # Пробуем разные способы преобразования
                if isinstance(val, (int, float)):
                    num = int(val)
                else:
                    # Пробуем извлечь число из строки
                    str_val = str(val).strip()
                    match = re.search(r"\d+", str_val)
                    if match:
                        num = int(match.group())
                    else:
                        continue

                # Поддерживаем уроки с 1 по 13
                if 1 <= num <= 13:
                    lesson_rows.append(r)
                    lesson_numbers.append(num)
                    print(f"Найден урок {num} в строке {r}")
            except (ValueError, TypeError, AttributeError):
                continue

    if not lesson_rows:
        lines.append("Не найдены уроки.")
        return "\n".join(lines)

    # Сортируем уроки по номеру
    sorted_lessons = sorted(zip(lesson_numbers, lesson_rows))

    for lesson_num, row in sorted_lessons:
        time = data[row, 2]
        main_subject = data[row, start_col]

        if pd.isna(main_subject):
            main_subject = ""
        else:
            main_subject = str(main_subject).strip()

        # Собираем информацию для вывода
        lesson_lines = []
        has_data = False

        # Добавляем строку с номером урока и временем
        lesson_lines.append("-" * 60 + "\n" + f"🔹 УРОК {lesson_num} | {time}")
        if main_subject:
            has_data = True
            lesson_lines.append(f"   📖 Предмет: {main_subject}")
        else:
            lesson_lines.append("   📖 Предмет: (нет основного предмета)")

        # Перебираем дополнительные колонки (подгруппы)
        for col in range(start_col + 1, end_col):
            teacher_cell = data[row, col]
            cabinet_cell = data[row + 1, col] if row + 1 < len(data) else None

            teacher, subgroup = parse_teacher_info(teacher_cell)
            cabinet = format_cabinet(cabinet_cell)

            if teacher is not None:
                has_data = True
                msg = f"     👫 Подгруппа {subgroup if subgroup else ''}: {teacher}"
                if cabinet:
                    msg += f"\n         🚪 Кабинет: {cabinet}"
                lesson_lines.append(msg)
            elif cabinet:
                has_data = True
                lesson_lines.append(f"   🚪 Кабинет: {cabinet}")

        lesson_lines.append("-" * 60)

        # Если нет никаких данных – пропускаем урок
        if has_data:
            lines.extend(lesson_lines)

    return "\n".join(lines)


def get_schedule(clas: str, date_file: str = None) -> str:
    """
    Возвращает расписание для указанного класса из файла по дате.

    Args:
        clas: название класса (например, "10а")
        date_file: название файла с датой (например, "28_февраля")

    Returns:
        строка с расписанием
    """
    # Определяем путь к файлу
    if date_file:
        # Если передана дата, ищем файл в папке SchoolSchedule
        file_path = Path("data\schedule_files") / f"{date_file}.xls"
        if not file_path.exists():
            # Пробуем без расширения .xls (если дата уже содержит расширение)
            file_path = Path("data\schedule_files") / date_file
            if not file_path.exists():
                return f"Файл для даты {date_file} не найден."
    else:
        return "❌ Не удалось загрузить расписание. Попробуйте, позже."

    data = load_schedule(file_path)
    if data is None:
        return f"Ошибка при загрузке файла {file_path}"

    header_row = data[2]  # строка с классами (индекс 2)
    classes = find_classes(header_row)

    if not classes:
        return "❌ Не удалось найти классы в файле."

    if clas not in classes:
        return f"❌ Класс {clas} не найден в расписании."

    # Сортируем классы по колонкам для правильного определения границ
    sorted_classes = sorted(classes.items(), key=lambda x: x[1])
    class_list = [name for name, _ in sorted_classes]
    class_cols = [col for _, col in sorted_classes]

    idx = class_list.index(clas)
    start_col = class_cols[idx]
    # конечная колонка – начало следующего класса или конец таблицы
    if idx + 1 < len(class_cols):
        end_col = class_cols[idx + 1]
    else:
        end_col = data.shape[1]

    schedule_text = get_schedule_text(data, clas, start_col, end_col)
    return schedule_text
