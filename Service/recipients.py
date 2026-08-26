from typing import Optional
from core.enums import Role
from core.ticket_core import User, Rule, Ticket
from repository.unit_of_work import UoW

class Recipients:
    def __init__(self,
                 manager: Optional[list[User]] = None,
                 depart:Optional[list[User]] = None,
                 owner: Optional[list[User]] = None):
        self.manager = manager or []
        self.depart = depart or []
        self.owner = owner or []

    def get_user_api_id(self)->set[int]:
        users = self.depart + self.manager + self.owner
        return {u.api_id for u in users}

class RecipientResolver:
    @staticmethod
    def get_create_recipients(uow: UoW,
                              actor: User,
                              rule: Rule)-> Recipients:
        recipients = Recipients()
        if actor.role == Role.EMPLOYEE:
            role_id = uow.role_mapper.get_roles_id(Role.MANAGER.name)
            recipients.manager = (uow.users.get({'branch_id': actor.branch_id,
                                                  'role_id': role_id,
                                                 'user_activity': 1}))
        if recipients.manager:
            return recipients
        depart_user = uow.users.get({"depart_id": rule.target.id,
                                     'user_activity': 1})
        if depart_user:
            recipients.depart = depart_user
        else:
            owner_id = uow.role_mapper.get_roles_id(Role.OWNER.name)
            recipients.owner = uow.users.get({'role_id': owner_id,
                                              'user_activity': 1})
        return recipients

    @staticmethod
    def get_update_recipient(action:str,
                             uow: UoW,
                             rule:Rule,
                             ticket: Ticket):
        depart_user = uow.users.get({"depart_id": rule.target.id,
                                     'user_activity': 1})
        owner_id = uow.role_mapper.get_roles_id(Role.OWNER.name)
        owner = uow.users.get({'role_id': owner_id,
                               'user_activity': 1})
        executor = depart_user if depart_user else owner
        role_id = uow.role_mapper.get_roles_id(Role.MANAGER.name)
        manager = uow.users.get({'branch_id': ticket.context.branch_id,
                                 'role_id': role_id,
                                 'user_activity': 1})
        creator =  uow.users.get({'user_id': ticket.context.actor_id})
        initiator = manager if manager else creator
        mapper_recipient = {
            'reject': [],
            'confirm': executor,
            'assign': initiator,
            'on_waiting': initiator,
            'finish': initiator,
            'close': executor,
        }
        return mapper_recipient.get(action)
