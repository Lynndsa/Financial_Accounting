from database.db import get_connection
from files_module.security import hash_password, verify_password


def register_user(username, email, password):

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute(
            "SELECT id_user FROM user WHERE username=%s",
            (username,)
        )

        if cur.fetchone():
            return False, "Логин уже существует"

        cur.execute(
            "SELECT email FROM profiles WHERE email=%s",
            (email,)
        )

        if cur.fetchone():
            return False, "Email уже существует"

        password_hash = hash_password(password)

        cur.execute("""
            INSERT INTO user
            (username, password)
            VALUES (%s, %s)
        """, (
            username,
            password_hash
        ))

        user_id = cur.lastrowid

        cur.execute("""
            INSERT INTO profiles
            (email, id_user)
            VALUES (%s, %s)
        """, (
            email,
            user_id
        ))

        conn.commit()

        return True, "OK"

    except pymysql.Error as e:
        conn.rollback()
        return False, f"Ошибка базы данных: {str(e)}"

    finally:
        cur.close()
        conn.close()


def login_user(username, password):

    conn = get_connection()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT *
            FROM user
            WHERE username=%s
        """, (username,))

        user = cur.fetchone()

        if not user:
            return False

        return verify_password(
            password,
            user["password"]
        )

    finally:
        cur.close()
        conn.close()