from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User, UserRole
from app.models.role import Role, Permission
from app.repositories.user import UserRepository
from app.services.authentication.password import hash_password


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
        role = db.query(Role).filter(Role.libelle == name).first()
        if not role:
            role = Role(libelle=name, description=f"Rôle {name}")
            db.add(role)
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
        permissions[code] = permission
    db.commit()

    # Assign all permissions to ADMIN role
    admin_role = roles[UserRole.ADMIN]
    for perm in permissions.values():
        if perm not in admin_role.permissions:
            admin_role.permissions.append(perm)
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
