import unittest
from unittest.mock import patch, MagicMock
from datetime import date
from decimal import Decimal
import json

from bottle import FormsDict 

from files_module.income import (
    get_income_categories,
    create_income_category,
    add_income,
    get_incomes_history,
    delete_income
)

class TestIncomesAPI(unittest.TestCase):

    def setUp(self):
        # Создаем моки для ответов и запросов
        self.response_mock = MagicMock()
        self.request_mock = MagicMock()
        
        # Инициализируем пустые структуры для Bottle
        self.request_mock.json = None
        self.request_mock.forms = FormsDict()
        self.request_mock.query = FormsDict()

        # Патчим request и response прямо внутри тестируемого файла,
        # чтобы его внутренние функции читали наши фейковые объекты
        self.patcher_req = patch('files_module.income.request', self.request_mock)
        self.patcher_res = patch('files_module.income.response', self.response_mock)
        
        self.patcher_req.start()
        self.patcher_res.start()

    def tearDown(self):
        # Останавливаем патчинг после каждого теста, чтобы не портить другие модули
        self.patcher_req.stop()
        self.patcher_res.stop()

    @patch('files_module.income.get_connection')
    def test_get_income_categories_success(self, mock_get_connection):
        """Успешное получение списка категорий доходов."""
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_connection.return_value = mock_conn
        
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'name': 'Зарплата'},
            {'id': 2, 'name': 'Фриланс'}
        ]

        result = get_income_categories()

        self.assertEqual(len(result['categories']), 2)
        self.assertEqual(result['categories'][0]['name'], 'Зарплата')
        mock_cursor.execute.assert_called_once_with('SELECT * FROM income_categories ORDER BY name ASC')

    @patch('files_module.income.validate_category_name')
    @patch('files_module.income.get_connection')
    def test_create_income_category_duplicate(self, mock_get_connection, mock_validate):
        """Ошибка при создании: категория с таким именем уже существует."""
        mock_validate.return_value = None 
        self.request_mock.json = {'name': ' Зарплата '}
        
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_connection.return_value = mock_conn
        mock_cursor.fetchone.return_value = {'id': 1} 

        result = create_income_category()

        self.assertEqual(self.response_mock.status, 400)
        self.assertEqual(result['error'], 'Категория с таким названием уже существует')

    @patch('files_module.income.validate_create_income')
    @patch('files_module.income.get_connection')
    def test_add_income_success(self, mock_get_connection, mock_validate):
        """Успешное добавление нового дохода."""
        self.request_mock.json = {'user_id': 21, 'id_card': 5, 'amount': 5000}

        mock_validate.return_value = (None, {
            'id_category': 1,
            'id_card': 5,
            'date_time': '2026-06-24T12:00:00',
            'sum': 5000.0
        })

        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_connection.return_value = mock_conn
        mock_cursor.fetchone.return_value = {'id_card': 5} 

        result = add_income()

        self.assertEqual(self.response_mock.status, 201)
        self.assertEqual(result['message'], 'Доход успешно зафиксирован')
        mock_cursor.callproc.assert_called_once_with('create_new_income', (1, 5, '2026-06-24T12:00:00', 5000.0))
        mock_conn.commit.assert_called_once()

    @patch('files_module.income.get_connection')
    def test_get_incomes_history_with_category_filter(self, mock_get_connection):
        """Проверка генерации SQL-запроса при фильтрации по конкретной категории."""
        query_dict = FormsDict()
        query_dict['user_id'] = '21'
        query_dict['month'] = '2026-06'
        query_dict['id_category'] = '3'
        self.request_mock.query = query_dict

        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_connection.return_value = mock_conn
        mock_cursor.fetchall.return_value = []

        get_incomes_history()

        called_sql = mock_cursor.execute.call_args[0][0]
        called_params = mock_cursor.execute.call_args[0][1]

        self.assertIn('AND i.id_category = %s', called_sql)
        self.assertEqual(called_params, ['21', '2026-06', 3])

    @patch('files_module.income.validate_id')
    @patch('files_module.income.get_connection')
    def test_delete_income_not_found(self, mock_get_connection, mock_validate_id):
        """Попытка удалить чужой или несуществующий доход приводит к 404."""
        mock_validate_id.return_value = None
        query_dict = FormsDict()
        query_dict['user_id'] = '21'
        self.request_mock.query = query_dict

        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_connection.return_value = mock_conn
        mock_cursor.fetchone.return_value = None 

        result = delete_income(999)

        self.assertEqual(self.response_mock.status, 404)
        self.assertEqual(result['error'], 'Доход не найден или доступ ограничен')
        mock_conn.commit.assert_not_called()


if __name__ == '__main__':
    unittest.main()