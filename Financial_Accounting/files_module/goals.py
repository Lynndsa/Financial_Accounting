"""
files_module/goals.py
API-маршруты для модуля "Копилка" (goals).

Подключите этот модуль в основном файле приложения (там же, где
уже импортируются auth.py / security.py), например:
    from files_module import goals  # noqa: F401  (роуты регистрируются при импорте)

ВРЕМЕННО (пока нет авторизации/сессий): id_user и id_card по умолчанию
берутся из констант DEFAULT_USER_ID / DEFAULT_CARD_ID ниже (1 и 2).
Если в запросе явно передан id_user - используется он, иначе дефолт.
Когда появится логин - убрать константы и брать id_user из сессии.
"""

from bottle import route, request, response
from datetime import date, datetime
from decimal import Decimal

from database.db import get_connection
from validations.goals_validation import (
    validate_create_goal,
    validate_update_goal,
    validate_id,
    validate_topup_amount,
)

# ВРЕМЕННО, пока нет авторизации/сессий: жёстко фиксируем пользователя и его карту.
# Когда появится логин - удалить эти константы и брать id_user из сессии.
DEFAULT_USER_ID = 1
DEFAULT_CARD_ID = 2


def _serialize_goal(row):
    """Приводит строку из БД к JSON-совместимому виду (Decimal/date -> str/float)."""
    result = dict(row)
    for key, value in result.items():
        if isinstance(value, Decimal):
            result[key] = float(value)
        elif isinstance(value, (date, datetime)):
            result[key] = value.isoformat()
    return result


def _get_request_data():
    """Достаёт данные запроса вне зависимости от того, JSON это или form-data."""
    if request.json:
        return request.json
    return dict(request.forms)


def _goal_belongs_to_user(conn, goal_id, id_user):
    """Проверяет, что цель с данным id принадлежит пользователю (защита от чужих id)."""
    with conn.cursor() as cursor:
        cursor.execute(
            'SELECT id FROM goals WHERE id = %s AND id_user = %s',
            (goal_id, id_user)
        )
        return cursor.fetchone() is not None


@route('/api/goals', method='GET')
def get_goals():
    """Список активных целей пользователя с прогрессом накопления."""
    id_user = request.query.get('id_user') or DEFAULT_USER_ID
    err = validate_id(id_user, 'id_user')
    if err:
        response.status = 400
        return {'error': err}

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT * FROM goals WHERE id_user = %s AND is_active = 1 '
                'ORDER BY deadline IS NULL, deadline',
                (id_user,)
            )
            rows = cursor.fetchall()

        goals_list = [_serialize_goal(row) for row in rows]
        for goal in goals_list:
            target = goal.get('target_amount') or 0
            current = goal.get('current_amount') or 0
            goal['progress_percent'] = round(min(current / target, 1) * 100, 1) if target else 0
            goal['is_completed'] = current >= target

        return {'goals': goals_list}
    except Exception as e:
        response.status = 500
        return {'error': 'Ошибка при получении целей', 'detail': str(e)}
    finally:
        conn.close()


@route('/api/goals/<goal_id:int>', method='GET')
def get_goal(goal_id):
    """Получение одной цели по id."""
    id_user = request.query.get('id_user') or DEFAULT_USER_ID
    err = validate_id(id_user, 'id_user') or validate_id(goal_id, 'id')
    if err:
        response.status = 400
        return {'error': err}

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT * FROM goals WHERE id = %s AND id_user = %s',
                (goal_id, id_user)
            )
            row = cursor.fetchone()

        if not row:
            response.status = 404
            return {'error': 'Цель не найдена'}
        return {'goal': _serialize_goal(row)}
    except Exception as e:
        response.status = 500
        return {'error': 'Ошибка при получении цели', 'detail': str(e)}
    finally:
        conn.close()


@route('/api/goals', method='POST')
def create_goal():
    """Создание новой цели (вызывает процедуру create_new_goal)."""
    data = _get_request_data()
    id_user = data.get('id_user') or DEFAULT_USER_ID

    id_err = validate_id(id_user, 'id_user')
    if id_err:
        response.status = 400
        return {'error': id_err}

    errors, cleaned = validate_create_goal(data)
    if errors:
        response.status = 400
        return {'errors': errors}

    if cleaned['id_card'] is None:
        cleaned['id_card'] = DEFAULT_CARD_ID

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # если указана карта - проверяем, что она принадлежит пользователю
            if cleaned['id_card'] is not None:
                cursor.execute(
                    'SELECT id_card FROM accounts WHERE id_card = %s AND id_user = %s',
                    (cleaned['id_card'], id_user)
                )
                if not cursor.fetchone():
                    response.status = 400
                    return {'error': 'Указанная карта не найдена или не принадлежит пользователю'}

            cursor.callproc('create_new_goal', (
                int(id_user),
                cleaned['name'],
                cleaned['target_amount'],
                cleaned['current_amount'],
                cleaned['id_card'],
                cleaned['deadline'],
                cleaned['description'],
            ))
            new_id = cursor.lastrowid

        conn.commit()
        response.status = 201
        return {'message': 'Цель успешно создана', 'id': new_id}
    except Exception as e:
        conn.rollback()
        response.status = 500
        return {'error': 'Ошибка при создании цели', 'detail': str(e)}
    finally:
        conn.close()


