import unittest
from unittest.mock import MagicMock, patch
from datetime import date, datetime, timedelta

# Импортируем тестируемые функции и константы
from validations.goals_validation import (
    validate_id,
    validate_topup_amount,
    validate_name,
    validate_target_amount,
    validate_current_amount,
    validate_deadline,
    validate_description,
    validate_id_card,
    validate_create_goal,
    validate_update_goal,
    MAX_NAME_LENGTH,
    MAX_UPDATE_NAME_LENGTH
)

class TestGoalsValidation(unittest.TestCase):

    # ==============================================================================
    # 1. ТЕСТЫ ОДИНОЧНЫХ ВАЛИДАТОРОВ ПОЛЕЙ
    # ==============================================================================

    def test_validate_id(self):
        """Проверка валидации идентификаторов."""
        self.assertIsNone(validate_id(10))
        self.assertIsNone(validate_id("5", "user_id"))
        self.assertEqual(validate_id(None), "Поле id обязательно")
        self.assertEqual(validate_id("   "), "Поле id обязательно")
        self.assertEqual(validate_id("abc"), "Поле id должно быть числом")
        self.assertEqual(validate_id(0), "Некорректный id")

    def test_validate_topup_amount(self):
        """Проверка валидации суммы пополнения копилки."""
        self.assertIsNone(validate_topup_amount(500))
        self.assertIsNone(validate_topup_amount("100.50"))
        self.assertEqual(validate_topup_amount(None), "Сумма пополнения обязательна")
        self.assertEqual(validate_topup_amount("xyz"), "Сумма пополнения должна быть числом")
        self.assertEqual(validate_topup_amount(0), "Сумма пополнения должна быть больше 0")
        self.assertEqual(validate_topup_amount(-10), "Сумма пополнения должна быть больше 0")
        self.assertEqual(validate_topup_amount(99999999999999.0), "Сумма пополнения слишком большая")

    def test_validate_name(self):
        """Проверка ограничений на имя цели."""
        self.assertIsNone(validate_name("Новый телефон"))
        self.assertEqual(validate_name(None), "Название цели обязательно")
        self.assertEqual(validate_name("   "), "Название цели не может быть пустым")
        
        long_name = "X" * (MAX_NAME_LENGTH + 1)
        self.assertEqual(validate_name(long_name), f"Название не должно превышать {MAX_NAME_LENGTH} символов")

    def test_validate_target_amount(self):
        """Проверка валидации целевой суммы."""
        self.assertIsNone(validate_target_amount("50000"))
        self.assertEqual(validate_target_amount(""), "Целевая сумма обязательна")
        self.assertEqual(validate_target_amount(0), "Целевая сумма должна быть больше 0")
        self.assertEqual(validate_target_amount("not-a-number"), "Целевая сумма должна быть числом")

    def test_validate_current_amount(self):
        """Проверка текущей (стартовой) суммы с учетом целевой."""
        self.assertIsNone(validate_current_amount(None))  # Поле необязательное
        self.assertIsNone(validate_current_amount("2000", "5000"))
        self.assertEqual(validate_current_amount("-50"), "Текущая сумма не может быть отрицательной")
        self.assertEqual(validate_current_amount("abc"), "Текущая сумма должна быть числом")
        
        # Превышение целевой суммы
        self.assertEqual(
            validate_current_amount("6000", "5000"), 
            "Текущая сумма не может превышать целевую сумму"
        )

    def test_validate_deadline(self):
        """Проверка формата даты и временных бизнес-ограничений."""
        self.assertIsNone(validate_deadline(None))  # Поле необязательное
        self.assertIsNone(validate_deadline(date.today()))
        self.assertIsNone(validate_deadline(date.today().strftime('%Y-%m-%d')))
        
        # Ошибки формата и логики
        self.assertEqual(validate_deadline("31-12-2026"), "Дата должна быть в формате ГГГГ-ММ-ДД")
        
        yesterday = date.today() - timedelta(days=1)
        self.assertEqual(validate_deadline(yesterday), "Дедлайн не может быть в прошлом")
        
        too_late = date(date.today().year + 11, 1, 1)
        max_year = date.today().year + 10
        self.assertIn(f"Дедлайн не может быть дальше {max_year} года", validate_deadline(too_late))

    def test_validate_description(self):
        """Проверка длины необязательного описания."""
        self.assertIsNone(validate_description(None))
        self.assertIsNone(validate_description("  "))
        self.assertIsNone(validate_description("Коплю на мечту"))
        
        long_desc = "D" * 201
        self.assertEqual(validate_description(long_desc), "Описание не должно превышать 200 символов")

    def test_validate_id_card(self):
        """Проверка идентификатора привязанной карты/счета."""
        self.assertIsNone(validate_id_card(None))  # Необязательно
        self.assertIsNone(validate_id_card("2"))
        self.assertEqual(validate_id_card("abc"), "Некорректный номер карты")
        self.assertEqual(validate_id_card(0), "Некорректный номер карты")

    # ==============================================================================
    # 2. ТЕСТЫ КОМПЛЕКСНОЙ ВАЛИДАЦИИ С ИСПОЛЬЗОВАНИЕМ МОКОВ БД
    # ==============================================================================

    def test_validate_create_goal_success(self):
        """Успешная комплексная проверка создания цели при отсутствии дубликатов."""
        data = {
            'name': ' Квартира ',
            'target_amount': '5000000',
            'current_amount': '100000',
            'id_card': '1',
            'deadline': '2027-01-01',
            'description': ' Первоначальный взнос '
        }
        
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = None  # Имя уникально, дубликатов нет

        errors, cleaned = validate_create_goal(data, mock_conn, id_user=21)

        self.assertEqual(errors, {})
        self.assertEqual(cleaned['name'], 'Квартира')
        self.assertEqual(cleaned['target_amount'], 5000000.0)
        self.assertEqual(cleaned['current_amount'], 100000.0)
        self.assertEqual(cleaned['id_card'], 1)
        self.assertEqual(cleaned['deadline'], '2027-01-01')
        self.assertEqual(cleaned['description'], 'Первоначальный взнос')

    def test_validate_create_goal_duplicate_error(self):
        """Ошибка создания, если у пользователя уже есть активная цель с таким именем."""
        data = {'name': 'Машина', 'target_amount': '1000000'}
        
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = {'id': 5}  # Цель-клон найдена в БД

        errors, cleaned = validate_create_goal(data, mock_conn, id_user=21)

        self.assertIn('name', errors)
        self.assertEqual(errors['name'], 'Цель с таким названием уже существует')
        self.assertEqual(cleaned, {})

    def test_validate_update_goal_success(self):
        """Успешное частичное обновление полей (включая лимит имени в 50 символов)."""
        data = {
            'name': 'Новое имя',
            'target_amount': '25000'
        }
        
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = None  # Имя свободно среди других записей

        errors, cleaned = validate_update_goal(data, mock_conn, id_user=21, goal_id=5)

        self.assertEqual(errors, {})
        self.assertEqual(cleaned['name'], 'Новое имя')
        self.assertEqual(cleaned['target_amount'], 25000.0)
        self.assertIsNone(cleaned['deadline'])  # Поля не было в запросе

    def test_validate_update_goal_name_too_long_for_update(self):
        """Ошибка обновления: при апдейте лимит длины имени жестче (50 символов)."""
        # Генерируем имя длиной 55 символов (больше 50, но меньше глобальных 100)
        long_update_name = "N" * (MAX_UPDATE_NAME_LENGTH + 5)
        data = {'name': long_update_name}
        
        mock_conn = MagicMock()

        errors, cleaned = validate_update_goal(data, mock_conn, id_user=21, goal_id=5)

        self.assertIn('name', errors)
        self.assertEqual(
            errors['name'], 
            f'Название не должно превышать {MAX_UPDATE_NAME_LENGTH} символов'
        )

    def test_validate_update_goal_duplicate_error(self):
        """Ошибка обновления при попытке занять имя чужой активной цели."""
        data = {'name': 'Ипотека'}
        
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        # Найдена другая цель (id != 5) с таким же именем
        mock_cursor.fetchone.return_value = {'id': 10} 

        errors, cleaned = validate_update_goal(data, mock_conn, id_user=21, goal_id=5)

        self.assertIn('name', errors)
        self.assertEqual(errors['name'], 'У вас уже есть другая активная цель с таким названием')


if __name__ == '__main__':
    unittest.main()