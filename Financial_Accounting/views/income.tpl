% rebase('layout', title=title, year=year)

<!-- Подключаем файл стилей (убедитесь, что путь совпадает с вашим проектом) -->
<link rel="stylesheet" href="static/content/income.css">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<main class="main-content">
    
    <div class="grid">
        <!-- КАРТОЧКА 1: ВВОД ДАННЫХ -->
        <div class="goals-wrapper">
            <h2 class="card-section-title">Ввод данных</h2>
            
            <form id="addIncomeForm">
                <div class="form-grid">
                    <div class="form-group">
                        <label for="incomeCategory">Категория:</label>
                        <select id="incomeCategory" class="form-control" required></select>
                    </div>
                    <div class="form-group">
                        <label for="incomeSum">Сумма (руб.):</label>
                        <input type="number" id="incomeSum" class="form-control" step="0.01" min="0.01" required>
                        <span id="sumError" class="validation-error"></span>
                    </div>
                    <div class="form-group full-width">
                        <label for="incomeDate">Дата операции:</label>
                        <input type="date" id="incomeDate" class="form-control">
                        <small class="helper-text">По умолчанию будет выбран сегодняшний день</small>
                    </div>
                </div>
                <button type="submit" class="btn btn-submit full-width-btn">Сохранить поступление</button>
            </form>
            
            <!-- Разделительная линия между формами -->
            <div class="form-divider"></div>
            
            <form id="addCategoryForm">
                <div class="form-grid">
                    <div class="form-group full-width">
                        <label for="newCategoryName">Новая категория:</label>
                        <input type="text" id="newCategoryName" class="form-control" placeholder="Название" required>
                        <span id="catError" class="validation-error"></span>
                    </div>
                </div>
                <button type="submit" class="btn btn-secondary full-width-btn">Создать категорию</button>
            </form>
        </div>

        <!-- КАРТОЧКА 2: АНАЛИТИКА И ДИАГРАММА -->
        <div class="goals-wrapper d-flex-center">
            <div class="form-group month-filter-group">
                <input type="month" id="filterMonth" class="form-control text-center">
            </div>
            
            <div class="chart-container">
                <canvas id="incomeDonutChart"></canvas>
            </div>
            <p id="noDataMessage" class="no-data-text">Нет транзакций за этот период</p>
            
            <button type="button" class="btn btn-secondary full-width-btn" id="toggleHistoryBtn">Показать историю операций</button>
        </div>
    </div>

    <!-- КАРТОЧКА 3: ИСТОРИЯ ОПЕРАЦИЙ -->
    <div class="goals-wrapper" id="historyCard">
        <div class="history-header">
            <h2 class="card-section-title m-0">История операций</h2>
            <div class="form-group filter-select-group">
                <select id="filterCategory" class="form-control">
                    <option value="all">Все категории</option>
                </select>
            </div>
        </div>
        
        <div class="table-responsive">
            <table id="historyTable" class="modern-table">
                <thead>
                    <tr>
                        <th>Дата</th>
                        <th>Категория</th>
                        <th>Счёт</th>
                        <th>Сумма</th>
                        <th>Действия</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
    </div>
</main>
<script>
    // Подхватываем авторизованные ID пользователя и его счета из Bottle
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
        const res = await fetch(`/api/incomes/chart?month=${month}&user_id=${CURRENT_USER_ID}`);
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
            backgroundColor: ['#E28F8F', '#F5D6D6', '#E2A96D', '#C86B85', '#A94A4A', '#F3E9DC'],
            borderWidth: 2,
            borderColor: '#5c0707' 
        }]
    },
    options: { 
        responsive: true, 
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top',
                labels: {
                    color: '#ffffff',
                    boxWidth: 20, // Сделали цветные квадратики легенды чуть больше
                    font: {
                        family: "'Inter', sans-serif",
                        size: 16, // УВЕЛИЧИЛИ: Шрифт категорий над диаграммой (было 13)
                        weight: '600'
                    }
                }
            },
            tooltip: {
                titleColor: '#ffffff',
                bodyColor: '#ffffff',
                backgroundColor: '#4c0505',
                borderRadius: 14,
                padding: 14,
                titleFont: { size: 16, weight: '700' }, // Увеличили шрифт заголовка подсказки
                bodyFont: { size: 15, weight: '500' }   // Увеличили шрифт суммы подсказки
            }
        }
    }
});
    } catch (err) { console.error(err); }
}

    async function loadHistory() {
        const month = document.getElementById('filterMonth').value;
        const category = document.getElementById('filterCategory').value;
        try {
            const res = await fetch(`/api/incomes/history?month=${month}&id_category=${category}&user_id=${CURRENT_USER_ID}`);
            const data = await res.json();
            const tbody = document.querySelector('#historyTable tbody');
            tbody.innerHTML = '';
            
            if (!data.history || data.history.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#7f8c8d;">Нет операций</td></tr>';
                return;
            }
            
            data.history.forEach(item => {
                const formattedDate = new Date(item.date_time).toLocaleDateString('ru-RU');
                
                // Создаем строку таблицы вручную, чтобы безопасно повесить событие клика на кнопку удаления
                const row = document.createElement('tr');
                
                row.innerHTML = `
                    <td>${formattedDate}</td>
                    <td>${item.category_name}</td>
                    <td>${item.name_card || 'Основной счёт'}</td>
                    <td style="color:#2ecc71; font-weight:bold;">+ ${item.sum.toFixed(2)} ₽</td>
                    <td></td>
                `;
                
                // Создаем кнопку «Удалить»
                const deleteBtn = document.createElement('button');
                deleteBtn.type = 'button';
                deleteBtn.textContent = 'Удалить';
                // Применяем простые стили, чтобы кнопка выделялась, или задай свой класс (например, btn-danger)
                deleteBtn.style.backgroundColor = '#e74c3c';
                deleteBtn.style.color = 'white';
                deleteBtn.style.border = 'none';
                deleteBtn.style.padding = '3px 8px';
                deleteBtn.style.borderRadius = '4px';
                deleteBtn.style.cursor = 'pointer';
                deleteBtn.style.width = 'auto';
                
                // Навешиваем событие клика на функцию удаления
                deleteBtn.addEventListener('click', () => deleteIncome(item.id_income));
                
                // Добавляем созданную кнопку в последнюю ячейку строки
                row.lastElementChild.appendChild(deleteBtn);
                tbody.appendChild(row);
            });
        } catch (err) { console.error(err); }
    }

    // НОВАЯ ФУНКЦИЯ: Удаление конкретной записи дохода
    async function deleteIncome(incomeId) {
        if (!confirm('Вы уверены, что хотите удалить эту операцию дохода?')) return;
        
        try {
            const res = await fetch(`/api/incomes/${incomeId}?user_id=${CURRENT_USER_ID}`, {
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

    document.getElementById('addIncomeForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (CURRENT_CARD_ID === 0) {
            alert('У вас нет зарегистрированных счетов! Сначала добавьте карту или счет.');
            return;
        }

        const payload = {
            id_category: parseInt(document.getElementById('incomeCategory').value),
            id_card: CURRENT_CARD_ID, 
            user_id: CURRENT_USER_ID, 
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