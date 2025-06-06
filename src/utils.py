from typing import List, Dict
from datetime import datetime, time


def filter_transactions_by_date(transactions: List[Dict], date_str: str) -> List[Dict]:
    """
    Фильтрует транзакции по дате операции.
    Принимает дату в формате 'ДД.ММ.ГГГГ'.
    Возвращает операции с начала месяца по указанную дату включительно.
    """

    input_date = datetime.strptime(date_str, "%d.%m.%Y")
    start_date = datetime.combine(input_date.replace(day=1).date(), time.min)
    end_date = datetime.combine(input_date.date(), time.max)

    filtered_list = []
    for transaction in transactions:
        try:
            raw_date = transaction["Дата операции"]
            if not isinstance(raw_date, str):
                continue
            operation_date = datetime.strptime(raw_date, "%d.%m.%Y %H:%M:%S")

            if start_date <= operation_date <= end_date:
                filtered_list.append(transaction)
        except (KeyError, ValueError):
            continue

    return filtered_list


if __name__ == "__main__":
    from src.data_loader import load_excel_transactions

    # Загружаем транзакции
    transactions = load_excel_transactions("../data/operations.xlsx")
    date_str = "31.12.2021"
    # Фильтруем транзакции
    filtered_tx = filter_transactions_by_date(transactions, date_str)
    for filtered in filtered_tx:
        print(filtered["Дата операции"], filtered["Описание"])
