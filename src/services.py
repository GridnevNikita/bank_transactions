import os
from typing import Dict, List

import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")


def get_currency_rates(currencies: List[str], base: str = "RUB") -> List[Dict[str, float]]:
    """
    Получает курсы заданных валют по отношению к базовой валюте (по умолчанию RUB).
    """
    url = f"https://financialmodelingprep.com/api/v3/fx?apikey={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Ошибка при запросе валютных курсов: {e}")
        return []

    results = []
    for currency in currencies:
        pair = f"{currency}/RUB"
        match = next((item for item in data if item.get("ticker") == pair), None)
        if match and "ask" in match:
            results.append({"currency": currency, "rate": round(match["ask"], 4)})
        else:
            print(f"Не найден курс для {pair}")

    return results


def get_stock_prices(stocks: List[str]) -> List[Dict[str, float]]:
    """
    Получает текущие цены акций по списку тикеров.
    """
    if not stocks:
        return []

    symbols = ",".join(stocks)
    url = f"https://financialmodelingprep.com/api/v3/quote/{symbols}?apikey={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Ошибка при запросе цен акций: {e}")
        return []

    results = []
    for item in data:
        if "symbol" in item and "price" in item:
            results.append({"stock": item["symbol"], "price": round(item["price"], 2)})
        else:
            print(f"Данные отсутствуют для {item.get('symbol', 'неизвестного тикера')}")

    return results


if __name__ == "__main__":
    from data_loader import load_user_settings

    settings = load_user_settings("../user_settings.json")
    currencies = settings.get("user_currencies", [])
    stocks = settings.get("user_stocks", [])
    prices = get_stock_prices(stocks)
    result = get_currency_rates(currencies)
    print(result)
    print(prices)
