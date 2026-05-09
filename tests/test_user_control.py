import pytest
from api.command import CmdFirstUser, CmdCreateBranch, CmdCreateUser
from service.user_service import create_first_owner
from tests.create_test_bd import init_test_db
from core.loader import load_config
from service.controllers import UserController,BranchController
from repository.read_model import get_users_with_data
from core.exceptions import PermissionDenied, IncorrectWrite,ServiseValidationBreak
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

@pytest.fixture
def first_user():
    return CmdFirstUser(user_name='Гендальф', api_user_id=9999)

def test_assert_first_user(first_user,config,db):
    create_first_owner(first_user,config,con=db)
    user = get_users_with_data({},db)[0]
    assert user["role_name"] == "OWNER"
    assert user['user_id'] == 1


def test_owner_assert_users(db,config):
    first = CmdFirstUser(user_name='Гендальф', api_user_id=9999)
    create_first_owner(first, config, con=db)
    gend_user = UserController(config,9999,con=db)
    creator = BranchController(config,9999, con=db)
    shir = CmdCreateBranch(name='Шир')
    creator.create_branch(shir)
    gend_user.create_user(CmdCreateUser(user_name="Фродо",
                                        api_user_id=1111,
                                        role_id=1,
                                        branch_id=1))  #employee
    gend_user.create_user(CmdCreateUser(user_name="Бильбо",
                                        api_user_id=1245,
                                        role_id=2,
                                        branch_id=1))  #manager
    gend_user.create_user(CmdCreateUser(user_name="Пипин",
                                        api_user_id=1456,
                                        role_id=3,
                                        depart_id=7))  #specialist
    gend_user.create_user(CmdCreateUser(user_name="Мерлин",
                                        api_user_id=7777,
                                        role_id=4))   #2 owner
    users = get_users_with_data(con=db)
    for i in users:
        if i["api_user_id"] == 1111:
            assert i['role_name'] == "EMPLOYEE"
        elif i["api_user_id"] == 1245:
            assert i['role_name'] == "MANAGER"
        elif i["api_user_id"] == 1456:
            assert i['role_name'] == "SPECIALIST"
        elif i["api_user_id"] == 7777:
            assert i['role_name'] == "OWNER"
