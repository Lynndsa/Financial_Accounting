from bottle import route, view, post, request, redirect, template, response
from datetime import datetime
from urllib.parse import unquote

from files_module.auth import register_user
from files_module.auth import login_user
from files_module import goals, income, expenses
from database.db import get_connection

from validations.auth_validation import validate_registration
from validations.personal_account_validation import validate_personal_account

# Главная страница приложения
@route('/')
def home():
    return template('hello_page.tpl')

# Выход из аккаунта и удаление cookie
@route('/logout')
def logout():
    response.delete_cookie('username', path='/')
    return template('hello_page.tpl')

# Страница авторизации
@route('/login_page')
def login_page():
    return template(
        'login.tpl', 
        error='', 
        success='', 
        username='',
    )

# Обработка входа пользователя
@route('/login', method='POST')
def login():

    # Получение данных формы
    username = request.forms.getunicode('username')
    password = request.forms.getunicode('password')

    # Проверка логина и пароля
    if login_user(username, password):
        response.set_cookie(
            'username',
            username,
            secure=False,
            httponly=True,
            max_age=3600,
            path='/'
        )

        # Подключение к БД для получения данных пользователя
        conn = get_connection()

        try:
            with conn.cursor() as cursor:

                # Получение данных профиля и счета
                cursor.execute("""
                    SELECT
                        p.name,
                        p.lastname,
                        p.surname,
                        p.datebirth,
                        p.email,
                        u.username,
                        a.name_card,
                        a.balance,
                        c.name AS currency_name
                    FROM profiles p
                    JOIN user u
                        ON p.id_user = u.id_user
                    LEFT JOIN accounts a
                        ON u.id_user = a.id_user
                    LEFT JOIN currencies c
                        ON a.id_currencies = c.id_currencies
                    WHERE u.username = %s
                """, (username,))

                user_data = cursor.fetchone()

        finally:
            conn.close()

        # Открытие личного кабинета
        return template(
            'personal_account.tpl',
            title='Личный кабинет',
            year=datetime.now().year,
            user=user_data,
            errors={},
            success=''
        )

    # Вывод ошибки при неверном логине или пароле
    return template(
        'login.tpl',
        error='Неверный логин или пароль',
        success='',
        username=username
    )

# Страница регистрации
@route('/register_page')
def register_page():
    return template(
        'registration.tpl',
        error='',
        errors={},
        username='',
        email='',
        password='',
        password2=''
    )

# Обработка регистрации нового пользователя
@route('/register', method='POST')
def register():

    # Получение данных формы
    username = request.forms.getunicode('username')
    email = request.forms.getunicode('email')
    password = request.forms.getunicode('password')
    password2 = request.forms.getunicode('password2')

    # Проверка корректности введенных данных
    errors = validate_registration(username, email, password, password2)

    # Возврат формы при наличии ошибок
    if errors:
        return template(
            'registration.tpl',
            error='',
            errors=errors,
            username=username,
            email=email,
            password=password,
            password2=password2
        )

    # Создание пользователя
    ok, msg = register_user(
        None,
        None,
        None,
        None,
        username,
        email,
        password
    )

    # Обработка ошибок создания пользователя
    if not ok:
        return template(
            'registration.tpl',
            error=msg,
            errors={},
            username=username,
            email=email,
            password=password,
            password2=password2
        )

    # Переход на страницу авторизации
    return template(
        'login.tpl',
        success='Регистрация успешно завершена',
        username='',
        error=''
    )

# Открытие страницы доходов
@route('/income')
def income_page():
    # Получение имени пользователя из cookie
    username = unquote(request.get_cookie('username') or '')
    if not username:
        return redirect('/login_page')

    user_id = None
    card_id = None

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Получение id пользователя
            cursor.execute('SELECT id_user FROM user WHERE username = %s', (username,))
            user_row = cursor.fetchone()
            if user_row:
                user_id = user_row['id_user']
                
                # Получение id счета пользователя
                cursor.execute('SELECT id_card FROM accounts WHERE id_user = %s LIMIT 1', (user_id,))
                card_row = cursor.fetchone()
                if card_row:
                    card_id = card_row['id_card']
    except Exception as e:
        print(f"Ошибка при получении данных сессии: {e}")
    finally:
        conn.close()

    # Если у нового пользователя ещё нет счетов, подставим заглушку, чтобы не падало
    if not card_id:
        card_id = 0 

    # Передача данных в шаблон
    return template(
        'income.tpl',
        title='Поступления',
        year=datetime.now().year,
        user_id=user_id,
        card_id=card_id
    )


# Открытие страницы расходов
@route('/expenses')
def expenses_page():
    # Получение имя пользователя из куки авторизации
    username = unquote(request.get_cookie('username') or '')
    if not username:
        return redirect('/login_page')

    user_id = None
    card_id = None

    # Получение id_user и его id_card
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id_user FROM user WHERE username = %s', (username,))
            user_row = cursor.fetchone()
            if user_row:
                user_id = user_row['id_user']
                
                # Поиск любой доступный счёт (карту) этого пользователя в таблице accounts
                cursor.execute('SELECT id_card FROM accounts WHERE id_user = %s LIMIT 1', (user_id,))
                card_row = cursor.fetchone()
                if card_row:
                    card_id = card_row['id_card']
    except Exception as e:
        print(f"Ошибка при получении данных сессии для расходов: {e}")
    finally:
        conn.close()

    # Если у пользователя ещё нет счетов, подставим заглушку, чтобы не падало
    if not card_id:
        card_id = 0 

    # Передача данных в шаблон tpl расходов
    return template(
        'expenses.tpl',
        title='Расходы',
        year=datetime.now().year,
        user_id=user_id,
        card_id=card_id
    )

