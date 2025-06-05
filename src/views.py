from datetime import datetime

def get_greeting(current_dt: datetime) -> str:
    """ Программа приветствует в зависимости от текущего времени. """
    hour = current_dt.hour
    if 6 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


if __name__ == "__main__":
    test_times = [
        "2023-06-05 07:30:00",
        "2023-06-05 13:00:00",
        "2023-06-05 19:45:00",
        "2023-06-05 02:15:00"
    ]

    for time_str in test_times:
        dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        greeting = get_greeting(dt)
        print(f"Время: {time_str} => Приветствие: {greeting}")