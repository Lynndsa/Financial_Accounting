import re

# Регулярное выражение для проверки корректности email
email_pattern = r'^(?!.*[._%+-]{2})(?!.*[._%+-]@)[a-zA-Z]{1}[a-zA-Z0-9._%+-]{3,50}@[a-zA-Z0-9-]{2,35}\.[a-zA-Z]{2,20}$'

# Функция проверки данных, введенных при регистрации
def validate_registration(username, email, password, password2):

    # Словарь ошибок валидации
    errors = {}

    # Проверка логина на пустое значение и минимальную длину
    if not username:
        errors["username"] = "Логин не может быть пустым"
    elif len(username) < 4:
        errors["username"] = "Минимум 4 символа в логине"

    # Проверка электронной почты
    if not email:
        errors["email"] = "Email не может быть пустым"
    elif not re.match(email_pattern, email):
        errors["email"] = "Введите корректный email"

    # Проверка пароля
    if not password:
        errors["password"] = "Пароль не может быть пустым"
    elif len(password) < 6:
        errors["password"] = "Минимум 6 символов в пароле"

    # Проверка совпадения паролей
    if password != password2:
        errors["password2"] = "Пароли не совпадают"

    # Возврат списка ошибок
    return errors
