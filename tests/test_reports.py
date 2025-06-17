import json
from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest
from dateutil.relativedelta import relativedelta

from src.reports import (auto_name_save_report, my_name_save_report, spending_by_category, spending_by_weekday,
                         spending_by_workday)


@pytest.fixture
def spending_by_category_transactions():
    data = {
        "Дата операции": [
            "06.02.2019 12:00:00",  # входит в 3 месяца до 06.05.2019
            "01.01.2019 10:00:00",  # вне диапазона
            "01.04.2019 15:00:00",  # входит
            "02.05.2019 08:00:00",  # входит
        ],
        "Категория": ["Супермаркеты", "Супермаркеты", "Рестораны", "Супермаркеты"],
        "Сумма операции": [-150.0, -200.0, -50.0, 100.0],
        "Статус": ["OK", "OK", "FAILED", "OK"],
    }
    return pd.DataFrame(data)


@pytest.mark.parametrize(
    "category, date_str, expected_records, expected_sums",
    [
        ("Супермаркеты", "2019-05-06", 1, [-150.0]),
        ("Рестораны", "2019-05-06", 0, []),
        ("Супермаркеты", "2019-02-01", 1, [-200.0]),
    ],
)
def test_spending_by_category_parametrized(
    spending_by_category_transactions, category, date_str, expected_records, expected_sums
):
    result_json = spending_by_category(spending_by_category_transactions, category=category, date=date_str)
    result = json.loads(result_json)

    assert len(result) == expected_records

    sums = [item["Сумма операции"] for item in result]
    assert sums == expected_sums

    if expected_records:
        date_dt = datetime.strptime(date_str, "%Y-%m-%d")
        start_date = date_dt - relativedelta(months=3)
        for item in result:
            dt = datetime.strptime(item["Дата операции"], "%Y-%m-%d")
            assert start_date <= dt <= date_dt
            assert item["Категория"] == category
            assert item["Сумма операции"] < 0


@patch("src.reports.datetime")
def test_spending_by_category_with_mocked_now(mock_datetime, spending_by_category_transactions):
    mock_datetime.now.return_value = datetime(2023, 6, 10)
    mock_datetime.strptime = datetime.strptime  # нужно для корректной работы внутри функции

    result_json = spending_by_category(spending_by_category_transactions, category="Супермаркеты")
    result = json.loads(result_json)

    assert isinstance(result, list)
    for item in result:
        assert item["Категория"] == "Супермаркеты"

        assert item["Сумма операции"] < 0

        dt = datetime.strptime(item["Дата операции"], "%Y-%m-%d")
        start_date = datetime(2023, 6, 10) - relativedelta(months=3)
        end_date = datetime(2023, 6, 10)

        assert start_date <= dt <= end_date


@pytest.fixture
def spending_by_weekday_transactions():
    data = {
        "Дата операции": [
            "01.03.2023 10:00:00",  # Среда (-100)
            "02.03.2023 12:00:00",  # Четверг (-200)
            "03.03.2023 14:00:00",  # Пятница (-300)
            "04.03.2023 16:00:00",  # Суббота (-400)
            "05.03.2023 18:00:00",  # Воскресенье (-500)
            "06.03.2023 20:00:00",  # Понедельник (-600)
            "07.03.2023 22:00:00",  # Вторник (-700)
        ],
        "Сумма операции": [-100, -200, -300, -400, -500, -600, -700],
        "Статус": ["OK"] * 7,
    }
    return pd.DataFrame(data)


@pytest.mark.parametrize(
    "date_str, expected_days, expected_values",
    [
        (
            "2023-03-10",
            ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"],
            [600.0, 700.0, 100.0, 200.0, 300.0, 400.0, 500.0],
        ),
    ],
)
def test_spending_by_weekday_parametrized(spending_by_weekday_transactions, date_str, expected_days, expected_values):
    result_json = spending_by_weekday(spending_by_weekday_transactions, date=date_str)
    result = json.loads(result_json)

    days = [item["День недели"] for item in result]
    values = [item["Средние траты"] for item in result]

    assert days == expected_days
    assert values == expected_values


