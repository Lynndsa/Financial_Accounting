% rebase('layout', title='Регистрация')

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400;14..32,500;14..32,600;14..32,700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="static/content/registration.css">

<main class="main-content">

    <!-- Контейнер формы регистрации -->
    <div class="auth-wrapper">
        <div class="auth-card">
            <h2>Регистрация</h2>
            <h3>Введите ваш логин, почту и пароль</h3>

            % if error:
                <div class="alert alert-error">{{error}}</div>
            % end

            % if errors:
                <div class="alert alert-error">
                    % for field, message in errors.items():
                        <p>{{message}}</p>
                    % end
                </div>
            % end

            <form action="/register" method="post">
                <div class="input-group">
                    <label for="reg_username">Логин</label>
                    <input type="text" id="reg_username" name="username" placeholder="Логин" value="{{username}}">
                </div>

                <div class="input-group">
                    <label for="reg_email">Почта</label>
                    <input type="email" id="reg_email" name="email" placeholder="Email" value="{{email}}">
                </div>

                <div class="input-group">
                    <label for="reg_password">Пароль</label>
                    <input type="password" id="reg_password" name="password" placeholder="Пароль" value="{{password}}">
                </div>

                <div class="input-group">
                    <label for="reg_password2">Пароль</label>
                    <input type="password" id="reg_password2" name="password2" placeholder="Повторите пароль" value="{{password2}}">
                </div>

                <button type="submit" class="btn-submit">Регистрация</button>
            </form>
        </div>
    </div>
</main>