from database import get_connection
import bcrypt


def register_user(username, email, password):
    conn = get_connection()
    cur = conn.cursor()

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

    password_hash = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

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

    cur.close()
    conn.close()

    return True, "OK"

def login_user(username, password):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM user
        WHERE username=%s
    """, (username,))

    user = cur.fetchone()

    cur.close()
    conn.close()

    if not user:
        return False

    return bcrypt.checkpw(
        password.encode(),
        user["password"].encode()
    )
