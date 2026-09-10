from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    id: int
    id_user: int
    type_notification: str
    titre: str
    message: str
    id_reservation: int | None = None
    id_depart: int | None = None
    canal: str
    est_lue: bool
    date_envoi: datetime
    date_lecture: datetime | None = None
    model_config = ConfigDict(from_attributes=True)

