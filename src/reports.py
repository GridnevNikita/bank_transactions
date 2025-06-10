import json
import locale
import logging
import os
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional

import pandas as pd
from dateutil.relativedelta import relativedelta


logger = logging.getLogger("reports")
logger.setLevel(logging.DEBUG)

log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "reports.log")
file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")

file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
logger.debug("Логгер инициализирован и готов к работе")

def auto_name_save_report(func: Callable) -> Callable:
    """
    Декоратор оборачивает функцию, которая возвращает JSON-строку (словарь или список).
    Сохраняет данные как JSON-файл в папку 'reports'.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger.debug(f"Декоратор auto_name_save_report вызвал функцию {func.__name__}")
        result = func(*args, **kwargs)

        if not isinstance(result, str):
            logger.error(f"Функция {func.__name__} вернула не строку, а {type(result)}")
            raise TypeError(f"Ожидается JSON-строка, а получен {type(result)}")

        try:
            data = json.loads(result)
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при декодировании JSON в функции {func.__name__}")
            raise ValueError(f"Ошибка при декодировании JSON: {e}")

        if not isinstance(data, (list, dict)):
            logger.error(f"Функция {func.__name__} вернула JSON не в виде списка или словаря")
            raise ValueError("Ожидается JSON, содержащий список или словарь")

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "reports")
        os.makedirs(data_dir, exist_ok=True)

        filename = f"report_{func.__name__}.json"
        filepath = os.path.join(data_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info(f"Файл {filename} успешно сохранён")

        return result

    return wrapper


def my_name_save_report(filename: str) -> Callable:
    """
    Декоратор: принимает название файла, затем оборачивает функцию,
    которая возвращает JSON-строку (словарь или список).
    Сохраняет данные как JSON-файл в папку 'reports'.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger.debug(f"Декоратор my_name_save_report вызвал функцию {func.__name__}")
            result = func(*args, **kwargs)

            if not isinstance(result, str):
                logger.error(f"Функция {func.__name__} вернула не строку, а {type(result)}")
                raise TypeError(f"Ожидается JSON-строка, а получен {type(result)}")

            try:
                data = json.loads(result)
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка при декодировании JSON в функции {func.__name__}")
                raise ValueError(f"Ошибка при декодировании JSON: {e}")

            if not isinstance(data, (list, dict)):
                logger.error(f"Функция {func.__name__} вернула JSON не в виде списка или словаря")
                raise ValueError("Ожидается список или словарь в JSON-строке")

            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "reports")
            os.makedirs(data_dir, exist_ok=True)

            filepath = os.path.join(data_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info(f"Файл {filename} успешно сохранён")

            return result

        return wrapper

    return decorator


@my_name_save_report("my_report_by_category.json")
@auto_name_save_report
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> str:
    """
    Возвращает JSON со списком трат по заданной категории
    за последние 3 календарных месяца до указанной даты (или текущей).
    """
    logger.debug(f"Анализ категории: {category}, дата: {date}")
    if date is None:
        date_dt = datetime.now()
    else:
        date_dt = datetime.strptime(date, "%Y-%m-%d")

    start_date = date_dt - relativedelta(months=3)
    logger.debug(f"Период фильтрации: {start_date.date()} — {date_dt.date()}")

    df = transactions.copy()

    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")

    filtered = df[
        (df["Категория"] == category)
        & (df["Дата операции"] >= start_date)
        & (df["Дата операции"] <= date_dt)
        & (df["Сумма операции"] < 0)
        & (df["Статус"] == "OK")
    ]
    logger.info(f"Найдено {len(filtered)} транзакций по категории '{category}'")

    filtered = filtered[["Дата операции", "Категория", "Сумма операции"]]
    filtered["Дата операции"] = filtered["Дата операции"].dt.strftime("%Y-%m-%d")

    filtered = filtered.reset_index(drop=True)
    result = filtered.to_dict(orient="records")
    logger.debug(f"Подготовлено {len(result)} записей для JSON-отчёта по категории '{category}'")
    return json.dumps(result, ensure_ascii=False, indent=2)


@my_name_save_report("my_report_by_weekday.json")
@auto_name_save_report
def spending_by_weekday(transactions: pd.DataFrame, date: Optional[str] = None) -> str:
    """
    Возвращает JSON со средними тратами по дням недели за последние 3 календарных месяца от переданной даты.
    Если дата не указана, берётся текущая дата.
    """
    logger.debug(f"Анализ трат по дням недели, дата: {date}")
    if date is None:
        date_dt = datetime.now()
    else:
        date_dt = datetime.strptime(date, "%Y-%m-%d")

    start_date = date_dt - relativedelta(months=3)
    logger.debug(f"Период: {start_date.date()} — {date_dt.date()}")

    df = transactions.copy()

    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")

    filtered = df[
        (df["Дата операции"] >= start_date)
        & (df["Дата операции"] <= date_dt)
        & (df["Сумма операции"] < 0)
        & (df["Статус"] == "OK")
    ].copy()

    logger.info(f"Количество трат за период: {len(filtered)}")

    filtered["День недели"] = filtered["Дата операции"].dt.day_name().map({
        "Monday": "Понедельник",
        "Tuesday": "Вторник",
        "Wednesday": "Среда",
        "Thursday": "Четверг",
        "Friday": "Пятница",
        "Saturday": "Суббота",
        "Sunday": "Воскресенье",
    })

    result = filtered.groupby("День недели")["Сумма операции"].mean().abs()

    weekday_order = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    result = result.reindex(weekday_order).fillna(0)

    result_list = [{"День недели": day, "Средние траты": round(result[day], 2)} for day in weekday_order]
    logger.debug(f"Подготовлено данных по средним тратам за дни недели: {len(result_list)} записей")

    return json.dumps(result_list, ensure_ascii=False, indent=2)


@my_name_save_report("my_report_by_workday.json")
@auto_name_save_report
def spending_by_workday(transactions: pd.DataFrame, date: Optional[str] = None) -> str:
    """
    Возвращает JSON со средними тратами в рабочий и выходной день за последние 3 календарных месяца от переданной даты.
    Если дата не указана, берётся текущая дата.
    """
    logger.debug(f"Анализ трат по типу дня (рабочий/выходной), дата: {date}")
    if date is None:
        date_dt = datetime.now()
    else:
        date_dt = datetime.strptime(date, "%Y-%m-%d")

    start_date = date_dt - relativedelta(months=3)
    logger.debug(f"Период: {start_date.date()} — {date_dt.date()}")
    df = transactions.copy()
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")
    filtered = df[
        (df["Дата операции"] >= start_date)
        & (df["Дата операции"] <= date_dt)
        & (df["Статус"] == "OK")
        & (df["Категория"] != "Переводы")
        & (df["Сумма операции"] < 0)
    ].copy()
    logger.info(f"Количество валидных трат: {len(filtered)}")
    filtered["Рабочий день"] = filtered["Дата операции"].dt.weekday < 5
    result = filtered.groupby("Рабочий день")["Сумма операции"].mean().abs()
    avg_weekday = round(result.get(True, 0), 2)
    avg_weekend = round(result.get(False, 0), 2)
    result_dict = {"Средние траты в рабочий день": avg_weekday, "Средние траты в выходной день": avg_weekend}
    logger.debug(f"Средние траты рассчитаны: рабочие дни = {avg_weekday}, выходные = {avg_weekend}")
    return json.dumps(result_dict, ensure_ascii=False, indent=2)


# if __name__ == "__main__":
#     base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#     data_path = os.path.join(base_dir, "data", "operations.xlsx")
#     df = pd.read_excel(data_path)
#     spending_by_category(df, category="Супермаркеты", date="2019-05-06")
#     spending_by_weekday(df, date="2019-05-06")
#     spending_by_workday(df, date="2019-05-06")
