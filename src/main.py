import os
import sys
from datetime import datetime
from typing import Any, List, Optional, Tuple

import pandas as pd

from src.reports import (auto_name_save_report, my_name_save_report, spending_by_category, spending_by_weekday,
                         spending_by_workday)
from src.services import (get_bonus_categories, investment_bank, search_by_phone_number, search_transactions,
                          search_transfers_to_individuals)
from src.utils import load_excel_transactions
from src.views import generate_report

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "operations.xlsx")


def load_data() -> Tuple[List[dict], pd.DataFrame]:
    """
    Загружает транзакции из Excel-файла.

    Проверяет наличие файла. Если файла нет — завершает программу.
    Возвращает список словарей с транзакциями и DataFrame для удобной работы с данными.
    """
    if not os.path.exists(DATA_PATH):
        print(f"Файл с транзакциями не найден: {DATA_PATH}")
        sys.exit(1)
    data_list = load_excel_transactions(DATA_PATH)
    print(f"Загружено {len(data_list)} транзакций из {DATA_PATH}")
    df = pd.DataFrame(data_list)
    return data_list, df


def print_menu() -> None:
    """
    Выводит в консоль список доступных действий для пользователя.
    """
    print("\nДоступные действия:")
    print("1. Полный отчёт")
    print("2. Траты по категории")
    print("3. Траты по дням недели")
    print("4. Траты в рабочие/выходные дни")
    print("5. Выгодные категории кешбэка")
    print("6. Инвесткопилка (10/50/100)")
    print("7. Поиск транзакций по строке")
    print("8. Поиск транзакций с номерами телефонов")
    print("9. Переводы физическим лицам")
    print("0. Выход")


def input_choice() -> str:
    """
    Запрашивает у пользователя номер действия и возвращает введённую строку.
    """
    choice = input("Введите номер действия: ").strip()
    return choice


def input_date_full() -> str:
    """
    Запрашивает у пользователя дату и время в формате 'YYYY-MM-DD HH:MM:SS'.
    Если введена пустая строка — возвращает текущую дату и время.
    Повторяет запрос при неверном формате.
    """
    while True:
        s = input("Введите дату и время (YYYY-MM-DD HH:MM:SS) или Enter для текущей: ").strip()
        if not s:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
            return s
        except ValueError:
            print("❌ Неверный формат даты и времени. Попробуйте ещё раз.")


def input_date_simple() -> Optional[str]:
    """
    Запрашивает у пользователя дату в формате 'YYYY-MM-DD'.
    Если введена пустая строка — возвращает None.
    Повторяет запрос при неверном формате.
    """
    while True:
        s = input("Введите дату (YYYY-MM-DD) или Enter для текущей: ").strip()
        if not s:
            return None
        try:
            datetime.strptime(s, "%Y-%m-%d")
            return s
        except ValueError:
            print("❌ Неверный формат даты. Попробуйте ещё раз.")


def input_year() -> int:
    """
    Запрашивает у пользователя год (4 цифры) для анализа кешбэка.
    Повторяет запрос при неверном вводе.
    """
    while True:
        year_str = input("Год для анализа кешбэка (YYYY): ").strip()
        if year_str.isdigit() and len(year_str) == 4:
            return int(year_str)
        print("❌ Некорректный год. Введите 4-значное число, например 2020.")


def input_month() -> int:
    """
    Запрашивает у пользователя номер месяца (1-12) для анализа кешбэка.
    Повторяет запрос при неверном вводе.
    """
    while True:
        month_str = input("Месяц для анализа кешбэка (MM): ").strip()
        if month_str.isdigit():
            month = int(month_str)
            if 1 <= month <= 12:
                return month
        print("❌ Некорректный месяц. Введите число от 1 до 12.")


