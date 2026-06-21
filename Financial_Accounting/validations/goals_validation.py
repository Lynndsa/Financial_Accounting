"""
Файл отвечает за проверку (валидацию) данных, которые вводит пользователь.
Защищает базу данных от некорректных типов, пустых строк и дат из будущего/прошлого.
"""

from datetime import datetime, date

# Константы
MAX_NAME_LENGTH = 100         
MAX_UPDATE_NAME_LENGTH = 50   
MAX_DESCRIPTION_LENGTH = 200  
MAX_AMOUNT = 9999999999999.99

def validate_id(id_value, field_name='id'):
    """Проверяет, что переданный ID является корректным целым числом больше 0."""
    if id_value is None or str(id_value).strip() == '':
        return f'Поле {field_name} обязательно'
    try:
        val = int(id_value)
        if val <= 0:
            return f'Некорректный {field_name}'
    except (TypeError, ValueError):
        return f'Поле {field_name} должно быть числом'
    return None


def validate_topup_amount(amount):
    """Проверяет сумму пополнения копилки: обязательна, должна быть числом и строго больше 0."""
    if amount is None or str(amount).strip() == '':
        return 'Сумма пополнения обязательна'
    if not _is_number(amount):
        return 'Сумма пополнения должна быть числом'
    
    amount = float(amount)
    if amount <= 0:
        return 'Сумма пополнения должна быть больше 0'
    if amount > MAX_AMOUNT:
        return 'Сумма пополнения слишком большая'
    return None


def _is_number(value):
    """
    Вспомогательная функция (начинается с подчеркивания, типа приватная).
    Проверяет, можно ли превратить строку в число с плавающей точкой (float).
    """
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def validate_name(name, max_len=MAX_NAME_LENGTH):
    """Проверяет имя цели. Оно обязательное, не пустое и не длиннее лимита."""
    if name is None:
        return 'Название цели обязательно'
    
    # .strip() убирает случайные пробелы по краям
    name = str(name).strip()
    if not name:
        return 'Название цели не может быть пустым'
    if len(name) > max_len:
        return f'Название не должно превышать {max_len} символов'
    return None  # Если ошибок нет — возвращаем None


def validate_target_amount(amount):
    """Проверяет целевую сумму: должна быть числом и строго больше 0."""
    if amount is None or str(amount).strip() == '':
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
    """Проверяет стартовую сумму: >= 0 и не может быть больше, чем сама цель."""
    if amount is None or str(amount).strip() == '':
        return None  # Поле необязательное (в БД дефолт 0.00)
    if not _is_number(amount):
        return 'Текущая сумма должна быть числом'
    
    amount = float(amount)
    if amount < 0:
        return 'Текущая сумма не может быть отрицательной'
    if amount > MAX_AMOUNT:
        return 'Текущая сумма слишком большая'
    
    # Если целевая сумма тоже прошла проверку, смотрим, чтобы мы не накопили больше, чем цель
    if target_amount is not None and _is_number(target_amount):
        if amount > float(target_amount):
            return 'Текущая сумма не может превышать целевую сумму'
    return None


def validate_deadline(deadline_value):
    """Проверяет дату: формат ГГГГ-ММ-ДД, не в прошлом и не дальше чем на 10 лет вперед."""
    if not deadline_value or str(deadline_value).strip() == '':
        return None  # Дата необязательна
        
    if isinstance(deadline_value, date):
        deadline_date = deadline_value
    else:
        try:
            # Пытаемся распарсить строку в реальный объект даты
            deadline_date = datetime.strptime(str(deadline_value).strip(), '%Y-%m-%d').date()
        except ValueError:
            return 'Дата должна быть в формате ГГГГ-ММ-ДД'
            
    # Проверка 1: Чтобы дедлайн не был вчера или раньше
    if deadline_date < date.today():
        return 'Дедлайн не может быть в прошлом'
        
    # Проверка 2: Ограничение "Текущий год + 10 лет"
    max_year = date.today().year + 10
    if deadline_date.year > max_year:
        return f'Дедлайн не может быть дальше {max_year} года (максимум на 10 лет вперед)'
        
    return None


