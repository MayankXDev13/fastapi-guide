from fastapi import FastAPI

from database import create_tables
from middleware.auth_middleware import AuthMiddleware
from routes.auth import router as auth_router

app = FastAPI()

app.add_middleware(AuthMiddleware)
app.include_router(auth_router)


@app.on_event("startup")
def on_startup():
    create_tables()