@patch("src.reports.datetime")
def test_spending_by_weekday_with_mocked_now(mock_datetime, spending_by_weekday_transactions):

    mock_datetime.now.return_value = datetime(2025, 6, 10)
    mock_datetime.strptime = datetime.strptime

    result_json = spending_by_weekday(spending_by_weekday_transactions)
    result = json.loads(result_json)

    assert isinstance(result, list)
    assert len(result) == 7

    assert result[0]["День недели"] == "Понедельник"
    assert result[-1]["День недели"] == "Воскресенье"


@pytest.fixture
def spending_by_workday_transactions():
    data = {
        "Дата операции": [
            "01.03.2023 10:00:00",  # Среда (-100)
            "02.03.2023 12:00:00",  # Четверг (-200)
            "03.03.2023 14:00:00",  # Пятница (-300)
            "04.03.2023 16:00:00",  # Суббота (-400)
            "05.03.2023 18:00:00",  # Воскресенье (-500)
            "06.03.2023 20:00:00",  # Понедельник (-600)
            "07.03.2023 22:00:00",  # Вторник (-700)
            "08.03.2023 10:00:00",  # Среда (Переводы -100, игнорируется)
            "09.03.2023 12:00:00",  # Четверг (Не OK -200, игнорируется)
            "10.03.2023 14:00:00",  # Пятница (Положительная 300, игнорируется)
        ],
        "Сумма операции": [-100, -200, -300, -400, -500, -600, -700, -100, -200, 300],
        "Статус": ["OK", "OK", "OK", "OK", "OK", "OK", "OK", "OK", "Failed", "OK"],
        "Категория": [
            "Покупка",
            "Покупка",
            "Покупка",
            "Покупка",
            "Покупка",
            "Покупка",
            "Покупка",
            "Переводы",
            "Покупка",
            "Покупка",
        ],
    }
    return pd.DataFrame(data)


@pytest.mark.parametrize(
    "date_str, expected_weekday, expected_weekend",
    [
        ("2023-03-10", 380.0, 450.0),
    ],
)
def test_spending_by_workday_parametrized(
    spending_by_workday_transactions, date_str, expected_weekday, expected_weekend
):
    result = json.loads(spending_by_workday(spending_by_workday_transactions, date=date_str))
    assert result["Средние траты в рабочий день"] == expected_weekday
    assert result["Средние траты в выходной день"] == expected_weekend


@patch("src.reports.datetime")
def test_spending_by_workday_with_mocked_now(mock_datetime, spending_by_workday_transactions):

    mock_datetime.now.return_value = datetime(2023, 3, 23)

    mock_datetime.strptime = datetime.strptime

    result = json.loads(spending_by_workday(spending_by_workday_transactions))

    assert isinstance(result, dict)
    assert result["Средние траты в рабочий день"] == 380.0
    assert result["Средние траты в выходной день"] == 450.0


@auto_name_save_report
def func_returns_not_string():
    return 123


@auto_name_save_report
def func_returns_invalid_json():
    return "not a json"


@auto_name_save_report
def func_returns_json_not_list_or_dict():
    return json.dumps(123)


@my_name_save_report("test_report.json")
def func_my_name_returns_not_string():
    return 456


@my_name_save_report("test_report.json")
def func_my_name_returns_invalid_json():
    return "bad json"


@my_name_save_report("test_report.json")
def func_my_name_returns_json_not_list_or_dict():
    return json.dumps("string")


def test_auto_name_save_report_type_error():
    with pytest.raises(TypeError):
        func_returns_not_string()


def test_auto_name_save_report_json_decode_error():
    with pytest.raises(ValueError):
        func_returns_invalid_json()


def test_auto_name_save_report_json_type_error():
    with pytest.raises(ValueError):
        func_returns_json_not_list_or_dict()


def test_my_name_save_report_type_error():
    with pytest.raises(TypeError):
        func_my_name_returns_not_string()


def test_my_name_save_report_json_decode_error():
    with pytest.raises(ValueError):
        func_my_name_returns_invalid_json()


def test_my_name_save_report_json_type_error():
    with pytest.raises(ValueError):
        func_my_name_returns_json_not_list_or_dict()
