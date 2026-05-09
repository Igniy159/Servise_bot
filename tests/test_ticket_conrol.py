import pytest

from api.command import CmdCreateBranch, CmdCreateUser
from service.user_service import create_first_owner
from tests.create_test_bd import init_test_db
from core.loader import load_config
from service.controllers import TicketController, BranchController, UserController
from repository.read_model import get_tickets_with_data
from core.exceptions import PermissionDenied, TicketError
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

def test_create_ticket(db,config):
    create_first_owner('Один',9999,config,con=db)
    branch_ctr = BranchController(config,9999,con=db)
    user_ctr = UserController(config,9999,con=db)

    odin_ctr = TicketController(config,9999,con=db)
    branch_ctr.create_branch(CmdCreateBranch(name='Асгард'))
    user_ctr.create_user(CmdCreateUser(name="Тор", 1234, role_id=1, branch_id=1))
    user_ctr.create_user("Фрейя", 2345, role_id=2, branch_id=1)
    tor = TicketController(config,1234,con=db)
    freya = TicketController(config,2345,con=db)
    event_valid_object = {
        "type": "OBJECT_PROBLEM",
        "problem_category": "sales",
        "problem_name": "FAUCET",
        "problem_class": "PRODUCTION_CRITICAL",
        "problem_type": "FULL_FAILURE",
        "zone": "sales",
        'branch_id':1
    }   #if create ticket OWNER in event need branch_id
    event_valid_request = {
        "type": "REQUEST",
        "problem_category": "SECURITY_REQUEST",
        "problem_name": "CASH_COLLECTION_REQUEST",
        "problem_class": "SECURITY_SERVICE",
        "problem_type": "REQUEST"
    }
    event_valid_alert = {
        "type": "ALERT",
        "problem_category": "CRITICAL_ALERTS",
        "problem_name": "NO_ELECTRICITY",
        "problem_class": "CRIT_ALERT",
        "problem_type": None,
    }
    odin_ctr.create(event_valid_object)
    tor.create(event_valid_alert)
    freya.create(event_valid_request)

    tickets = get_tickets_with_data(con=db)
    for ticket in tickets:
        assert ticket['problem_name'] in ("FAUCET","CASH_COLLECTION_REQUEST","NO_ELECTRICITY")
        if ticket["problem_name"] == "FAUCET":
            assert ticket['current_state'] == "CONFIRMED"
            assert ticket['target'] == "TOP_MANAGEMENT"
            assert ticket['assigned_to'] is None  #escalation rules
            assert ticket["priority"] == "critical"
        elif ticket['problem_name'] == "CASH_COLLECTION_REQUEST":
            assert ticket['current_state'] == "NEW"
            assert ticket['target'] == "TOP_MANAGEMENT"
        elif ticket['problem_name'] == "NO_ELECTRICITY":
            assert ticket['current_state'] ==  "NEW"  #employee can create only NEW state

def test_specialist_has_not_permission_create(db,config):
    with pytest.raises(PermissionDenied):
        event_valid_request = {
            "type": "REQUEST",
            "problem_category": "SECURITY_REQUEST",
            "problem_name": "CASH_COLLECTION_REQUEST",
            "problem_class": "SECURITY_SERVICE",
            "problem_type": "REQUEST"
        }
        create_first_owner('Один', 9999, config, con=db)
        branch_ctr = BranchController(config, 9999, con=db)
        user_ctr = UserController(config, 9999, con=db)
        branch_ctr.create_branch("Асгард")
        user_ctr.create_user("Локи", 4567, role_id=3, depart_id=2)
        loki = CreateApplyTicket(config, 4567, con=db)
        loki.create(event_valid_request)

