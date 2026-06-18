from bottle import route, view, post, request, redirect, template, response
from datetime import datetime
from urllib.parse import unquote

from files_module.auth import register_user
from files_module.auth import login_user
from files_module import goals

from validations.auth_validation import validate_registration

@route('/')
def home():
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
def personal_account():

    username = unquote(request.get_cookie('username') or '')

    if not username:
        return redirect('/')

    return template(
        'personal_account.tpl',
        title='Личный кабинет',
        year=datetime.now().year
    )
