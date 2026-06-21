import re
from datetime import datetime

fio_pattern = r'^[А-Яа-яЁёA-Za-z]{3,40}$'
card_name_pattern = r'^[А-Яа-яЁёA-Za-z0-9 ]{5,50}$'

def validate_personal_account(name, lastname, surname, datebirth, name_card):

    errors = {}

    if name:
        if not re.match(fio_pattern, name):
            errors["name"] = (
                "Имя должно содержать только буквы "
                "(от 3 до 40 символов)"
            )

    if lastname:
        if not re.match(fio_pattern, lastname):
            errors["lastname"] = (
                "Фамилия должна содержать только буквы "
                "(от 3 до 40 символов)"
            )

    if surname:
        if not re.match(fio_pattern, surname):
            errors["surname"] = (
                "Отчество должно содержать только буквы "
                "(от 3 до 40 символов)"
            )

    if name_card:
        if not re.match(card_name_pattern, name_card):
            errors["name_card"] = (
                "Название счета должно содержать только буквы, цифры и пробелы"
                "(от 5 до 50 символов)"
            )

        elif not name_card.strip():
            errors["name_card"] = (
                "Название счета не может состоять только из пробелов"
            )

    if datebirth:
        try:
            birth_date = datetime.strptime(datebirth, "%Y-%m-%d").date()
            today = datetime.today().date()

            # не позже сегодняшнего дня
            if birth_date > today:
                errors["datebirth"] = "Дата рождения не может быть больше сегодняшней"

            # возраст не более 100 лет
            elif today.year - birth_date.year > 100:
                errors["datebirth"] = "Возраст не может превышать 100 лет"

        except ValueError:
            errors["datebirth"] = "Некорректная дата"

    return errors
