from bottle import route, view, post, request, redirect, template, response
from datetime import datetime
from urllib.parse import unquote

from files_module.auth import register_user
from files_module.auth import login_user

from files_module.validation import validate_registration

@route('/')
@view('login')
def login():
    return dict(
        title='Вход',
        year=datetime.now().year
    )


@route('/income')
@view('income')
def income():
    return dict(
        title='Доходы',
        year=datetime.now().year
    )


@route('/expenses')
@view('expenses')
def expenses():
    return dict(
        title='Расходы',
        year=datetime.now().year
    )
def home():
    return template(
        'login.tpl',
        title='Авторизация',
        error='',
        errors={},
        username=''
    )

@route('/login', method='POST')
def login():

    username = request.forms.getunicode('username')
    password = request.forms.getunicode('password')

    if login_user(username, password):

        response.set_cookie(
            'username',
            username
        )

        redirect('/main')

    return template(
        'login.tpl',
        title='Авторизация',
        error='Неверный логин или пароль',
        errors={},
        username=username
    )

@route('/register', method='POST')
def register():
    username = request.forms.getunicode('username')
    email = request.forms.getunicode('email')
    password = request.forms.getunicode('password')
    password2 = request.forms.getunicode('password2')

    errors = validate_registration(
        username,
        email,
        password,
        password2
    )

    if errors:

        return template(
            'login.tpl',
            title='Авторизация',
            error='',
            errors = errors
        )

    ok, msg = register_user(
        username,
        email,
        password
    )

    if not ok:

        return template(
            'login.tpl',
            title='Авторизация',
            error=msg,
            errors={}
        )


@route('/goals')
@view('goals')
def goals():
    return dict(
        title='Копилка',
        year=datetime.now().year
    redirect('/')


@route('/main')
def main():
    username = unquote(request.get_cookie('username') or '')

    if not username:
        redirect('/')

    return template(
        'main',
        title='Главная',
        username=username
    )


@route('/personal_account')
@view('personal_account')
def personal_account():
    return dict(
        title='Личный кабинет',
        year=datetime.now().year
    )