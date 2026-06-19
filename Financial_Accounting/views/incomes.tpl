<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Доходы</title>
</head>
<body>

    <h1>Модуль «Доходы»</h1>
    
    <div>
        <h2>Добавить доход</h2>
        <form id="addIncomeForm">
            <div>
                <label for="incomeCategory">Категория дохода:</label>
                <select id="incomeCategory" required></select>
            </div>
            
            <div>
                <label for="incomeSum">Сумма (руб.):</label>
                <input type="number" id="incomeSum" step="0.01" min="0.01" required>
                <span id="sumError" style="color: red; display: none;"></span>
            </div>

            <div>
                <label for="incomeDate">Дата операции (необязательно):</label>
                <input type="date" id="incomeDate">
            </div>

            <button type="submit">Сохранить операцию</button>
        </form>
    </div>

    <br><hr><br>

    <div>
        <h2>Создать новую категорию</h2>
        <form id="addCategoryForm">
            <div>
                <input type="text" id="newCategoryName" placeholder="Название категории" required>
                <span id="catError" style="color: red; display: none;"></span>
            </div>
            <button type="submit">Добавить категорию</button>
        </form>
    </div>

    <br><hr><br>

    <div>
        <h2>Фильтры и Аналитика</h2>
        <div>
            <label for="filterMonth">Выберите месяц:</label>
            <input type="month" id="filterMonth">
        </div>
        <div>
            <label for="filterCategory">Категория:</label>
            <select id="filterCategory">
                <option value="all">Все категории</option>
            </select>
        </div>
    </div>

    <div>
        <h3>Данные для диаграммы (сгруппировано):</h3>
        <ul id="chartDataList">
            </ul>
    </div>

    <br><hr><br>

    <div>
        <h2>История операций</h2>
        <table border="1" id="historyTable">
            <thead>
                <tr>
                    <th>Дата</th>
                    <th>Категория</th>
                    <th>Счёт / Карта</th>
                    <th>Сумма</th>
                </tr>
            </thead>
            <tbody>
                </tbody>
        </table>
    </div>

<script>
    // Текущий месяц по умолчанию (ГГГГ-ММ)
    const currentMonthStr = new Date().toISOString().slice(0, 7);
    document.getElementById('filterMonth').value = currentMonthStr;
    
    // Загрузка данных при старте страницы
    document.addEventListener("DOMContentLoaded", () => {
        loadCategories();
        loadChartData();
        loadHistory();
        
        // Перезагрузка при изменении фильтров
        document.getElementById('filterMonth').addEventListener('change', () => {
            loadChartData();
            loadHistory();
        });
        document.getElementById('filterCategory').addEventListener('change', loadHistory);
    });

    // 1. Загрузка категорий в выпадающие списки
    async function loadCategories() {
        try {
            const res = await fetch('/api/income-categories');
            const data = await res.json();
            
            const mainSelect = document.getElementById('incomeCategory');
            const filterSelect = document.getElementById('filterCategory');
            
            mainSelect.innerHTML = '';
            filterSelect.innerHTML = '<option value="all">Все категории</option>';
            
            data.categories.forEach(cat => {
                mainSelect.innerHTML += `<option value="${cat.id}">${cat.name}</option>`;
                filterSelect.innerHTML += `<option value="${cat.id}">${cat.name}</option>`;
            });
        } catch (err) {
            console.error("Ошибка загрузки категорий:", err);
        }
    }

    // 2. Сохранение операции дохода
    document.getElementById('addIncomeForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const payload = {
            id_category: document.getElementById('incomeCategory').value,
            sum: document.getElementById('incomeSum').value,
            date_time: document.getElementById('incomeDate').value
        };
        
        const res = await fetch('/api/incomes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const result = await res.json();
        if (res.status === 200 || res.status === 201) {
            document.getElementById('addIncomeForm').reset();
            document.getElementById('sumError').style.display = 'none';
            loadChartData();
            loadHistory();
            alert('Доход добавлен!');
        } else {
            if (result.errors && result.errors.sum) {
                document.getElementById('sumError').innerText = result.errors.sum;
                document.getElementById('sumError').style.display = 'inline';
            } else {
                alert(result.error || 'Ошибка сохранения');
            }
        }
    });

    // 3. Создание новой категории
    document.getElementById('addCategoryForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const catName = document.getElementById('newCategoryName').value;
        
        const res = await fetch('/api/income-categories', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: catName })
        });
        
        const result = await res.json();
        if (res.status === 201) {
            document.getElementById('newCategoryName').value = '';
            document.getElementById('catError').style.display = 'none';
            await loadCategories();
            alert('Категория создана!');
        } else {
            document.getElementById('catError').innerText = result.error || 'Ошибка';
            document.getElementById('catError').style.display = 'inline';
        }
    });

    // 4. Получение данных для диаграммы (просто списком, чтобы верстальщик привязал к плагину графиков)
    async function loadChartData() {
        const month = document.getElementById('filterMonth').value;
        try {
            const res = await fetch(`/api/incomes/chart?month=${month}`);
            const data = await res.json();
            
            const list = document.getElementById('chartDataList');
            list.innerHTML = '';
            
            if (!data.chart_data || data.chart_data.length === 0) {
                list.innerHTML = '<li>Нет данных за этот месяц</li>';
                return;
            }
            
            data.chart_data.forEach(item => {
                list.innerHTML += `<li>${item.category}: <strong>${item.sum.toFixed(2)} ₽</strong></li>`;
            });
        } catch (err) {
            console.error("Ошибка аналитики:", err);
        }
    }

    // 5. Загрузка таблицы истории
    async function loadHistory() {
        const month = document.getElementById('filterMonth').value;
        const category = document.getElementById('filterCategory').value;
        
        try {
            const res = await fetch(`/api/incomes/history?month=${month}&id_category=${category}`);
            const data = await res.json();
            
            const tbody = document.querySelector('#historyTable tbody');
            tbody.innerHTML = '';
            
            if (!data.history || data.history.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;">Операций не найдено</td></tr>';
                return;
            }
            
            data.history.forEach(item => {
                const dateObj = new Date(item.date_time);
                const formattedDate = dateObj.toLocaleDateString('ru-RU');

                tbody.innerHTML += `
                    <tr>
                        <td>${formattedDate}</td>
                        <td>${item.category_name}</td>
                        <td>${item.name_card || 'Основной счет'}</td>
                        <td>+ ${item.sum.toFixed(2)} ₽</td>
                    </tr>
                `;
            });
        } catch (err) {
            console.error("Ошибка истории:", err);
        }
    }
</script>

</body>
</html>