import unittest
from unittest.mock import patch, MagicMock
from datetime import date
from decimal import Decimal

from bottle import FormsDict

# Импортируем тестируемые функции
from files_module.goals import (
    get_goals,
    get_goal,
    create_goal,
    update_goal,
    delete_goal,
    topup_goal,
    archive_goal
)

class TestGoalsAPI(unittest.TestCase):

    def setUp(self):
        # Создаем изолированные моки для каждого теста
        self.response_mock = MagicMock()
        self.request_mock = MagicMock()
        
        # Инициализируем структуры данных Bottle
        self.request_mock.json = None
        self.request_mock.forms = FormsDict()
        self.request_mock.query = FormsDict()

        # Патчим request и response прямо внутри целевого модуля целей
        self.patcher_req = patch('files_module.goals.request', self.request_mock)
        self.patcher_res = patch('files_module.goals.response', self.response_mock)
        
        self.patcher_req.start()
        self.patcher_res.start()

    def tearDown(self):
        # Обязательно сбрасываем патчинг после выполнения каждого теста
        self.patcher_req.stop()
        self.patcher_res.stop()

    # ==============================================================================
    # 1. ТЕСТЫ ПОЛУЧЕНИЯ ЦЕЛЕЙ
    # ==============================================================================

    @patch('files_module.goals.get_connection')
    def test_get_goals_success_with_calculation(self, mock_get_connection):
        """Успешное получение активных целей и проверка расчета процентов прогресса."""
        query_dict = FormsDict()
        query_dict['user_id'] = '21'
        self.request_mock.query = query_dict

        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_connection.return_value = mock_conn
        
        # Симулируем две цели: одну незавершенную, другую закрытую по сумме
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'name': 'На отпуск', 'target_amount': Decimal('100000.00'), 'current_amount': Decimal('25000.00'), 'is_active': 1},
            {'id': 2, 'name': 'Курс', 'target_amount': Decimal('10000.00'), 'current_amount': Decimal('12000.00'), 'is_active': 1}
        ]

        result = get_goals()

        self.assertIn('goals', result)
        self.assertEqual(len(result['goals']), 2)
        
        # Проверяем расчет прогресса: (25000 / 100000) * 100 = 25.0%
        self.assertEqual(result['goals'][0]['progress_percent'], 25.0)
        self.assertFalse(result['goals'][0]['is_completed'])
        
        # Проверяем ограничение min(current/target, 1) -> 100.0% при перевыполнении
        self.assertEqual(result['goals'][1]['progress_percent'], 100.0)
        self.assertTrue(result['goals'][1]['is_completed'])

    @patch('files_module.goals.get_connection')
    def test_get_goal_not_found(self, mock_get_connection):
        """Попытка получить одну цель, которая не существует или принадлежит чужому пользователю (404)."""
        query_dict = FormsDict()
        query_dict['user_id'] = '21'
        self.request_mock.query = query_dict

        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_connection.return_value = mock_conn
        mock_cursor.fetchone.return_value = None  # Цель в БД не найдена

        result = get_goal(999)

        self.assertEqual(self.response_mock.status, 404)
        self.assertEqual(result['error'], 'Цель не найдена')

    # ==============================================================================
    # 2. ТЕСТЫ СОЗДАНИЯ И ОБНОВЛЕНИЯ
    # ==============================================================================

    @patch('files_module.goals.validate_create_goal')
    @patch('files_module.goals.get_connection')
    def test_create_goal_success(self, mock_get_connection, mock_validate):
        """Успешное создание цели с проверкой передачи 7 параметров в процедуру."""
        self.request_mock.json = {'user_id': 21, 'id_card': 2}
        
        mock_validate.return_value = (None, {
            'name': 'Новый ПК',
            'target_amount': 75000.0,
            'current_amount': 0.0,
            'deadline': '2026-12-31',
            'description': 'Для работы и игр'
        })

        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_connection.return_value = mock_conn
        mock_cursor.fetchone.return_value = {'id_card': 2}  # Счет принадлежит пользователю
        mock_cursor.lastrowid = 42

        result = create_goal()

        self.assertEqual(self.response_mock.status, 201)
        self.assertEqual(result['id'], 42)
        # Проверяем строгий порядок аргументов в процедуре СУБД
        mock_cursor.callproc.assert_called_once_with('create_new_goal', (
            21, 'Новый ПК', 75000.0, 0.0, 2, '2026-12-31', 'Для работы и игр'
        ))
        mock_conn.commit.assert_called_once()

    # ==============================================================================
    # 3. ТЕСТЫ ПОПОЛНЕНИЯ (TOPUP)
    # ==============================================================================

    @patch('files_module.goals.get_connection')
    def test_topup_goal_insufficient_funds(self, mock_get_connection):
        """Ошибка пополнения копилки: не хватает денег на привязанном счете."""
        self.request_mock.json = {'user_id': 21, 'amount': 5000.0}

        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_connection.return_value = mock_conn
        
        # Симулируем, что цель активна и привязана к id_card = 2
        mock_cursor.fetchone.side_effect = [
            {'current_amount': Decimal('1000.00'), 'target_amount': Decimal('10000.00'), 'id_card': 2, 'is_active': 1}, # Первый вызов (цель)
            {'balance': Decimal('1500.00')} # Второй вызов (баланс карты)
        ]

        result = topup_goal(1)

        self.assertEqual(self.response_mock.status, 400)
        self.assertIn('На счете недостаточно средств', result['error'])
        mock_conn.commit.assert_not_called()

    @patch('files_module.goals.get_connection')
    def test_topup_goal_success_and_auto_close(self, mock_get_connection):
        """Успешное пополнение копилки, приводящее к достижению цели (is_completed = True)."""
        self.request_mock.json = {'user_id': 21, 'amount': 4000.0}

        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_connection.return_value = mock_conn
        
        # Цель требует еще 3000 до закрытия (текущая 7000, цель 10000). Пополняем на 4000
        mock_cursor.fetchone.side_effect = [
            {'current_amount': Decimal('7000.00'), 'target_amount': Decimal('10000.00'), 'id_card': 2, 'is_active': 1},
            {'balance': Decimal('5000.00')}
        ]

        result = topup_goal(1)

        # Проверяем математику бэкенда
        self.assertEqual(result['current_amount'], 11000.0)
        self.assertTrue(result['is_completed'])
        
        # Проверяем, что в базу ушел статус is_active = 0, так как цель закрылась
        mock_cursor.execute.assert_any_call(
            'UPDATE goals SET current_amount = %s, is_active = %s WHERE id = %s',
            (11000.0, 0, 1)
        )
        mock_conn.commit.assert_called_once()

    # ==============================================================================
    # 4. УДАЛЕНИЕ И АРХИВАЦИЯ
    # ==============================================================================

    @patch('files_module.goals._goal_belongs_to_user')
    @patch('files_module.goals.get_connection')
    def test_delete_goal_success(self, mock_get_connection, mock_belongs):
        """Успешное удаление финансовой цели."""
        query_dict = FormsDict()
        query_dict['user_id'] = '21'
        self.request_mock.query = query_dict
        
        mock_belongs.return_value = True

        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_connection.return_value = mock_conn

        result = delete_goal(5)

        self.assertEqual(result['message'], 'Цель успешно удалена')
        mock_cursor.callproc.assert_called_once_with('delete_goals', (5,))
        mock_conn.commit.assert_called_once()

    @patch('files_module.goals._goal_belongs_to_user')
    @patch('files_module.goals.get_connection')
    def test_archive_goal_success(self, mock_get_connection, mock_belongs):
        """Успешный перевод активной цели в архив (is_active = 0)."""
        query_dict = FormsDict()
        query_dict['user_id'] = '21'
        self.request_mock.query = query_dict
        
        mock_belongs.return_value = True

        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_get_connection.return_value = mock_conn

        result = archive_goal(5)

        self.assertEqual(result['message'], 'Цель архивирована')
        mock_cursor.execute.assert_called_once_with(
            'UPDATE goals SET is_active = 0 WHERE id = %s', (5,)
        )
        mock_conn.commit.assert_called_once()


if __name__ == '__main__':
    unittest.main()