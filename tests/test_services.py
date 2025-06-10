import json
from typing import Any, Dict, List

import pandas as pd
import pytest

from src.services import (get_bonus_categories, investment_bank, search_by_phone_number, search_transactions,
                          search_transfers_to_individuals)


@pytest.fixture
def sample_transactions() -> List[Dict[str, Any]]:
    return [
        {"Описание": "Покупка в магазине", "Категория": "Супермаркеты"},
        {"Описание": "Перевод другу", "Категория": "Переводы"},
        {"Описание": "Оплата связи", "Категория": "Связь"},
        {"Описание": "Кофе в кафе", "Категория": "Рестораны"},
        {"Описание": None, "Категория": "Переводы"},
        {"Описание": "Покупка телефона", "Категория": None},
    ]


@pytest.mark.parametrize(
    "query, expected_count",
    [
        ("пере", 2),  # должно найти 2: "Перевод другу" и категория "Переводы"
        ("магазин", 1),  # 1 совпадение в описании
        ("", 0),  # пустой запрос — пустой список
        ("кофе", 1),  # 1 совпадение
        ("нет", 0),  # нет совпадений
        ("Покупка", 2),  # в описании "Покупка в магазине" и "Покупка телефона"
    ],
)
def test_search_transactions(sample_transactions, query, expected_count):
    result_json = search_transactions(sample_transactions, query)
    result = json.loads(result_json)
    assert isinstance(result, list)
    assert len(result) == expected_count


@pytest.fixture
def phone_transactions() -> List[Dict[str, Any]]:
    return [
        {"Описание": "Пополнение телефона +7 911 198-78-58", "Категория": "Связь"},
        {"Описание": "Перевод другу +7-985-111-11-11", "Категория": "Переводы"},
        {"Описание": "Оплата услуги", "Категория": "Услуги"},
        {"Описание": "Звонок +7 (903) 123 45 67", "Категория": "Связь"},
        {"Описание": "+79111234567", "Категория": "Связь"},
        {"Описание": None, "Категория": "Связь"},
        {"Описание": "Номер телефона 8 800 555 35 35", "Категория": "Справка"},
    ]


@pytest.mark.parametrize("expected_count", [4])
def test_search_by_phone_number(phone_transactions, expected_count):
    result_json = search_by_phone_number(phone_transactions)
    result = json.loads(result_json)

    assert isinstance(result, list)
    assert len(result) == expected_count


@pytest.fixture
def individual_transfer_transactions() -> List[Dict[str, Any]]:
    return [
        {"Описание": "Валерий А.", "Категория": "Переводы"},
        {"Описание": "Сергей З.", "Категория": "переводы"},
        {"Описание": "Артем П.", "Категория": "Перевод физ лицу"},
        {"Описание": "ООО Ромашка", "Категория": "Перевод"},
        {"Описание": "Кофе с собой", "Категория": "Кафе"},
        {"Описание": None, "Категория": "перевод"},
        {"Описание": "Николай П.", "Категория": None},
        {"Описание": "Валентина С.", "Категория": "ПЕРЕВОДЫ"},
    ]


@pytest.mark.parametrize("expected_count", [3])
def test_search_transfers_to_individuals(individual_transfer_transactions, expected_count):
    result_json = search_transfers_to_individuals(individual_transfer_transactions)
    result = json.loads(result_json)
    assert isinstance(result, list)
    assert len(result) == expected_count


@pytest.fixture
def cashback_transactions() -> List[Dict[str, Any]]:
    return [
        {"Дата операции": "15.06.2023 12:00:00", "Категория": "Фастфуд", "Кэшбэк": 50.5},
        {"Дата операции": "20.06.2023 15:30:00", "Категория": "Фастфуд", "Кэшбэк": pd.NA},
        {"Дата операции": "05.06.2023 09:00:00", "Категория": "Аптеки", "Кэшбэк": pd.NA},
        {"Дата операции": "10.05.2023 14:00:00", "Категория": "Аптеки", "Кэшбэк": 10},
        {"Дата операции": "25.06.2023 18:00:00", "Категория": "Различные товары", "Кэшбэк": 30},
    ]


@pytest.mark.parametrize(
    "year, month, expected_result",
    [
        (2023, 6, {"Фастфуд": 50, "Различные товары": 30}),
        (2023, 5, {"Аптеки": 10}),
        (2023, 7, {}),
    ],
)
def test_get_bonus_categories(cashback_transactions, year, month, expected_result):
    result_json = get_bonus_categories(cashback_transactions, year, month)
    result = json.loads(result_json)
    assert isinstance(result, dict)
    assert result == expected_result


@pytest.fixture
def investment_bank_transactions() -> List[Dict[str, Any]]:
    return [
        {"Дата операции": "15.10.2018 12:00:00", "Сумма операции": -1712.0, "Категория": "Фастфуд", "Статус": "OK"},
        {"Дата операции": "20.10.2018 15:30:00", "Сумма операции": -49.0, "Категория": "Переводы", "Статус": "OK"},
        {"Дата операции": "05.10.2018 09:00:00", "Сумма операции": 1000.0, "Категория": "Аптеки", "Статус": "OK"},
        {
            "Дата операции": "10.09.2018 14:00:00",
            "Сумма операции": -118.12,
            "Категория": "Различные товары",
            "Статус": "FAILED",
        },
        {
            "Дата операции": "25.10.2018 18:00:00",
            "Сумма операции": -38.0,
            "Категория": float("nan"),  # nan категория
            "Статус": "OK",
        },
        {"Дата операции": "30.10.2018 21:00:00", "Сумма операции": -60.0, "Категория": "Развлечения", "Статус": "OK"},
    ]


@pytest.mark.parametrize(
    "month, limit, expected_savings",
    [
        ("2018-10", 10, {"total_savings": 8, "limit": 10, "month": "2018-10"}),
        ("2018-10", 50, {"total_savings": 78, "limit": 50, "month": "2018-10"}),
        ("2018-10", 100, {"total_savings": 128, "limit": 100, "month": "2018-10"}),
        ("2018-09", 10, {"total_savings": 0, "limit": 10, "month": "2018-09"}),
    ],
)
def test_investment_bank(investment_bank_transactions, month, limit, expected_savings):
    result_json = investment_bank(month, investment_bank_transactions, limit)
    result = json.loads(result_json)
    assert isinstance(result, dict)
    assert abs(result == expected_savings)


def test_investment_bank_invalid_limit(investment_bank_transactions):
    with pytest.raises(ValueError):
        investment_bank("2018-10", investment_bank_transactions, 15)
