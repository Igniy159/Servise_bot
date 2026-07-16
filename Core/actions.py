from datetime import datetime

class Actions:
    def __init__(self, cmd):
        self.cmd = cmd
class ConfirmAction(Actions):
    pass
class RejectAction(Actions):
    def __init__(self, cmd):
        cmd.date_close = datetime.now()
        super().__init__(cmd)
class PriorityAction(Actions):
    pass
class AssignAction(Actions):
    pass
class OnWaitAction(Actions):
    pass
class OffWaitAction(Actions):
    pass
class FinishAction(Actions):
    pass
class CloseAction(Actions):
    def __init__(self, cmd):
        cmd.date_close = datetime.now()
        super().__init__(cmd)
