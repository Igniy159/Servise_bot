class AppError(Exception):pass

class RepositoryError(AppError): pass   #OpertionalError
class IncorrectWrite(RepositoryError): pass  #IntegrityError
class SQLValidationBreak(RepositoryError):pass


class TicketError(AppError): pass
class CoreValidationBreak(TicketError): pass
class LifecycleError(TicketError): pass

class ServiseError(AppError):pass
class PermissionDenied(ServiseError): pass
class ServiseValidationBreak(ServiseError): pass