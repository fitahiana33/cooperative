from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User, UserRole
from app.models.role import Role, Permission
from app.repositories.user import UserRepository
from app.services.authentication.password import hash_password
from sqlalchemy import func
from app.core.roles import normalize_role


def seed_default_admin(db: Session) -> None:
    role_names = {
        UserRole.ADMIN,
        UserRole.RESPONSABLE_GARE,
        UserRole.AGENT_GARE,
        UserRole.RESPONSABLE_COOPERATIVE,
        UserRole.CHAUFFEUR,
        UserRole.PASSAGER,
    }
    roles = {}
    for name in role_names:
        role = db.query(Role).filter(func.lower(Role.libelle) == normalize_role(name)).first()
        if not role:
            role = Role(libelle=name, description=f"Rôle {name}")
            db.add(role)
        if role and role.libelle != name:
            role.libelle = name
        role.is_active = True
        roles[name] = role
    db.commit()

    permission_definitions = [
        # GARE
        ("GARE_READ", "Lecture des gares", "GARE"),
        ("GARE_CREATE", "Création de gares", "GARE"),
        ("GARE_UPDATE", "Modification de gares", "GARE"),
        ("GARE_DELETE", "Suppression de gares", "GARE"),
        # COOPERATIVE
        ("COOPERATIVE_READ", "Lecture des coopératives", "COOPERATIVE"),
        ("COOPERATIVE_CREATE", "Création de coopératives", "COOPERATIVE"),
        ("COOPERATIVE_UPDATE", "Modification de coopératives", "COOPERATIVE"),
        ("COOPERATIVE_DELETE", "Suppression de coopératives", "COOPERATIVE"),
        # USER
        ("USER_READ", "Consultation utilisateurs", "USER"),
        ("USER_CREATE", "Création d'utilisateurs", "USER"),
        ("USER_UPDATE", "Modification d'utilisateurs", "USER"),
        ("USER_DELETE", "Suppression d'utilisateurs", "USER"),
        # ROLE
        ("ROLE_MANAGE", "Gestion des rôles et permissions", "ROLE"),
        # VEHICULE
        ("VEHICULE_READ", "Consultation des véhicules", "VEHICULE"),
        ("VEHICULE_CREATE", "Ajout de véhicules", "VEHICULE"),
        ("VEHICULE_UPDATE", "Modification de véhicules", "VEHICULE"),
        ("VEHICULE_DELETE", "Suppression des véhicules", "VEHICULE"),
        ("CHAUFFEUR_READ", "Consultation des chauffeurs", "CHAUFFEUR"),
        ("CHAUFFEUR_CREATE", "Ajout de chauffeurs", "CHAUFFEUR"),
        ("CHAUFFEUR_UPDATE", "Modification des chauffeurs", "CHAUFFEUR"),
        ("CHAUFFEUR_DELETE", "Suppression des chauffeurs", "CHAUFFEUR"),
        # DEPART
        ("DEPART_CREATE", "Création de départs", "DEPART"),
        ("DEPART_READ", "Consultation des départs", "DEPART"),
        ("DEPART_UPDATE", "Mise à jour des départs", "DEPART"),
        ("DEPART_CANCEL", "Annulation de départs", "DEPART"),
        # RESERVATION
        ("RESERVATION_CREATE", "Prise de réservations", "RESERVATION"),
        ("RESERVATION_READ", "Consultation des réservations", "RESERVATION"),
        ("RESERVATION_CANCEL", "Annulation de réservations", "RESERVATION"),
        # PAIEMENT
        ("PAIEMENT_READ", "Consultation des paiements", "PAIEMENT"),
        ("PAIEMENT_PROCESS", "Traitement des paiements", "PAIEMENT"),
    ]

    permissions = {}
    for code, libelle, module in permission_definitions:
        permission = db.query(Permission).filter(Permission.code == code).first()
        if not permission:
            permission = Permission(code=code, libelle=libelle, module=module)
            db.add(permission)
        else:
            permission.libelle = libelle
            permission.module = module
            permission.is_active = True
        permissions[code] = permission
    db.commit()

    # Assign all permissions to ADMIN role
    admin_role = roles[UserRole.ADMIN]
    for perm in permissions.values():
        if perm not in admin_role.permissions:
            admin_role.permissions.append(perm)
    db.commit()

    role_permissions = {
        UserRole.RESPONSABLE_GARE: {"GARE_READ", "GARE_CREATE", "GARE_UPDATE", "GARE_DELETE"},
        UserRole.AGENT_GARE: {"GARE_READ"},
        UserRole.RESPONSABLE_COOPERATIVE: {
            "COOPERATIVE_READ", "COOPERATIVE_CREATE", "COOPERATIVE_UPDATE", "COOPERATIVE_DELETE",
            "VEHICULE_READ", "VEHICULE_CREATE", "VEHICULE_UPDATE", "VEHICULE_DELETE",
            "CHAUFFEUR_READ", "CHAUFFEUR_CREATE", "CHAUFFEUR_UPDATE", "CHAUFFEUR_DELETE",
        },
        UserRole.CHAUFFEUR: {"VEHICULE_READ"},
    }
    for role_name, codes in role_permissions.items():
        for code in codes:
            if permissions[code] not in roles[role_name].permissions:
                roles[role_name].permissions.append(permissions[code])
    db.commit()

    repository = UserRepository(db)
    existing_admin = repository.find_by_email(settings.default_admin_email)
    if existing_admin:
        if admin_role not in existing_admin.roles:
            existing_admin.roles.append(admin_role)
        db.commit()
        return

    admin = repository.create(User(
        name="Admin",
        first_name="Système",
        email=settings.default_admin_email,
        password_hash=hash_password(settings.default_admin_password),
        is_active=True,
    ))
    admin.roles.append(admin_role)
    db.commit()
