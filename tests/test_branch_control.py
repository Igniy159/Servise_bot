import pytest

from service.service_laier import create_first_owner
from tests.create_test_bd import init_test_db
from core.loader import load_config
from service.controllers import BranchController, UserController
from repository.read_model import get_branch_with_data
from core.exceptions import PermissionDenied, IncorrectWrite, ServiseValidationBreak
import sqlite3 as sq


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

def test_owner_branch_create(db, config):
    create_first_owner("Атрейдес",1234,config,con=db)
    atrey = BranchController(config,1234,con=db)
    atrey.create_branch("Арракис")
    branch = get_branch_with_data(con=db)[0]
    assert branch['branch_name'] == "Арракис"
    assert branch['branch_id'] == 1

def test_owner_branch_rename(db,config):
    create_first_owner("Атрейдес",1234,config,con=db)
    atrey = BranchController(config,1234,con=db)
    atrey.create_branch("Арракис")
    atrey.rename_branch(1,"Новый Арракис")
    branch = get_branch_with_data(con=db)[0]
    assert branch['branch_name'] == "Новый Арракис"
    assert branch['branch_id'] == 1

def test_owner_branch_delete(db,config):
    create_first_owner("Атрейдес",1234,config,con=db)
    atrey = BranchController(config,1234,con=db)
    atrey.create_branch("Арракис")
    atrey.delete_branch(1)
    def show_branch(con=None):
        cur = con.cursor()
        res = cur.execute("""SELECT * FROM branch""").fetchone()
        return res
    branch = show_branch(con=db)
    assert branch['branch_activity'] == 0

def test_not_user_and_branch_control(db,config):
    with pytest.raises(PermissionDenied):
        atrey = BranchController(config,1234,con=db)
        atrey.create_branch("Арракис")

def test_has_not_permission(db,config):
    with pytest.raises(PermissionDenied):
        create_first_owner("Атрейдес",1234,config,con=db)
        atrey = BranchController(config, 1234, con=db)   #создаю филиал и добавляю пользователя
        u_atrey = UserController(config,1234,con=db)
        atrey.create_branch("Арракис")
        u_atrey.create_user("Голлум",1223,1,branch_id=1)   #пользователь(не владелец)
        gollum = BranchController(config,1223,con=db)
        gollum.create_branch("Моя прелесть!")

def test_not_found_del_branch(db,config):
    with pytest.raises(IncorrectWrite):
        create_first_owner("Атрейдес",1234,config,con=db)
        atrey = BranchController(config, 1234, con=db)
        atrey.create_branch("Арракис")
        atrey.delete_branch(999)

def test_not_found_rename_branch(db,config):
    with pytest.raises(IncorrectWrite):
        create_first_owner("Атрейдес",1234,config,con=db)
        atrey = BranchController(config, 1234, con=db)
        atrey.create_branch("Арракис")
        atrey.rename_branch(999, "Новый Арракис")

def test_create_null_branch(db,config):
    with pytest.raises(ServiseValidationBreak):
        create_first_owner("Атрейдес",1234,config,con=db)
        atrey = BranchController(config, 1234, con=db)
        atrey.create_branch("")
def test_double_delete(db,config):
    create_first_owner("Атрейдес",1234,config,con=db)
    atrey = BranchController(config,1234,con=db)
    atrey.create_branch("Арракис")
    atrey.delete_branch(1)
    atrey.delete_branch(1)
    def show_branch(con=None):
        cur = con.cursor()
        res = cur.execute("""SELECT * FROM branch""").fetchone()
        return res
    branch = show_branch(con=db)
    assert branch['branch_activity'] == 0
