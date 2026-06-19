from bottle import route, view, post, request, redirect, template, response
from datetime import datetime
from urllib.parse import unquote

from files_module.auth import register_user
from files_module.auth import login_user
from files_module import goals, income
from database.db import get_connection

from validations.auth_validation import validate_registration

@route('/')
def home():
    return template('hello_page.tpl')

@route('/logout')
def logout():
    response.delete_cookie('username', path='/')
    return template('hello_page.tpl')

@route('/login_page')
def login_page():
    return template(
        'login.tpl', 
        error='', 
        success='', 
        username='',
    )

@route('/login', method='POST')
def login():
    username = request.forms.getunicode('username')
    password = request.forms.getunicode('password')

    if login_user(username, password):
        response.set_cookie(
            'username',
            username,
            secure=False,
            httponly=True,
            max_age=3600,
            path='/'
        )
        return template(
            'personal_account.tpl',
            title='Личный кабинет',
            year=datetime.now().year
        )

    return template(
        'login.tpl',
        error='Неверный логин или пароль',
        success='',
        username=username
    )

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

@route('/register', method='POST')
def register():
    username = request.forms.getunicode('username')
    email = request.forms.getunicode('email')
    password = request.forms.getunicode('password')
    password2 = request.forms.getunicode('password2')

    errors = validate_registration(username, email, password, password2)
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

    ok, msg = register_user(
        None,
        None,
        None,
        None,
        username,
        email,
        password
    )

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

    return template(
        'login.tpl',
        success='Регистрация успешно завершена',
        username='',
        error=''
    )


@route('/income')
def income_page():
    # 1. Получаем имя пользователя из куки авторизации
    username = unquote(request.get_cookie('username') or '')
    if not username:
        return redirect('/login_page')

    user_id = None
    card_id = None

    # 2. Идём в БД, чтобы узнать id_user и его id_card
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Находим ID пользователя по его логину
            cursor.execute('SELECT id_user FROM user WHERE username = %s', (username,))
            user_row = cursor.fetchone()
            if user_row:
                user_id = user_row['id_user']
                
                # Ищем любой доступный счёт (карту) этого пользователя в таблице accounts
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

    # 3. Передаем всё это напрямую в шаблон tpl
    return template(
        'income.tpl',
        title='Доходы',
        year=datetime.now().year,
        user_id=user_id,
        card_id=card_id
    )


@route('/expenses')
def expenses_page():
    return template('expenses.tpl', title='Расходы', year=datetime.now().year)


@route('/goals')
def goals_page():
    # 1. Проверяем авторизацию через куки
    username = unquote(request.get_cookie('username') or '')
    if not username:
        return redirect('/login_page')

    user_id = None
    card_id = None

    # 2. Получаем реальные ID пользователя и его счета
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id_user FROM user WHERE username = %s', (username,))
            user_row = cursor.fetchone()
            if user_row:
                user_id = user_row['id_user']
                
                # Ищем активный счёт
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

    # 3. Передаем переменные в шаблон tpl
    return template(
        'goals.tpl',  # убедись, что файл в паблике называется goals.tpl
        title='Копилка',
        year=datetime.now().year,
        user_id=user_id,
        card_id=card_id
    )


@route('/personal_account')
def personal_account():
    username = unquote(request.get_cookie('username') or '')
    if not username:
        return redirect('/')

    return template(
        'personal_account.tpl',
        title='Личный кабинет',
        year=datetime.now().year
    )