% rebase('layout.tpl', title=title, year=year)

<!-- Подключаем стили личного кабинета из файла site.css -->
<link rel="stylesheet" type="text/css" href="/static/content/personal_account.css" />

<main class="main-content">
    <!-- Обновленное красивое приветствие -->
    <h1 class="welcome-title text-center">Рады видеть вас, <span class="accent-name">{{user['username']}}</span></h1>

    % if success:
        <div class="alert alert-success text-center">{{success}}</div>
    % end

    <form action="/update_personal_account" method="post" class="account-grid">
        
        <!-- ЛЕВАЯ КАРТОЧКА: ЛИЧНЫЕ ДАННЫЕ -->
        <div class="account-card user-data-card">
            
            <!-- Ряд: Фамилия и Имя на одной линии -->
            <div class="form-row-twin">
                <div class="form-group">
                    <input type="text" name="lastname" placeholder="Фамилия" value="{{user['lastname'] or ''}}">
                    % if errors.get('lastname'):
                        <div class="validation-error-text">{{errors['lastname']}}</div>
                    % end
                </div>
                
                <div class="form-group">
                    <input type="text" name="name" placeholder="Имя" value="{{user['name'] or ''}}">
                    % if errors.get('name'):
                        <div class="validation-error-text">{{errors['name']}}</div>
                    % end
                </div>
            </div>

            <!-- Отчество -->
            <div class="form-group full-width">
                <input type="text" name="surname" placeholder="Отчество" value="{{user['surname'] or ''}}">
                % if errors.get('surname'):
                    <div class="validation-error-text">{{errors['surname']}}</div>
                % end
            </div>

            <!-- Дата рождения -->
            <div class="form-group full-width">
                <input type="date" name="datebirth" value="{{user['datebirth']}}">
                % if errors.get('datebirth'):
                    <div class="validation-error-text">{{errors['datebirth']}}</div>
                % end
            </div>

            <!-- Почта (Email) -->
            <div class="form-group full-width">
                <input type="text" value="{{user['email']}}" readonly class="readonly-field">
            </div>

            <!-- Логин -->
            <div class="form-group full-width">
                <input type="text" value="Логин: {{user['username']}}" readonly class="readonly-field">
            </div>

            <!-- Большая кнопка изменения данных внизу карточки -->
            <button type="submit" class="btn-account-submit">Изменить данные</button>
        </div>

        <!-- ПРАВАЯ КАРТОЧКА: БАЛАНС И СЧЁТ -->
        <div class="account-card balance-card">
            <h2 class="balance-label">Баланс счета</h2>
            <div class="balance-value">{{user['balance']}} р.</div>
            
            <!-- Дополнительное редактирование названия счета -->
            <div class="form-group card-name-group">
                <label for="name_card">Название счёта:</label>
                <input type="text" id="name_card" name="name_card" placeholder="Основной счёт" value="{{user['name_card'] or ''}}">
                % if errors.get('name_card'):
                    <div class="validation-error-text">{{errors['name_card']}}</div>
                % end
            </div>
        </div>

    </form>
</main>