#
# def test_owner_delete_users(db,config):
#     create_first_owner('Гендальф', 9999,config, con=db)
#     gend_user = UserController(config,9999,con=db)
#     creator = BranchController(config,9999, con=db)
#     creator.create_branch("Шир")
#     gend_user.create_user("Фродо",1111,1,branch_id=1)
#     gend_user.create_user("Бильбо", 1245, 2, branch_id=1)
#     gend_user.create_user("Пипин",1456,3, depart_id=7)
#     gend_user.create_user("Мерлин", 7777,4)
#     gend_user.delete_user(2)
#     gend_user.delete_user(3)
#     gend_user.delete_user(4)
#     gend_user.delete_user(5)
#     def show_bd(con=None):
#         cur = con.cursor()
#         res = cur.execute("""SELECT * FROM users""").fetchall()
#         return res
#     users= show_bd(con=db)
#     for i in users:
#         if i["user_id"] != 1:
#             assert i['user_activity'] == 0   #проверяю что все пользователи кроме OWNER удалены
#
# def test_owner_change_param(db,config):
#     create_first_owner('Гендальф', 9999,config, con=db)
#     gend_user = UserController(config,9999,con=db)
#     creator = BranchController(config,9999, con=db)
#     creator.create_branch("Шир")
#     gend_user.create_user("Фродо",1111,1,branch_id=1)
#     gend_user.create_user("Бильбо", 1245, 2, branch_id=1)
#     gend_user.create_user("Пипин",1456,3, depart_id=7)
#     gend_user.create_user("Мерлин", 7777,4)
#     bilbo_beg = UserController(config,1245,con=db)
#     bilbo_beg.create_user("Мартин",8745,role_id=1)
#     gend_user.change_user(2,role_id=4) #upply role employee -> owner
#     gend_user.change_user(3,role_id=3,depart_id=1) #uply role manager -> specialist
#     gend_user.change_user(4,role_id=1,branch_id=1) #uply role specialist - employee
#     gend_user.change_user(5,role_id=2, branch_id=1) #down role two owner -> manager
#     frodo = get_users_with_data(con=db, filter_value={'api_user_id':1111})[0]
#     bilbo = get_users_with_data(con=db, filter_value={'api_user_id': 1245})[0]
#     pipin = get_users_with_data(con=db, filter_value={'api_user_id': 1456})[0]
#     merlin = get_users_with_data(con=db, filter_value={'api_user_id': 7777})[0]
#     martin = get_users_with_data(con=db, filter_value={'api_user_id': 8745})[0]
#
#     assert frodo["role_name"] == "OWNER"
#     assert frodo['branch_name'] is None
#     assert frodo["depart_name"] is None
#
#     assert bilbo["role_name"] == "SPECIALIST"
#     assert bilbo['branch_name'] is None
#     assert bilbo["depart_name"] is not None
#
#     assert pipin["role_name"] == "EMPLOYEE"
#     assert pipin['branch_name'] is not None
#     assert pipin["depart_name"] is  None
#
#     assert merlin["role_name"] == "MANAGER"
#     assert merlin['branch_name'] is not None
#     assert merlin["depart_name"] is None
#
#     assert martin["role_name"] == "EMPLOYEE"
#     assert martin['branch_name'] is not None
#     assert martin["depart_name"] is None
#
# def test_employee_not_permission_create(config,db):
#     with pytest.raises(PermissionDenied):
#         create_first_owner('Гендальф', 9999,config, con=db)
#         gend_user = UserController(config,9999,con=db)
#         creator = BranchController(config,9999, con=db)
#         creator.create_branch("Шир")
#         gend_user.create_user("Фродо",1111,1,branch_id=1)
#         frodo = UserController(config,1111,con=db)
#         frodo.create_user("Бильбо", 1245, 2, branch_id=1)
#
# def test_create_user_in_null_branch(config,db):
#     with pytest.raises(IncorrectWrite):
#         create_first_owner('Гендальф', 9999,config, con=db)
#         gend_user = UserController(config,9999,con=db)
#         gend_user.create_user("Леголас",5454,2,branch_id=999)
#
# def test_create_user_in_null_depart(config,db):
#     with pytest.raises(PermissionDenied):
#         create_first_owner('Гендальф', 9999,config, con=db)
#         gend_user = UserController(config,9999,con=db)
#         gend_user.create_user("Леголас",5454,2, depart_id=777)
#
# def test_create_double_owner(config,db):
#     with pytest.raises(ServiseValidationBreak):
#         create_first_owner('Гендальф', 9999,config, con=db)
#         create_first_owner('Гендальф', 9999, config, con=db)
#
# def test_create_double_user(config,db):
#     with pytest.raises(IncorrectWrite):
#         create_first_owner('Гендальф', 9999,config, con=db)
#         gend_user = UserController(config, 9999, con=db)
#         creator = BranchController(config,9999, con=db)
#         creator.create_branch("Шир")
#         gend_user.create_user('Леголас',8888,role_id=1,branch_id=1)
#         gend_user.create_user('Галадриэль', 8888, role_id=1, branch_id=1)
#
# def soft_delete_user_and_double_del(config,db):
#     with pytest.raises(IncorrectWrite):
#         create_first_owner('Гендальф', 9999,config, con=db)
#         gend_user = UserController(config, 9999, con=db)
#         creator = BranchController(config,9999, con=db)
#         creator.create_branch("Шир")
#         gend_user.create_user("Фродо", 1111, 1, branch_id=1)
#         gend_user.create_user("Бильбо", 1245, 2, branch_id=1)
#         gend_user.create_user("Пипин", 1456, 3, depart_id=7)
#         gend_user.create_user("Мерлин", 7777, 4)
#         gend_user.delete_user(2)
#         gend_user.delete_user(2)
#         gend_user.delete_user(3)
#         gend_user.delete_user(4)
#         gend_user.delete_user(5)
#
#         def show_user(con=None):
#             cur = con.cursor()
#             res = cur.execute("""SELECT * FROM users""").fetchone()
#             return res
#
#         users = show_user(con=db)
#         for user in users:
#             if user['user_name'] == 'Гендальф':
#                 continue
#             assert user['user_activity'] == 0
#
# def test_suicide_not_permission(config,db):
#     with pytest.raises(IncorrectWrite):
#         create_first_owner('Курт Кобейн', 9999,config, con=db)
#         own_user = UserController(config, 9999, con=db)
#         own_user.delete_user(9999)
#
# def test_self_action(config,db):
#     with pytest.raises(ServiseValidationBreak):
#         create_first_owner('Великий рыцарь Зот', 9999,config, con=db)
#         own_user = UserController(config, 9999, con=db)
#         creator = BranchController(config,9999, con=db)
#         creator.create_branch("Хэлоунест")
#         own_user.change_user(9999,role_id=1, depart_id=1)
#
# def test_change_user_not_permission(config,db):
#     with pytest.raises(PermissionDenied):
#         create_first_owner('Великий Прекрасный рыцарь Зот', 9999,config, con=db)
#         own_user = UserController(config, 9999, con=db)
#         creator = BranchController(config,9999, con=db)
#         creator.create_branch("Хэлоунест")
#         own_user.create_user("Ложный рыцарь",9784,role_id=1,branch_id=1)
#         employee = UserController(config,9784,con=db)
#         employee.change_user(9999,role_id=1,branch_id=1)
#
# def test_rename_user(config,db):
#     create_first_owner('Черв', 9999, config, con=db)
#     own_user = UserController(config, 9999, con=db)
#     creator = BranchController(config, 9999, con=db)
#     creator.create_branch("Хэлоунест")
#     own_user.create_user("Могучий Рыцарь ЗОТ",9874,1,branch_id=1)
#     own_user.rename_user(2,"Зот")
#     user = get_users_with_data(filter_value={'api_user_id':9874},con=db)[0]
#     assert user['user_name'] == "Зот"
#
# def test_create_null_user(config,db):
#     with pytest.raises(ServiseValidationBreak):
#         create_first_owner('Гендальф', 9999,config, con=db)
#         gend_user = UserController(config, 9999, con=db)
#         creator = BranchController(config,9999, con=db)
#         creator.create_branch("Шир")
#         gend_user.create_user('',8888,role_id=1,branch_id=1)
