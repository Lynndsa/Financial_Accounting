<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Finance Helper</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400;14..32,500;14..32,600;14..32,700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="static/content/hello_page.css">
</head>
<body>
    <header class="header">
        <div class="logo">
            <img src="static/img/ava.png" alt="" class="logo-icon" onerror="this.style.display='none'">
            <span>Finance Helper</span>
        </div>
        <form action="/login_page" method="get">
            <button class="btn-login" type="submit">Войти</button>
        </form>
    </header>

    <main class="container">
        <div class="content-left">
            <h2>Первое веб-приложение для ведения личных финансов:</h2>
            <p class="description">
                Учета доходов, расходов, управления счетами, категориями, 
                финансовыми целями, а также для анализа финансового состояния пользователя
            </p>
            <form action="/register_page" method="get">
                <button class="btn-register" type="submit">Создать профиль</button>
            </form>
        </div>
        <div class="content-right">
            <img src="static/img/misterCrabs.png" alt="Mr. Krabs with money" class="hero-image">
        </div>
    </main>
</body>
</html>
