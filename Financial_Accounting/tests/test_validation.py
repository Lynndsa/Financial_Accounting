import unittest
from datetime import datetime, timedelta

from validations.auth_validation import validate_registration
from validations.personal_account_validation import validate_personal_account

class TestValidateRegistration(unittest.TestCase):

    def test_correct_data(self):
        errors = validate_registration(
            "user123",
            "user@gmail.com",
            "123456",
            "123456"
        )
        self.assertEqual(errors, {})

    def test_empty_username(self):
        errors = validate_registration(
            "",
            "user@gmail.com",
            "123456",
            "123456"
        )
        self.assertIn("username", errors)

    def test_short_username(self):
        errors = validate_registration(
            "abc",
            "user@gmail.com",
            "123456",
            "123456"
        )
        self.assertIn("username", errors)

    def test_invalid_email(self):
        errors = validate_registration(
            "user123",
            "abc",
            "123456",
            "123456"
        )
        self.assertIn("email", errors)

    def test_short_password(self):
        errors = validate_registration(
            "user123",
            "user@gmail.com",
            "123",
            "123"
        )
        self.assertIn("password", errors)

    def test_passwords_not_equal(self):
        errors = validate_registration(
            "user123",
            "user@gmail.com",
            "123456",
            "654321"
        )
        self.assertIn("password2", errors)


class TestValidatePersonalAccount(unittest.TestCase):

    def test_correct_data(self):
        errors = validate_personal_account(
            "Иван",
            "Иванов",
            "Иванович",
            "2000-01-01",
            "Основной счет"
        )

        self.assertEqual(errors, {})

    def test_invalid_name(self):
        errors = validate_personal_account(
            "И1",
            "Иванов",
            "Иванович",
            "2000-01-01",
            "Основной счет"
        )

        self.assertIn("name", errors)

    def test_invalid_lastname(self):
        errors = validate_personal_account(
            "Иван",
            "123",
            "Иванович",
            "2000-01-01",
            "Основной счет"
        )

        self.assertIn("lastname", errors)

    def test_invalid_surname(self):
        errors = validate_personal_account(
            "Иван",
            "Иванов",
            "@@@",
            "2000-01-01",
            "Основной счет"
        )

        self.assertIn("surname", errors)

    def test_invalid_card_name(self):
        errors = validate_personal_account(
            "Иван",
            "Иванов",
            "Иванович",
            "2000-01-01",
            "$$$"
        )

        self.assertIn("name_card", errors)

    def test_future_date(self):

        tomorrow = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")

        errors = validate_personal_account(
            "Иван",
            "Иванов",
            "Иванович",
            tomorrow,
            "Основной счет"
        )

        self.assertIn("datebirth", errors)

    def test_too_old(self):
        errors = validate_personal_account(
            "Иван",
            "Иванов",
            "Иванович",
            "1900-01-01",
            "Основной счет"
        )

        self.assertIn("datebirth", errors)


if __name__ == '__main__':
    unittest.main()