# Открытие страницы накоплений
@route('/goals')
def goals_page():
    # 1. Проверка авторизацию через куки
    username = unquote(request.get_cookie('username') or '')
    if not username:
        return redirect('/login_page')

    user_id = None
    card_id = None

    # Получение реальныого ID пользователя и его счета
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id_user FROM user WHERE username = %s', (username,))
            user_row = cursor.fetchone()
            if user_row:
                user_id = user_row['id_user']
                
                # Поиск активного счёта
                cursor.execute('SELECT id_card FROM accounts WHERE id_user = %s LIMIT 1', (user_id,))
                card_row = cursor.fetchone()
                if card_row:
                    card_id = card_row['id_card']
    except Exception as e:
        print(f"Ошибка при получении данных сессии для целей: {e}")
    finally:
        conn.close()

    if not card_id:
        card_id = 0 

    # Передача переменных в шаблон tpl
    return template(
        'goals.tpl',
        title='Копилка',
        year=datetime.now().year,
        user_id=user_id,
        card_id=card_id
    )

# Отображение личного кабинета пользователя
@route('/personal_account')
def personal_account():

    # Получение логина пользователя из cookie
    username = unquote(request.get_cookie('username') or '')

    # Проверка авторизации
    if not username:
        return redirect('/')

    conn = get_connection()

    try:
        with conn.cursor() as cursor:

            # Получение информации о пользователе и его счете
            cursor.execute("""
                SELECT
                    p.name,
                    p.lastname,
                    p.surname,
                    p.datebirth,
                    p.email,
                    u.username,
                    a.name_card,
                    a.balance,
                    c.name AS currency_name
                FROM profiles p
                JOIN user u
                    ON p.id_user = u.id_user
                LEFT JOIN accounts a
                    ON u.id_user = a.id_user
                LEFT JOIN currencies c
                    ON a.id_currencies = c.id_currencies
                WHERE u.username = %s
            """, (username,))

            user_data = cursor.fetchone()

            if not user_data:
                response.delete_cookie('username', path='/')
                return template('hello_page.tpl')

    finally:
        conn.close()

    # Отображение страницы личного кабинета
    return template(
        'personal_account.tpl',
        title='Личный кабинет',
        year=datetime.now().year,
        user=user_data,
        errors={},
        success=''
    )

# Обновление данных личного кабинета
@route('/update_personal_account', method='post')
def update_personal_account():

    # Получение логина текущего пользователя
    username = unquote(request.get_cookie('username') or '')

    if not username:
        return redirect('/')

    # Получение данных формы
    name = request.forms.getunicode('name')
    lastname = request.forms.getunicode('lastname')
    surname = request.forms.getunicode('surname')
    datebirth = request.forms.getunicode('datebirth')
    name_card = request.forms.getunicode('name_card')

    # Проверка корректности введенных данных
    errors = validate_personal_account(name, lastname, surname, datebirth, name_card)
    
    conn = get_connection()

    if errors:

        try:
            with conn.cursor() as cursor:

                cursor.execute("""
                    SELECT
                        p.name,
                        p.lastname,
                        p.surname,
                        p.datebirth,
                        p.email,
                        u.username,
                        a.name_card,
                        a.balance,
                        c.name AS currency_name
                    FROM profiles p
                    JOIN user u
                        ON p.id_user = u.id_user
                    LEFT JOIN accounts a
                        ON u.id_user = a.id_user
                    LEFT JOIN currencies c
                        ON a.id_currencies = c.id_currencies
                    WHERE u.username = %s
                """, (username,))

                user_data = cursor.fetchone()

                if not user_data:
                    response.delete_cookie('username', path='/')
                    return template('hello_page.tpl')

            conn.commit()

        finally:
            conn.close()

        return template(
            'personal_account.tpl',
            title='Личный кабинет',
            year=datetime.now().year,
            user=user_data,
            errors=errors,
            success=''
        )

    
    try:
        with conn.cursor() as cursor:

            # Обновление профиля пользователя
            cursor.execute("""
                UPDATE profiles p
                JOIN user u ON p.id_user=u.id_user
                SET
                    p.name=%s,
                    p.lastname=%s,
                    p.surname=%s,
                    p.datebirth=%s
                WHERE u.username=%s
            """, (
                name,
                lastname,
                surname,
                datebirth,
                username
            ))

            # Обновление названия счета
            cursor.execute("""
                UPDATE accounts a
                JOIN user u ON a.id_user=u.id_user
                SET a.name_card=%s
                WHERE u.username=%s
            """, (
                name_card,
                username
            ))

            # Повторное получение данных после изменения
            cursor.execute("""
                SELECT
                    p.name,
                    p.lastname,
                    p.surname,
                    p.datebirth,
                    p.email,
                    u.username,
                    a.name_card,
                    a.balance,
                    c.name AS currency_name
                FROM profiles p
                JOIN user u
                    ON p.id_user = u.id_user
                LEFT JOIN accounts a
                    ON u.id_user = a.id_user
                LEFT JOIN currencies c
                    ON a.id_currencies = c.id_currencies
                WHERE u.username = %s
            """, (username,))

            user_data = cursor.fetchone()

            if not user_data:
                response.delete_cookie('username', path='/')
                return template('hello_page.tpl')

        # Подтверждение транзакции
        conn.commit()

    finally:
        conn.close()

    # Вывод страницы с сообщением об успешном обновлении
    return template(
        'personal_account.tpl',
        title='Личный кабинет',
        year=datetime.now().year,
        user=user_data,
        errors={},
        success='Данные успешно обновлены'
    )
