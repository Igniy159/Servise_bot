from Core.Ticket_core import string_shema_validator
from Core.loader import config
from Repository.create_migrations import get_connect, create_migration_shema,run_migrations


if __name__== '__main__':
    string_shema_validator(config)
    con = get_connect()
    create_migration_shema(con)
    run_migrations(con)













