import logging
import os
from datetime import datetime, time
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

logger = logging.getLogger("utils")
logger.setLevel(logging.DEBUG)

log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "utils.log")
file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")

file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
logger.debug("Логгер инициализирован и готов к работе")

def filter_transactions_by_date(transactions: List[Dict], date_str: str) -> List[Dict]:
    """
    Фильтрует транзакции по дате операции.
    Принимает дату в формате 'ДД.ММ.ГГГГ'.
    Возвращает операции с начала месяца по указанную дату включительно.
    """
    logger.debug(f"Начинаем фильтрацию транзакций по дате: {date_str}")
    input_date = datetime.strptime(date_str, "%d.%m.%Y")
    start_date = datetime.combine(input_date.replace(day=1).date(), time.min)
    end_date = datetime.combine(input_date.date(), time.max)

    filtered_list = []
    for transaction in transactions:
        try:
            raw_date = transaction["Дата операции"]
            if not isinstance(raw_date, str):
                logger.warning(f"Неверный формат даты операции: {raw_date} (не строка)")
                continue
            operation_date = datetime.strptime(raw_date, "%d.%m.%Y %H:%M:%S")

            if start_date <= operation_date <= end_date:
                filtered_list.append(transaction)
        except (KeyError, ValueError):
            logger.warning(f"Ошибка при обработке транзакции {transaction.get('id', '')}: {e}")
            continue
    logger.debug(f"Отфильтровано транзакций: {len(filtered_list)} из {len(transactions)}")
    return filtered_list


def get_greeting() -> str:
    """Программа приветствует в зависимости от текущего времени."""
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        greeting = "Доброе утро!"
    elif 12 <= current_hour < 18:
        greeting = "Добрый день!"
    elif 18 <= current_hour < 23:
        greeting = "Добрый вечер!"
    else:
        greeting = "Доброй ночи!"
    logger.debug(f"Выдано приветствие: {greeting}")
    return greeting


def get_cards_summary(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Возвращает список словарей с данными по каждой карте.
    """
    logger.debug("Начинаем подсчет данных по картам")
    cards_summary: Dict[str, float] = {}

    for transaction in transactions:
        if (
            isinstance(transaction.get("Номер карты"), str)
            and transaction.get("Статус") != "FAILED"
            and isinstance(transaction.get("Сумма операции"), (int, float))
            and transaction["Сумма операции"] < 0
        ):
            card = transaction["Номер карты"][-4:]
            amount = -transaction["Сумма операции"]

            cards_summary[card] = cards_summary.get(card, 0) + amount

    result = []
    for last_digits, total_spent in cards_summary.items():
        result.append(
            {
                "last_digits": last_digits,
                "total_spent": round(total_spent, 2),
                "cashback": round(total_spent * 0.01, 2),
            }
        )
    logger.debug(f"Подсчитано данных по картам: {len(result)}")
    return result


def get_top_transactions(transactions: List[Dict], top_n: int = 5) -> List[Dict]:
    """
    Возвращает топ-N транзакций с наибольшими расходами.
    Учитываются только транзакции со статусом 'OK' и отрицательной суммой.
    """
    logger.debug(f"Получаем топ {top_n} транзакций по расходам")
    filtered = [
        transaction
        for transaction in transactions
        if transaction.get("Статус") == "OK"
        and isinstance(transaction.get("Сумма операции"), (int, float))
        and transaction["Сумма операции"] < 0
    ]
    sorted_tx = sorted(filtered, key=lambda x: abs(x["Сумма операции"]), reverse=True)
    top_transactions = []
    for i in sorted_tx[:top_n]:
        top_transactions.append(
            {
                "date": i.get("Дата платежа", ""),
                "amount": round(abs(i["Сумма операции"]), 2),
                "category": i.get("Категория", ""),
                "description": i.get("Описание", ""),
            }
        )
    logger.debug(f"Сформирован список топ транзакций: {len(top_transactions)}")
    return top_transactions


def get_currency_rates(currencies: List[str], base: str = "RUB") -> List[Dict[str, float]]:
    """
    Получает курсы заданных валют по отношению к базовой валюте (по умолчанию RUB).
    """
    logger.debug(f"Запрос курсов валют: {currencies} относительно {base}")
    load_dotenv()
    API_KEY = os.getenv("API_KEY")

    url = f"https://financialmodelingprep.com/api/v3/fx?apikey={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.debug("Получены данные с API курсов валют")
    except Exception as e:
        logger.error(f"Ошибка при запросе валютных курсов: {e}")
        return []

    results = []
    for currency in currencies:
        pair = f"{currency}/RUB"
        match = next((item for item in data if item.get("ticker") == pair), None)
        if match and "ask" in match:
            results.append({"currency": currency, "rate": round(match["ask"], 4)})
            logger.debug(f"Найден курс для {pair}: {match['ask']}")
        else:
            logger.warning(f"Не найден курс для {pair}")

    return results


def get_stock_prices(stocks: List[str]) -> List[Dict[str, float]]:
    """
    Получает текущие цены акций по списку тикеров.
    """
    logger.debug(f"Запрос цен акций для: {stocks}")
    if not stocks:
        logger.debug("Список акций пуст, возвращаем пустой список")
        return []

    load_dotenv()
    API_KEY = os.getenv("API_KEY")

    symbols = ",".join(stocks)
    url = f"https://financialmodelingprep.com/api/v3/quote/{symbols}?apikey={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.debug("Получены данные с API цен акций")
    except Exception as e:
        logger.error(f"Ошибка при запросе цен акций: {e}")
        return []

    results = []
    for item in data:
        if "symbol" in item and "price" in item:
            results.append({"stock": item["symbol"], "price": round(item["price"], 2)})
            logger.debug(f"Цена акции {item['symbol']}: {item['price']}")
        else:
            logger.warning(f"Данные отсутствуют для {item.get('symbol', 'неизвестного тикера')}")

    return results
