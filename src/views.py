import json
from datetime import datetime
from typing import Any, Dict

from src.utils import (filter_transactions_by_date, get_cards_summary, get_currency_rates, get_greeting,
                       get_stock_prices, get_top_transactions, load_excel_transactions, load_user_settings)


def generate_report(date_str: str) -> str:
    """
    Главная функция: принимает дату (YYYY-MM-DD HH:MM:SS),
    возвращает JSON-строку с аналитикой.
    """
    input_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    formatted_date = input_date.strftime("%d.%m.%Y")

    transactions = load_excel_transactions("../data/operations.xlsx")
    settings = load_user_settings("../user_settings.json")
    currencies = settings.get("user_currencies", [])
    stocks = settings.get("user_stocks", [])

    filtered = filter_transactions_by_date(transactions, formatted_date)

    report_data: Dict[str, Any] = {
        "greeting": get_greeting(),
        "cards": get_cards_summary(filtered),
        "top_transactions": get_top_transactions(filtered),
        "currency_rates": get_currency_rates(currencies),
        "stock_prices": get_stock_prices(stocks),
    }

    json_result = json.dumps(report_data, ensure_ascii=False, indent=2)
    return json_result
