from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.chauffeur import Chauffeur

class ChauffeurRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, chauffeur_id: int) -> Chauffeur | None:
        return self.db.get(Chauffeur, chauffeur_id)

    def find_by_user_id(self, user_id: int) -> Chauffeur | None:
        return self.db.scalar(select(Chauffeur).where(Chauffeur.id_user == user_id))

    def find_by_numero_permis(self, numero_permis: str) -> Chauffeur | None:
        return self.db.scalar(select(Chauffeur).where(Chauffeur.numero_permis == numero_permis.strip()))

    def create(self, chauffeur: Chauffeur) -> Chauffeur:
        self.db.add(chauffeur)
        self.db.commit()
        self.db.refresh(chauffeur)
        return chauffeur

    def update(self, chauffeur: Chauffeur) -> Chauffeur:
        self.db.commit()
        self.db.refresh(chauffeur)
        return chauffeur

    def delete(self, chauffeur: Chauffeur) -> None:
        self.db.delete(chauffeur)
        self.db.commit()
