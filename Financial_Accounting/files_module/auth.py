import pymysql, hashlib
from database.db import get_connection

# Функция регистрации нового пользователя
def register_user(name, lastname, surname, datebirth, username, email, password):

    # Создание соединения с базой данных
    conn = get_connection()
    cur = conn.cursor()

    try:

        # Вызов процедуры создания пользователя
        cur.callproc(
            'create_new_user',
            (
                name,
                lastname,
                surname,
                datebirth,
                username,
                email,
                password
            )
        )

        # Подтверждение изменений
        conn.commit()

        return True, 'OK'

    # Обработка нарушения уникальности логина или email
    except pymysql.err.IntegrityError as e:

        conn.rollback()

        if "user.username" in str(e):
            return False, "Логин уже существует"

        if "profiles.email" in str(e):
            return False, "Email уже существует"

        return False, "Нарушено ограничение уникальности"

    except pymysql.Error as e:
        conn.rollback()
        return False, f"Ошибка базы данных: {str(e)}"

    finally:
        cur.close()
        conn.close()

# Функция авторизации пользователя
def login_user(username, password):

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.callproc(
            'check_password',
            (
                username,
                password
            )
        )

        result = cur.fetchall()

        if result and result[0]['id_user'] is not None:
            return True

        return False

    except pymysql.Error:
        return False

    finally:
        cur.close()
        conn.close()