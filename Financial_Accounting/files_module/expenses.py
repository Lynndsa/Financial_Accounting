from bottle import route, request, response
from datetime import date, datetime
from decimal import Decimal

from database.db import get_connection
from validations.expenses_validation import (
    validate_id,
    validate_category_name,
    validate_create_expense
)

def _serialize_row(row):
    # Преобразуем строку БД (dict) в JSON-формат: Decimal -> float, даты -> ISO-строки
    result = dict(row)
    for key, value in result.items():
        if isinstance(value, Decimal):
            result[key] = float(value)
        elif isinstance(value, (date, datetime)):
            result[key] = value.isoformat()
    return result


def _get_request_data():
    # Универсальный перехват данных: приоритет за JSON, иначе забираем данные из обычных веб-форм
    if request.json:
        return request.json
    return dict(request.forms)


# ==============================================================================
# 1. КАТЕГОРИИ РАСХОДОВ
# ==============================================================================

@route('/api/expense-categories', method='GET')
def get_expense_categories():
    # Получение списка всех категорий расходов для выпадающих списков на фронте
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Исключаем категорию "Копилка" из выпадающего списка для пользователя
            cursor.execute("SELECT * FROM expense_categories WHERE name != 'Копилка' ORDER BY name ASC")
            rows = cursor.fetchall()
        return {'categories': [dict(r) for r in rows]}
    except Exception as e:
        response.status = 500
        return {'error': 'Ошибка при получении категорий расходов', 'detail': str(e)}
    finally:
        conn.close()


@route('/api/expense-categories', method='POST')
def create_expense_category():
    # Создание новой пользовательской категории расходов
    data = _get_request_data()
    name = data.get('name')

    # Шаг 1: Валидация базовой длины и заполненности имени
    err = validate_category_name(name)
    if err:
        response.status = 400
        return {'error': err}

    name_clean = str(name).strip()
    
    # Защита: не даем пользователю вручную создать еще одну категорию "Копилка"
    if name_clean.lower() == 'копилка':
        response.status = 400
        return {'error': 'Категория "Копилка" является системной и не может быть создана вручную'}

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Шаг 2: Проверяем базу на уникальность имени, чтобы избежать дублей
            cursor.execute('SELECT id FROM expense_categories WHERE name = %s', (name_clean,))
            if cursor.fetchone():
                response.status = 400
                return {'error': 'Категория расходов с таким названием уже существует'}

            # Шаг 3: Добавляем запись через хранимую процедуру
            cursor.callproc('create_new_expense_category', (name_clean,))
        conn.commit()
        response.status = 201
        return {'message': 'Категория расходов успешно добавлена'}
    except Exception as e:
        conn.rollback()
        response.status = 500
        return {'error': 'Ошибка при добавлении категории расходов', 'detail': str(e)}
    finally:
        conn.close()


# ==============================================================================
# 2. ОПЕРАЦИИ С РАСХОДАМИ
# ==============================================================================

@route('/api/expenses', method='POST')
def add_expense():
    # Регистрация новой расходной операции пользователя
    data = _get_request_data()
    user_id = data.get('user_id')

    # Шаг 1: Валидация переданных полей (счета, категории, суммы, формата даты)
    errors, cleaned = validate_create_expense(data)
    if errors:
        response.status = 400
        return {'errors': errors}

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Шаг 2: Проверка существования счета и его принадлежности текущему пользователю
            cursor.execute(
                'SELECT id_card, balance FROM accounts WHERE id_card = %s AND id_user = %s',
                (cleaned['id_card'], user_id)
            )
            account = cursor.fetchone()
            if not account:
                response.status = 400
                return {'error': 'Указанный счёт не найден или не принадлежит пользователю'}

            # Шаг 3: Проверка баланса на бэкенде перед списанием
            if float(account['balance']) < cleaned['sum']:
                response.status = 400
                return {'error': f"Недостаточно средств. Текущий баланс: {account['balance']} ₽"}

            # Шаг 4: Вызов процедуры вставки расхода
            cursor.callproc('create_new_expenses', (
                cleaned['id_category'],
                cleaned['id_card'],
                cleaned['date_time'],
                cleaned['sum']
            ))
            
        conn.commit()
        response.status = 201
        return {'message': 'Расход успешно зафиксирован'}
    except Exception as e:
        conn.rollback()
        response.status = 500
        return {'error': 'Ошибка при создании операции расхода', 'detail': str(e)}
    finally:
        conn.close()


