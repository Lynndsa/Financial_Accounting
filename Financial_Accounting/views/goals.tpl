% rebase('layout', title=title, year=year)

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

    <div class="form-group" id="current-amount-group">
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
    // Получаем ID авторизованного юзера и его счета из Bottle шаблонизатора
    var CURRENT_USER_ID = {{user_id}};
    var CURRENT_CARD_ID = {{card_id}};

    var apiBase = '/api/goals';

    var tableBody = document.getElementById('goals-table-body');
    var form = document.getElementById('goal-form');
    var idField = document.getElementById('goal-id');
    var nameField = document.getElementById('goal-name');
    var targetField = document.getElementById('goal-target');
    var currentField = document.getElementById('goal-current');
    var currentGroup = document.getElementById('current-amount-group');
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

    function apiRequest(url, options) {
        return fetch(url, options).then(function (res) {
            return res.text().then(function (text) {
                var data;
                try {
                    data = text ? JSON.parse(text) : {};
                } catch (e) {
                    console.error('Ответ сервера:', text);
                    throw new Error('Сервер вернул не JSON (код ' + res.status + ').');
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
        currentGroup.style.display = 'inline-block';
        currentField.disabled = false;
        descriptionField.disabled = false;
        submitBtn.textContent = 'Создать цель';
        if (cancelBtn) cancelBtn.style.display = 'none';
        var formWrapper = document.getElementById('form-wrapper');
        if (formWrapper) formWrapper.style.display = 'none'; // Закрываем контейнер формы
    }

    function loadGoals() {
        // Добавляем параметр user_id в GET запрос
        apiRequest(apiBase + '?user_id=' + CURRENT_USER_ID)
            .then(function (data) {
                if (data.error) {
                    tableBody.innerHTML = '<div class="loading-status">' + data.error + '</div>';
                    return;
                }
                renderGoals(data.goals || []);
            })
            .catch(function (err) {
                tableBody.innerHTML = '<div class="loading-status">Не удалось загрузить цели: ' + err.message + '</div>';
                console.error(err);
            });
    }

    // РЕНДЕРИНГ КАРТОЧЕК: Переводит список целей из табличного формата в блочные карточки с прогресс-барами
    function renderGoals(goals) {
        if (!goals.length) {
            tableBody.innerHTML = '<div class="loading-status">Пока нет целей</div>';
            return;
        }

        tableBody.innerHTML = '';

        goals.forEach(function (goal) {
            var item = document.createElement('div');
            item.className = 'goal-item';

            var progress = goal.progress_percent || 0;
            if (progress > 100) progress = 100; // Ограничиваем заполнение шкалы до 100%

            // Генерируем адаптивную разметку для карточки с прогресс-баром
            item.innerHTML =
                '<div class="goal-header">' +
                    '<div class="goal-title">' + goal.name + ' — ' + goal.current_amount + ' ₽ из ' + goal.target_amount + ' ₽</div>' +
                    '<div class="goal-actions"></div>' + 
                '</div>' +
                '<div class="progress-bar-container">' +
                    '<div class="progress-bar-fill" style="width:' + progress + '%; display: flex; align-items: center; justify-content: center; font-weight: 700; color: #4c0505; font-size: 1.1rem;">' + 
                        (progress > 5 ? progress + '%' : '') + 
                    '</div>' +
                '</div>';

            var actionsContainer = item.querySelector('.goal-actions');

            var topupBtn = document.createElement('button');
            topupBtn.className = 'btn-inline btn-topup';
            topupBtn.textContent = 'Пополнить';
            topupBtn.onclick = function () { topupGoal(goal.id); };

            var editBtn = document.createElement('button');
            editBtn.className = 'btn-inline btn-edit';
            editBtn.textContent = 'Изменить';
            editBtn.onclick = function () { editGoal(goal); };

            var deleteBtn = document.createElement('button');
            deleteBtn.className = 'btn-inline btn-delete';
            deleteBtn.textContent = 'Удалить';
            deleteBtn.onclick = function () { deleteGoal(goal.id); };

            actionsContainer.appendChild(topupBtn);
            actionsContainer.appendChild(editBtn);
            actionsContainer.appendChild(deleteBtn);

            tableBody.appendChild(item);
        });
    }

    function editGoal(goal) {
        idField.value = goal.id;
        nameField.value = goal.name;
        targetField.value = goal.target_amount;
        
        currentField.value = goal.current_amount;
        currentGroup.style.display = 'none'; 
        
        deadlineField.value = goal.deadline || '';
        descriptionField.value = goal.description || '';
        descriptionField.disabled = false; 
        
        submitBtn.textContent = 'Сохранить изменения';
        if (cancelBtn) cancelBtn.style.display = 'inline-block';
        window.scrollTo(0, form.offsetTop - 100);
    }

    function deleteGoal(id) {
        if (!confirm('Удалить эту цель?')) return;
        // Передаем user_id параметром строки в DELETE
        apiRequest(apiBase + '/' + id + '?user_id=' + CURRENT_USER_ID, { method: 'DELETE' })
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
        var amountStr = prompt('Сумма пополнения, ₽:');
        if (amountStr === null) return;
        
        var amount = parseFloat(amountStr.trim());
        if (isNaN(amount) || amount <= 0 || !isFinite(amount)) {
            showMessage('Пожалуйста, введите корректную сумму больше 0', true);
            return;
        }

        apiRequest(apiBase + '/' + id + '/topup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount: amount, user_id: CURRENT_USER_ID }) // Добавили user_id
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

        if (CURRENT_CARD_ID === 0) {
            alert('У вас нет активных счетов! Сначала добавьте карту или счет.');
            return;
        }

        var id = idField.value;

        if (id) {
            // Запрос на ОБНОВЛЕНИЕ (PUT)
            apiRequest(apiBase + '/' + id, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: CURRENT_USER_ID, // Передаем владельца
                    name: nameField.value,
                    target_amount: targetField.value,
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
        } else {
            // Запрос на СОЗДАНИЕ (POST)
            apiRequest(apiBase, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: CURRENT_USER_ID, // Реальный юзер
                    id_card: CURRENT_CARD_ID, // Реальный счет
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