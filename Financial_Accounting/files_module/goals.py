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

    # Валидация входного ID пользователя
    err = validate_id(id_user, 'user_id')
    if err:
        response.status = 400
        return {'error': err}

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Выборка активных целей с сортировкой (сначала с дедлайнами, затем без)
            cursor.execute(
                'SELECT * FROM goals WHERE id_user = %s AND is_active = 1 '
                'ORDER BY deadline IS NULL ASC, deadline ASC',
                (id_user,)
            )
            rows = cursor.fetchall()

        # Сериализация строк и расчет вычисляемых полей для фронтенда (прогресс и статус)
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

    # Валидация ID пользователя и ID искомой цели
    err = validate_id(id_user, 'user_id') or validate_id(goal_id, 'id')
    if err:
        response.status = 400
        return {'error': err}

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Строгая проверка: ищем запись, принадлежащую именно этому user_id
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
    """Создание новой цели с вызовом процедуры create_new_goal (строго 7 параметров)."""
    data = _get_request_data()
    id_user = data.get('user_id')
    id_card = data.get('id_card')

    id_err = validate_id(id_user, 'user_id')
    if id_err:
        response.status = 400
        return {'error': id_err}

    conn = get_connection()
    try:
        # Комплексная валидация полей формы и проверка на уникальность имени в БД
        errors, cleaned = validate_create_goal(data, conn, id_user)
        if errors:
            response.status = 400
            return {'errors': errors}

        with conn.cursor() as cursor:
            # Проверяем, существует ли привязываемая карта и принадлежит ли она юзеру
            cursor.execute(
                'SELECT id_card FROM accounts WHERE id_card = %s AND id_user = %s',
                (id_card, id_user)
            )
            if not cursor.fetchone():
                response.status = 400
                return {'error': 'Указанный счет не найден или не принадлежит пользователю'}

            # Передаем строго 7 параметров в соответствии с PROCEDURE create_new_goal
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
    """Обновление метаданных цели через процедуру update_goals."""
    data = _get_request_data()
    id_user = data.get('user_id')

    id_err = validate_id(id_user, 'user_id') or validate_id(goal_id, 'id')
    if id_err:
        response.status = 400
        return {'error': id_err}

    conn = get_connection()
    try:
        # Валидация основных изменяемых полей (лимит имени 50 символов и уникальность)
        errors, cleaned = validate_update_goal(data, conn, id_user, goal_id)

        # Отдельная валидация и очистка текстового описания
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
            # Запрашиваем текущие значения из БД для реализации частичного обновления (coalesce на бэке)
            cursor.execute(
                'SELECT name, target_amount, deadline, description FROM goals WHERE id = %s AND id_user = %s',
                (goal_id, id_user)
            )
            current_db_row = cursor.fetchone()

        if not current_db_row:
            response.status = 404
            return {'error': 'Цель не найдена'}

        # Формируем итоговые значения: если поле не передано в запросе, берем старое значение из БД
        final_name = cleaned['name'] if cleaned['name'] is not None else current_db_row['name']
        final_target = cleaned['target_amount'] if cleaned['target_amount'] is not None else float(current_db_row['target_amount'])
        
        if cleaned['deadline'] is not None:
            final_deadline = cleaned['deadline']
        else:
            db_deadline = current_db_row['deadline']
            final_deadline = db_deadline.isoformat() if isinstance(db_deadline, (date, datetime)) else db_deadline

        final_description = cleaned['description'] if 'description' in data else current_db_row['description']

        with conn.cursor() as cursor:
            # Вызов процедуры перезаписи измененных метаданных цели
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
    """Удаление цели через процедуру delete_goals."""
    id_user = request.query.get('user_id')
    id_err = validate_id(id_user, 'user_id') or validate_id(goal_id, 'id')
    if id_err:
        response.status = 400
        return {'error': id_err}

    conn = get_connection()
    try:
        # Безопасность: проверяем, что удаляемая запись принадлежит автору запроса
        if not _goal_belongs_to_user(conn, goal_id, id_user):
            response.status = 404
            return {'error': 'Цель не найдена'}

        with conn.cursor() as cursor:
            # Процедура удаляет цель (или меняет флаг удаления в зависимоти от логики БД)
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
    Пополнение копилки делегировано триггерам БД.
    Бэкенд только валидирует баланс и инкрементирует текущую сумму цели.
    """
    data = _get_request_data()
    id_user = data.get('user_id')
    amount = data.get('amount')

    # Проверка корректности переданных ID и суммы пополнения
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
            # 1. Загружаем текущие параметры финансовой цели
            cursor.execute(
                'SELECT current_amount, target_amount, id_card, is_active FROM goals WHERE id = %s AND id_user = %s',
                (goal_id, id_user)
            )
            goal_row = cursor.fetchone()
            if not goal_row:
                response.status = 404
                return {'error': 'Цель не найдена'}

            # Проверка бизнес-логики: нельзя слать деньги в закрытую цель
            if not goal_row['is_active']:
                response.status = 400
                return {'error': 'Эта цель уже закрыта или заархивирована'}

            id_card = goal_row['id_card']
            if not id_card:
                response.status = 400
                return {'error': 'К этой цели не привязан счет для списания'}

            # 2. Проверяем баланс карты на стороне бэкенда перед транзакцией
            cursor.execute('SELECT balance FROM accounts WHERE id_card = %s', (id_card,))
            account_row = cursor.fetchone()
            if not account_row:
                response.status = 400
                return {'error': 'Привязанный к цели счет не найден'}

            if float(account_row['balance']) < topup_sum:
                response.status = 400
                return {'error': f"На счете недостаточно средств. Баланс: {account_row['balance']} ₽"}

            # 3. ОБНОВЛЕНИЕ СУММЫ ЦЕЛИ
            # Рассчитываем новое состояние накоплений и проверяем, выполнена ли цель
            new_amount = float(goal_row['current_amount']) + topup_sum
            target_amount = float(goal_row['target_amount'])
            
            is_completed = new_amount >= target_amount
            new_active_status = 0 if is_completed else 1

            # Выполняем обычный UPDATE. Автоматический расчет разницы и логирование системного 
            # расхода со счета переложено на СУБД (триггер goals_AFTER_UPDATE).
            cursor.execute(
                'UPDATE goals SET current_amount = %s, is_active = %s WHERE id = %s',
                (new_amount, new_active_status, goal_id)
            )

        conn.commit()
        return {
            'message': 'Копилка успешно пополнена, изменения обработаны триггером БД!',
            'current_amount': new_amount,
            'is_completed': is_completed,
        }
    except Exception as e:
        conn.rollback()
        response.status = 500
        return {'error': 'Ошибка при пополнении копилки', 'detail': str(e)}
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
        # Проверка принадлежности цели текущему пользователю
        if not _goal_belongs_to_user(conn, goal_id, id_user):
            response.status = 404
            return {'error': 'Цель не найдена'}

        with conn.cursor() as cursor:
            # Деактивация записи без удаления физической строки из таблицы
            cursor.execute('UPDATE goals SET is_active = 0 WHERE id = %s', (goal_id,))
        conn.commit()
        return {'message': 'Цель архивирована'}
    except Exception as e:
        conn.rollback()
        response.status = 500
        return {'error': 'Ошибка при архивации цели', 'detail': str(e)}
    finally:
        conn.close()