def test_full_lifecycle_ticket(db,config):
    event_valid_request = {
        "type": "REQUEST",
        "problem_category": "SECURITY_REQUEST",
        "problem_name": "CASH_COLLECTION_REQUEST",
        "problem_class": "SECURITY_SERVICE",
        "problem_type": "REQUEST"
    }
    create_first_owner('Один',9999,config,con=db)
    branch_ctr = BranchController(config,9999,con=db)
    user_ctr = UserController(config,9999,con=db)
    odin_ctr = CreateApplyTicket(config,9999,con=db)
    branch_ctr.create_branch("Асгард")
    user_ctr.create_user("Тор",1234,role_id=1,branch_id=1)
    user_ctr.create_user("Локи",4567,role_id=3,depart_id=2)
    user_ctr.create_user("Фрейя", 2345, role_id=2, branch_id=1)
    freya = CreateApplyTicket(config, 2345, con=db)
    tor = CreateApplyTicket(config,1234,con=db)
    loki = CreateApplyTicket(config,4567,con=db)
    tor.create(event_valid_request,comment="Нужно золото!")
    ticket = get_tickets_with_data(con=db)[0]
    assert ticket['problem_name'] == "CASH_COLLECTION_REQUEST"
    assert ticket['current_state'] == "NEW"

    freya.confirm(1,comment='Заявка подтверждена')
    ticket = get_tickets_with_data(con=db)[0]
    assert ticket['current_state'] == "CONFIRMED"

    loki.assign(1,comment="Заявка принята")
    ticket = get_tickets_with_data(con=db)[0]
    assert ticket['current_state'] == "IN_PROGRESS"
    assert ticket['assigned_to'] == "Локи"

    loki.on_waiting(1,comment='Жду поступления в банке')
    ticket = get_tickets_with_data(con=db)[0]
    assert ticket['current_state'] == "WAITING_EXTERNAL"

    loki.off_waiting(1,comment="Золото получено, ожидайте")
    ticket = get_tickets_with_data(con=db)[0]
    assert ticket['current_state'] == 'IN_PROGRESS'

    loki.finish(1,comment="Передал кассиру")
    ticket = get_tickets_with_data(con=db)[0]
    assert ticket['current_state'] == 'RESOLVED'

    odin_ctr.close(1,comment='Заявка закрыта')
    ticket = get_tickets_with_data(con=db)[0]
    assert ticket['current_state'] == 'CLOSED'

def test_incorrect_lifecycle_assign(db,config):
    with pytest.raises(PermissionDenied):
        event_valid_request = {
            "type": "REQUEST",
            "problem_category": "SECURITY_REQUEST",
            "problem_name": "CASH_COLLECTION_REQUEST",
            "problem_class": "SECURITY_SERVICE",
            "problem_type": "REQUEST"
        }
        create_first_owner('Один',9999,config,con=db)
        branch_ctr = BranchController(config,9999,con=db)
        user_ctr = UserController(config,9999,con=db)
        odin_ctr = CreateApplyTicket(config,9999,con=db)
        branch_ctr.create_branch("Асгард")
        user_ctr.create_user("Тор",1234,role_id=1,branch_id=1)
        user_ctr.create_user("Локи",4567,role_id=3,depart_id=2)
        user_ctr.create_user("Фрейя", 2345, role_id=2, branch_id=1)
        freya = CreateApplyTicket(config, 2345, con=db)
        tor = CreateApplyTicket(config,1234,con=db)
        loki = CreateApplyTicket(config,4567,con=db)
        tor.create(event_valid_request,comment="Нужно золото!")
        freya.confirm(1,comment='Заявка подтверждена')
        loki.assign(1,comment="Заявка принята")
        loki.on_waiting(1,comment='Жду поступления в банке')
        loki.off_waiting(1,comment="Золото получено, ожидайте")
        loki.finish(1,comment="Передал кассиру")
        odin_ctr.close(1,comment='Заявка закрыта')
        odin_ctr.assign(1,comment='НЕВОЗМОЖНО ИЗМЕНИТЬ ЗАКРЫТЫЙ ТИКЕТ')

def test_incorrect_lifecycle_confirm(db,config):
    with pytest.raises(TicketError):
        event_valid_request = {
            "type": "REQUEST",
            "problem_category": "SECURITY_REQUEST",
            "problem_name": "CASH_COLLECTION_REQUEST",
            "problem_class": "SECURITY_SERVICE",
            "problem_type": "REQUEST"
        }
        create_first_owner('Один',9999,config,con=db)
        branch_ctr = BranchController(config,9999,con=db)
        user_ctr = UserController(config,9999,con=db)
        odin_ctr = CreateApplyTicket(config,9999,con=db)
        branch_ctr.create_branch("Асгард")
        user_ctr.create_user("Тор",1234,role_id=1,branch_id=1)
        user_ctr.create_user("Локи",4567,role_id=3,depart_id=2)
        user_ctr.create_user("Фрейя", 2345, role_id=2, branch_id=1)
        freya = CreateApplyTicket(config, 2345, con=db)
        tor = CreateApplyTicket(config,1234,con=db)
        tor.create(event_valid_request,comment="Нужно золото!")
        odin_ctr.reject(1, "Отмена")
        freya.confirm(1,comment='НЕВОЗМОЖНО ИЗМЕНИТЬ ЗАКРЫТЫЙ ТИКЕТ')

