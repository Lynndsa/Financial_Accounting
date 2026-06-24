import unittest
from datetime import date, timedelta

# Импортируем функции валидации расходов
from validations.expenses_validation import (
    validate_id,
    validate_expense_sum,
    validate_category_name,
    validate_create_expense
)

class TestExpensesValidation(unittest.TestCase):

    # ==============================================================================
    # 1. ТЕСТЫ ВАЛИДАЦИИ ID (validate_id)
    # ==============================================================================

    def test_validate_id_success(self):
        """Успешная валидация корректного ID."""
        self.assertIsNone(validate_id(12))
        self.assertIsNone(validate_id("42", "id_category"))

    def test_validate_id_missing_or_empty(self):
        """Ошибка, если ID отсутствует или является пустой строкой."""
        self.assertEqual(validate_id(None), "Поле id обязательно")
        self.assertEqual(validate_id("   ", "id_card"), "Поле id_card обязательно")

    def test_validate_id_not_a_number(self):
        """Ошибка, если передан некорректный тип (не число)."""
        self.assertEqual(validate_id("not_a_number"), "Поле id должно быть числом")

    def test_validate_id_negative_or_zero(self):
        """Ошибка, если ID выходит за границы корректных значений (<= 0)."""
        self.assertEqual(validate_id(0), "Некорректный id")
        self.assertEqual(validate_id("-15", "user_id"), "Некорректный user_id")

    # ==============================================================================
    # 2. ТЕСТЫ ВАЛИДАЦИИ СУММЫ РАСХОДА (validate_expense_sum)
    # ==============================================================================

    def test_validate_expense_sum_success(self):
        """Успешная валидация корректной суммы расхода."""
        self.assertIsNone(validate_expense_sum(12.50))
        self.assertIsNone(validate_expense_sum("4500"))

    def test_validate_expense_sum_missing(self):
        """Ошибка, если сумма отсутствует."""
        self.assertEqual(validate_expense_sum(None), "Сумма расхода обязательна")
        self.assertEqual(validate_expense_sum("  "), "Сумма расхода обязательна")

    def test_validate_expense_sum_not_a_number(self):
        """Ошибка, если сумма не парсится в число."""
        self.assertEqual(validate_expense_sum("five_hundred"), "Сумма расхода должна быть числом")

    def test_validate_expense_sum_invalid_values(self):
        """Ошибка при неположительной или запредельно большой сумме."""
        self.assertEqual(validate_expense_sum(0), "Сумма расхода должна быть больше 0")
        self.assertEqual(validate_expense_sum(-100.5), "Сумма расхода должна быть больше 0")
        self.assertEqual(validate_expense_sum(9999999999999.0), "Сумма слишком большая")

    # ==============================================================================
    # 3. ТЕСТЫ ВАЛИДАЦИИ НАЗВАНИЯ КАТЕГОРИИ (validate_category_name)
    # ==============================================================================

    def test_validate_category_name_success(self):
        """Успешная валидация корректного названия категории расходов."""
        self.assertIsNone(validate_category_name("Продукты"))
        self.assertIsNone(validate_category_name("  Коммуналка  "))  # Пробелы обрезаются

    def test_validate_category_name_empty(self):
        """Ошибка, если название не передано или состоит из одних пробелов."""
        self.assertEqual(validate_category_name(None), "Название категории обязательно")
        self.assertEqual(validate_category_name("   "), "Название категории не может быть пустым")

    def test_validate_category_name_too_long(self):
        """Ошибка, если длина названия превышает лимит в 100 символов."""
        long_name = "X" * 101
        self.assertEqual(
            validate_category_name(long_name), 
            "Название категории не должно превышать 100 символов"
        )

    # ==============================================================================
    # 4. КОМПЛЕКСНАЯ ВАЛИДАЦИЯ ОПЕРАЦИИ РАСХОДА (validate_create_expense)
    # ==============================================================================

    def test_validate_create_expense_success_with_date(self):
        """Успешная валидация структуры со специфической валидной датой."""
        data = {
            'id_category': '3',
            'id_card': '5',
            'sum': '750.25',
            'date_time': '2026-06-20'
        }
        errors, cleaned = validate_create_expense(data)

        self.assertEqual(errors, {})
        self.assertEqual(cleaned['id_category'], 3)
        self.assertEqual(cleaned['id_card'], 5)
        self.assertEqual(cleaned['sum'], 750.25)
        self.assertEqual(cleaned['date_time'], '2026-06-20')

    def test_validate_create_expense_success_default_date(self):
        """Успешная валидация: подстановка сегодняшней даты, если поле date_time не передано."""
        data = {
            'id_category': 1,
            'id_card': 2,
            'sum': 150
        }
        errors, cleaned = validate_create_expense(data)

        self.assertEqual(errors, {})
        self.assertEqual(cleaned['date_time'], date.today().isoformat())

    def test_validate_create_expense_future_date_error(self):
        """Ошибка валидации, если дата расхода указана в будущем."""
        tomorrow = date.today() + timedelta(days=1)
        data = {
            'id_category': 1,
            'id_card': 2,
            'sum': 500,
            'date_time': tomorrow.strftime('%Y-%m-%d')
        }
        errors, cleaned = validate_create_expense(data)

        self.assertIn('date_time', errors)
        self.assertEqual(errors['date_time'], 'Дата расхода не может быть в будущем')
        self.assertEqual(cleaned, {})

    def test_validate_create_expense_bad_date_format_error(self):
        """Ошибка валидации, если формат даты не соответствует ГГГГ-ММ-ДД."""
        data = {
            'id_category': 1,
            'id_card': 2,
            'sum': 500,
            'date_time': '2026/06/24'  # Неверный разделитель
        }
        errors, cleaned = validate_create_expense(data)

        self.assertIn('date_time', errors)
        self.assertEqual(errors['date_time'], 'Дата должна быть в формате ГГГГ-ММ-ДД')
        self.assertEqual(cleaned, {})

    def test_validate_create_expense_multiple_errors(self):
        """Проверка агрегации нескольких ошибок валидации по разным полям."""
        data = {
            'id_category': 'abc',
            'id_card': None,
            'sum': '-500'
        }
        errors, cleaned = validate_create_expense(data)

        self.assertIn('id_category', errors)
        self.assertIn('id_card', errors)
        self.assertIn('sum', errors)
        self.assertEqual(cleaned, {})


if __name__ == '__main__':
    unittest.main()