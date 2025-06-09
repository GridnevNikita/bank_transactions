import json
import os
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional

import pandas as pd
from dateutil.relativedelta import relativedelta


def save_report(func: Callable) -> Callable:
    """
    Декоратор оборачивает функцию, которая возвращает JSON-строку (список словарей).
    Сохраняет данные как CSV-файл в папку 'data'.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        result = func(*args, **kwargs)

        if not isinstance(result, str):
            raise TypeError(f"Ожидается JSON-строка, а получен {type(result)}")

        try:
            data = json.loads(result)
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка при декодировании JSON: {e}")

        if not isinstance(data, (list, dict)):
            raise ValueError("Ожидается JSON, содержащий список или словарь")

        if isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            df = pd.DataFrame(data)

        # Путь до корня проекта (на уровень выше src)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        filename = f"report_{func.__name__}.csv"
        filepath = os.path.join(data_dir, filename)

        df.to_csv(filepath, index=False)
        return result

    return wrapper


def save_report_to(filename: str) -> Callable:
    """
    Декоратор: принимает название файла, затем оборачивает функцию,
    которая возвращает JSON-строку (список словарей).
    Сохраняет данные как CSV-файл в папку 'data'.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)

            if not isinstance(result, str):
                raise TypeError(f"Ожидается JSON-строка, а получен {type(result)}")

            try:
                data = json.loads(result)
            except json.JSONDecodeError as e:
                raise ValueError(f"Ошибка при декодировании JSON: {e}")

            if not isinstance(data, list):
                raise ValueError("Ожидается список словарей в JSON-строке")

            if isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                df = pd.DataFrame(data)

            # Путь до папки 'data' на уровень выше текущего файла
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data")

            # Создаём папку, если её нет
            os.makedirs(data_dir, exist_ok=True)

            filepath = os.path.join(data_dir, filename)
            df.to_csv(filepath, index=False, encoding="utf-8-sig")

            return result  # Возвращаем ту же JSON-строку

        return wrapper

    return decorator


# @save_report_to("my_report.csv")
@save_report
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> str:
    """
    Возвращает JSON со списком трат по заданной категории
    за последние 3 календарных месяца до указанной даты (или текущей).
    """
    if date is None:
        date_dt = datetime.now()
    else:
        date_dt = datetime.strptime(date, "%Y-%m-%d")

    start_date = date_dt - relativedelta(months=3)

    df = transactions.copy()

    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")

    filtered = df[
        (df["Категория"] == category)
        & (df["Дата операции"] >= start_date)
        & (df["Дата операции"] <= date_dt)
        & (df["Сумма операции"] < 0)
        & (df["Статус"] == "OK")
    ]

    filtered = filtered[["Дата операции", "Категория", "Сумма операции"]]
    filtered["Дата операции"] = filtered["Дата операции"].dt.strftime("%Y-%m-%d")

    filtered = filtered.reset_index(drop=True)
    result = filtered.to_dict(orient="records")
    return json.dumps(result, ensure_ascii=False, indent=2)


# @save_report_to("my_report.csv")
@save_report
def spending_by_weekday(transactions: pd.DataFrame, date: Optional[str] = None) -> str:
    """
    Возвращает JSON со средними тратами по дням недели за последние 3 календарных месяца от переданной даты.
    Если дата не указана, берётся текущая дата.
    """
    if date is None:
        date_dt = datetime.now()
    else:
        date_dt = datetime.strptime(date, "%Y-%m-%d")

    start_date = date_dt - relativedelta(months=3)

    df = transactions.copy()

    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")

    filtered = df[
        (df["Дата операции"] >= start_date)
        & (df["Дата операции"] <= date_dt)
        & (df["Сумма операции"] < 0)
        & (df["Статус"] == "OK")
    ].copy()

    filtered["День недели"] = filtered["Дата операции"].dt.day_name()

    result = filtered.groupby("День недели")["Сумма операции"].mean().abs()

    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    result = result.reindex(weekday_order).fillna(0)

    result_list = [{"День недели": day, "Средние траты": round(result[day], 2)} for day in weekday_order]

    return json.dumps(result_list, ensure_ascii=False, indent=2)


@save_report
def spending_by_workday(transactions: pd.DataFrame, date: Optional[str] = None) -> str:
    """
    Возвращает JSON со средними тратами в рабочий и выходной день за последние 3 календарных месяца от переданной даты.
    Если дата не указана, берётся текущая дата.
    """
    if date is None:
        date_dt = datetime.now()
    else:
        date_dt = datetime.strptime(date, "%Y-%m-%d")

    start_date = date_dt - relativedelta(months=3)
    df = transactions.copy()
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")
    filtered = df[
        (df["Дата операции"] >= start_date)
        & (df["Дата операции"] <= date_dt)
        & (df["Статус"] == "OK")
        & (df["Категория"] != "Переводы")
        & (df["Сумма операции"] < 0)
    ].copy()

    filtered["Рабочий день"] = filtered["Дата операции"].dt.weekday < 5
    result = filtered.groupby("Рабочий день")["Сумма операции"].mean().abs()
    avg_weekday = round(result.get(True, 0), 2)
    avg_weekend = round(result.get(False, 0), 2)
    result_dict = {"Средние траты в рабочий день": avg_weekday, "Средние траты в выходной день": avg_weekend}

    return json.dumps(result_dict, ensure_ascii=False, indent=2)


# if __name__ == "__main__":
#     df = pd.read_excel("../data/operations.xlsx")
#     spending_by_category(df, category="Супермаркеты", date="2019-05-06")
#     spending_by_weekday(df, date="2019-05-06")
#     spending_by_workday(df, date="2019-05-06")
