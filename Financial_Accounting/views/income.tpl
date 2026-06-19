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
            background-color: #2ecc71;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            width: 100%;
        }
        button:hover { background-color: #27ae60; }
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
            <form id="addIncomeForm">
                <div class="form-group">
                    <label>Категория:</label>
                    <select id="incomeCategory" class="form-control" required></select>
                </div>
                <div class="form-group">
                    <label>Сумма (руб.):</label>
                    <input type="number" id="incomeSum" class="form-control" step="0.01" min="0.01" required>
                    <span id="sumError" style="color: red; display: none;"></span>
                </div>
                <div class="form-group">
                    <label>Дата:</label>
                    <input type="date" id="incomeDate" class="form-control">
                </div>
                <button type="submit">Сохранить операцию</button>
            </form>
            
            <br>
            <form id="addCategoryForm">
                <div class="form-group">
                    <label>Новая категория:</label>
                    <input type="text" id="newCategoryName" class="form-control" placeholder="Название" required>
                    <span id="catError" style="color: red; display: none;"></span>
                </div>
                <button type="submit" class="btn-secondary">Создать категорию</button>
            </form>
        </div>

        <div class="card" style="text-align: center;">
            <h2>Визуализация доходов</h2>
            <div class="form-group" style="max-width: 150px; margin: 0 auto 15px;">
                <input type="month" id="filterMonth" class="form-control">
            </div>
            
            <div class="chart-container">
                <canvas id="incomeDonutChart"></canvas>
            </div>
            <p id="noDataMessage" style="color: #7f8c8d; display: none;">Нет транзакций за этот период</p>
            
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
                </tr>
            </thead>
            <tbody></tbody>
        </table>
    </div>
</div>

<script>
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
        } catch (err) { console.error(err); }
    }

    async function loadChartData() {
        const month = document.getElementById('filterMonth').value;
        try {
            const res = await fetch(`/api/incomes/chart?month=${month}`);
            const data = await res.json();
            const canvas = document.getElementById('incomeDonutChart');
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
                        backgroundColor: ['#2ecc71', '#3498db', '#9b59b6', '#f1c40f', '#e67e22', '#e74c3c']
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
            const res = await fetch(`/api/incomes/history?month=${month}&id_category=${category}`);
            const data = await res.json();
            const tbody = document.querySelector('#historyTable tbody');
            tbody.innerHTML = '';
            
            if (!data.history || data.history.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:#7f8c8d;">Нет операций</td></tr>';
                return;
            }
            
            data.history.forEach(item => {
                const formattedDate = new Date(item.date_time).toLocaleDateString('ru-RU');
                tbody.innerHTML += `
                    <tr>
                        <td>${formattedDate}</td>
                        <td>${item.category_name}</td>
                        <td>${item.name_card || 'Основной счёт'}</td>
                        <td style="color:#2ecc71; font-weight:bold;">+ ${item.sum.toFixed(2)} ₽</td>
                    </tr>
                `;
            });
        } catch (err) { console.error(err); }
    }

    // Сохранение дохода
    document.getElementById('addIncomeForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const payload = {
            id_category: parseInt(document.getElementById('incomeCategory').value),
            id_card: 2, // Явно передаем дефолтный ID счета, чтобы удовлетворить бэкенд-валидатор
            sum: parseFloat(document.getElementById('incomeSum').value),
            date_time: document.getElementById('incomeDate').value || null
        };
        
        const res = await fetch('/api/incomes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            document.getElementById('addIncomeForm').reset();
            await loadChartData();
            if(document.getElementById('historyCard').style.display === 'block') await loadHistory();
            alert('Успешно добавлено!');
        } else {
            const errData = await res.json();
            alert('Ошибка: ' + (errData.error || JSON.stringify(errData.errors)));
        }
    });

    // Создание категории
    document.getElementById('addCategoryForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const res = await fetch('/api/income-categories', {
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