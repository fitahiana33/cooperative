from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.finance import Paiement, Caisse, OperationCaisse

class FinanceRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_paiement_by_id(self, id_paiement: int) -> Paiement | None:
        return self.db.get(Paiement, id_paiement)

    def find_caisse_by_id(self, id_caisse: int) -> Caisse | None:
        return self.db.get(Caisse, id_caisse)

    def find_operation_by_id(self, id_operation: int) -> OperationCaisse | None:
        return self.db.get(OperationCaisse, id_operation)

    def find_caisse_ouverte(self, id_gare: int) -> Caisse | None:
        return self.db.scalar(select(Caisse).where(Caisse.id_gare == id_gare, Caisse.statut == "ouverte"))

    def create_paiement(self, paiement: Paiement) -> Paiement:
        self.db.add(paiement)
        self.db.commit()
        self.db.refresh(paiement)
        return paiement

    def create_caisse(self, caisse: Caisse) -> Caisse:
        self.db.add(caisse)
        self.db.commit()
        self.db.refresh(caisse)
        return caisse

    def create_operation(self, operation: OperationCaisse) -> OperationCaisse:
        self.db.add(operation)
        self.db.commit()
        self.db.refresh(operation)
        return operation

    def update_paiement(self, paiement: Paiement) -> Paiement:
        self.db.commit()
        self.db.refresh(paiement)
        return paiement

    def update_caisse(self, caisse: Caisse) -> Caisse:
        self.db.commit()
        self.db.refresh(caisse)
        return caisse

    def delete_paiement(self, paiement: Paiement) -> None:
        self.db.delete(paiement)
        self.db.commit()
