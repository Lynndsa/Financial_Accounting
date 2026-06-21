from bottle import route, request, response
from datetime import date, datetime
from decimal import Decimal

from database.db import get_connection
from validations.goals_validation import (
    validate_create_goal,
    validate_update_goal,
    validate_id,
    validate_topup_amount,
    validate_description,  
)


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
    """Список активных целей конкретного пользователя."""
    id_user = request.query.get('user_id')
    if not id_user:
        response.status = 400
        return {'error': 'Параметр user_id обязателен'}

    err = validate_id(id_user, 'user_id')
    if err:
        response.status = 400
        return {'error': err}

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT * FROM goals WHERE id_user = %s AND is_active = 1 '
                'ORDER BY deadline IS NULL ASC, deadline ASC',
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
    """Получение одной цели по id (с проверкой владельца)."""
    id_user = request.query.get('user_id')
    if not id_user:
        response.status = 400
        return {'error': 'Параметр user_id обязателен'}

    err = validate_id(id_user, 'user_id') or validate_id(goal_id, 'id')
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
    """Создание новой цели."""
    data = _get_request_data()
    id_user = data.get('user_id')
    id_card = data.get('id_card')

    id_err = validate_id(id_user, 'user_id')
    if id_err:
        response.status = 400
        return {'error': id_err}

    conn = get_connection()
    try:
        errors, cleaned = validate_create_goal(data, conn, id_user)
        if errors:
            response.status = 400
            return {'errors': errors}

        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT id_card FROM accounts WHERE id_card = %s AND id_user = %s',
                (id_card, id_user)
            )
            if not cursor.fetchone():
                response.status = 400
                return {'error': 'Указанный счет не найден или не принадлежит пользователю'}

            cursor.callproc('create_new_goal', (
                int(id_user),
                cleaned['name'],
                cleaned['target_amount'],
                cleaned['current_amount'],
                int(id_card),
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
    """Обновление цели."""
    data = _get_request_data()
    id_user = data.get('user_id')

    id_err = validate_id(id_user, 'user_id') or validate_id(goal_id, 'id')
    if id_err:
        response.status = 400
        return {'error': id_err}

    conn = get_connection()
    try:
        errors, cleaned = validate_update_goal(data, conn, id_user, goal_id)

        description_raw = data.get('description')
        desc_err = validate_description(description_raw)
        if desc_err:
            errors['description'] = desc_err
        else:
            if 'description' in data:
                cleaned['description'] = str(description_raw).strip() if description_raw and str(description_raw).strip() else ""
            else:
                cleaned['description'] = None

        if errors:
            response.status = 400
            return {'errors': errors}

        with conn.cursor() as cursor:
            cursor.execute(
                'SELECT name, target_amount, deadline, description FROM goals WHERE id = %s AND id_user = %s',
                (goal_id, id_user)
            )
            current_db_row = cursor.fetchone()

        if not current_db_row:
            response.status = 404
            return {'error': 'Цель не найдена'}

        final_name = cleaned['name'] if cleaned['name'] is not None else current_db_row['name']
        final_target = cleaned['target_amount'] if cleaned['target_amount'] is not None else float(current_db_row['target_amount'])
        
        if cleaned['deadline'] is not None:
            final_deadline = cleaned['deadline']
        else:
            db_deadline = current_db_row['deadline']
            final_deadline = db_deadline.isoformat() if isinstance(db_deadline, (date, datetime)) else db_deadline

        final_description = cleaned['description'] if 'description' in data else current_db_row['description']

        with conn.cursor() as cursor:
            cursor.callproc('update_goals', (
                goal_id,
                final_name,
                final_target,
                final_deadline,
                final_description
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
    """Удаление цели."""
    id_user = request.query.get('user_id')
    id_err = validate_id(id_user, 'user_id') or validate_id(goal_id, 'id')
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
    """Пополнение копилки (прибавляем к цели) со списанием с карты (вычитаем оттуда) и фиксацией расхода."""
    data = _get_request_data()
    id_user = data.get('user_id')
    amount = data.get('amount')

    # 1. Валидации ID и суммы
    id_err = validate_id(id_user, 'user_id') or validate_id(goal_id, 'id')
    if id_err:
        response.status = 400
        return {'error': id_err}

    amount_err = validate_topup_amount(amount)
    if amount_err:
        response.status = 400
        return {'error': amount_err}

    topup_sum = float(amount)
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 2. Получаем информацию о цели (копилке)
            cursor.execute(
                'SELECT name, current_amount, target_amount, id_card, is_active FROM goals WHERE id = %s AND id_user = %s',
                (goal_id, id_user)
            )
            goal_row = cursor.fetchone()
            if not goal_row:
                response.status = 404
                return {'error': 'Цель не найдена'}

            if not goal_row['is_active']:
                response.status = 400
                return {'error': 'Эта цель уже закрыта или заархивирована'}

            id_card = goal_row['id_card']
            goal_name = goal_row['name']
            
            if not id_card:
                response.status = 400
                return {'error': 'К этой цели не привязан счет/карта для списания средств'}

            # 3. Проверяем баланс карты/счета в accounts (откуда списываем)
            cursor.execute('SELECT balance FROM accounts WHERE id_card = %s', (id_card,))
            account_row = cursor.fetchone()
            if not account_row:
                response.status = 400
                return {'error': 'Привязанный к цели счет не найден'}

            if float(account_row['balance']) < topup_sum:
                response.status = 400
                return {'error': f"На счете недостаточно средств. Баланс: {account_row['balance']} ₽"}

            # 4. Категория расхода: "Копилка: Название"
            expense_cat_name = f"Копилка: {goal_name}"
            cursor.execute('SELECT id FROM expense_categories WHERE name = %s', (expense_cat_name,))
            category_row = cursor.fetchone()
            
            if category_row:
                id_category = category_row['id']
            else:
                # Если категории нет — создаем
                cursor.callproc('create_new_expense_category', (expense_cat_name,))
                cursor.execute('SELECT LAST_INSERT_ID() as id')
                id_category = cursor.fetchone()['id']

            # 5. Добавляем операцию в РАСХОДЫ (деньги ушли в копилку)
            current_date_str = date.today().isoformat()
            cursor.callproc('create_new_expenses', (
                int(id_category),
                int(id_card),
                current_date_str,
                topup_sum
            ))

            # 6. СПИСЫВАЕМ деньги с баланса карты/счета (уменьшаем баланс карты)
            cursor.execute(
                'UPDATE accounts SET balance = balance - %s WHERE id_card = %s',
                (topup_sum, id_card)
            )

            # 7. НАКАПЛИВАЕМ деньги в копилке: прибавляем сумму пополнения к текущей сумме цели (current_amount)
            new_amount = float(goal_row['current_amount']) + topup_sum
            target_amount = float(goal_row['target_amount'])
            
            # Проверяем, выполнена ли цель
            is_completed = new_amount >= target_amount
            new_active_status = 0 if is_completed else 1

            cursor.execute(
                'UPDATE goals SET current_amount = %s, is_active = %s WHERE id = %s',
                (new_amount, new_active_status, goal_id)
            )

        # Подтверждаем транзакцию
        conn.commit()
        
        return {
            'message': 'Копилка успешно пополнена, расход зафиксирован!',
            'current_amount': new_amount,
            'is_completed': is_completed,
        }

    except Exception as e:
        conn.rollback()
        response.status = 500
        import traceback
        error_details = traceback.format_exc()
        print(error_details)  # Выведет полную ошибку в терминал Питона
        return {'error': 'Ошибка при проведении транзакции пополнения', 'message': str(e), 'detail': error_details}
    finally:
        conn.close()


@route('/api/goals/<goal_id:int>/archive', method='POST')
def archive_goal(goal_id):
    """Архивация цели."""
    id_user = request.query.get('user_id')
    id_err = validate_id(id_user, 'user_id') or validate_id(goal_id, 'id')
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