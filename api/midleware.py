from fastapi import Request
from repository.unit_of_work import UowFactory
from repository.create_migrations import DB_PATH

async def uow_middleware(request: Request, call_next):
    main_factory_uow = UowFactory(DB_PATH)
    uow = main_factory_uow()
    request.state.uow = uow
    try:
        with uow:
            response = await call_next(request)
            return response
    except Exception:
        raise
