from repository.create_migrations import get_connect,sq
from repository.read_model import get_users_with_data
from core.exceptions import AppError, IncorrectWrite, PermissionDenied, CoreValidationBreak


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
        except PermissionDenied:
            raise
        except CoreValidationBreak:
            raise

        finally:
            if not external_con:
                con.close()

    return wrapper

def check_user(api_user_id:int,con=None)-> list:
    con = con or get_connect()
    with con:
        user = get_users_with_data({'api_user_id':api_user_id,
                                   'user_activity': 1},con=con)
    return user
