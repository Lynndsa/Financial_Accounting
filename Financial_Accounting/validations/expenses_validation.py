from datetime import datetime, date

# Глобальные константы для жестких ограничений валидации (бизнес-правила)
MAX_NAME_LENGTH = 100
MAX_AMOUNT = 9999999999.99

def _is_number(value):
    # Вспомогательная функция проверки: можно ли привести значение к числу с плавающей точкой
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def validate_id(id_value, field_name='id'):
    # Валидация первичных и внешних ключей (ID) на заполненность, тип данных и положительное значение
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
    # Комплексная проверка суммы: на пустоту, числовой формат, диапазон (больше нуля и не выше максимума)
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
    # Валидация текстового названия категории (проверка длины строки и пустых пробелов)
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
    errors = {} # Словарь для накопления ошибок по конкретным полям формы
    
    id_category = data.get('id_category')
    id_card = data.get('id_card')
    expense_sum = data.get('sum')
    date_time = data.get('date_time')

    # Шаг 1: Проверка валидности внешних ключей (категории и счета)
    err = validate_id(id_category, 'id_category')
    if err: errors['id_category'] = err

    err = validate_id(id_card, 'id_card')
    if err: errors['id_card'] = err

    # Шаг 2: Проверка корректности вводимой суммы
    err = validate_expense_sum(expense_sum)
    if err: errors['sum'] = err

    # Шаг 3: Валидация даты (парсинг строки, проверка формата ISO и блокировка записей "из будущего")
    cleaned_date = None
    if date_time and str(date_time).strip():
        try:
            cleaned_date = datetime.strptime(str(date_time).strip(), '%Y-%m-%d').date()
            if cleaned_date > date.today():
                errors['date_time'] = 'Дата расхода не может быть в будущем'
        except ValueError:
            errors['date_time'] = 'Дата должна быть в формате ГГГГ-ММ-ДД'
    else:
        # Если дата не передана пользователем, автоматически подставляем сегодняшний день
        cleaned_date = date.today()

    # Шаг 4: Формирование словаря очищенных (валидных) данных, готовых к отправке в БД
    cleaned = {}
    if not errors:
        cleaned = {
            'id_category': int(id_category),
            'id_card': int(id_card),
            'sum': float(expense_sum),
            'date_time': cleaned_date.isoformat()
        }

    return errors, cleaned