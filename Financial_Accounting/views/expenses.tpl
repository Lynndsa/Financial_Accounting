% rebase('layout', title=title, year=year)
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>{{title}} — Копилка</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background-color: #f4f6f9;
            color: #333;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        h1, h2, h3 { color: #2c3e50; }
        
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .card {
            background: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-control {
            width: 100%;
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
            box-sizing: border-box;
        }
        
        button {
            background-color: #e74c3c; /* Красный цвет для кнопки расхода */
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            width: 100%;
        }
        button:hover { background-color: #c0392b; }
        .btn-secondary { background-color: #34495e; }
        .btn-secondary:hover { background-color: #2c3e50; }
        
        #historyCard {
            display: none;
            margin-top: 20px;
            animation: fadeIn 0.3s ease-in-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        table th, table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        table th { background-color: #f8f9fa; }
        
        .chart-container {
            position: relative;
            margin: auto;
            height: 220px;
            width: 220px;
        }
    </style>
</head>
<body>

<div class="container">
    <h1>{{title}} ({{year}} г.)</h1>
    
    <div class="grid">
        <div class="card">
            <h2>Ввод данных</h2>
            <form id="addExpenseForm">
                <div class="form-group">
                    <label>Категория расхода:</label>
                    <select id="expenseCategory" class="form-control" required></select>
                </div>
                <div class="form-group">
                    <label>Сумма (руб.):</label>
                    <input type="number" id="expenseSum" class="form-control" step="0.01" min="0.01" required>
                </div>
                <div class="form-group">
                    <label>Дата операции:</label>
                    <input type="date" id="expenseDate" class="form-control">
                    <small style="color: #7f8c8d; display: block; margin-top: 4px;">По умолчанию будет выбран сегодняшний день</small>
                </div>
                <button type="submit">Сохранить расход</button>
            </form>
            
            <br>
            <form id="addCategoryForm">
                <div class="form-group">
                    <label>Новая категория расходов:</label>
                    <input type="text" id="newCategoryName" class="form-control" placeholder="Название" required>
                </div>
                <button type="submit" class="btn-secondary">Создать категорию</button>
            </form>
        </div>

        <div class="card" style="text-align: center;">
            <h2>Визуализация расходов</h2>
            <div class="form-group" style="max-width: 150px; margin: 0 auto 15px;">
                <input type="month" id="filterMonth" class="form-control">
            </div>
            
            <div class="chart-container">
                <canvas id="expenseDonutChart"></canvas>
            </div>
            <p id="noDataMessage" style="color: #7f8c8d; display: none;">Нет расходов за этот период</p>
            
            <br>
            <button type="button" class="btn-secondary" id="toggleHistoryBtn">Показать историю операций</button>
        </div>
    </div>

    <div class="card" id="historyCard">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h2>История операций</h2>
            <div class="form-group" style="width: 200px; margin: 0;">
                <select id="filterCategory" class="form-control">
                    <option value="all">Все категории</option>
                </select>
            </div>
        </div>
        
        <table id="historyTable">
            <thead>
                <tr>
                    <th>Дата</th>
                    <th>Категория</th>
                    <th>Счёт</th>
                    <th>Сумма</th>
                    <th>Действие</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>
    </div>
</div>

<script>
    const CURRENT_USER_ID = {{user_id}};
    const CURRENT_CARD_ID = {{card_id}};

    const currentMonthStr = new Date().toISOString().slice(0, 7);
    document.getElementById('filterMonth').value = currentMonthStr;
    
    let myChart = null;

    document.addEventListener("DOMContentLoaded", () => {
        loadCategories();
        loadChartData();
        
        document.getElementById('filterMonth').addEventListener('change', () => {
            loadChartData();
            if(document.getElementById('historyCard').style.display === 'block') {
                loadHistory();
            }
        });
        document.getElementById('filterCategory').addEventListener('change', loadHistory);

        document.getElementById('toggleHistoryBtn').addEventListener('click', () => {
            const historyCard = document.getElementById('historyCard');
            if (historyCard.style.display === 'block') {
                historyCard.style.display = 'none';
                document.getElementById('toggleHistoryBtn').innerText = 'Показать историю операций';
            } else {
                historyCard.style.display = 'block';
                document.getElementById('toggleHistoryBtn').innerText = 'Скрыть историю операций';
                loadHistory();
            }
        });
    });

    async function loadCategories() {
        try {
            const res = await fetch('/api/expense-categories');
            const data = await res.json();
            const mainSelect = document.getElementById('expenseCategory');
            const filterSelect = document.getElementById('filterCategory');
            
            mainSelect.innerHTML = '';
            filterSelect.innerHTML = '<option value="all">Все категории</option>';
            
            data.categories.forEach(cat => {
                mainSelect.innerHTML += `<option value="${cat.id}">${cat.name}</option>`;
                filterSelect.innerHTML += `<option value="${cat.id}">${cat.name}</option>`;
            });
        } catch (err) { console.error(err); }
    }

    async function loadChartData() {
        const month = document.getElementById('filterMonth').value;
        try {
            const res = await fetch(`/api/expenses/chart?month=${month}&user_id=${CURRENT_USER_ID}`);
            const data = await res.json();
            const canvas = document.getElementById('expenseDonutChart');
            const msg = document.getElementById('noDataMessage');
            
            if (!data.chart_data || data.chart_data.length === 0) {
                canvas.style.display = 'none';
                msg.style.display = 'block';
                if(myChart) myChart.destroy();
                return;
            }
            
            canvas.style.display = 'block';
            msg.style.display = 'none';
            
            if(myChart) myChart.destroy();
            
            myChart = new Chart(canvas, {
                type: 'doughnut',
                data: {
                    labels: data.chart_data.map(i => i.category),
                    datasets: [{
                        data: data.chart_data.map(i => i.sum),
                        backgroundColor: ['#e74c3c', '#e67e22', '#f1c40f', '#3498db', '#9b59b6', '#1abc9c']
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });
        } catch (err) { console.error(err); }
    }

    async function loadHistory() {
        const month = document.getElementById('filterMonth').value;
        const category = document.getElementById('filterCategory').value;
        try {
            const res = await fetch(`/api/expenses/history?month=${month}&id_category=${category}&user_id=${CURRENT_USER_ID}`);
            const data = await res.json();
            const tbody = document.querySelector('#historyTable tbody');
            tbody.innerHTML = '';
            
            if (!data.history || data.history.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#7f8c8d;">Нет операций</td></tr>';
                return;
            }
            
            data.history.forEach(item => {
                const formattedDate = new Date(item.date_time).toLocaleDateString('ru-RU');
                const row = document.createElement('tr');
                
                row.innerHTML = `
                    <td>${formattedDate}</td>
                    <td>${item.category_name}</td>
                    <td>${item.name_card || 'Основной счёт'}</td>
                    <td style="color:#e74c3c; font-weight:bold;">- ${item.sum.toFixed(2)} ₽</td>
                    <td></td>
                `;
                
                const deleteBtn = document.createElement('button');
                deleteBtn.type = 'button';
                deleteBtn.textContent = 'Удалить';
                deleteBtn.style.backgroundColor = '#e74c3c';
                deleteBtn.style.color = 'white';
                deleteBtn.style.border = 'none';
                deleteBtn.style.padding = '3px 8px';
                deleteBtn.style.borderRadius = '4px';
                deleteBtn.style.cursor = 'pointer';
                deleteBtn.style.width = 'auto';
                
                deleteBtn.addEventListener('click', () => deleteExpense(item.id_expense));
                
                row.lastElementChild.appendChild(deleteBtn);
                tbody.appendChild(row);
            });
        } catch (err) { console.error(err); }
    }

    async function deleteExpense(expenseId) {
        if (!confirm('Вы уверены, что хотите удалить эту операцию расхода?')) return;
        
        try {
            const res = await fetch(`/api/expenses/${expenseId}?user_id=${CURRENT_USER_ID}`, {
                method: 'DELETE'
            });
            
            if (res.ok) {
                alert('Операция успешно удалена!');
                await loadChartData();
                await loadHistory();
            } else {
                const errData = await res.json();
                alert('Не удалось удалить: ' + (errData.error || 'Ошибка сервера'));
            }
        } catch (err) {
            console.error(err);
            alert('Произошла ошибка при отправке запроса на удаление.');
        }
    }

    document.getElementById('addExpenseForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (CURRENT_CARD_ID === 0) {
            alert('У вас нет зарегистрированных счетов! Сначала добавьте карту или счет.');
            return;
        }

        const payload = {
            id_category: parseInt(document.getElementById('expenseCategory').value),
            id_card: CURRENT_CARD_ID, 
            user_id: CURRENT_USER_ID, 
            sum: parseFloat(document.getElementById('expenseSum').value),
            date_time: document.getElementById('expenseDate').value || null
        };
        
        const res = await fetch('/api/expenses', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            document.getElementById('addExpenseForm').reset();
            await loadChartData();
            if(document.getElementById('historyCard').style.display === 'block') await loadHistory();
            alert('Успешно добавлено!');
        } else {
            const errData = await res.json();
            alert('Ошибка: ' + (errData.error || JSON.stringify(errData.errors)));
        }
    });

    document.getElementById('addCategoryForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const res = await fetch('/api/expense-categories', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: document.getElementById('newCategoryName').value })
        });
        if (res.ok) {
            document.getElementById('newCategoryName').value = '';
            await loadCategories();
            alert('Категория создана!');
        } else {
            const errData = await res.json();
            alert('Ошибка: ' + errData.error);
        }
    });
</script>
</body>
</html>