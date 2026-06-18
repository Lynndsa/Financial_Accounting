from datetime import datetime

def validate_name(name):
    """
    Проверка названия цели.
    """

    if not name:
        return False, "Введите название цели."

    name = name.strip()

    if len(name) == 0:
        return False, "Введите название цели."

    if len(name) > 100:
        return False, "Название не должно превышать 100 символов."

    return True, ""


def validate_target_amount(amount):
    """
    Проверка целевой суммы.
    """

    if amount == "":
        return False, "Введите целевую сумму."

    try:
        amount = float(amount)

        if amount <= 0:
            return False, "Целевая сумма должна быть больше нуля."

    except ValueError:
        return False, "Целевая сумма должна быть числом."

    return True, ""


def validate_current_amount(amount):
    """
    Проверка уже накопленной суммы.
    """

    if amount == "":
        return True, ""

    try:
        amount = float(amount)

        if amount < 0:
            return False, "Накопленная сумма не может быть отрицательной."

    except ValueError:
        return False, "Накопленная сумма должна быть числом."

    return True, ""


def validate_deadline(deadline):
    """
    Проверка даты.
    """

    if deadline == "":
        return True, ""

    try:
        deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()

        if deadline_date < datetime.today().date():
            return False, "Дата окончания не может быть раньше сегодняшнего дня."

    except ValueError:
        return False, "Некорректный формат даты."

    return True, ""


def validate_description(description):
    """
    Проверка описания.
    """

    if description == "":
        return True, ""

    if len(description) > 200:
        return False, "Описание не должно превышать 200 символов."

    return True, ""


def validate_goal(data):
    """
    Полная проверка формы.
    Возвращает:
    (True, "")
    либо
    (False, "Ошибка")
    """

    validators = [
        validate_name(data.get("name")),
        validate_target_amount(data.get("target_amount")),
        validate_current_amount(data.get("current_amount")),
        validate_deadline(data.get("deadline")),
        validate_description(data.get("description"))
    ]

    for valid, message in validators:
        if not valid:
            return False, message

    return True, ""