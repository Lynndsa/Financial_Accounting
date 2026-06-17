"""
Routes and views for the bottle application.
"""

from bottle import route, view
from datetime import datetime


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