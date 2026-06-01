from fastapi import FastAPI

from database import create_tables
from middleware.auth_middleware import AuthMiddleware
from routes.auth import router as auth_router
from routes.project import router as project_router

app = FastAPI()

app.add_middleware(AuthMiddleware)
app.include_router(auth_router)
app.include_router(project_router)


@app.on_event("startup")
def on_startup():
    create_tables()
