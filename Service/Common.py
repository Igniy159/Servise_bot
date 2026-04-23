from Repository.create_migrations import get_connect,sq
from Repository.read_model import get_users_with_data
from Core.exceptions import AppError,IncorrectWrite, ServiseValidationBreak,PermissionDenied
from Core.Ticket_core import User
from typing import Optional

def transactional(func):
    def wrapper(*args, **kwargs):
        external_con = kwargs.get("con")
        con = external_con or get_connect()

        try:
            kwargs["con"] = con
            result = func(*args, **kwargs)
            if not external_con:
                con.commit()
            return result


        except AppError:
            if not external_con:
                con.rollback()
            raise

        except sq.Error as e:
            if not external_con:
                con.rollback()
            raise IncorrectWrite(str(e))

        finally:
            if not external_con:
                con.close()

    return wrapper

#валидация фильтров - уйдет в Pydantic
def filters_key_validator(filters: dict):
    if not isinstance(filters,dict):
        raise ServiseValidationBreak(f"this filters incorrect type")
    branch_key = {"branch_id", "branch_name", "branch_activity"}
    user_key = {"user_id","api_user_id","user_branch_id","user_depart_id","role_id","user_activity"}
    ticket_key = {"ticket_id","zone","branch_id","depart_id","creator_id","status","priority", 'state','sort_priority',"sort_status"}
    prohibit_keys = branch_key | user_key | ticket_key
    type_map ={"branch_id": int,
               "branch_name": str,
               "branch_activity": int,
               "user_id": int,
               "api_user_id": int,
               "user_branch_id": int,
                "user_depart_id": int,
               "role_id": int,
               "user_activity": int,
               "ticket_id": int,
               'zone': str,
               "depart_id": int,
               "creator_id": int,
               "status": int,
               "priority": int,
               'state': str,
               'sort_priority': str,
               "sort_status": str
    }
    for key, val in filters.items():
        if key not in prohibit_keys:
            raise ServiseValidationBreak(f"this key {key} not in prohibit_keys")
        elif not isinstance(val,type_map[key]):
            raise ServiseValidationBreak(f"This {val} incorrect type for {key}")
        elif key in ("user_activity", "branch_activity") and  val not in (0,1):
            raise ServiseValidationBreak(f"This {val} incorrect value for {key}")
        elif key in ('sort_priority', "sort_status") and  val not in ('asc','desc'):
            raise ServiseValidationBreak(f"This {val} incorrect value for {key}")
    return None
def apply_scope(user:Optional[User], filters:dict):
    scoped = dict(filters or {})
    if user.role == "MANAGER":
        scoped["branch_id"] = user["branch_id"]
        scoped["user_branch_id"] = user["branch_id"]

    if user.role == "SPECIALIST":
        scoped["depart_id"] = user["depart_id"]

    if user.role == "EMPLOYEE":
        scoped["creator_id"] = user["user_id"]

    return scoped
def filters_validator(user:Optional[User], filters= None):
    white_list_manager = ("branch_id","user_branch_id","user_activity",'ticket_id','state','sort_status')
    white_list_specialist =("ticket_id","zone","branch_id","depart_id","status","priority",'state','sort_priority',"sort_status")
    white_list_employee = ("creator_id","sort_status")
    if user.role == "OWNER":
        return None
    elif user.role == "MANAGER":
        if filters is None:
            raise PermissionDenied("MANAGER must have filter on data ")
        for key in filters:
            if key not in white_list_manager:
                raise PermissionDenied(f"Incorrect {key} value for MANAGER")
            elif key == "user_branch_id" and user.branch_id != filters["user_branch_id"]:
                raise PermissionDenied("Manager can view only mine branch")
            elif key == "branch_id" and user.branch_id != filters["branch_id"]:
                raise PermissionDenied("Manager can view only mine branch")
    elif user.role == "SPECIALIST":
        if filters is None:
            raise PermissionDenied("SPECIALIST must have filter on data ")
        for key in filters:
            if key not in white_list_specialist:
                raise PermissionDenied(f"Incorrect {key} value for SPECIALIST")
            elif key == "depart_id" and user.depart_id != filters["depart_id"]:
                raise PermissionDenied("Specialist can view only mine departament")
    elif user.role == "EMPLOYEE":
        if filters is None:
            raise PermissionDenied("EMPLOYEE must have filter on data ")
        for key in filters:
            if key not in white_list_employee:
                raise PermissionDenied(f"Incorrect {key} value for Employee")
            elif key == "creator_id" and user.id != filters["creator_id"]:
                raise PermissionDenied("EMPLOYEE can view only mine tickets")
    return None

def check_user(api_user_id:int,con=None)-> tuple|bool:
    con = con or get_connect()
    with con:
        res = get_users_with_data({'api_user_id':api_user_id,
                                   'user_activity': 1},con=con)