def test_incorrect_lifecycle_resolve(db,config):
    with pytest.raises(TicketError):
        event_valid_request = {
            "type": "REQUEST",
            "problem_category": "SECURITY_REQUEST",
            "problem_name": "CASH_COLLECTION_REQUEST",
            "problem_class": "SECURITY_SERVICE",
            "problem_type": "REQUEST"
        }
        create_first_owner('Один',9999,config,con=db)
        branch_ctr = BranchController(config,9999,con=db)
        user_ctr = UserController(config,9999,con=db)
        odin_ctr = CreateApplyTicket(config,9999,con=db)
        branch_ctr.create_branch("Асгард")
        user_ctr.create_user("Тор",1234,role_id=1,branch_id=1)
        user_ctr.create_user("Локи",4567,role_id=3,depart_id=2)
        user_ctr.create_user("Фрейя", 2345, role_id=2, branch_id=1)
        freya = CreateApplyTicket(config, 2345, con=db)
        tor = CreateApplyTicket(config,1234,con=db)
        loki = CreateApplyTicket(config,4567,con=db)
        tor.create(event_valid_request,comment="Нужно золото!")
        freya.confirm(1,comment='Заявка подтверждена')
        loki.assign(1,comment="Заявка принята")
        loki.on_waiting(1,comment='Жду поступления в банке')
        loki.off_waiting(1,comment="Золото получено, ожидайте")
        odin_ctr.reject(1, "Отмена")
        loki.finish(1,comment="Передал кассиру")
        odin_ctr.close(1,comment='Заявка закрыта')

def test_incorrect_lifecycle_wait(db,config):
    with pytest.raises(TicketError):
        event_valid_request = {
            "type": "REQUEST",
            "problem_category": "SECURITY_REQUEST",
            "problem_name": "CASH_COLLECTION_REQUEST",
            "problem_class": "SECURITY_SERVICE",
            "problem_type": "REQUEST"
        }
        create_first_owner('Один',9999,config,con=db)
        branch_ctr = BranchController(config,9999,con=db)
        user_ctr = UserController(config,9999,con=db)
        odin_ctr = CreateApplyTicket(config,9999,con=db)
        branch_ctr.create_branch("Асгард")
        user_ctr.create_user("Тор",1234,role_id=1,branch_id=1)
        user_ctr.create_user("Локи",4567,role_id=3,depart_id=2)
        user_ctr.create_user("Фрейя", 2345, role_id=2, branch_id=1)
        freya = CreateApplyTicket(config, 2345, con=db)
        tor = CreateApplyTicket(config,1234,con=db)
        loki = CreateApplyTicket(config,4567,con=db)
        tor.create(event_valid_request,comment="Нужно золото!")
        freya.confirm(1,comment='Заявка подтверждена')
        loki.assign(1,comment="Заявка принята")
        odin_ctr.reject(1, "Отмена")
        loki.on_waiting(1,comment='Жду поступления в банке')




def test_escalation(db,config):
    event_valid_request = {
        "type": "REQUEST",
        "problem_category": "SECURITY_REQUEST",
        "problem_name": "CASH_COLLECTION_REQUEST",
        "problem_class": "SECURITY_SERVICE",
        "problem_type": "REQUEST"
    }
    create_first_owner('Один', 9999, config, con=db)
    branch_ctr = BranchController(config, 9999, con=db)
    user_ctr = UserController(config, 9999, con=db)
    branch_ctr.create_branch("Асгард")
    user_ctr.create_user("Тор", 1234, role_id=1, branch_id=1)   #if not manager and in depart not spec ticket -confirmed and assigned OWNER
    tor = CreateApplyTicket(config,1234, con=db)
    tor.create(event_valid_request, comment="Нужно золото!")
    ticket = get_tickets_with_data(con=db)[0]
    assert ticket['current_state'] == "IN_PROGRESS"
    assert ticket['problem_name'] == "CASH_COLLECTION_REQUEST"
    assert ticket['assigned_to'] == "Один"

