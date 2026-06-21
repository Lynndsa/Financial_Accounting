from bottle import route, request, response, redirect, template
from datetime import date, datetime
from decimal import Decimal
from urllib.parse import unquote

from database.db import get_connection
from validations.incomes_validation import (
    validate_id,
    validate_category_name,
    validate_create_income
)

def _serialize_row(row):
    result = dict(row)
    for key, value in result.items():
        if isinstance(value, Decimal):
            result[key] = float(value)
        elif isinstance(value, (date, datetime)):
            result[key] = value.isoformat()
    return result


def _get_request_data():
    if request.json:
        return request.json
    return dict(request.forms)


@route('/api/income-categories', method='GET')
def get_income_categories():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM income_categories ORDER BY name ASC')
            rows = cursor.fetchall()
        return {'categories': [dict(r) for r in rows]}
    except Exception as e:
        response.status = 500
        return {'error': 'Ошибка при получении категорий доходов', 'detail': str(e)}
    finally:
        conn.close()


@route('/api/income-categories', method='POST')
def create_income_category():
    data = _get_request_data()
    name = data.get('name')

    err = validate_category_name(name)
    if err:
        response.status = 400
        return {'error': err}

    name_clean = str(name).strip()
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id FROM income_categories WHERE name = %s', (name_clean,))
            if cursor.fetchone():
                response.status = 400
                return {'error': 'Категория с таким названием уже существует'}

            cursor.callproc('create_new_income_categories', (name_clean,))
        conn.commit()
        response.status = 201
        return {'message': 'Категория доходов успешно добавлена'}
    except Exception as e:
        conn.rollback()
        response.status = 500
        return {'error': 'Ошибка при добавлении категории', 'detail': str(e)}
    finally:
        conn.close()


@route('/api/incomes', method='POST')
def add_income():
    data = _get_request_data()
    user_id = data.get('user_id')

    errors, cleaned = validate_create_income(data)
    if errors:
        response.status = 400
        return {'errors': errors}

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT id_card FROM accounts WHERE id_card = %s AND id_user = %s',
                (cleaned['id_card'], user_id)
            )
            if not cursor.fetchone():
                response.status = 400
                return {'error': 'Указанный счёт не найден или не принадлежит пользователю'}

            # Триггер incomes_AFTER_INSERT автоматически обновит баланс в accounts
            cursor.callproc('create_new_income', (
                cleaned['id_category'],
                cleaned['id_card'],
                cleaned['date_time'],
                cleaned['sum']
            ))
            
        conn.commit()
        response.status = 201
        return {'message': 'Доход успешно зафиксирован'}
    except Exception as e:
        conn.rollback()
        response.status = 500
        import traceback
        print(traceback.format_exc())
        return {'error': 'Ошибка при создании операции дохода', 'detail': str(e)}
    finally:
        conn.close()


@route('/api/incomes/history', method='GET')
def get_incomes_history():
    user_id = request.query.get('user_id')
    selected_month = request.query.get('month') or date.today().strftime('%Y-%m')
    id_category = request.query.get('id_category') or 'all'

    query = """
        SELECT i.id_income, i.sum, i.date_time, c.name AS category_name, a.name_card
        FROM incomes i
        JOIN income_categories c ON i.id_category = c.id
        JOIN accounts a ON i.id_card = a.id_card
        WHERE a.id_user = %s 
          AND DATE_FORMAT(i.date_time, '%%Y-%%m') = %s
    """
    params = [user_id, selected_month]

    if id_category != 'all':
        query += " AND i.id_category = %s"
        params.append(int(id_category))

    query += " ORDER BY i.date_time DESC, i.id_income DESC"

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        return {'history': [_serialize_row(r) for r in rows]}
    except Exception as e:
        response.status = 500
        return {'error': 'Ошибка при получении истории доходов', 'detail': str(e)}
    finally:
        conn.close()


@route('/api/incomes/chart', method='GET')
def get_incomes_chart_data():
    user_id = request.query.get('user_id')
    selected_month = request.query.get('month') or date.today().strftime('%Y-%m')

    query = """
        SELECT c.name AS category_name, SUM(i.sum) AS total_sum
        FROM incomes i
        JOIN income_categories c ON i.id_category = c.id
        JOIN accounts a ON i.id_card = a.id_card
        WHERE a.id_user = %s 
          AND DATE_FORMAT(i.date_time, '%%Y-%%m') = %s
        GROUP BY c.id, c.name
        ORDER BY total_sum DESC
    """

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, [user_id, selected_month])
            rows = cursor.fetchall()
        
        chart_data = [{'category': r['category_name'], 'sum': float(r['total_sum'])} for r in rows]
        return {'chart_data': chart_data}
    except Exception as e:
        response.status = 500
        return {'error': 'Ошибка при формировании данных диаграммы', 'detail': str(e)}
    finally:
        conn.close()


@route('/api/incomes/<income_id:int>', method='DELETE')
def delete_income(income_id):
    """Удаление операции дохода. Корректировка баланса происходит автоматически в СУБД."""
    id_user = request.query.get('user_id')

    id_err = validate_id(id_user, 'user_id') or validate_id(income_id, 'id')
    if id_err:
        response.status = 400
        return {'error': id_err}

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Проверяем, принадлежит ли доход пользователю
            cursor.execute('''
                SELECT i.id_income 
                FROM incomes i
                JOIN accounts a ON i.id_card = a.id_card
                WHERE i.id_income = %s AND a.id_user = %s
            ''', (income_id, id_user))
            
            if not cursor.fetchone():
                response.status = 404
                return {'error': 'Доход не найден или доступ ограничен'}

            # Триггер incomes_AFTER_DELETE автоматически вычтет сумму из accounts
            cursor.execute('DELETE FROM incomes WHERE id_income = %s', (income_id,))
        
        conn.commit()
        return {'message': 'Операция успешно удалена!'}
        
    except Exception as e:
        conn.rollback()
        response.status = 500
        import traceback
        print(traceback.format_exc())
        return {'error': 'Ошибка при удалении дохода', 'detail': str(e)}
    finally:
        conn.close()


@route('/income')
def income_page():
    username = unquote(request.get_cookie('username') or '')
    if not username:
        return redirect('/login_page')

    user_id = None
    card_id = None

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id_user FROM user WHERE username = %s', (username,))
            user_row = cursor.fetchone()
            if user_row:
                user_id = user_row['id_user']
                
                cursor.execute('SELECT id_card FROM accounts WHERE id_user = %s LIMIT 1', (user_id,))
                card_row = cursor.fetchone()
                if card_row:
                    card_id = card_row['id_card']
    except Exception as e:
        print(f"Ошибка при получении данных сессии: {e}")
    finally:
        conn.close()

    if not card_id:
        card_id = 0 

    return template(
        'income.tpl',
        title='Поступления',
        year=datetime.now().year,
        user_id=user_id,
        card_id=card_id
    )