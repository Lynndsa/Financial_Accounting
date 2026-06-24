import unittest
from unittest.mock import patch, MagicMock
from datetime import date, datetime
from decimal import Decimal

from bottle import FormsDict

# Импортируем тестируемые функции
from files_module.expenses import (
    get_expense_categories,
    create_expense_category,
    add_expense,
    get_expenses_history,
    get_expenses_chart_data,
    delete_expense
)

class TestExpensesAPI(unittest.TestCase):

    def setUp(self):
        # Создаем изолированные моки для каждого теста
        self.response_mock = MagicMock()
        self.request_mock = MagicMock()
        
        # Инициализируем структуры данных Bottle
        self.request_mock.json = None
        self.request_mock.forms = FormsDict()
        self.request_mock.query = FormsDict()

        # Мокаем request и response непосредственно внутри целевого модуля расходов
        self.patcher_req = patch('files_module.expenses.request', self.request_mock)
        self.patcher_res = patch('files_module.expenses.response', self.response_mock)
        
        self.patcher_req.start()
        self.patcher_res.start()

    def tearDown(self):
        # Гарантированно сбрасываем патчинг
        self.patcher_req.stop()
        self.patcher_res.stop()

    # ==============================================================================
    # 1. ТЕСТЫ КАТЕГОРИЙ РАСХОДОВ
    # ==============================================================================

    @patch('files_module.expenses.get_connection')
    def test_get_expense_categories_success(self, mock_get_connection):
        """Успешное получение списка категорий расходов (без 'Копилка')."""
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_connection.return_value = mock_conn
        
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'name': 'Продукты'},
            {'id': 2, 'name': 'Транспорт'}
        ]

        result = get_expense_categories()

        self.assertEqual(len(result['categories']), 2)
        self.assertEqual(result['categories'][0]['name'], 'Продукты')
        mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM expense_categories WHERE name != 'Копилка' ORDER BY name ASC"
        )

    @patch('files_module.expenses.validate_category_name')
    def test_create_expense_category_kopilka_restriction(self, mock_validate):
        """Запрет на ручное создание системной категории 'Копилка'."""
        mock_validate.return_value = None  # Валидация пройдена успешна
        self.request_mock.json = {'name': ' Копилка '}

        result = create_expense_category()

        self.assertEqual(self.response_mock.status, 400)
        self.assertIn('является системной', result['error'])

    @patch('files_module.expenses.validate_category_name')
    @patch('files_module.expenses.get_connection')
    def test_create_expense_category_duplicate(self, mock_get_connection, mock_validate):
        """Ошибка при создании: дубликат категории расходов."""
        mock_validate.return_value = None
        self.request_mock.json = {'name': 'Продукты'}
        
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_connection.return_value = mock_conn
        mock_cursor.fetchone.return_value = {'id': 1}  # Нашли существующую запись

        result = create_expense_category()

        self.assertEqual(self.response_mock.status, 400)
        self.assertEqual(result['error'], 'Категория расходов с таким названием уже существует')

    # ==============================================================================
    # 2. ТЕСТЫ ОПЕРАЦИЙ С РАСХОДАМИ
    # ==============================================================================

    @patch('files_module.expenses.validate_create_expense')
    @patch('files_module.expenses.get_connection')
    def test_add_expense_insufficient_funds(self, mock_get_connection, mock_validate):
        """Ошибка добавления расхода: недостаточно средств на балансе счета."""
        self.request_mock.json = {'user_id': 21, 'id_card': 2, 'amount': 1500}
        
        mock_validate.return_value = (None, {
            'id_category': 3,
            'id_card': 2,
            'date_time': '2026-06-24T15:00:00',
            'sum': 1500.0
        })

        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_connection.return_value = mock_conn
        
        # Симулируем, что на счету только 500 рублей
        mock_cursor.fetchone.return_value = {'id_card': 2, 'balance': Decimal('500.00')}

        result = add_expense()

        self.assertEqual(self.response_mock.status, 400)
        self.assertIn('Недостаточно средств', result['error'])
        mock_conn.commit.assert_not_called()

    @patch('files_module.expenses.validate_create_expense')
    @patch('files_module.expenses.get_connection')
    def test_add_expense_success(self, mock_get_connection, mock_validate):
        """Успешное добавление нового расхода при корректном балансе."""
        self.request_mock.json = {'user_id': 21, 'id_card': 2, 'amount': 300}
        
        mock_validate.return_value = (None, {
            'id_category': 3,
            'id_card': 2,
            'date_time': '2026-06-24T15:00:00',
            'sum': 300.0
        })

        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_connection.return_value = mock_conn
        
        # Денег на балансе достаточно
        mock_cursor.fetchone.return_value = {'id_card': 2, 'balance': Decimal('2000.00')}

        result = add_expense()

        self.assertEqual(self.response_mock.status, 201)
        self.assertEqual(result['message'], 'Расход успешно зафиксирован')
        mock_cursor.callproc.assert_called_once_with('create_new_expenses', (3, 2, '2026-06-24T15:00:00', 300.0))
        mock_conn.commit.assert_called_once()

    @patch('files_module.expenses.get_connection')
    def test_get_expenses_history_with_filter(self, mock_get_connection):
        """Проверка динамической генерации SQL-запроса при явной фильтрации по категории."""
        query_dict = FormsDict()
        query_dict['user_id'] = '21'
        query_dict['month'] = '2026-06'
        query_dict['id_category'] = '5'
        self.request_mock.query = query_dict

        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_connection.return_value = mock_conn
        mock_cursor.fetchall.return_value = []

        get_expenses_history()

        called_sql = mock_cursor.execute.call_args[0][0]
        called_params = mock_cursor.execute.call_args[0][1]

        self.assertIn('AND e.id_category = %s', called_sql)
        self.assertEqual(called_params, ['21', '2026-06', 5])

    @patch('files_module.expenses.get_connection')
    def test_get_expenses_chart_data_success(self, mock_get_connection):
        """Проверка сериализации агрегированных данных для построения графика."""
        query_dict = FormsDict()
        query_dict['user_id'] = '21'
        query_dict['month'] = '2026-06'
        self.request_mock.query = query_dict

        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_connection.return_value = mock_conn
        
        # Имитируем ответ БД со сгруппированными суммами
        mock_cursor.fetchall.return_value = [
            {'category_name': 'Продукты', 'total_sum': Decimal('4500.50')},
            {'category_name': 'Кафе', 'total_sum': Decimal('1200.00')}
        ]

        result = get_expenses_chart_data()

        self.assertIn('chart_data', result)
        self.assertEqual(result['chart_data'][0]['category'], 'Продукты')
        self.assertEqual(result['chart_data'][0]['sum'], 4500.5)

    @patch('files_module.expenses.get_connection')
    def test_delete_expense_not_found(self, mock_get_connection):
        """Попытка удаления чужого или отсутствующего расхода приводит к 404."""
        query_dict = FormsDict()
        query_dict['user_id'] = '21'
        self.request_mock.query = query_dict

        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_connection.return_value = mock_conn
        
        # База данных не нашла связку расход + пользователь
        mock_cursor.fetchone.return_value = None 

        result = delete_expense(777)

        self.assertEqual(self.response_mock.status, 404)
        self.assertEqual(result['error'], 'Расход не найден или доступ ограничен')
        mock_conn.commit.assert_not_called()


if __name__ == '__main__':
    unittest.main()