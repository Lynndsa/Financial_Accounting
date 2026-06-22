import unittest
from unittest.mock import patch, MagicMock
import pymysql

from files_module.auth import register_user, login_user


class TestRegisterUser(unittest.TestCase):
    @patch("files_module.auth.get_connection")
    def test_register_success(self, mock_connection):

        conn = MagicMock()
        cursor = MagicMock()

        conn.cursor.return_value = cursor
        mock_connection.return_value = conn

        ok, msg = register_user(
            None,
            None,
            None,
            None,
            "user",
            "user@gmail.com",
            "123456"
        )

        self.assertTrue(ok)
        self.assertEqual(msg, "OK")

    @patch("files_module.auth.get_connection")
    def test_username_exists(self, mock_connection):

        conn = MagicMock()
        cursor = MagicMock()

        cursor.callproc.side_effect = pymysql.err.IntegrityError(1062,"Duplicate entry for user.username")

        conn.cursor.return_value = cursor
        mock_connection.return_value = conn

        ok, msg = register_user(
            None,
            None,
            None,
            None,
            "user",
            "user@gmail.com",
            "123456"
        )

        self.assertFalse(ok)


class TestLoginUser(unittest.TestCase):
    @patch("files_module.auth.get_connection")
    def test_login_success(self, mock_connection):

        conn = MagicMock()
        cursor = MagicMock()

        cursor.fetchall.return_value = [
            {"id_user": 1}
        ]

        conn.cursor.return_value = cursor
        mock_connection.return_value = conn

        result = login_user("user", "123456")

        self.assertTrue(result)

    @patch("files_module.auth.get_connection")
    def test_login_fail(self, mock_connection):

        conn = MagicMock()
        cursor = MagicMock()

        cursor.fetchall.return_value = []

        conn.cursor.return_value = cursor
        mock_connection.return_value = conn

        result = login_user("user", "123456")

        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
