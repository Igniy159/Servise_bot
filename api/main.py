import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from api.routers import private_router
from api.midleware import uow_middleware

app = FastAPI()

app.middleware("http")(uow_middleware)
app.include_router(private_router)

FASTAPI_URL = os.getenv("FASTAPI_INTERNAL_URL", "http://localhost:8000/api/v1/auth")


if __name__ == '__main__':
    load_dotenv()
    uvicorn.run('api.main:app',host="0.0.0.0", port=8000)
