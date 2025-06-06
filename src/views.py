from datetime import datetime
from typing import List, Dict, Any


def get_greeting() -> str:
    """Программа приветствует в зависимости от текущего времени."""
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        return "Доброе утро!"
    elif 12 <= current_hour < 18:
        return "Добрый день!"
    elif 18 <= current_hour < 23:
        return "Добрый вечер!"
    else:
        return "Доброй ночи!"

def get_cards_summary(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Возвращает список словарей с данными по каждой карте.
    """
    cards_summary: Dict[str, float] = {}

    for transaction in transactions:
        if (
                isinstance(transaction.get("Номер карты"), str)
                and transaction.get("Статус") != "FAILED"
                and isinstance(transaction.get("Сумма операции"), (int, float))
                and transaction["Сумма операции"] < 0
        ):
            card = transaction["Номер карты"][-4:]
            amount = -transaction["Сумма операции"]

            cards_summary[card] = cards_summary.get(card, 0) + amount

    result = []
    for last_digits, total_spent in cards_summary.items():
        result.append({
            "last_digits": last_digits,
            "total_spent": round(total_spent, 2),
            "cashback": round(total_spent * 0.01, 2)  # 1% от расходов
        })

    return result


from typing import List, Dict

def get_top_transactions(transactions: List[Dict], top_n: int = 5) -> List[Dict]:
    """
    Возвращает топ-N транзакций с наибольшими расходами.
    Учитываются только транзакции со статусом 'OK' и отрицательной суммой.
    """
    filtered = [
        transaction for transaction in transactions
        if transaction.get("Статус") == "OK"
           and isinstance(transaction.get("Сумма операции"), (int, float))
           and transaction["Сумма операции"] < 0
    ]
    sorted_tx = sorted(filtered, key=lambda i: abs(i["Сумма операции"]), reverse=True)
    top_transactions = []
    for i in sorted_tx[:top_n]:
        top_transactions.append({
            "date": i.get("Дата платежа", ""),
            "amount": round(abs(i["Сумма операции"]), 2),
            "category": i.get("Категория", ""),
            "description": i.get("Описание", "")
        })

    return top_transactions



if __name__ == "__main__":
    print(get_greeting())
    from data_loader import load_excel_transactions
    from utils import filter_transactions_by_date
    transactions = load_excel_transactions("../data/operations.xlsx")
    filtered_transactions = filter_transactions_by_date(transactions, "31.12.2021")
    report = get_cards_summary(filtered_transactions)
    top = get_top_transactions(filtered_transactions)
    # print("Отчёт по картам:")
    print(top)