@route('/api/goals/<goal_id:int>', method='PUT')
def update_goal(goal_id):
    """Обновление цели: name, target_amount, deadline (процедура update_goals)."""
    data = _get_request_data()
    id_user = data.get('id_user') or DEFAULT_USER_ID

    id_err = validate_id(id_user, 'id_user') or validate_id(goal_id, 'id')
    if id_err:
        response.status = 400
        return {'error': id_err}

    errors, cleaned = validate_update_goal(data)
    if errors:
        response.status = 400
        return {'errors': errors}

    if all(value is None for value in cleaned.values()):
        response.status = 400
        return {'error': 'Не передано ни одного поля для обновления'}

    conn = get_connection()
    try:
        if not _goal_belongs_to_user(conn, goal_id, id_user):
            response.status = 404
            return {'error': 'Цель не найдена'}

        with conn.cursor() as cursor:
            cursor.callproc('update_goals', (
                goal_id,
                cleaned['name'],
                cleaned['target_amount'],
                cleaned['deadline'],
            ))
        conn.commit()
        return {'message': 'Цель успешно обновлена'}
    except Exception as e:
        conn.rollback()
        response.status = 500
        return {'error': 'Ошибка при обновлении цели', 'detail': str(e)}
    finally:
        conn.close()


@route('/api/goals/<goal_id:int>', method='DELETE')
def delete_goal(goal_id):
    """Удаление цели (процедура delete_goals)."""
    id_user = request.query.get('id_user') or DEFAULT_USER_ID
    id_err = validate_id(id_user, 'id_user') or validate_id(goal_id, 'id')
    if id_err:
        response.status = 400
        return {'error': id_err}

    conn = get_connection()
    try:
        if not _goal_belongs_to_user(conn, goal_id, id_user):
            response.status = 404
            return {'error': 'Цель не найдена'}

        with conn.cursor() as cursor:
            cursor.callproc('delete_goals', (goal_id,))
        conn.commit()
        return {'message': 'Цель успешно удалена'}
    except Exception as e:
        conn.rollback()
        response.status = 500
        return {'error': 'Ошибка при удалении цели', 'detail': str(e)}
    finally:
        conn.close()


@route('/api/goals/<goal_id:int>/topup', method='POST')
def topup_goal(goal_id):
    """
    Пополнение копилки (увеличение current_amount).
    Отдельной хранимки под это нет, поэтому используется обычный UPDATE.
    """
    data = _get_request_data()
    id_user = data.get('id_user') or DEFAULT_USER_ID
    amount = data.get('amount')

    id_err = validate_id(id_user, 'id_user') or validate_id(goal_id, 'id')
    if id_err:
        response.status = 400
        return {'error': id_err}

    amount_err = validate_topup_amount(amount)
    if amount_err:
        response.status = 400
        return {'error': amount_err}

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT current_amount, target_amount FROM goals WHERE id = %s AND id_user = %s',
                (goal_id, id_user)
            )
            row = cursor.fetchone()
            if not row:
                response.status = 404
                return {'error': 'Цель не найдена'}

            new_amount = float(row['current_amount']) + float(amount)
            cursor.execute(
                'UPDATE goals SET current_amount = %s WHERE id = %s',
                (new_amount, goal_id)
            )
        conn.commit()
        return {
            'message': 'Копилка пополнена',
            'current_amount': new_amount,
            'is_completed': new_amount >= float(row['target_amount']),
        }
    except Exception as e:
        conn.rollback()
        response.status = 500
        return {'error': 'Ошибка при пополнении копилки', 'detail': str(e)}
    finally:
        conn.close()


@route('/api/goals/<goal_id:int>/archive', method='POST')
def archive_goal(goal_id):
    """Скрыть цель без удаления (is_active = 0) - вариант мягкого удаления."""
    id_user = request.query.get('id_user') or DEFAULT_USER_ID
    id_err = validate_id(id_user, 'id_user') or validate_id(goal_id, 'id')
    if id_err:
        response.status = 400
        return {'error': id_err}

    conn = get_connection()
    try:
        if not _goal_belongs_to_user(conn, goal_id, id_user):
            response.status = 404
            return {'error': 'Цель не найдена'}

        with conn.cursor() as cursor:
            cursor.execute('UPDATE goals SET is_active = 0 WHERE id = %s', (goal_id,))
        conn.commit()
        return {'message': 'Цель архивирована'}
    except Exception as e:
        conn.rollback()
        response.status = 500
        return {'error': 'Ошибка при архивации цели', 'detail': str(e)}
    finally:
        conn.close()