def input_category(categories: List[str]) -> str:
    """
    Предлагает выбрать категорию из списка по номеру.
    Повторяет запрос при неверном выборе.
    """
    while True:
        print("Доступные категории:")
        for idx, cat in enumerate(categories, 1):
            print(f"{idx}. {cat}")
        sel = input("Выберите категорию по номеру: ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(categories):
            return categories[int(sel) - 1]
        print("❌ Некорректный выбор категории. Попробуйте ещё раз.")


def input_month_string() -> str:
    """
    Запрашивает дату в формате 'YYYY-MM'.
    Повторяет запрос при неверном формате.
    """
    while True:
        s = input("Дата (YYYY-MM): ").strip()
        if len(s) == 7 and s[4] == "-":
            y, m = s.split("-")
            if y.isdigit() and m.isdigit() and 1 <= int(m) <= 12:
                return s
        print("❌ Неверный формат даты. Ожидается YYYY-MM, например 2024-06.")


def input_rounding_limit() -> int:
    """
    Запрашивает порог округления для инвесткопилки (10, 50 или 100).
    Повторяет запрос при неверном вводе.
    """
    while True:
        s = input("Порог округления (10, 50 или 100): ").strip()
        if s in {"10", "50", "100"}:
            return int(s)
        print("❌ Некорректный порог. Введите 10, 50 или 100.")


def save_report_interactive(func: Any, *args: Any, **kwargs: Any) -> Any:
    """
    Вспомогательная функция для интерактивного вызова отчётов.

    Предлагает пользователю варианты сохранения отчёта:
    - автоматически с автогенерацией имени,
    - вручную с вводом имени,
    - без сохранения.

    Оборачивает функцию декораторами сохранения при необходимости.
    """
    print("Хотите сохранить отчёт в файл?")
    print("1 - Да, сохранить автоматически (имя генерируется)")
    print("2 - Да, ввести имя файла вручную")
    print("0 - Не сохранять")

    choice = input("Выберите вариант: ").strip()
    if choice == "1":
        decorated_func = auto_name_save_report(func)
        result = decorated_func(*args, **kwargs)
        print(f"✅ Отчёт сохранён автоматически в файл: report_{func.__name__}.json")
        return result
    elif choice == "2":
        filename = input("Введите имя файла для сохранения (с расширением .json): ").strip()
        if not filename.endswith(".json"):
            filename += ".json"
        decorated_func = my_name_save_report(filename)(func)
        result = decorated_func(*args, **kwargs)
        print(f"✅ Отчёт сохранён вручную в файл: {filename}")
        return result
    else:
        return func(*args, **kwargs)


def main() -> None:
    """
    Основная функция запуска программы.

    Загружает данные и предоставляет меню для выбора действий.
    Обрабатывает пользовательский ввод и вызывает соответствующие функции отчётов и сервисов.
    """
    data_list, df = load_data()

    while True:
        print_menu()
        choice = input_choice()

        if choice == "0":
            print("Завершаем работу.")
            break

        elif choice == "1":
            date_str = input_date_full()
            print("Генерируем полный отчёт...")
            result = generate_report(date_str)
            print(result)

        elif choice == "2":
            date = input_date_simple()
            cats = df["Категория"].dropna().unique().tolist()
            category = input_category(cats)
            print(f"Генерируем отчёт по категории '{category}'...")
            result = save_report_interactive(spending_by_category, df, category=category, date=date)
            print(result)

        elif choice == "3":
            date = input_date_simple()
            print("Генерируем отчёт по дням недели...")
            result = save_report_interactive(spending_by_weekday, df, date=date)
            print(result)

        elif choice == "4":
            date = input_date_simple()
            print("Генерируем отчёт по рабочим/выходным дням...")
            result = save_report_interactive(spending_by_workday, df, date=date)
            print(result)

        elif choice == "5":
            year = input_year()
            month = input_month()
            print("Генерируем выгодные категории кешбэка...")
            try:
                result = get_bonus_categories(data_list, year, month)
                print(result)
            except Exception as e:
                print(f"⚠️ Ошибка при анализе кешбэка: {e}")

        elif choice == "6":
            month_str = input_month_string()
            limit = input_rounding_limit()
            print("Генерируем инвесткопилку...")
            try:
                result = investment_bank(month_str, data_list, limit)
                print(result)
            except Exception as e:
                print(f"⚠️ Ошибка при генерации инвесткопилки: {e}")

        elif choice == "7":
            query = input("Строка для поиска: ").strip()
            print("Ищем транзакции...")
            result = search_transactions(data_list, query)
            print(result)

        elif choice == "8":
            print("Ищем номера телефонов в транзакциях...")
            result = search_by_phone_number(data_list)
            print(result)

        elif choice == "9":
            print("Ищем переводы физическим лицам...")
            result = search_transfers_to_individuals(data_list)
            print(result)

        else:
            print("❌ Неизвестная команда. Попробуйте ещё раз.")


if __name__ == "__main__":
    main()
