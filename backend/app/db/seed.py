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

    # Older development databases used translated/legacy labels. Consolidate
    # them instead of leaving users with a role that no longer receives the
    # canonical permissions.
    legacy_to_canonical = {
        "passager": UserRole.PASSAGER,
        "manager": UserRole.RESPONSABLE_GARE,
        "driver": UserRole.CHAUFFEUR,
    }
    for legacy_name, canonical_name in legacy_to_canonical.items():
        legacy_role = db.query(Role).filter(func.lower(Role.libelle) == legacy_name).first()
        canonical_role = roles[canonical_name]
        if not legacy_role or legacy_role.id == canonical_role.id:
            continue
        for user in list(legacy_role.users):
            if canonical_role not in user.roles:
                user.roles.append(canonical_role)
            user.roles.remove(legacy_role)
        db.delete(legacy_role)
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
        ("RESERVATION_UPDATE", "Confirmation et modification des reservations", "RESERVATION"),
        ("PLACE_MANAGE", "Gestion des places des departs", "RESERVATION"),
        ("BILLET_READ", "Consultation des billets", "BILLET"),
        ("EMBARQUEMENT_READ", "Controle des billets", "EMBARQUEMENT"),
        ("EMBARQUEMENT_MANAGE", "Validation de l embarquement", "EMBARQUEMENT"),
        # PAIEMENT
        ("PAIEMENT_READ", "Consultation des paiements", "PAIEMENT"),
        ("PAIEMENT_PROCESS", "Traitement des paiements", "PAIEMENT"),
        ("PAIEMENT_REFUND", "Remboursement des paiements", "PAIEMENT"),
        ("CAISSE_READ", "Consultation de la caisse", "CAISSE"),
        ("CAISSE_OPEN", "Ouverture de caisse", "CAISSE"),
        ("CAISSE_CLOSE", "Cloture de caisse", "CAISSE"),
        ("CAISSE_MANAGE", "Gestion des operations de caisse", "CAISSE"),
        ("DASHBOARD_READ", "Consultation du tableau de bord", "DASHBOARD"),
        ("STATISTIQUE_READ", "Consultation des statistiques", "STATISTIQUE"),
        ("NOTIFICATION_READ", "Consultation des notifications", "NOTIFICATION"),
        ("NOTIFICATION_MANAGE", "Gestion des notifications", "NOTIFICATION"),
        # SPRINT 6 - DESTINATIONS, ITINERAIRES ET TARIFS
        ("DESTINATION_READ", "Consultation des destinations", "DESTINATION"),
        ("DESTINATION_CREATE", "Création de destinations", "DESTINATION"),
        ("DESTINATION_UPDATE", "Modification de destinations", "DESTINATION"),
        ("DESTINATION_DELETE", "Suppression de destinations", "DESTINATION"),
        ("ITINERAIRE_READ", "Consultation des itinéraires", "ITINERAIRE"),
        ("ITINERAIRE_CREATE", "Création d'itinéraires", "ITINERAIRE"),
        ("ITINERAIRE_UPDATE", "Modification d'itinéraires", "ITINERAIRE"),
        ("ITINERAIRE_DELETE", "Suppression d'itinéraires", "ITINERAIRE"),
        ("ITINERAIRE_COOPERATIVE_MANAGE", "Association des coopératives aux itinéraires", "ITINERAIRE"),
        ("TARIF_READ", "Consultation des tarifs", "TARIF"),
        ("TARIF_CREATE", "Création de tarifs", "TARIF"),
        ("TARIF_UPDATE", "Modification de tarifs", "TARIF"),
        ("TARIF_DELETE", "Suppression de tarifs", "TARIF"),
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
        UserRole.RESPONSABLE_GARE: {
            "GARE_READ", "GARE_CREATE", "GARE_UPDATE", "GARE_DELETE",
            "COOPERATIVE_READ",
            "VEHICULE_READ", "CHAUFFEUR_READ",
            "DEPART_READ", "DEPART_CREATE", "DEPART_UPDATE", "DEPART_CANCEL",
            "RESERVATION_READ", "RESERVATION_UPDATE", "PLACE_MANAGE", "BILLET_READ",
            "EMBARQUEMENT_READ", "EMBARQUEMENT_MANAGE", "PAIEMENT_READ", "PAIEMENT_PROCESS", "PAIEMENT_REFUND",
            "CAISSE_READ", "CAISSE_OPEN", "CAISSE_CLOSE", "CAISSE_MANAGE",
            "DASHBOARD_READ", "STATISTIQUE_READ", "NOTIFICATION_READ", "NOTIFICATION_MANAGE",
            "DESTINATION_READ", "ITINERAIRE_READ", "TARIF_READ",
        },
        UserRole.RESPONSABLE_COOPERATIVE: {
            "COOPERATIVE_READ", "COOPERATIVE_UPDATE",
            "VEHICULE_READ", "VEHICULE_CREATE", "VEHICULE_UPDATE", "VEHICULE_DELETE",
            "CHAUFFEUR_READ", "CHAUFFEUR_CREATE", "CHAUFFEUR_UPDATE", "CHAUFFEUR_DELETE",
            "DEPART_READ", "DEPART_CREATE", "DEPART_UPDATE", "DEPART_CANCEL",
            "RESERVATION_READ", "RESERVATION_CREATE", "RESERVATION_UPDATE", "RESERVATION_CANCEL", "BILLET_READ", "PAIEMENT_READ",
            "DASHBOARD_READ", "STATISTIQUE_READ", "NOTIFICATION_READ",
            "DESTINATION_READ", "ITINERAIRE_READ", "TARIF_READ",
            "ITINERAIRE_COOPERATIVE_MANAGE",
        },
        UserRole.AGENT_GARE: {
            "GARE_READ", "DEPART_READ", "RESERVATION_READ", "RESERVATION_UPDATE", "BILLET_READ",
            "EMBARQUEMENT_READ", "EMBARQUEMENT_MANAGE", "PAIEMENT_READ", "PAIEMENT_PROCESS",
            "CAISSE_READ", "CAISSE_OPEN", "CAISSE_CLOSE", "CAISSE_MANAGE", "DASHBOARD_READ",
            "DESTINATION_READ", "ITINERAIRE_READ", "TARIF_READ", "NOTIFICATION_READ",
        },
        UserRole.CHAUFFEUR: {"CHAUFFEUR_READ", "VEHICULE_READ", "DEPART_READ", "RESERVATION_READ", "BILLET_READ", "NOTIFICATION_READ", "DESTINATION_READ", "ITINERAIRE_READ", "TARIF_READ"},
        UserRole.PASSAGER: {"DEPART_READ", "RESERVATION_CREATE", "RESERVATION_READ", "RESERVATION_UPDATE", "RESERVATION_CANCEL", "BILLET_READ", "NOTIFICATION_READ", "DESTINATION_READ", "ITINERAIRE_READ", "TARIF_READ"},
    }
    managed_permission_codes = {
        code for code, _, _ in permission_definitions
    }
    for role_name, codes in role_permissions.items():
        role = roles[role_name]
        # The seed is declarative: permissions removed from the contract are
        # also removed from the role. Custom permissions remain untouched.
        for permission in list(role.permissions):
            if permission.code in managed_permission_codes and permission.code not in codes:
                role.permissions.remove(permission)
        for code in codes:
            if permissions[code] not in role.permissions:
                role.permissions.append(permissions[code])
    db.commit()

    # This permission existed in an older seed and must not remain active.
    legacy_user_manage = db.query(Permission).filter(Permission.code == "USER_MANAGE").first()
    if legacy_user_manage:
        legacy_user_manage.is_active = False
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
