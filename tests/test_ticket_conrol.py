import pytest
import sqlite3 as sq

from core.loader import load_config
from tests.create_test_bd import init_test_db


@pytest.fixture
def db():
    con = sq.connect(":memory:")
    con.execute("PRAGMA foreign_keys = ON")
    con.row_factory = sq.Row
    init_test_db(con)
    yield con
    con.close()

@pytest.fixture
def config():
    return load_config("C:/Users/User/Desktop/Servise bot/config")

