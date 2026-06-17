% rebase('layout.tpl', title=title)

<head>
    <meta charset="utf-8">
    <title>Авторизация</title>
</head>
<body>

<div id="login_block">

    <h2>Название</h2>

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

<div id="register_block" style="display:none;">

    <button onclick="showLogin()">
        Назад
    </button>

    <h2>Название</h2>

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