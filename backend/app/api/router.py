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
from app.api.controllers.destination import router as destination_router
from app.api.controllers.itineraire import router as itineraire_router
from app.api.controllers.tarif import router as tarif_router
from app.api.controllers.depart import router as depart_router
from app.api.controllers.reservation import router as reservation_router
from app.api.controllers.billet import router as billet_router
from app.api.controllers.embarquement import router as embarquement_router
from app.api.controllers.finance import router as finance_router
from app.api.controllers.notification import router as notification_router
from app.api.controllers.dashboard import router as dashboard_router

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
api_router.include_router(destination_router)
api_router.include_router(itineraire_router)
api_router.include_router(tarif_router)
api_router.include_router(depart_router)
api_router.include_router(reservation_router)
api_router.include_router(billet_router)
api_router.include_router(embarquement_router)
api_router.include_router(finance_router)
api_router.include_router(notification_router)
api_router.include_router(dashboard_router)
