<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Авторизация</title>
    <link rel="preconnect" href="https://googleapis.com">
    <link rel="preconnect" href="https://gstatic.com" crossorigin>
    <link href="https://googleapis.com/css2?family=Inter:opsz,wght@14..32,400;14..32,500;14..32,600;14..32,700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="static/content/login.css">
</head>
<body>
    <div class="auth-card">
        <h2>Авторизация</h2>
        <h3>Введите ваш логин и пароль</h3>

        <!-- Блок уведомлений -->
        % if error:
            <div class="alert alert-error">{{error}}</div>
        % end
        % if success:
            <div class="alert alert-success">{{success}}</div>
        % end   

        <form action="/login" method="post">
            <div class="input-group">
                <label for="auth_username">Логин</label>
                <input type="text" id="auth_username" name="username" placeholder="Логин" value="{{username}}">
            </div>

            <div class="input-group">
                <label for="auth_password">Пароль</label>
                <input type="password" id="auth_password" name="password" placeholder="Пароль">
            </div>

            <button type="submit" class="btn-submit">Войти</button>
        </form>

        <button class="btn-link" onclick="window.location='/register_page'">
            Нет аккаунта?
        </button>
    </div>
</body>
</html>
