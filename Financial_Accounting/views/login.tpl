<head>
    <meta charset="utf-8">
    <title>Авторизация</title>
</head>
<body>

    <h2>Авторизация</h2>
    <h3>Введите ваш логин и пароль</h3>

    % if error:
        <div>
            {{error}}
        </div>
    % end

    % if success:
        <div>
            {{success}}
        </div>
    % end   

    <form action="/login" method="post">
        <input type="text" id="auth_username" name="username" placeholder="Логин" value="{{username}}"><br><br>

        <input type="password" id="auth_password" name="password" placeholder="Пароль"><br><br>

        <button type="submit">Вход</button>
    </form>

    <br>

    <button onclick="window.location='/register_page'">
        Регистрация
    </button>

   
</body>
</html>