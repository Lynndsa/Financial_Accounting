<head>
    <meta charset="utf-8">
    <title>Авторизация</title>
</head>
<body>

% if mode == 'register':
    <div id="login_block" style="display:none;">
% else:
    <div id="login_block">
% end

    <h2>Авторизация</h2>
    <h3>Введите ваш логин и пароль</h3>

    % if error:
        <div>
            {{error}}
        </div>
    % end

    <form action="/login" method="post">
        <input type="text" name="username" placeholder="Логин"><br><br>

        <input type="password" name="password" placeholder="Пароль"><br><br>

        <button type="submit">Вход</button>
    </form>

    <br>

    <button onclick="showRegister()">
        Регистрация
    </button>

</div>

% if mode != 'register':
    <div id="register_block" style="display:none;">
% else:
    <div id="register_block">
% end

    <button onclick="showLogin()">
        Назад
    </button>

    <h2>Регистрация</h2>
    <h3>Введите ваш логин, почту, пароль</h3>

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
               placeholder="Логин"><br><br>

        <input type="email"
               name="email"
               placeholder="Email"><br><br>

        <input type="password"
               name="password"
               placeholder="Пароль"><br><br>

        <input type="password"
               name="password2"
               placeholder="Повторный пароль"><br><br>

        <button type="submit">
            Регистрация
        </button>

    </form>

</div>

<script>

function showRegister() {
    document.getElementById("login_block").style.display = "none";
    document.getElementById("register_block").style.display = "block";
}

function showLogin() {
    document.getElementById("register_block").style.display = "none";
    document.getElementById("login_block").style.display = "block";
}

</script>

</body>
</html>