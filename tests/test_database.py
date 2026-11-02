import os
import unittest
from unittest.mock import Mock, patch

import database


class DatabaseHelpersTests(unittest.TestCase):
    def test_ids_fit_schema_and_are_distinct(self):
        ids = {database.new_id("event") for _ in range(100)}
        self.assertEqual(len(ids), 100)
        self.assertTrue(all(len(value) <= 40 for value in ids))
        with self.assertRaises(ValueError):
            database.new_id("too-long-prefix")

    def test_missing_password_is_explicit(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "MYSQL_PASSWORD"):
                database.connection_config()

    def test_transaction_commits_and_closes(self):
        connection = Mock()
        with patch.object(database, "connect", return_value=connection):
            with database.transaction() as actual:
                self.assertIs(actual, connection)
        connection.commit.assert_called_once()
        connection.rollback.assert_not_called()
        connection.close.assert_called_once()

    def test_transaction_rolls_back_and_closes_on_failure(self):
        connection = Mock()
        with patch.object(database, "connect", return_value=connection):
            with self.assertRaises(ValueError):
                with database.transaction():
                    raise ValueError("failure")
        connection.rollback.assert_called_once()
        connection.commit.assert_not_called()
        connection.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
