% rebase('layout', title=title, year=year)
<!-- если ваш layout-файл называется иначе (например _Layout) - поправьте имя выше -->

<h2>{{title}}</h2>

<div id="goal-form-message" style="display:none;"></div>

<form id="goal-form" class="form-inline" style="margin-bottom: 20px;">
    <input type="hidden" id="goal-id" value="" />

    <div class="form-group">
        <label for="goal-name">Название</label>
        <input type="text" id="goal-name" class="form-control" placeholder="Например, Отпуск" required maxlength="100" />
    </div>

    <div class="form-group">
        <label for="goal-target">Цель, ₽</label>
        <input type="number" id="goal-target" class="form-control" placeholder="50000" min="0.01" step="0.01" required />
    </div>

    <div class="form-group">
        <label for="goal-current">Уже накоплено, ₽</label>
        <input type="number" id="goal-current" class="form-control" placeholder="0" min="0" step="0.01" />
    </div>

    <div class="form-group">
        <label for="goal-deadline">Дедлайн</label>
        <input type="date" id="goal-deadline" class="form-control" />
    </div>

    <div class="form-group">
        <label for="goal-description">Описание</label>
        <input type="text" id="goal-description" class="form-control" placeholder="Необязательно" maxlength="200" />
    </div>

    <button type="submit" class="btn btn-primary" id="goal-submit-btn">Создать цель</button>
    <button type="button" class="btn btn-default" id="goal-cancel-btn" style="display:none;">Отмена</button>
</form>

<table class="table table-bordered" id="goals-table">
    <thead>
        <tr>
            <th>Название</th>
            <th>Накоплено</th>
            <th>Цель</th>
            <th>Прогресс</th>
            <th>Дедлайн</th>
            <th>Описание</th>
            <th>Действия</th>
        </tr>
    </thead>
    <tbody id="goals-table-body">
        <tr><td colspan="7">Загрузка...</td></tr>
    </tbody>
</table>

