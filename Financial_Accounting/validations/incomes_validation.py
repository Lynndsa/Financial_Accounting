from datetime import datetime, date

# Глобальные константы ограничений для полей доходов (бизнес-логика)
MAX_NAME_LENGTH = 100
MAX_AMOUNT = 9999999999.99

def _is_number(value):
    # Вспомогательная проверка: возможно ли безопасно привести значение к типу float
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def validate_id(id_value, field_name='id'):
    # Проверка идентификаторов (первичных/внешних ключей) на заполненность, тип данных и знак
    if id_value is None or str(id_value).strip() == '':
        return f'Поле {field_name} обязательно'
    try:
        val = int(id_value)
        if val <= 0:
            return f'Некорректный {field_name}'
    except (TypeError, ValueError):
        return f'Поле {field_name} должно быть числом'
    return None


def validate_income_sum(amount):
    # Проверка суммы транзакции: не пустая, строго числовая, в границах допустимого (от 0 до MAX_AMOUNT)
    if amount is None or str(amount).strip() == '':
        return 'Сумма дохода обязательна'
    if not _is_number(amount):
        return 'Сумма дохода должна быть числом'
    
    amount = float(amount)
    if amount <= 0:
        return 'Сумма дохода должна быть больше 0'
    if amount > MAX_AMOUNT:
        return 'Сумма слишком большая'
    return None


def validate_category_name(name):
    # Проверка текстового наименования категории доходов (исключение пустых строк и ограничение по длине)
    if name is None:
        return 'Название категории обязательно'
    name = str(name).strip()
    if not name:
        return 'Название категории не может быть пустым'
    if len(name) > MAX_NAME_LENGTH:
        return f'Название категории не должно превышать {MAX_NAME_LENGTH} символов'
    return None


def validate_create_income(data):
    """Валидация добавления новой операции дохода."""
    errors = {} # Словарь для группировки ошибок валидации по полям формы
    
    id_category = data.get('id_category')
    id_card = data.get('id_card')
    income_sum = data.get('sum')
    date_time = data.get('date_time')

    # Шаг 1: Контроль внешних ключей — проверяем ID категории и ID счета (карты)
    err = validate_id(id_category, 'id_category')
    if err: errors['id_category'] = err

    err = validate_id(id_card, 'id_card')
    if err: errors['id_card'] = err

    # Шаг 2: Контроль финансовой составляющей — валидация суммы входящего платежа
    err = validate_income_sum(income_sum)
    if err: errors['sum'] = err

    # Шаг 3: Проверка даты операции (парсинг ISO, обработка ошибок формата, запрет на фиксацию "в будущем")
    cleaned_date = None
    if date_time and str(date_time).strip():
        try:
            cleaned_date = datetime.strptime(str(date_time).strip(), '%Y-%m-%d').date()
            if cleaned_date > date.today():
                errors['date_time'] = 'Дата дохода не может быть в будущем'
        except ValueError:
            errors['date_time'] = 'Дата должна быть в формате ГГГГ-ММ-ДД'
    else:
        # Если дата не отправлена клиентом — автоматически проставляем текущие сутки
        cleaned_date = date.today()

    # Шаг 4: Формирование структуры очищенных данных с явным приведением типов для СУБД
    cleaned = {}
    if not errors:
        cleaned = {
            'id_category': int(id_category),
            'id_card': int(id_card),
            'sum': float(income_sum),
            'date_time': cleaned_date.isoformat()
        }

    return errors, cleaned