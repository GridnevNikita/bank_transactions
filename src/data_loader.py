import json
from typing import Any, Dict, List, cast

import pandas as pd


def load_excel_transactions(path: str) -> List[Dict[str, Any]]:
    """
    Загружает транзакции из Excel-файла и возвращает список словарей.
    """
    df = pd.read_excel(path)
    return cast(List[Dict[str, Any]], df.to_dict(orient="records"))


def load_user_settings(path: str) -> Dict[str, Any]:
    """
    Загружает пользовательские настройки из JSON-файла.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            settings = json.load(f)
        return cast(Dict[str, Any], settings)
    except FileNotFoundError:
        print(f"Файл настроек не найден по пути: {path}")
        return {}
    except json.JSONDecodeError:
        print(f"Ошибка при разборе JSON в файле: {path}")
        return {}


# if __name__ == "__main__":
#     # Тестируем загрузку транзакций из Excel
#     excel_path = "../data/operations.xlsx"
#     transactions = load_excel_transactions(excel_path)
#     print(f"Загружено транзакций: {len(transactions)}")
#     for i, transaction in enumerate(transactions[:5], 1):
#         print(f"\nТранзакция {i}:")
#         print(json.dumps(transaction, ensure_ascii=False, indent=4))
# #
# #     # Тестируем загрузку настроек пользователя из JSON
# #     settings_path = "../user_settings.json"
# #     settings = load_user_settings(settings_path)
# #     print("Загруженные настройки пользователя:", settings)
# #     print("Валюты:", settings.get("user_currencies"))
# #     print("Акции:", settings.get("user_stocks"))
