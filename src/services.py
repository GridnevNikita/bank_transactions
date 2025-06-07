import json
import re
from typing import Any, Dict, List


def search_transactions(transactions: List[Dict[str, Any]], query: str) -> str:
    """
    Ищет транзакции, где query содержится в 'Описание' или 'Категория' (регистр игнорируется).
    Если query пустая или состоит из пробелов — возвращает пустой список.
    Возвращает JSON-строку со списком найденных транзакций.
    """
    if not query or query.strip() == "":
        # Можно вернуть пустой список или все транзакции, в зависимости от задачи
        return json.dumps([], ensure_ascii=False, indent=2)

    search = re.compile(re.escape(query) + r"\w*", re.IGNORECASE)
    filtered = []
    for transaction in transactions:
        description = transaction.get("Описание")
        category = transaction.get("Категория")

        if (
            isinstance(description, str)
            and search.search(description)
            or isinstance(category, str)
            and search.search(category)
        ):
            filtered.append(transaction)

    return json.dumps(filtered, ensure_ascii=False, indent=2)


def search_by_phone_number(transactions: List[Dict[str, Any]]) -> str:
    """
    Ищет транзакции, содержащими в описании мобильные номера.
    Возвращает JSON-строку со списком найденных транзакций.
    """
    phone_string = re.compile(r"\+7[\s\-()]*\d{3}[\s\-()]*\d{3}[\s\-()]*\d{2}[\s\-()]*\d{2}")
    filtered_numbers = []
    for transaction in transactions:
        description = transaction.get("Описание")
        if isinstance(description, str) and phone_string.search(description):
            filtered_numbers.append(transaction)

    return json.dumps(filtered_numbers, ensure_ascii=False, indent=2)


def search_transfers_to_individuals(transactions: List[Dict[str, Any]]) -> str:
    """
    Ищет транзакции, которые относятся к переводам физическим лицам.
    Возвращает JSON-строку со списком найденных транзакций.
    """
    person_transfer = re.compile(r"\w+ \w\.", re.IGNORECASE)
    transfer = re.compile(r"перевод\w*", re.IGNORECASE)
    filtered_person = []
    for transaction in transactions:
        description = transaction.get("Описание")
        category = transaction.get("Категория")
        if (
            isinstance(category, str)
            and transfer.search(category)
            and isinstance(description, str)
            and person_transfer.search(description)
        ):
            filtered_person.append(transaction)

    return json.dumps(filtered_person, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    from data_loader import load_excel_transactions

    transactions = load_excel_transactions("../data/operations.xlsx")
    # query = 'маГНИТ'
    # result_json = search_transactions(transactions, query)
    result_json = search_transfers_to_individuals(transactions)
    print(result_json)
