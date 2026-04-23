from Service.service_laier import (check_user, lead_branches, write_ticket, apply_write_patch, chek_permission,
                                   create_user, delete_user, change_user, receive_tickets, rename_user,
                                   receive_user, receive_history)
from Core.exceptions import PermissionDenied
from Core.Ticket_core import User
from datetime import datetime


class BaseController:
    def __init__(self,config,api_user_id:int,con=None):
        user = check_user(api_user_id, con=con)
        if not user:
            raise PermissionDenied("User not found")
        self.user = User(user[0])
        self.config = config
        self.con = con


class BranchController(BaseController):

    def create_branch(self,name:str):
        return lead_branches(self.user,"create_branch",self.config,name=name,con=self.con)
    def rename_branch(self,branch_id:int, new_name:str):
        return lead_branches(self.user,"rename_branch", self.config, branch_id=branch_id,name=new_name,con=self.con)
    def receive_branch(self):
        filters = {"branch_activity": 1}
        return lead_branches(self.user,"receive_branch", self.config, filters=filters, con=self.con)
    def delete_branch(self, branch_id:int):
        return lead_branches(self.user,"delete_branch",self.config,branch_id=branch_id, con=self.con)

class TicketController(BaseController):
    def create(self,
               event_data: dict):
        return write_ticket(self.config, self.user, event_data, con=self.con)

    def confirm(self, ticket_id: int, comment= None):
        patch = {'current_state': 'CONFIRMED',
                 'comment': comment}
        return apply_write_patch(self.config,self.user, patch, ticket_id, 'confirm', con=self.con)

    def reject(self, ticket_id: int, reject_comment:str):
        patch = {'current_state': 'CANCELLED',
                 'reject_comment': reject_comment,
                 'date_close': datetime.now()}
        return apply_write_patch(self.config, self.user, patch, ticket_id,'reject_comment', con=self.con)

    def priority(self, ticket_id: int, new_priority_id: int,comment=None):
        patch = {"priority": new_priority_id,
                 'comment': comment}
        return apply_write_patch(self.config, self.user, patch, ticket_id,'change_priority', con=self.con)
    def assign(self, ticket_id, comment=None):
        patch = {'current_state': 'IN_PROGRESS',
                 'assigned_to': self.user["user_id"],
                 'comment': comment}
        return apply_write_patch(self.config, self.user, patch, ticket_id,'assigned_to', con=self.con)

    def on_waiting(self, ticket_id, comment):
        patch = {'current_state': 'WAITING_EXTERNAL',
                 'comment': comment}
        return apply_write_patch(self.config, self.user, patch, ticket_id,'on_off_external', con=self.con)

    def off_waiting(self, ticket_id, comment=None):
        patch = {'current_state': 'IN_PROGRESS',
                 'comment': comment}
        return apply_write_patch(self.config, self.user, patch, ticket_id,'on_off_external', con=self.con)

    def finish(self, ticket_id, comment=None):
        patch = {'current_state': 'RESOLVED',
                 'comment': comment}
        return apply_write_patch(self.config, self.user, patch, ticket_id,'finish_ticket', con=self.con)
    def close(self,ticket_id,comment= None):
        patch = {'current_state': 'CLOSED',
                 'comment': comment,
                 'date_close': datetime.now()}
        return apply_write_patch(self.config, self.user, patch, ticket_id,'close_ticket',con=self.con)

    def get_ticket(self,filters=None, size='short'):
        tickets = receive_tickets(self.user,filters=filters, size=size,con=self.con)
        event_alert = {'self': self.user['api_user_id'], 'tickets':tickets, 'action': 'receive_tickets'}
        return event_alert

    def get_history_ticket(self,ticket_id:int):
        history = receive_history(self.user, ticket_id, self.config, con=self.con)
        event_alert = {'self': self.user['api_user_id'], 'history': history, 'action': 'receive_history'}
        return event_alert

class UserController(BaseController):
    def create_user(self,user_name:str, api_user_id:int, role_id, depart_id=None, branch_id=None):
        chek_permission(self.user,'lead_user',self.config)
        return create_user(self.user, user_name,api_user_id, role_id,
                depart_id=depart_id, branch_id=branch_id, con=self.con)


    def delete_user(self, user_id:int):
        chek_permission(self.user, 'lead_user', self.config)
        return delete_user(user=self.user, user_id=user_id,con=self.con)


    def change_user(self, user_id:int, role_id:int, depart_id=None, branch_id= None):
        chek_permission(self.user, 'admin_lead_user', self.config)
        return change_user(self.user
                           ,user_id= user_id,
                           role_id= role_id,
                           depart_id=depart_id,
                           branch_id=branch_id,
                           con=self.con)
    def rename_user(self,user_id:int,user_name:str):
        chek_permission(self.user, 'admin_lead_user', self.config)
        return rename_user(self.user, user_id,user_name,con=self.con)

    def receive_activity(self)-> list[dict]:
        filters = {'user_activity':1}
        chek_permission(self.user, 'lead_user', self.config)
        return receive_user(self.user,filters= filters,con=self.con)


    def receive_on_role(self,role_id:int)-> list[dict]:
        filters ={"role_id": role_id,
                  'user_activity': 1}
        chek_permission(self.user, 'admin_lead_user', self.config)
        return receive_user(self.user,self.config,filters=filters,con=self.con)


    def receive_on_depart(self,depart_id:int)-> list[dict]:
        filters = {"user_depart_id": depart_id,
                   'user_activity': 1}
        chek_permission(self.user, 'admin_lead_user', self.config)
        return receive_user(self.user, filters=filters,con=self.con)


    def receive_on_branch(self,branch_id)-> list[dict]:
        filters = {"user_branch_id": branch_id,
                   'user_activity': 1}
        chek_permission(self.user, 'admin_lead_user', self.config)
        return receive_user(self.user, filters=filters,con=self.con)


class Metrix: pass