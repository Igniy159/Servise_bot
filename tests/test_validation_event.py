import pytest

from tests.create_test_bd import init_test_db
from core.loader import load_config
from core.ticket_core import validate_event
from core.exceptions import CoreValidationBreak
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

def test_validation_object(config):
    event_valid_object_sales = {
        "type": "OBJECT_PROBLEM",
        "problem_category": "sales",
        "problem_name": "FAUCET",
        "problem_class": "PRODUCTION_CRITICAL",
        "problem_type": "FULL_FAILURE",
        "zone": "sales",
        'branch_id':1
    }
    validate_event(event_valid_object_sales,config)
    event_valid_object_bar = {
        "type": "OBJECT_PROBLEM",
        "problem_category": "bar",
        "problem_name": "FREEZER",
        "problem_class": "PRODUCTION_IMPORTANT",
        "problem_type": "PARTIAL_PROBLEM",
        "zone": "bar"
    }
    validate_event(event_valid_object_bar,config)
    event_valid_object_outdoor = {
        "type": "OBJECT_PROBLEM",
        "problem_category": "outdoor",
        "problem_name": "LIGHTING",
        "problem_class": "PRODUCTION_IMPORTANT",
        "problem_type": "MINOR_ISSUE",
        "zone": "outdoor"
    }
    validate_event(event_valid_object_outdoor,config)

def test_validation_request(config):
    event_valid_request_sb = {
        "type": "REQUEST",
        "problem_category": "SECURITY_REQUEST",
        "problem_name": "CASH_COLLECTION_REQUEST",
        "problem_class": "SECURITY_SERVICE",
        "problem_type": "REQUEST"
    }
    validate_event(event_valid_request_sb,config)
    event_valid_request_store = {
        "type": "REQUEST",
        "problem_category": "STORE_REQUEST",
        "problem_name": "BAR_FRESH",
        "problem_class": "SUPPLY_REGULAR",
        "problem_type": "REQUEST",
        'zone': "bar"
    }
    validate_event(event_valid_request_store,config)
    event_valid_request_inventory= {
        "type": "REQUEST",
        "problem_category": "INVENTORY_REQUEST",
        "problem_name": "EMPLOYEE_UNIFORM",
        "problem_class": "INVENTORY",
        "problem_type": "REQUEST",
        'zone': "sales"
    }
    validate_event(event_valid_request_inventory,config)
    event_valid_request_it = {
        "type": "REQUEST",
        "problem_category": "IT_REQUEST",
        "problem_name": "POS_NOT_WORK",
        "problem_class": "IT_SERVICE",
        "problem_type": "INCIDENT"
    }
    validate_event(event_valid_request_it,config)

def test_event_validation_alert(config):
    event_valid_alert = {
        "type": "ALERT",
        "problem_category": "CRITICAL_ALERTS",
        "problem_name": "NO_ELECTRICITY",
        "problem_class": "CRIT_ALERT",
        "problem_type": None,
    }
    validate_event(event_valid_alert,config)
    event_valid_alert_high = {
        "type": "ALERT",
        "problem_category": "CRITICAL_ALERTS",
        "problem_name": "NO_COLD_OR_HOT_WATER",
        "problem_class": "HIGH_ALERT",
        "problem_type": None,
    }
    validate_event(event_valid_alert_high,config)
    event_valid_alert_sb = {
        "type": "ALERT",
        "problem_category": "SECURITY_ALERTS",
        "problem_name": "THEFTS_ALERT",
        "problem_class": "SEC_ALERT",
        "problem_type": None,
    }
    validate_event(event_valid_alert_sb,config)

@pytest.mark.parametrize("field,value", [
    ("type", "WRONG"),
    ("problem_category", "saJes"),
    ("problem_name", "FAUCeT"),
    ("problem_class", "PRODUCTION_CRiTICAL"),
    ("problem_type", "FULL_FAIL"),
    ("zone", "sale"),
])
def test_object_negative(field, value, config):
    event = {"type": "OBJECT_PROBLEM", "problem_category": "sales", "problem_name": "FAUCET",
             "problem_class": "PRODUCTION_CRITICAL", "problem_type": "FULL_FAILURE", "zone": "sales", field: value}
    with pytest.raises(CoreValidationBreak):
        validate_event(event, config)

def test_alert_negative(config):
    event_not_valid_alert = {
        "type": "ALERT",
        "problem_category": "CRITICAL_ALERTS",
        "problem_name": "NO_ELECTRICITY",
        "problem_class": "CRIT_ALERT",
        "problem_type": "WRONG"
    }
    with pytest.raises(CoreValidationBreak):
        validate_event(event_not_valid_alert, config)
def test_none_field(config):
    event_not_valid_request= {
        "type": "REQUEST",
        "problem_category": "INVENTORY_REQUEST",
        "problem_name": "EMPLOYEE_UNIFORM",
        "problem_class": None,
        "problem_type": "REQUEST",
        'zone': "sales"
    }
    with pytest.raises(CoreValidationBreak):
        validate_event(event_not_valid_request, config)

def test_object(config):
    event_not_valid_object_sales = {
        "type": "OBJECT_PROBLEM",
        "problem_category": "bar",
        "problem_name": "FAUCET",
        "problem_class": "PRODUCTION_CRITICAL",
        "problem_type": "FULL_FAILURE",
        "zone": "sales",
        'branch_id':1
    }
    with pytest.raises(CoreValidationBreak):
        validate_event(event_not_valid_object_sales, config)

def test_object_incorrect_matrix(config):
    event_not_valid_object_sales = {
        "type": "OBJECT_PROBLEM",
        "problem_category": "bar",
        "problem_name": "FAUCET",
        "problem_class": "COMFORT",
        "problem_type": "FULL_FAILURE",
        "zone": "bar",
        'branch_id':1
    }
    with pytest.raises(CoreValidationBreak):
        validate_event(event_not_valid_object_sales, config)

