import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger("services")
logger.setLevel(logging.DEBUG)

log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "services.log")
file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")

file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
logger.debug("Логгер инициализирован и готов к работе")


def get_bonus_categories(data: List[Dict], year: int, month: int) -> str:
    """
    Анализ выгодных категорий повышенного кешбэка.
    """
    logger.debug(f"Запущен анализ кешбэка за {month:02}.{year}")
    cashback_by_category: Dict[str, float] = {}

    for i in data:
        date_str = i["Дата операции"]
        date = datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")

        if date.year != year or date.month != month:
            continue

        category = i["Категория"]
        cashback = i.get("Кэшбэк", 0)
        if pd.isna(cashback):
            cashback = 0

        cashback_by_category[category] = cashback_by_category.get(category, 0) + cashback
    cashback_by_category_filtered = {k: v for k, v in cashback_by_category.items() if v != 0}
    cashback_by_category_rounded = dict(
        sorted(((k, round(v)) for k, v in cashback_by_category_filtered.items()), key=lambda x: x[1], reverse=True)
    )
    logger.info(f"Завершён анализ кешбэка: найдено {len(cashback_by_category_rounded)} c выгодным кэшбэком")
    return json.dumps(cashback_by_category_rounded, ensure_ascii=False, indent=4)


def investment_bank(month: str, investment_transactions: List[Dict[str, Any]], input_limit: int) -> str:
    """
    Показывает накопления через округление ваших трат за указанный период.
    """
    logger.debug(f"Запущена функция Инвесткопилки за период {month}, с лимитом {input_limit}")
    if input_limit not in (10, 50, 100):
        logger.error(f"Неверный порог округления: {input_limit}")
        raise ValueError("Порог округления limit должен быть одним из: 10, 50, 100")

    total_savings = 0.0

    month_date = datetime.strptime(month, "%Y-%m")
    year = month_date.year
    my_month = month_date.month

    for transaction in investment_transactions:
        date_str = transaction.get("Дата операции")
        amount = transaction.get("Сумма операции")
        category = transaction.get("Категория")
        status = transaction.get("Статус")

        if pd.isna(category):
            continue

        if status == "FAILED" or (amount is not None and amount >= 0) or category == "Переводы":
            continue

        if not isinstance(date_str, str) or amount is None:
            continue

        transaction_date = datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")

        if transaction_date.year != year or transaction_date.month != my_month:
            continue

        rounded = ((-amount + input_limit - 1) // input_limit) * input_limit
        saving = rounded + amount
        total_savings += saving
    total_savings_rounded = round(total_savings, 2)
    logger.info(f"Всего накоплено в инвесткопилку: {round(total_savings, 2)} при пороге {input_limit}")
    result = {"Ваши накопления": total_savings_rounded, "Лимит": input_limit, "За период": month}

    return json.dumps(result, ensure_ascii=False)


def search_transactions(query_transactions: List[Dict[str, Any]], input_query: str) -> str:
    """
    Ищет транзакции, где query содержится в 'Описание' или 'Категория' (регистр игнорируется).
    Если query пустая или состоит из пробелов — возвращает пустой список.
    Возвращает JSON-строку со списком найденных транзакций.
    """
    logger.debug(f"Запущена функция поиска транзакций по запросу: '{input_query}'")
    if not input_query or input_query.strip() == "":
        logger.info("Пустой запрос — возвращён пустой список.")
        return json.dumps([], ensure_ascii=False, indent=2)

    search = re.compile(re.escape(input_query) + r"\w*", re.IGNORECASE)
    filtered = []
    for transaction in query_transactions:
        description = transaction.get("Описание")
        category = transaction.get("Категория")

        if (
            isinstance(description, str)
            and search.search(description)
            or isinstance(category, str)
            and search.search(category)
        ):
            filtered.append(transaction)
    logger.info(f"Найдено транзакций по запросу '{input_query}': {len(filtered)}")
    return json.dumps(filtered, ensure_ascii=False, indent=2)


def search_by_phone_number(phone_transactions: List[Dict[str, Any]]) -> str:
    """
    Ищет транзакции, содержащими в описании мобильные номера.
    Возвращает JSON-строку со списком найденных транзакций.
    """
    logger.debug("Запущена функция для поиска транзакций где есть мобильные номера")
    phone_string = re.compile(r"\+7[\s\-()]*\d{3}[\s\-()]*\d{3}[\s\-()]*\d{2}[\s\-()]*\d{2}")
    filtered_numbers = []
    for transaction in phone_transactions:
        description = transaction.get("Описание")
        if isinstance(description, str) and phone_string.search(description):
            filtered_numbers.append(transaction)
    logger.info(f"Найдено транзакций с номером телефона: {len(filtered_numbers)}")
    return json.dumps(filtered_numbers, ensure_ascii=False, indent=2)


def search_transfers_to_individuals(transfers_transactions: List[Dict[str, Any]]) -> str:
    """
    Ищет транзакции, которые относятся к переводам физическим лицам.
    Возвращает JSON-строку со списком найденных транзакций.
    """
    logger.debug("Запущена функция для поиска транзакций переводов физическим лицам")
    person_transfer = re.compile(r"\w+ \w\.", re.IGNORECASE)
    transfer = re.compile(r"^переводы$", re.IGNORECASE)
    filtered_person = []
    for transaction in transfers_transactions:
        description = transaction.get("Описание")
        category = transaction.get("Категория")
        if (
            isinstance(category, str)
            and transfer.search(category)
            and isinstance(description, str)
            and person_transfer.search(description)
        ):
            filtered_person.append(transaction)
    logger.info(f"Найдено транзакций с переводами физическим лицам: {len(filtered_person)}")
    return json.dumps(filtered_person, ensure_ascii=False, indent=2)


# if __name__ == "__main__":
#     from utils import load_excel_transactions
#
#     transactions = load_excel_transactions("../data/operations.xlsx")
#     # print(get_bonus_categories(transactions, 2018, 4))
#     for limit in (10, 50, 100):
#         print(investment_bank("2018-10", transactions, limit))
#     # query = "маГНИТ"
#     # print(search_transactions(transactions, query))
#     # print(search_by_phone_number(transactions))
#     # print(search_transfers_to_individuals(transactions))
