"""
validations/goals_validation.py
Валидация данных для модуля "Копилка" (таблица goals).
Используется в files_module/goals.py перед обращением к БД.
"""

from datetime import datetime, date

MAX_NAME_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 200
MAX_AMOUNT = 9999999999999.99  # максимум для decimal(15,2)


def _is_number(value):
    """Проверяет, что значение можно преобразовать в float."""
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def validate_name(name):
    """Название цели: обязательное, строка, 1-100 символов (varchar(100))."""
    if name is None:
        return 'Название цели обязательно'
    name = str(name).strip()
    if not name:
        return 'Название цели не может быть пустым'
    if len(name) > MAX_NAME_LENGTH:
        return f'Название не должно превышать {MAX_NAME_LENGTH} символов'
    return None


def validate_target_amount(amount):
    """Целевая сумма: обязательна, число > 0 (CHECK target_amount > 0)."""
    if amount is None or amount == '':
        return 'Целевая сумма обязательна'
    if not _is_number(amount):
        return 'Целевая сумма должна быть числом'
    amount = float(amount)
    if amount <= 0:
        return 'Целевая сумма должна быть больше 0'
    if amount > MAX_AMOUNT:
        return 'Целевая сумма слишком большая'
    return None


def validate_current_amount(amount, target_amount=None):
    """Текущая сумма: число >= 0 (CHECK current_amount >= 0), не больше цели."""
    if amount is None or amount == '':
        return None  # необязательно, по умолчанию 0
    if not _is_number(amount):
        return 'Текущая сумма должна быть числом'
    amount = float(amount)
    if amount < 0:
        return 'Текущая сумма не может быть отрицательной'
    if amount > MAX_AMOUNT:
        return 'Текущая сумма слишком большая'
    if target_amount is not None and _is_number(target_amount) and amount > float(target_amount):
        return 'Текущая сумма не может превышать целевую сумму'
    return None


def validate_deadline(deadline_value):
    """Дедлайн: необязательная дата YYYY-MM-DD, не в прошлом."""
    if not deadline_value:
        return None
    if isinstance(deadline_value, date):
        deadline_date = deadline_value
    else:
        try:
            deadline_date = datetime.strptime(str(deadline_value), '%Y-%m-%d').date()
        except ValueError:
            return 'Дата должна быть в формате ГГГГ-ММ-ДД'
    if deadline_date < date.today():
        return 'Дедлайн не может быть в прошлом'
    return None


def validate_description(description):
    """Описание: необязательное, до 200 символов (varchar(200))."""
    if not description:
        return None
    if len(str(description)) > MAX_DESCRIPTION_LENGTH:
        return f'Описание не должно превышать {MAX_DESCRIPTION_LENGTH} символов'
    return None


def validate_id_card(id_card):
    """id_card: необязательный, положительное целое число."""
    if id_card is None or id_card == '':
        return None
    try:
        id_card_int = int(id_card)
    except (TypeError, ValueError):
        return 'Некорректный номер карты'
    if id_card_int <= 0:
        return 'Некорректный номер карты'
    return None


def validate_id(value, field_name='id'):
    """Проверка положительного целочисленного идентификатора (id, id_user, goal_id)."""
    try:
        value_int = int(value)
    except (TypeError, ValueError):
        return f'Некорректный {field_name}'
    if value_int <= 0:
        return f'Некорректный {field_name}'
    return None


def validate_topup_amount(amount):
    """Сумма пополнения копилки: число > 0."""
    if amount is None or amount == '':
        return 'Сумма пополнения обязательна'
    if not _is_number(amount):
        return 'Сумма пополнения должна быть числом'
    amount = float(amount)
    if amount <= 0:
        return 'Сумма пополнения должна быть больше 0'
    if amount > MAX_AMOUNT:
        return 'Сумма слишком большая'
    return None


def validate_create_goal(data):
    """
    Валидация данных для создания цели (процедура create_new_goal).
    data: dict с ключами name, target_amount, current_amount, id_card, deadline, description
    Возвращает (errors: dict, cleaned: dict). errors пуст, если данные валидны.
    """
    errors = {}
    name = data.get('name')
    target_amount = data.get('target_amount')
    current_amount = data.get('current_amount', 0)
    id_card = data.get('id_card')
    deadline = data.get('deadline')
    description = data.get('description')

    err = validate_name(name)
    if err:
        errors['name'] = err

    err = validate_target_amount(target_amount)
    if err:
        errors['target_amount'] = err

    err = validate_current_amount(current_amount, target_amount if 'target_amount' not in errors else None)
    if err:
        errors['current_amount'] = err

    err = validate_id_card(id_card)
    if err:
        errors['id_card'] = err

    err = validate_deadline(deadline)
    if err:
        errors['deadline'] = err

    err = validate_description(description)
    if err:
        errors['description'] = err

    cleaned = {
        'name': str(name).strip() if name else None,
        'target_amount': float(target_amount) if target_amount not in (None, '') else None,
        'current_amount': float(current_amount) if current_amount not in (None, '') else 0.0,
        'id_card': int(id_card) if id_card not in (None, '') else None,
        'deadline': deadline if deadline else None,
        'description': str(description).strip() if description else None,
    }
    return errors, cleaned


def validate_update_goal(data):
    """
    Валидация данных для обновления цели.
    Процедура update_goals обновляет только name, target_amount, deadline
    (current_amount, id_card, description через неё не меняются).
    Все поля необязательны - обновляется только то, что передано.
    Возвращает (errors: dict, cleaned: dict).
    """
    errors = {}
    cleaned = {}

    if data.get('name') not in (None, ''):
        err = validate_name(data.get('name'))
        if err:
            errors['name'] = err
        else:
            cleaned['name'] = str(data.get('name')).strip()
    else:
        cleaned['name'] = None

    if data.get('target_amount') not in (None, ''):
        err = validate_target_amount(data.get('target_amount'))
        if err:
            errors['target_amount'] = err
        else:
            cleaned['target_amount'] = float(data.get('target_amount'))
    else:
        cleaned['target_amount'] = None

    if data.get('deadline') not in (None, ''):
        err = validate_deadline(data.get('deadline'))
        if err:
            errors['deadline'] = err
        else:
            cleaned['deadline'] = data.get('deadline')
    else:
        cleaned['deadline'] = None

    return errors, cleaned