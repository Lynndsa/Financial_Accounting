import re

email_pattern = r'^(?!.*[._%+-]{2})(?!.*[._%+-]@)[a-zA-Z]{1}[a-zA-Z0-9._%+-]{3,50}@[a-zA-Z0-9-]{2,35}\.[a-zA-Z]{2,20}$'


def validate_registration(username, email, password, password2):

    errors = {}

    if not username:
        errors["username"] = "Логин не может быть пустым"
    elif len(username) < 4:
        errors["username"] = "Минимум 4 символа"

    if not email:
        errors["email"] = "Email не может быть пустым"
    elif not re.match(email_pattern, email):
        errors["email"] = "Введите корректный email"

    if not password:
        errors["password"] = "Пароль не может быть пустым"
    elif len(password) < 6:
        errors["password"] = "Минимум 6 символов"

    if password != password2:
        errors["password2"] = "Пароли не совпадают"

    return errors