def validate_description(description):
    """Проверяет описание: необязательное, максимум 200 символов."""
    if description is None:
        return None
    description_str = str(description).strip()
    if not description_str:
        return None
    if len(description_str) > MAX_DESCRIPTION_LENGTH:
        return f'Описание не должно превышать {MAX_DESCRIPTION_LENGTH} символов'
    return None


def validate_id_card(id_card):
    """Проверяет привязанную карту: это должен быть корректный ID (целое число > 0)."""
    if id_card is None or str(id_card).strip() == '':
        return None  # Карта необязательна
    try:
        id_card_int = int(id_card)
    except (TypeError, ValueError):
        return 'Некорректный номер карты'
    if id_card_int <= 0:
        return 'Некорректный номер карты'
    return None


def validate_create_goal(data, conn, id_user):
    """
    Главная функция для валидации СОЗДАНИЯ цели. 
    Принимает словарь из формы, соединение с БД и id_user.
    """
    errors = {}
    
    name = data.get('name')
    target_amount = data.get('target_amount')
    current_amount = data.get('current_amount', 0)
    id_card = data.get('id_card')
    deadline = data.get('deadline')
    description = data.get('description')

    err = validate_name(name, MAX_NAME_LENGTH)
    if err: 
        errors['name'] = err
    else:
        # Проверка на дубликат имени среди активных целей пользователя
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT id FROM goals WHERE id_user = %s AND name = %s AND is_active = 1',
                (id_user, str(name).strip())
            )
            if cursor.fetchone():
                errors['name'] = 'Цель с таким названием уже существует'

    err = validate_target_amount(target_amount)
    if err: errors['target_amount'] = err

    err = validate_current_amount(current_amount, target_amount if 'target_amount' not in errors else None)
    if err: errors['current_amount'] = err

    err = validate_id_card(id_card)
    if err: errors['id_card'] = err

    err = validate_deadline(deadline)
    if err: errors['deadline'] = err

    err = validate_description(description)
    if err: errors['description'] = err

    # Если ошибок нет, создаем "cleaned" — словарь с правильными типами данных для БД
    cleaned = {}
    if not errors:
        cleaned = {
            'name': str(name).strip(),
            'target_amount': float(target_amount),
            'current_amount': float(current_amount) if current_amount not in (None, '') else 0.0,
            'id_card': int(id_card) if id_card not in (None, '') else None,
            'deadline': str(deadline).strip() if deadline and str(deadline).strip() else None,
            'description': str(description).strip() if description and str(description).strip() else None,
        }

    return errors, cleaned


def validate_update_goal(data, conn, id_user, goal_id):
    """
    Главная функция для валидации ОБНОВЛЕНИЯ цели.
    Учитывает, что нельзя переименовать цель в уже существующую (исключая саму себя).
    """
    errors = {}
    cleaned = {}

    # Проверяем имя (если оно пришло в запросе)
    if 'name' in data and data.get('name') not in (None, ''):
        err = validate_name(data.get('name'), MAX_UPDATE_NAME_LENGTH) # Передаем лимит 50!
        if err: 
            errors['name'] = err
        else:
            # Проверяем на дубликат (но игнорируем текущую обновляемую цель по goal_id)
            with conn.cursor() as cursor:
                cursor.execute(
                    'SELECT id FROM goals WHERE id_user = %s AND name = %s AND id != %s AND is_active = 1',
                    (id_user, str(data.get('name')).strip(), goal_id)
                )
                if cursor.fetchone():
                    errors['name'] = 'У вас уже есть другая активная цель с таким названием'
            
            if 'name' not in errors:
                cleaned['name'] = str(data.get('name')).strip()
    else:
        cleaned['name'] = None

    # Проверяем целевую сумму
    if 'target_amount' in data and data.get('target_amount') not in (None, ''):
        err = validate_target_amount(data.get('target_amount'))
        if err: errors['target_amount'] = err
        else: cleaned['target_amount'] = float(data.get('target_amount'))
    else:
        cleaned['target_amount'] = None

    # Проверяем дедлайн
    if 'deadline' in data and data.get('deadline') not in (None, ''):
        err = validate_deadline(data.get('deadline'))
        if err: errors['deadline'] = err
        else: cleaned['deadline'] = str(data.get('deadline')).strip()
    else:
        cleaned['deadline'] = None

    return errors, cleaned
