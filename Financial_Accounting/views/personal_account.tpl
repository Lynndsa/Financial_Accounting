% rebase('layout.tpl', title=title, year=year)

<h2>Личный кабинет</h2>

% if success:
    <div>
        {{success}}
    </div>
% end

<form action="/update_personal_account" method="post">

    <p>Имя</p>
    <input type="text" name="name" value="{{user['name'] or ''}}">

    % if errors.get('name'):
        <div>{{errors['name']}}</div>
    % end

    <p>Фамилия</p>
    <input type="text" name="lastname" value="{{user['lastname'] or ''}}">

     % if errors.get('lastname'):
        <div>{{errors['lastname']}}</div>
    % end

    <p>Отчество</p>
    <input type="text" name="surname" value="{{user['surname'] or ''}}">

    % if errors.get('surname'):
        <div>{{errors['surname']}}</div>
    % end

    <p>Дата рождения</p>
    <input type="date" name="datebirth" value="{{user['datebirth']}}">

    % if errors.get('datebirth'):
        <div>{{errors['datebirth']}}</div>
    % end

    <p>Логин</p>
    <input type="text" value="{{user['username']}}" readonly>

    <p>Email</p>
    <input type="text" value="{{user['email']}}" readonly>

    <hr>

    <h3>Счёт</h3>

    <p>Название счёта</p>
    <input type="text" name="name_card" value="{{user['name_card'] or ''}}">

    % if errors.get('name_card'):
        <div>{{errors['name_card']}}</div>
    % end

    <p>Баланс</p>
    <input type="text" value="{{user['balance']}} ₽" readonly>

    <p>Валюта</p>
    <input type="text" value="Рубли" readonly>

    <br><br>

    <button type="submit">
        Сохранить
    </button>

</form>