def test_extra_function(db,config):
    event_valid_request = {
        "type": "REQUEST",
        "problem_category": "SECURITY_REQUEST",
        "problem_name": "CASH_COLLECTION_REQUEST",
        "problem_class": "SECURITY_SERVICE",
        "problem_type": "REQUEST"
    }
    create_first_owner('Один', 9999, config, con=db)
    branch_ctr = BranchController(config, 9999, con=db)
    user_ctr = UserController(config, 9999, con=db)
    odin_ctr = CreateApplyTicket(config, 9999, con=db)
    branch_ctr.create_branch("Асгард")
    user_ctr.create_user("Тор", 1234, role_id=1, branch_id=1)
    user_ctr.create_user("Локи", 4567, role_id=3, depart_id=2)
    user_ctr.create_user("Фрейя", 2345, role_id=2, branch_id=1)
    freya = CreateApplyTicket(config, 2345, con=db)
    tor = CreateApplyTicket(config, 1234, con=db)
    loki = CreateApplyTicket(config, 4567, con=db)
    tor.create(event_valid_request, comment="Нужно золото!")
    freya.confirm(1, comment='Заявка подтверждена')
    odin_ctr.priority(1, 1, comment="Срочно нужны монеты!")
    ticket = get_tickets_with_data(con=db)[0]
    assert ticket['priority'] == 'critical'

    loki.assign(1, comment="Заявка принята")
    loki.on_waiting(1, comment='Жду поступления в банке')
    loki.off_waiting(1, comment="Золото получено, ожидайте")
    odin_ctr.reject(1,"Отмена")
    ticket = get_tickets_with_data(con=db)[0]
    assert ticket['current_state'] == 'CANCELLED'

def test_cross_branch_permission_denied(db, config):
    create_first_owner('Один', 9999, config, con=db)
    branch_ctr = BranchController(config, 9999, con=db)
    user_ctr = UserController(config, 9999, con=db)

    event_valid_request = {
        "type": "REQUEST",
        "problem_category": "SECURITY_REQUEST",
        "problem_name": "CASH_COLLECTION_REQUEST",
        "problem_class": "SECURITY_SERVICE",
        "problem_type": "REQUEST"
    }

    branch_ctr.create_branch("Асгард")
    branch_ctr.create_branch("Ванахейм")

    user_ctr.create_user("Тор", 1234, role_id=1, branch_id=1)
    user_ctr.create_user("Бальдр", 5678, role_id=2, branch_id=2)

    tor = CreateApplyTicket(config, 1234, con=db)
    baldr = CreateApplyTicket(config, 5678, con=db)

    tor.create(event_valid_request)

    with pytest.raises(PermissionDenied):
        baldr.confirm(1)

def test_specialist_cannot_reject(db,config):
    event_valid_request = {
        "type": "REQUEST",
        "problem_category": "SECURITY_REQUEST",
        "problem_name": "CASH_COLLECTION_REQUEST",
        "problem_class": "SECURITY_SERVICE",
        "problem_type": "REQUEST"
    }
    create_first_owner('Один',9999,config,con=db)
    branch_ctr = BranchController(config,9999,con=db)
    user_ctr = UserController(config,9999,con=db)
    branch_ctr.create_branch("Асгард")
    user_ctr.create_user("Тор",1234,role_id=1,branch_id=1)
    user_ctr.create_user("Локи",4567,role_id=3,depart_id=2)
    user_ctr.create_user("Фрейя", 2345, role_id=2, branch_id=1)
    freya = CreateApplyTicket(config, 2345, con=db)
    tor = CreateApplyTicket(config,1234,con=db)
    loki = CreateApplyTicket(config,4567,con=db)
    tor.create(event_valid_request,comment="Нужно золото!")
    freya.confirm(1,comment='Заявка подтверждена')
    with pytest.raises(PermissionDenied):
        loki.reject(1,'НЕ ПРИВЕЗУ')

def test_specialist_cannot_priority(db,config):
    event_valid_request = {
        "type": "REQUEST",
        "problem_category": "SECURITY_REQUEST",
        "problem_name": "CASH_COLLECTION_REQUEST",
        "problem_class": "SECURITY_SERVICE",
        "problem_type": "REQUEST"
    }
    create_first_owner('Один',9999,config,con=db)
    branch_ctr = BranchController(config,9999,con=db)
    user_ctr = UserController(config,9999,con=db)
    branch_ctr.create_branch("Асгард")
    user_ctr.create_user("Тор",1234,role_id=1,branch_id=1)
    user_ctr.create_user("Локи",4567,role_id=3,depart_id=2)
    user_ctr.create_user("Фрейя", 2345, role_id=2, branch_id=1)
    freya = CreateApplyTicket(config, 2345, con=db)
    tor = CreateApplyTicket(config,1234,con=db)
    loki = CreateApplyTicket(config,4567,con=db)
    tor.create(event_valid_request,comment="Нужно золото!")
    freya.confirm(1,comment='Заявка подтверждена')
    with pytest.raises(PermissionDenied):
        loki.priority(1,4)