<script>
(function () {
    var apiBase = '/api/goals';

    var tableBody = document.getElementById('goals-table-body');
    var form = document.getElementById('goal-form');
    var idField = document.getElementById('goal-id');
    var nameField = document.getElementById('goal-name');
    var targetField = document.getElementById('goal-target');
    var currentField = document.getElementById('goal-current');
    var deadlineField = document.getElementById('goal-deadline');
    var descriptionField = document.getElementById('goal-description');
    var submitBtn = document.getElementById('goal-submit-btn');
    var cancelBtn = document.getElementById('goal-cancel-btn');
    var messageBox = document.getElementById('goal-form-message');

    function showMessage(text, isError) {
        messageBox.textContent = text;
        messageBox.className = isError ? 'alert alert-danger' : 'alert alert-success';
        messageBox.style.display = 'block';
        setTimeout(function () { messageBox.style.display = 'none'; }, 4000);
    }

    // Общая обёртка над fetch: достаёт текст ответа и аккуратно парсит JSON.
    // Если бэкенд вернул не JSON (например, HTML-страницу 404, потому что
    // роут не зарегистрирован) - кидает понятную ошибку вместо молчаливого падения.
    function apiRequest(url, options) {
        return fetch(url, options).then(function (res) {
            return res.text().then(function (text) {
                var data;
                try {
                    data = text ? JSON.parse(text) : {};
                } catch (e) {
                    console.error('Ответ сервера:', text);
                    throw new Error('Сервер вернул не JSON (код ' + res.status + '). Проверь консоль и что роут /api/goals подключён в приложении.');
                }
                if (!res.ok && !data.error && !data.errors) {
                    throw new Error('Ошибка сервера, код ' + res.status);
                }
                return data;
            });
        });
    }

    function resetForm() {
        form.reset();
        idField.value = '';
        currentField.disabled = false;
        descriptionField.disabled = false;
        submitBtn.textContent = 'Создать цель';
        cancelBtn.style.display = 'none';
    }

    function loadGoals() {
        apiRequest(apiBase)
            .then(function (data) {
                if (data.error) {
                    tableBody.innerHTML = '<tr><td colspan="7">' + data.error + '</td></tr>';
                    return;
                }
                renderGoals(data.goals || []);
            })
            .catch(function (err) {
                tableBody.innerHTML = '<tr><td colspan="7">Не удалось загрузить цели: ' + err.message + '</td></tr>';
                console.error(err);
            });
    }

    function renderGoals(goals) {
        if (!goals.length) {
            tableBody.innerHTML = '<tr><td colspan="7">Пока нет целей</td></tr>';
            return;
        }

        tableBody.innerHTML = '';

        goals.forEach(function (goal) {
            var row = document.createElement('tr');
            var progress = goal.progress_percent || 0;

            row.innerHTML =
                '<td>' + goal.name + '</td>' +
                '<td>' + goal.current_amount + ' ₽</td>' +
                '<td>' + goal.target_amount + ' ₽</td>' +
                '<td>' +
                    '<div class="progress" style="margin-bottom:0;">' +
                        '<div class="progress-bar" style="width:' + progress + '%;">' + progress + '%</div>' +
                    '</div>' +
                '</td>' +
                '<td>' + (goal.deadline || '-') + '</td>' +
                '<td>' + (goal.description || '-') + '</td>' +
                '<td></td>';

            var actionsCell = row.lastElementChild;

            var topupBtn = document.createElement('button');
            topupBtn.className = 'btn btn-success btn-xs';
            topupBtn.textContent = 'Пополнить';
            topupBtn.onclick = function () { topupGoal(goal.id); };

            var editBtn = document.createElement('button');
            editBtn.className = 'btn btn-default btn-xs';
            editBtn.textContent = 'Изменить';
            editBtn.onclick = function () { editGoal(goal); };

            var deleteBtn = document.createElement('button');
            deleteBtn.className = 'btn btn-danger btn-xs';
            deleteBtn.textContent = 'Удалить';
            deleteBtn.onclick = function () { deleteGoal(goal.id); };

            actionsCell.appendChild(topupBtn);
            actionsCell.appendChild(document.createTextNode(' '));
            actionsCell.appendChild(editBtn);
            actionsCell.appendChild(document.createTextNode(' '));
            actionsCell.appendChild(deleteBtn);

            tableBody.appendChild(row);
        });
    }

    function editGoal(goal) {
        // процедура update_goals меняет только name, target_amount, deadline,
        // поэтому "накоплено" и "описание" в режиме редактирования блокируем
        idField.value = goal.id;
        nameField.value = goal.name;
        targetField.value = goal.target_amount;
        currentField.value = goal.current_amount;
        currentField.disabled = true;
        deadlineField.value = goal.deadline || '';
        descriptionField.value = goal.description || '';
        descriptionField.disabled = true;
        submitBtn.textContent = 'Сохранить изменения';
        cancelBtn.style.display = 'inline-block';
        window.scrollTo(0, form.offsetTop);
    }

    function deleteGoal(id) {
        if (!confirm('Удалить эту цель?')) return;
        apiRequest(apiBase + '/' + id, { method: 'DELETE' })
            .then(function (data) {
                if (data.error) {
                    showMessage(data.error, true);
                    return;
                }
                showMessage(data.message, false);
                loadGoals();
            })
            .catch(function (err) {
                showMessage(err.message, true);
                console.error(err);
            });
    }

    function topupGoal(id) {
        var amount = prompt('Сумма пополнения, ₽:');
        if (amount === null) return;
        apiRequest(apiBase + '/' + id + '/topup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount: amount })
        })
            .then(function (data) {
                if (data.error) {
                    showMessage(data.error, true);
                    return;
                }
                showMessage(data.message, false);
                loadGoals();
            })
            .catch(function (err) {
                showMessage(err.message, true);
                console.error(err);
            });
    }

    cancelBtn.addEventListener('click', resetForm);

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        var id = idField.value;

        if (id) {
            apiRequest(apiBase + '/' + id, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: nameField.value,
                    target_amount: targetField.value,
                    deadline: deadlineField.value || null
                })
            })
                .then(function (data) {
                    if (data.error || data.errors) {
                        showMessage(data.error || JSON.stringify(data.errors), true);
                        return;
                    }
                    showMessage(data.message, false);
                    resetForm();
                    loadGoals();
                })
                .catch(function (err) {
                    showMessage(err.message, true);
                    console.error(err);
                });
        } else {
            apiRequest(apiBase, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: nameField.value,
                    target_amount: targetField.value,
                    current_amount: currentField.value || 0,
                    deadline: deadlineField.value || null,
                    description: descriptionField.value || null
                })
            })
                .then(function (data) {
                    if (data.error || data.errors) {
                        showMessage(data.error || JSON.stringify(data.errors), true);
                        return;
                    }
                    showMessage(data.message, false);
                    resetForm();
                    loadGoals();
                })
                .catch(function (err) {
                    showMessage(err.message, true);
                    console.error(err);
                });
        }
    });

    loadGoals();
})();
</script>
