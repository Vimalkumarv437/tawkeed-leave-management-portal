from fastapi import APIRouter

from app.api.routes import admin, auth, employees, leaves, manager,audit


api_router = APIRouter(
    prefix="/api",
)


api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(manager.router)
api_router.include_router(employees.router)
api_router.include_router(leaves.router)
api_router.include_router(audit.router)