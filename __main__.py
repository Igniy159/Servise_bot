from core.ticket_core import string_shema_validator
from core.loader import config
from repository.create_migrations import get_connect, create_migration_shema,run_migrations


if __name__== '__main__':
    string_shema_validator(config)
    con = get_connect()
    create_migration_shema(con)
    run_migrations(con)
