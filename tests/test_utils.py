from unittest.mock import Mock, patch

import pytest

from src.utils import (filter_transactions_by_date, get_cards_summary, get_currency_rates, get_greeting,
                       get_stock_prices, get_top_transactions)


@pytest.fixture
def sample_transactions():
    return [
        {"Дата операции": "10.05.2024 12:30:00", "Сумма операции": -100.0},
        {"Дата операции": "25.05.2024 09:15:00", "Сумма операции": -200.0},
        {"Дата операции": "01.04.2024 10:00:00", "Сумма операции": -150.0},
        {"Дата операции": "30.05.2024 23:59:59", "Сумма операции": -250.0},
        {"Дата операции": "01.05.2024 00:00:00", "Сумма операции": -300.0},
        {"Дата операции": None, "Сумма операции": -50.0},
        {"Сумма операции": -70.0},
        {"Дата операции": "неверный формат", "Сумма операции": -90.0},
    ]


@pytest.mark.parametrize(
    "input_date, expected_count",
    [
        ("30.05.2024", 4),
        ("10.05.2024", 2),
        ("01.04.2024", 1),
        ("01.06.2024", 0),
    ],
)
def test_filter_transactions_by_date(input_date, expected_count, sample_transactions):
    result = filter_transactions_by_date(sample_transactions, input_date)
    assert len(result) == expected_count


@pytest.fixture
def mock_datetime_now():
    def _mock(hour):
        mock_now = Mock()
        mock_now.hour = hour
        return mock_now

    return _mock


@pytest.mark.parametrize(
    "hour, expected",
    [
        (6, "Доброе утро!"),
        (13, "Добрый день!"),
        (19, "Добрый вечер!"),
        (2, "Доброй ночи!"),
    ],
)
@patch("src.utils.datetime")
def test_get_greeting(mock_datetime, hour, expected, mock_datetime_now):
    mock_datetime.now.return_value = mock_datetime_now(hour)
    assert get_greeting() == expected


@pytest.fixture
def summary_transactions():
    return [
        {"Номер карты": "*7197", "Статус": "OK", "Сумма операции": -100.0},
        {"Номер карты": "*7197", "Статус": "OK", "Сумма операции": -50.5},
        {"Номер карты": "*1234", "Статус": "FAILED", "Сумма операции": -200.0},
        {"Номер карты": "*1234", "Статус": "OK", "Сумма операции": 300.0},
        {"Номер карты": None, "Статус": "OK", "Сумма операции": -10.0},
    ]


@pytest.mark.parametrize(
    "transactions, expected",
    [
        ([], []),
        (
            [
                {"Номер карты": "*1111", "Статус": "OK", "Сумма операции": -100},
                {"Номер карты": "*1111", "Статус": "OK", "Сумма операции": -50},
            ],
            [{"last_digits": "1111", "total_spent": 150, "cashback": 1.5}],
        ),
        (
            [
                {"Номер карты": "*2222", "Статус": "FAILED", "Сумма операции": -100},
                {"Номер карты": "*2222", "Статус": "OK", "Сумма операции": 200},
            ],
            [],
        ),
    ],
)
def test_get_cards_summary_parametrized(transactions, expected):
    result = get_cards_summary(transactions)
    assert result == expected


def test_get_cards_summary_with_fixture(summary_transactions):
    result = get_cards_summary(summary_transactions)
    assert len(result) == 1
    assert result[0]["last_digits"] == "7197"
    assert result[0]["total_spent"] == 150.5
    assert result[0]["cashback"] == 1.51


@pytest.fixture
def transactions_sample():
    return [
        {
            "Статус": "OK",
            "Сумма операции": -300.0,
            "Дата платежа": "01.06.2024",
            "Категория": "Питание",
            "Описание": "Ресторан",
        },
        {
            "Статус": "OK",
            "Сумма операции": -150.0,
            "Дата платежа": "02.06.2024",
            "Категория": "Транспорт",
            "Описание": "Такси",
        },
        {
            "Статус": "FAILED",
            "Сумма операции": -500.0,
            "Дата платежа": "03.06.2024",
            "Категория": "Развлечения",
            "Описание": "Кино",
        },
        {
            "Статус": "OK",
            "Сумма операции": 200.0,
            "Дата платежа": "04.06.2024",
            "Категория": "Доход",
            "Описание": "Зарплата",
        },
        {
            "Статус": "OK",
            "Сумма операции": -50.0,
            "Дата платежа": "05.06.2024",
            "Категория": "Кафе",
            "Описание": "Кофе",
        },
        {
            "Статус": "OK",
            "Сумма операции": -600.0,
            "Дата платежа": "06.06.2024",
            "Категория": "Покупки",
            "Описание": "Электроника",
        },
        {
            "Статус": "OK",
            "Сумма операции": -100.0,
            "Дата платежа": "07.06.2024",
            "Категория": "Подарки",
            "Описание": "Книга",
        },
    ]


@pytest.mark.parametrize(
    "top_n, expected_amounts",
    [
        (3, [600.0, 300.0, 150.0]),
        (5, [600.0, 300.0, 150.0, 100.0, 50.0]),
        (10, [600.0, 300.0, 150.0, 100.0, 50.0]),
        (0, []),
    ],
)
def test_get_top_transactions(transactions_sample, top_n, expected_amounts):
    result = get_top_transactions(transactions_sample, top_n=top_n)

    assert len(result) == len(expected_amounts)

    amounts = [i["amount"] for i in result]
    assert amounts == expected_amounts

    for i in result:
        assert "date" in i
        assert "amount" in i
        assert "category" in i
        assert "description" in i


@pytest.fixture
def fake_currency_data():
    return [
        {"ticker": "USD/RUB", "ask": 91.2345},
        {"ticker": "EUR/RUB", "ask": 98.7654},
        {"ticker": "CNY/RUB", "ask": 12.3456},
    ]


@patch("src.utils.requests.get")
@patch("src.utils.os.getenv")
def test_get_currency_rates(mock_getenv, mock_get, fake_currency_data):
    mock_getenv.return_value = "fake_api_key"

    mock_response = Mock()
    mock_response.json.return_value = fake_currency_data
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    currencies = ["USD", "EUR", "CNY"]
    expected = [
        {"currency": "USD", "rate": 91.2345},
        {"currency": "EUR", "rate": 98.7654},
        {"currency": "CNY", "rate": 12.3456},
    ]

    result = get_currency_rates(currencies)

    assert result == expected
    mock_get.assert_called_once()
    mock_getenv.assert_called()


@patch("src.utils.requests.get")
@patch("src.utils.os.getenv")
def test_get_stock_prices(mock_getenv, mock_get):
    mock_getenv.return_value = "fake_api_key"

    fake_stock_data = [
        {"symbol": "AAPL", "price": 189.23},
        {"symbol": "GOOGL", "price": 2823.45},
        {"symbol": "MSFT", "price": 332.10},
    ]
    mock_response = Mock()
    mock_response.json.return_value = fake_stock_data
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    stocks = ["AAPL", "GOOGL", "MSFT"]
    expected = [
        {"stock": "AAPL", "price": 189.23},
        {"stock": "GOOGL", "price": 2823.45},
        {"stock": "MSFT", "price": 332.10},
    ]

    result = get_stock_prices(stocks)

    assert result == expected
    mock_get.assert_called_once()
    mock_getenv.assert_called()
