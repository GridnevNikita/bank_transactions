import json
from datetime import datetime
from typing import Any, Dict

from src.data_loader import load_excel_transactions, load_user_settings
from src.utils import (filter_transactions_by_date, get_cards_summary, get_currency_rates, get_greeting,
                       get_stock_prices, get_top_transactions)


def generate_report(date_str: str) -> str:
    """
    Главная функция: принимает дату (YYYY-MM-DD HH:MM:SS),
    возвращает JSON-строку с аналитикой.
    """
    # Преобразуем дату
    input_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    formatted_date = input_date.strftime("%d.%m.%Y")

    # Загружаем данные
    transactions = load_excel_transactions("../data/operations.xlsx")
    settings = load_user_settings("../user_settings.json")
    currencies = settings.get("user_currencies", [])
    stocks = settings.get("user_stocks", [])

    # Фильтрация транзакций по дате
    filtered = filter_transactions_by_date(transactions, formatted_date)

    # Сбор данных в словарь
    report_data: Dict[str, Any] = {
        "greeting": get_greeting(),
        "cards": get_cards_summary(filtered),
        "top_transactions": get_top_transactions(filtered),
        "currency_rates": get_currency_rates(currencies),
        "stock_prices": get_stock_prices(stocks),
    }

    # Преобразование в JSON-строку
    json_result = json.dumps(report_data, ensure_ascii=False, indent=2)
    return json_result


# if __name__ == "__main__":
#     input_date = "2021-12-31 23:59:59"
#     result = generate_report(input_date)
#     print(result)
