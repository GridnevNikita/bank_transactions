import json
from unittest.mock import patch, Mock

from src.data_loader import load_user_settings, load_excel_transactions


@patch("json.load")
@patch("builtins.open")
def test_load_user_settings_success(mock_open, mock_json_load):
    mock_json_load.return_value = {"theme": "dark"}
    result = load_user_settings("settings.json")

    mock_open.assert_called_once_with("settings.json", "r", encoding="utf-8")
    mock_json_load.assert_called_once()
    assert result == {"theme": "dark"}


@patch("builtins.open", side_effect=FileNotFoundError)
def test_load_user_settings_file_not_found(mock_open):
    result = load_user_settings("missing.json")

    mock_open.assert_called_once_with("missing.json", "r", encoding="utf-8")
    assert result == {}


@patch("json.load", side_effect=json.JSONDecodeError("msg", "doc", 0))
@patch("builtins.open")
def test_load_user_settings_json_decode_error(mock_open, mock_json_load):
    result = load_user_settings("bad.json")

    mock_open.assert_called_once_with("bad.json", "r", encoding="utf-8")
    mock_json_load.assert_called_once()
    assert result == {}

@patch("src.data_loader.pd.read_excel")
def test_load_excel_transactions_success(mock_read_excel):
    mock_df = Mock()
    mock_df.to_dict.return_value = [{"id": 1, "amount": 100}, {"id": 2, "amount": 200}]
    mock_read_excel.return_value = mock_df

    result = load_excel_transactions("file.xlsx")

    mock_read_excel.assert_called_once_with("file.xlsx")
    mock_df.to_dict.assert_called_once_with(orient="records")
    assert result == [{"id": 1, "amount": 100}, {"id": 2, "amount": 200}]
