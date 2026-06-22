import re
from datetime import datetime

# Регулярное выражение для проверки имени, фамилии и отчества
fio_pattern = r'^[А-Яа-яЁёA-Za-z]{3,40}$'

# Регулярное выражение для проверки названия счета
card_name_pattern = r'^[А-Яа-яЁёA-Za-z0-9 ]{5,50}$'

# Функция проверки данных личного кабинета
def validate_personal_account(name, lastname, surname, datebirth, name_card):

    # Словарь ошибок валидации
    errors = {}

    # Проверка имени
    if name:
        if not re.match(fio_pattern, name):
            errors["name"] = (
                "Имя должно содержать только буквы "
                "(от 3 до 40 символов)"
            )

    # Проверка фамилии
    if lastname:
        if not re.match(fio_pattern, lastname):
            errors["lastname"] = (
                "Фамилия должна содержать только буквы "
                "(от 3 до 40 символов)"
            )

    # Проверка отчества
    if surname:
        if not re.match(fio_pattern, surname):
            errors["surname"] = (
                "Отчество должно содержать только буквы "
                "(от 3 до 40 символов)"
            )

    # Проверка названия счета
    if name_card:
        # Проверка на допустимые символы и длину строки
        if not re.match(card_name_pattern, name_card):
            errors["name_card"] = (
                "Название счета должно содержать только буквы, цифры и пробелы"
                "(от 5 до 50 символов)"
            )

        # Проверка на строку, состоящую только из пробелов
        elif not name_card.strip():
            errors["name_card"] = (
                "Название счета не может состоять только из пробелов"
            )

    # Проверка даты рождения
    if datebirth:
        try:
             # Преобразование строки в дату
            birth_date = datetime.strptime(datebirth, "%Y-%m-%d").date()
            today = datetime.today().date()

            if birth_date > today:
                errors["datebirth"] = "Дата рождения не может быть больше сегодняшней"

            # Возраст не более 100 лет
            elif today.year - birth_date.year > 100:
                errors["datebirth"] = "Возраст не может превышать 100 лет"

        except ValueError:
            errors["datebirth"] = "Некорректная дата"

    return errors
