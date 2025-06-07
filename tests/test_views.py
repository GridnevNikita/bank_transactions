from unittest.mock import patch

import pytest

from src.views import generate_report


@pytest.fixture
def fake_transactions():
    return [
        {
            "Дата операции": "30.12.2021 10:00:00",
            "Сумма операции": -100,
            "Категория": "Продукты",
            "Номер карты": "1234",
            "Кэшбэк": 1,
            "Статус": "OK",
        },
        {
            "Дата операции": "31.12.2021 15:00:00",
            "Сумма операции": -200,
            "Категория": "Транспорт",
            "Номер карты": "5678",
            "Кэшбэк": 2,
            "Статус": "OK",
        },
    ]


@pytest.fixture
def fake_settings():
    return {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "GOOG"]}


@pytest.mark.parametrize(
    "date_str,expected_day", [("2021-12-31 23:59:59", "31.12.2021"), ("2021-12-30 08:00:00", "30.12.2021")]
)
@patch("src.views.get_stock_prices")
@patch("src.views.get_currency_rates")
@patch("src.views.get_top_transactions")
@patch("src.views.get_cards_summary")
@patch("src.views.get_greeting")
@patch("src.views.load_user_settings")
@patch("src.views.load_excel_transactions")
def test_generate_report(
    mock_load_excel,
    mock_load_settings,
    mock_greeting,
    mock_cards,
    mock_top,
    mock_currency,
    mock_stocks,
    date_str,
    expected_day,
    fake_transactions,
    fake_settings,
):
    mock_load_excel.return_value = fake_transactions
    mock_load_settings.return_value = fake_settings
    mock_greeting.return_value = "Добрый день"
    mock_cards.return_value = [{"last_digits": "1234", "total_spent": 100, "cashback": 1}]
    mock_top.return_value = [{"category": "Продукты", "amount": -100}]
    mock_currency.return_value = {"USD": 90.0, "EUR": 100.0}
    mock_stocks.return_value = {"AAPL": 150.0, "GOOG": 2800.0}

    result = generate_report(date_str)

    assert result["greeting"] == "Добрый день"
    assert "cards" in result
    assert isinstance(result["cards"], list)
    assert "currency_rates" in result
    assert "stock_prices" in result

    mock_load_excel.assert_called_once()
    mock_load_settings.assert_called_once()
    mock_currency.assert_called_once_with(["USD", "EUR"])
    mock_stocks.assert_called_once_with(["AAPL", "GOOG"])
