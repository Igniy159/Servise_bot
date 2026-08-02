from sqlite3 import Connection
from repository.mapper_repo import MapperDepart
def up(con: Connection):
    cur = con.cursor()
    crit_alert = ['NO_ELECTRICITY','NO_INTERNET','GOVERNMENT_INSPECTION','NOT_WATER']
    seq_alert = ['THEFTS_ALERT','AGGRESSIONS_ALERT','ALARM_ALERT','LOST_KEY_ALERT']
    hr_alert = [ 'STAFF_SHORTAGES','INTERN_DID_NOT_SHOW_UP','SCHEDULING_ISSUES','TEAM_CONFLICT']
    cash_alert = ['RETURNS','REPORTING_ERRORS','CASH_DISCREPANCIES']
    service_alert = ['CUSTOMER_COMPLAINTS','CONFLICT','CONTACT']
    mapper = MapperDepart(con)

    def write_rule_alert(class_alert: str,
                         alerts: list,
                         depart_id: int
                         ):
        for alert in alerts:
            cur.execute("""INSERT INTO rules_alert (class_alert,name_alert,target_id)
            VALUES (?,?,?)""",(class_alert,alert,depart_id))

    write_rule_alert('CRITICAL_ALERTS',crit_alert, mapper.get_depart_id('TOP_MANAGEMENT'))
    write_rule_alert('SECURITY_ALERTS',seq_alert,mapper.get_depart_id('SECURITY'))
    write_rule_alert('HR_ALERTS', hr_alert,mapper.get_depart_id('HR'))
    write_rule_alert('CASH_ALERTS',cash_alert,mapper.get_depart_id('ACCOUNTANT'))
    write_rule_alert('SERVICE_ALERTS',service_alert,mapper.get_depart_id('SERVICE'))
