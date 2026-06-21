from datetime import datetime, date

MAX_NAME_LENGTH = 100
MAX_AMOUNT = 9999999999.99

def _is_number(value):
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def validate_id(id_value, field_name='id'):
    if id_value is None or str(id_value).strip() == '':
        return f'Поле {field_name} обязательно'
    try:
        val = int(id_value)
        if val <= 0:
            return f'Некорректный {field_name}'
    except (TypeError, ValueError):
        return f'Поле {field_name} должно быть числом'
    return None


def validate_expense_sum(amount):
    if amount is None or str(amount).strip() == '':
        return 'Сумма расхода обязательна'
    if not _is_number(amount):
        return 'Сумма расхода должна быть числом'
    
    amount = float(amount)
    if amount <= 0:
        return 'Сумма расхода должна быть больше 0'
    if amount > MAX_AMOUNT:
        return 'Сумма слишком большая'
    return None


def validate_category_name(name):
    if name is None:
        return 'Название категории обязательно'
    name = str(name).strip()
    if not name:
        return 'Название категории не может быть пустым'
    if len(name) > MAX_NAME_LENGTH:
        return f'Название категории не должно превышать {MAX_NAME_LENGTH} символов'
    return None


def validate_create_expense(data):
    """Валидация добавления новой операции расхода."""
    errors = {}
    
    id_category = data.get('id_category')
    id_card = data.get('id_card')
    expense_sum = data.get('sum')
    date_time = data.get('date_time')

    # Проверка связей
    err = validate_id(id_category, 'id_category')
    if err: errors['id_category'] = err

    err = validate_id(id_card, 'id_card')
    if err: errors['id_card'] = err

    # Проверка суммы
    err = validate_expense_sum(expense_sum)
    if err: errors['sum'] = err

    # Валидация даты (если не передана, берем текущую)
    cleaned_date = None
    if date_time and str(date_time).strip():
        try:
            cleaned_date = datetime.strptime(str(date_time).strip(), '%Y-%m-%d').date()
            if cleaned_date > date.today():
                errors['date_time'] = 'Дата расхода не может быть в будущем'
        except ValueError:
            errors['date_time'] = 'Дата должна быть в формате ГГГГ-ММ-ДД'
    else:
        cleaned_date = date.today()

    cleaned = {}
    if not errors:
        cleaned = {
            'id_category': int(id_category),
            'id_card': int(id_card),
            'sum': float(expense_sum),
            'date_time': cleaned_date.isoformat()
        }

    return errors, cleaned