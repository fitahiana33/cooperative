from fastapi import APIRouter

from app.api.controllers.user import router as user_router
from app.api.controllers.authentication import router as authentication_router
from app.api.controllers.role import router as role_router
from app.api.controllers.permission import router as permission_router
from app.api.controllers.gare import router as gare_router
from app.api.controllers.cooperative import router as cooperative_router
from app.api.controllers.marque import router as marque_router
from app.api.controllers.modele import router as modele_router
from app.api.controllers.vehicule import router as vehicule_router
from app.api.controllers.chauffeur import router as chauffeur_router

api_router = APIRouter()
api_router.include_router(authentication_router)
api_router.include_router(user_router)
api_router.include_router(role_router)
api_router.include_router(permission_router)
api_router.include_router(gare_router)
api_router.include_router(cooperative_router)
api_router.include_router(marque_router)
api_router.include_router(modele_router)
api_router.include_router(vehicule_router)
api_router.include_router(chauffeur_router)
