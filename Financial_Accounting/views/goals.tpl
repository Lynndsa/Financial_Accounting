% rebase('layout', title=title, year=year)
<!-- если ваш layout-файл называется иначе (например _Layout) - поправьте имя выше -->

<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Финансовые цели</title>
    <link rel="preconnect" href="https://googleapis.com">
    <link rel="preconnect" href="https://gstatic.com" crossorigin>
    <link href="https://googleapis.com/css2?family=Inter:opsz,wght@14..32,400;14..32,500;14..32,600;14..32,700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="static/content/goals.css">
</head>
<body>
    <!-- Левая панель навигации (Сайдбар) -->
    <aside class="sidebar">
        <nav class="menu-top">
            <a href="/dashboard" class="menu-item">Личный кабинет</a>
            <a href="/incomes" class="menu-item">Доходы</a>
            <a href="/expenses" class="menu-item">Расходы</a>
            <a href="/goals" class="menu-item active">Цели</a>
        </nav>
        <a href="/logout" class="menu-item exit-btn">Выход</a>
    </aside>

    <!-- Основной контент справа -->
    <main class="main-content">
        <!-- Блок сообщений JS -->
        <div id="goal-form-message" style="display:none;"></div>

        <!-- Верхняя панель действий -->
        <div class="action-bar">
            <button type="button" class="btn btn-action" onclick="toggleForm()">Добавить цель</button>
            <button type="button" class="btn btn-action">Редактировать цели</button>
        </div>

        <!-- Скрытая/всплывающая форма управления (динамически стилизована) -->
        <div class="form-container" id="form-wrapper" style="display: none;">
            <form id="goal-form">
                <input type="hidden" id="goal-id" value="" />
                
                <div class="form-grid">
                    <div class="form-group">
                        <label for="goal-name">Название</label>
                        <input type="text" id="goal-name" placeholder="Например, Отпуск" required maxlength="100" />
                    </div>
                    <div class="form-group">
                        <label for="goal-target">Цель, ₽</label>
                        <input type="number" id="goal-target" placeholder="50000" min="0.01" step="0.01" required />
                    </div>
                    <div class="form-group">
                        <label for="goal-current">Уже накоплено, ₽</label>
                        <input type="number" id="goal-current" placeholder="0" min="0" step="0.01" />
                    </div>
                    <div class="form-group">
                        <label for="goal-deadline">Дедлайн</label>
                        <input type="date" id="goal-deadline" />
                    </div>
                    <div class="form-group full-width">
                        <label for="goal-description">Описание</label>
                        <input type="text" id="goal-description" placeholder="Необязательно" maxlength="200" />
                    </div>
                </div>

                <div class="form-buttons">
                    <button type="submit" class="btn btn-submit" id="goal-submit-btn">Создать цель</button>
                    <button type="button" class="btn btn-cancel" id="goal-cancel-btn">Отмена</button>
                </div>
            </form>
        </div>

        <!-- Контейнер для карточек прогресса целей -->
        <div class="goals-wrapper">
            <div class="goals-card-list" id="goals-table-body">
                <!-- Сюда ваш JS будет вставлять карточки целей вместо строк <tr> -->
                <div class="loading-status">Загрузка целей...</div>
            </div>
        </div>
    </main>

    <!-- Небольшой скрипт для открытия/закрытия формы -->
    <script>
        function toggleForm() {
            var form = document.getElementById('form-wrapper');
            form.style.display = (form.style.display === 'none') ? 'block' : 'none';
        }
        // Интегрируем кнопку отмены с вашей функцией resetForm
        document.getElementById('goal-cancel-btn').addEventListener('click', function() {
            document.getElementById('form-wrapper').style.display = 'none';
        });
    </script>
</body>
</html>
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

    // Общая обёртка над fetch для работы с JSON
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
        if (cancelBtn) cancelBtn.style.display = 'none';
        var formWrapper = document.getElementById('form-wrapper');
        if (formWrapper) formWrapper.style.display = 'none'; // Закрываем контейнер формы
    }

    function loadGoals() {
        apiRequest(apiBase)
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
        var formWrapper = document.getElementById('form-wrapper');
        if (formWrapper) formWrapper.style.display = 'block'; // Показываем скрытую форму при редактировании

        idField.value = goal.id;
        nameField.value = goal.name;
        targetField.value = goal.target_amount;
        currentField.value = goal.current_amount;
        currentField.disabled = true;
        deadlineField.value = goal.deadline || '';
        descriptionField.value = goal.description || '';
        descriptionField.disabled = true;
        submitBtn.textContent = 'Сохранить изменения';
        if (cancelBtn) cancelBtn.style.display = 'inline-block';
        window.scrollTo(0, form.offsetTop - 100);
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
