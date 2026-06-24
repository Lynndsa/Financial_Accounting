import unittest
from datetime import date, timedelta

# Импортируем функции валидации доходов
from validations.incomes_validation import (
    validate_id,
    validate_income_sum,
    validate_category_name,
    validate_create_income
)

class TestIncomesValidation(unittest.TestCase):

    # ==============================================================================
    # 1. ТЕСТЫ ВАЛИДАЦИИ ID (validate_id)
    # ==============================================================================

    def test_validate_id_success(self):
        """Успешная валидация корректного ID."""
        self.assertIsNone(validate_id(5))
        self.assertIsNone(validate_id("10", "custom_id"))

    def test_validate_id_missing_or_empty(self):
        """Ошибка, если ID отсутствует или пустой."""
        self.assertEqual(validate_id(None), "Поле id обязательно")
        self.assertEqual(validate_id("   ", "card_id"), "Поле card_id обязательно")

    def test_validate_id_not_a_number(self):
        """Ошибка, если ID передан не числом."""
        self.assertEqual(validate_id("abc"), "Поле id должно быть числом")

    def test_validate_id_negative_or_zero(self):
        """Ошибка, если ID меньше либо равен нулю."""
        self.assertEqual(validate_id(0), "Некорректный id")
        self.assertEqual(validate_id(-1, "user_id"), "Некорректный user_id")


    # ==============================================================================
    # 2. ТЕСТЫ ВАЛИДАЦИИ СУММЫ ДОХОДА (validate_income_sum)
    # ==============================================================================

    def test_validate_income_sum_success(self):
        """Успешная валидация корректной суммы дохода."""
        self.assertIsNone(validate_income_sum(150.50))
        self.assertIsNone(validate_income_sum("5000"))

    def test_validate_income_sum_missing(self):
        """Ошибка при отсутствии суммы."""
        self.assertEqual(validate_income_sum(None), "Сумма дохода обязательна")
        self.assertEqual(validate_income_sum("  "), "Сумма дохода обязательна")

    def test_validate_income_sum_not_a_number(self):
        """Ошибка, если сумма не является числом."""
        self.assertEqual(validate_income_sum("price"), "Сумма дохода должна быть числом")

    def test_validate_income_sum_invalid_values(self):
        """Ошибка, если сумма отрицательная, ноль или слишком большая."""
        self.assertEqual(validate_income_sum(0), "Сумма дохода должна быть больше 0")
        self.assertEqual(validate_income_sum(-50), "Сумма дохода должна быть больше 0")
        self.assertEqual(validate_income_sum(999999999999.0), "Сумма слишком большая")


    # ==============================================================================
    # 3. ТЕСТЫ ВАЛИДАЦИИ НАЗВАНИЯ КАТЕГОРИИ (validate_category_name)
    # ==============================================================================

    def test_validate_category_name_success(self):
        """Успешная валидация названия категории."""
        self.assertIsNone(validate_category_name("Зарплата"))
        self.assertIsNone(validate_category_name("  Фриланс  "))  # Пробелы должны обрезаться

    def test_validate_category_name_empty(self):
        """Ошибка, если название пустое или отсутствует."""
        self.assertEqual(validate_category_name(None), "Название категории обязательно")
        self.assertEqual(validate_category_name("   "), "Название категории не может быть пустым")

    def test_validate_category_name_too_long(self):
        """Ошибка, если длина названия превышает лимит."""
        long_name = "A" * 101
        self.assertEqual(
            validate_category_name(long_name), 
            "Название категории не должно превышать 100 символов"
        )


    # ==============================================================================
    # 4. КОМПЛЕКСНАЯ ВАЛИДАЦИЯ ОПЕРАЦИИ (validate_create_income)
    # ==============================================================================

    def test_validate_create_income_success_with_date(self):
        """Успешный разбор структуры с явно переданной корректной датой."""
        data = {
            'id_category': '1',
            'id_card': 2,
            'sum': '1500.75',
            'date_time': '2026-06-20'
        }
        errors, cleaned = validate_create_income(data)

        self.assertEqual(errors, {})
        self.assertEqual(cleaned['id_category'], 1)
        self.assertEqual(cleaned['id_card'], 2)
        self.assertEqual(cleaned['sum'], 1500.75)
        self.assertEqual(cleaned['date_time'], '2026-06-20')

    def test_validate_create_income_success_default_date(self):
        """Успешная валидация: если дата не передана, подставляется текущая сегодняшняя дата."""
        data = {
            'id_category': 3,
            'id_card': 4,
            'sum': 1000
        }
        errors, cleaned = validate_create_income(data)

        self.assertEqual(errors, {})
        self.assertEqual(cleaned['date_time'], date.today().isoformat())

    def test_validate_create_income_future_date_error(self):
        """Ошибка валидации, если дата дохода указана в будущем."""
        tomorrow = date.today() + timedelta(days=1)
        data = {
            'id_category': 1,
            'id_card': 2,
            'sum': 500,
            'date_time': tomorrow.strftime('%Y-%m-%d')
        }
        errors, cleaned = validate_create_income(data)

        self.assertIn('date_time', errors)
        self.assertEqual(errors['date_time'], 'Дата дохода не может быть в будущем')
        self.assertEqual(cleaned, {})

    def test_validate_create_income_bad_date_format_error(self):
        """Ошибка валидации при некорректном формате даты."""
        data = {
            'id_category': 1,
            'id_card': 2,
            'sum': 500,
            'date_time': '24-06-2026'  # Неверный формат (должен быть ГГГГ-ММ-ДД)
        }
        errors, cleaned = validate_create_income(data)

        self.assertIn('date_time', errors)
        self.assertEqual(errors['date_time'], 'Дата должна быть в формате ГГГГ-ММ-ДД')
        self.assertEqual(cleaned, {})

    def test_validate_create_income_multiple_errors(self):
        """Проверка сбора нескольких ошибок одновременно."""
        data = {
            'id_category': 'not-an-id',
            'id_card': -5,
            'sum': '-100'
        }
        errors, cleaned = validate_create_income(data)

        self.assertIn('id_category', errors)
        self.assertIn('id_card', errors)
        self.assertIn('sum', errors)
        self.assertEqual(cleaned, {})


if __name__ == '__main__':
    unittest.main()