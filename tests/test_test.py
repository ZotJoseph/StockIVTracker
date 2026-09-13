import unittest
import pytest

def test_save_user(mocker):
    mock_conn = mocker.patch("sqlite3.connect")
    mock_cursor = mock_conn.return_value.something.return_value