from fastapi import APIRouter

from app.api.controllers.user import router as user_router
from app.api.controllers.authentication import router as authentication_router

api_router = APIRouter()
api_router.include_router(user_router)
api_router.include_router(authentication_router)
