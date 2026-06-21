<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link rel="stylesheet" type="text/css" href="/static/content/bootstrap.min.css" />
    <!-- Стиль берётся строго из файла site.css -->
    <link rel="stylesheet" type="text/css" href="/static/content/site.css" />
    <script src="/static/scripts/modernizr-2.6.2.js"></script>
</head>

<body>
    <!-- Левая панель навигации (Сайдбар) -->
    <aside class="sidebar">
        <div class="menu-top">
            <a href="/personal_account" class="menu-item">Личный кабинет</a>
            <a href="/income" class="menu-item">Доходы</a>
            <a href="/expenses" class="menu-item">Расходы</a>
            <a href="/goals" class="menu-item">Цели</a>
        </div>

        <div class="logout-container">
            <a href="/logout" class="btn-logout-sidebar">Выход</a>
        </div>
    </aside>

    <!-- Основной контент справа -->
    <div class="container body-content">
        {{!base}}
    </div>

    <script src="/static/scripts/jquery-1.10.2.js"></script>
    <script src="/static/scripts/bootstrap.js"></script>
    <script src="/static/scripts/respond.js"></script>

</body>
</html>