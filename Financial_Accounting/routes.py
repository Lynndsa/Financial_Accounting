from bottle import route, view, post, request, redirect, template, response
from datetime import datetime
from urllib.parse import unquote

from files_module.auth import register_user
from files_module.auth import login_user

from validations.auth_validation import validate_registration

@route('/')
def home():
    return template(
        'hello_page.tpl'
    )

@route('/login_page')
def login_page():
    mode = request.query.mode or 'login'
    success = request.query.success

    success_message = ''

    if success == '1':
        success_message = 'Регистрация успешно завершена'

    return template(
        'login.tpl', 
        error='', 
        success=success_message, 
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

        redirect('/main')

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
            success='',
            errors=errors,
            username=username,
            email=email,
            password=password,
            password2=password2
        )

    ok, msg = register_user(
        username,
        email,
        password
    )

    if not ok:

        return template(
            'registration.tpl',
            error=msg,
            success='',
            errors={},
            username=username,
            email=email,
            password=password,
            password2=password2
        )

    redirect('/login_page?success=1')

@route('/main')
def main():
    username = unquote(request.get_cookie('username') or '')

    if not username:
        redirect('/')

    return template(
        'main.tpl',
        title='Главная',
        username=username
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


@route('/goals')
@view('goals')
def goals():
    return dict(
        title='Копилка',
        year=datetime.now().year
    )



@route('/personal_account')
@view('personal_account')
def personal_account():
    return dict(
        title='Личный кабинет',
        year=datetime.now().year
    )