@route('/api/expenses/history', method='GET')
def get_expenses_history():
    # Получение списка расходов с фильтрацией по месяцам и категориям
    user_id = request.query.get('user_id')
    # Если месяц не выбран — берем текущий по умолчанию (ГГГГ-ММ)
    selected_month = request.query.get('month') or date.today().strftime('%Y-%m')
    id_category = request.query.get('id_category') or 'all'

    # Базовый SQL-запрос с объединением (JOIN) таблиц счетов и категорий
    query = """
        SELECT e.id_expense, e.sum, e.date_time, c.name AS category_name, a.name_card
        FROM expenses e
        JOIN expense_categories c ON e.id_category = c.id
        JOIN accounts a ON e.id_card = a.id_card
        WHERE a.id_user = %s 
          AND DATE_FORMAT(e.date_time, '%%Y-%%m') = %s
    """
    params = [user_id, selected_month]

    # Динамическая подстановка фильтра по категории, если выбрана не вкладка 'all'
    if id_category != 'all':
        query += " AND e.id_category = %s"
        params.append(int(id_category))

    # Сортировка: сначала свежие операции
    query += " ORDER BY e.date_time DESC, e.id_expense DESC"

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        # Сериализуем каждую строку для корректной JSON-передачи дат и чисел
        return {'history': [_serialize_row(r) for r in rows]}
    except Exception as e:
        response.status = 500
        return {'error': 'Ошибка при получении истории расходов', 'detail': str(e)}
    finally:
        conn.close()


@route('/api/expenses/chart', method='GET')
def get_expenses_chart_data():
    # Агрегация сумм по категориям для построения круговой диаграммы (pie-chart)
    user_id = request.query.get('user_id')
    selected_month = request.query.get('month') or date.today().strftime('%Y-%m')

    # Группировка (GROUP BY) и суммирование расходов за указанный месяц
    query = """
        SELECT c.name AS category_name, SUM(e.sum) AS total_sum
        FROM expenses e
        JOIN expense_categories c ON e.id_category = c.id
        JOIN accounts a ON e.id_card = a.id_card
        WHERE a.id_user = %s 
          AND DATE_FORMAT(e.date_time, '%%Y-%%m') = %s
        GROUP BY c.id, c.name
        ORDER BY total_sum DESC
    """

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, [user_id, selected_month])
            rows = cursor.fetchall()
        
        # Мапим данные в формат ключей, удобный для JS-библиотек графиков
        chart_data = [{'category': r['category_name'], 'sum': float(r['total_sum'])} for r in rows]
        return {'chart_data': chart_data}
    except Exception as e:
        response.status = 500
        return {'error': 'Ошибка при формировании данных диаграммы расходов', 'detail': str(e)}
    finally:
        conn.close()


@route('/api/expenses/<expense_id:int>', method='DELETE')
def delete_expense(expense_id):
    """
    Удаление расхода из истории.
    Откат суммы цели (goals) делает триггер expenses_BEFORE_DELETE.
    Возврат денег на карту делает триггер expenses_AFTER_DELETE автоматически.
    """
    id_user = request.query.get('user_id')

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Шаг 1: Проверяем, существует ли расход и принадлежит ли он именно этому юзеру
            cursor.execute('''
                SELECT e.id_expense
                FROM expenses e
                JOIN accounts a ON e.id_card = a.id_card
                WHERE e.id_expense = %s AND a.id_user = %s
            ''', (expense_id, id_user))
            expense = cursor.fetchone()
            
            if not expense:
                response.status = 404
                return {'error': 'Расход не найден или доступ ограничен'}

            # Шаг 2: Вызываем удаление строки. Всю зеркальную логику выполнит СУБД!
            cursor.callproc('delete_expense', (expense_id,))
        
        conn.commit()
        return {'message': 'Операция расхода успешно удалена, баланс и цели скорректированы базой данных.'}
    except Exception as e:
        conn.rollback()
        response.status = 500
        return {'error': 'Ошибка при удалении расходов', 'detail': str(e)}
    finally:
        conn.close()