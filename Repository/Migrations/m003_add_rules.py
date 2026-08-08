from sqlite3 import Connection
from core.enums import ClassAlert, ClassTicket, Depart,KindRule
from repository.mapper_repo import MapperDepart

def up(con: Connection):
    cur = con.cursor()
    crit_alert = ['NO_ELECTRICITY','NO_INTERNET','GOVERNMENT_INSPECTION','NOT_WATER']
    sequrity_alert = ['THEFTS_ALERT','AGGRESSIONS_ALERT','ALARM_ALERT','LOST_KEY_ALERT']
    hr_alert = [ 'STAFF_SHORTAGES','INTERN_DID_NOT_SHOW_UP','SCHEDULING_ISSUES','TEAM_CONFLICT']
    cash_alert = ['RETURNS','REPORTING_ERRORS','CASH_DISCREPANCIES']
    service_alert = ['CUSTOMER_COMPLAINTS','CONFLICT','CONTACT']
    store = ['BAR_FRESH','BAR_CONSUMABLES',
            'BAR_DRINKS_AND_COFFEE', 'SALES_CONSUMABLES',
            'SALES_CHEMICAL', 'SALES_HOUSE_GOODS',
            'BAR_NOT_MILK_FAST', 'BAR_NOT_COFFEE_FAST', 'SALES_NOT_NEEDED']
    inventory = ['TABLEWARE', 'KNIVES_SPATULAS', 'PRICE_TAG_HOLDER','BAKING_EQUIPMENT',
                 'STAFF_EQUIPMENT', 'CLEANING_EQUIPMENT', 'EMPLOYEE_UNIFORM']
    marketing = ['REQUEST_MERCH', 'REQUEST_CURRENT_PROMOTION', 'TV_ADVERTISING',
                 'REMOVE_OUTDATED_ADVERTISING','A3_MENU', 'A4_MENU', 'POSTERS']
    sequrity = ['CAMERA_FOOTAGE_REQUEST', 'CASH_COLLECTION_REQUEST', 'BA0_SEAL_CHANGE_REQUEST']
    it = ['POS_NOT_WORK', 'MONOBLOCK_NOT_WORK', 'POS_BAR_TABLET_NOT_WORK', 'OPTIONS_POS',
          'CHANGE_PRICES', 'ADD_POSITION', 'DEL_POSITION']
    bar_eq = ['COFFEE_MACHINE', 'COFFEE_GRINDER',
              'BOILER', 'ICE_MAKER','ICE_CRUSH',
              'JUICER', 'BLENDER']
    ref = ['REFRIGERATOR', 'FREEZER',
           'SHOWCASE_REFRIGERATOR', 'COLD_SHOWCASE', 'DRY_SHOWCASE']
    el = ['LIGHTING', 'SOCKET', 'TV', 'SIGNBOARD']
    pl = ['FAUCET', 'PIPES', 'SINK', 'TOILET', 'WATER_FILTER']
    fr = ['FURNITURE', 'SHELF', 'LOCKER', 'OUTDOOR_FURNITURE']
    cl = ['AIR_CONDITIONER', 'HEATER']
    cons = ['SOAP_DISPENSER', 'PAPER_DISPENSER', 'HAND_DRYER']

    mapper = MapperDepart(con)

    def write_rule(kind:KindRule,
                   class_event: str,
                    events: list,
                    depart_id: int
                         ):
        for event in events:
            cur.execute("""INSERT INTO rules (kind,class,name,target_id)
            VALUES (?,?,?,?)""",(kind.name,class_event,event,depart_id))

    write_rule(KindRule.ALERT,ClassAlert.CRITICAL_ALERTS.name,crit_alert, mapper.get_depart_id(Depart.TOP_MANAGEMENT.name))
    write_rule(KindRule.ALERT,ClassAlert.SECURITY_ALERTS.name,sequrity_alert,mapper.get_depart_id(Depart.SECURITY.name))
    write_rule(KindRule.ALERT,ClassAlert.HR_ALERTS.name, hr_alert,mapper.get_depart_id(Depart.HR.name))
    write_rule(KindRule.ALERT,ClassAlert.CASH_ALERTS.name,cash_alert,mapper.get_depart_id(Depart.ACCOUNTANT.name))
    write_rule(KindRule.ALERT,ClassAlert.SERVICE_ALERTS.name,service_alert,mapper.get_depart_id(Depart.SERVICE.name))
    write_rule(KindRule.REQUEST,ClassTicket.STORE_REQUEST.name, store, mapper.get_depart_id(Depart.STORE.name))
    write_rule(KindRule.REQUEST,ClassTicket.INVENTORY_REQUEST.name, inventory, mapper.get_depart_id(Depart.INVENTORY.name))
    write_rule(KindRule.REQUEST,ClassTicket.MARKETING_REQUEST.name, marketing, mapper.get_depart_id(Depart.MARKETING.name))
    write_rule(KindRule.REQUEST,ClassTicket.SECURITY_REQUEST.name, sequrity, mapper.get_depart_id(Depart.SECURITY.name))
    write_rule(KindRule.REQUEST,ClassTicket.IT_REQUEST.name, it, mapper.get_depart_id(Depart.IT.name))
    ars_id = mapper.get_depart_id(Depart.ARS.name)
    write_rule(KindRule.OBJECT, ClassTicket.BAR_EQUIPMENT.name, bar_eq, ars_id)
    write_rule(KindRule.OBJECT,ClassTicket.REFRIGERATION.name, ref, ars_id)
    write_rule(KindRule.OBJECT,ClassTicket.ELECTRICAL.name, el, ars_id)
    write_rule(KindRule.OBJECT,ClassTicket.PLUMBING.name, pl, ars_id)
    write_rule(KindRule.OBJECT,ClassTicket.FURNITURE.name, fr, ars_id)
    write_rule(KindRule.OBJECT,ClassTicket.CLIMATE.name, cl, ars_id)
    write_rule(KindRule.OBJECT,ClassTicket.CONSUMABLE_EQUIPMENT.name, cons,ars_id)
