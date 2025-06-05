from typing import List, Dict
from datetime import datetime, time


def filter_transactions_by_date(
        transactions: List[Dict], date_str: str
) -> List[Dict]:
    """
    Фильтрует транзакции по дате.
    Возвращает операции с начала месяца по указанную дату включительно (весь день).
    """
    input_date = datetime.strptime(date_str, '%Y-%m-%d')

    # Начало месяца - первый день с 00:00:00
    start_date = input_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Конец дня входящей даты — 23:59:59, чтобы включить все операции за этот день
    end_date = datetime.combine(input_date.date(), time.max)

    filtered_list = []
    for transaction in transactions:
        # Преобразуем дату из транзакции из формата Excel ('ДД.ММ.ГГГГ ЧЧ:ММ:СС')
        tx_date = datetime.strptime(transaction['Дата операции'], '%d.%m.%Y %H:%M:%S')

        # Проверяем, что дата операции лежит в нужном интервале
        if start_date <= tx_date <= end_date:
            filtered_list.append(transaction)

    return filtered_list


if __name__ == "__main__":
    from src.data_loader import load_excel_transactions
    # Загружаем транзакции
    transactions = load_excel_transactions("../data/operations.xlsx")
    date_str = "2021-12-31"
    # Фильтруем транзакции
    filtered_tx = filter_transactions_by_date(transactions, date_str)
    for tx in filtered_tx:
        print(tx["Дата операции"], tx["Описание"])