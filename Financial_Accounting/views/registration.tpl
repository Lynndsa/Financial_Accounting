<head>
    <meta charset="utf-8">
    <title>Регистрация</title>
</head>
<body>

     <button onclick="window.location='/login_page'">
        Назад
    </button>

    <h2>Регистрация</h2>
    <h3>Введите ваш логин, почту, пароль</h3>

    % if error:
        <div>
            {{error}}
        </div>
    % end

    % if errors:
        <div>
            % for field, message in errors.items():
                <p>{{message}}</p>
            % end
        </div>
    % end

    <form action="/register" method="post">

        <input type="text"
               name="username"
               placeholder="Логин"
               value="{{username}}"><br><br>

        <input type="email"
               name="email"
               placeholder="Email"
               value="{{email}}"><br><br>

        <input type="password"
               name="password"
               placeholder="Пароль"
               value="{{password}}"><br><br>

        <input type="password"
               name="password2"
               placeholder="Повторный пароль"
               value="{{password2}}"><br><br>

        <button type="submit">
            Регистрация
        </button>

    </form>

</body>
