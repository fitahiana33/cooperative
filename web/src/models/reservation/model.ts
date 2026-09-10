export type PlaceStatus = 'DISPONIBLE' | 'RESERVEE' | 'BLOQUEE' | 'OCCUPEE'
export type ReservationStatus = 'EN_ATTENTE' | 'CONFIRMEE' | 'PAYEE' | 'ANNULEE' | 'EXPIREE' | 'EMBARQUEE' | 'TERMINEE'

export interface DepartPlace {
  id: number
  id_depart: number
  numero_place: number
  statut: PlaceStatus
}

export interface ReservationPlaceInput {
  id_depart_place: number
  nom_passager: string
  telephone_passager?: string
}

export interface Reservation {
  id: number
  numero_reservation: string
  id_depart: number
  id_user: number
  montant_total: number
  statut: ReservationStatus
  date_expiration?: string | null
  created_at: string
  depart?: { id: number; id_itineraire: number; id_cooperative: number; id_vehicule: number; date_depart: string; heure_depart: string; nombre_places: number; places_reservees: number; places_disponibles: number; statut: string }
  places: Array<{ id: number; id_depart_place: number; nom_passager: string; telephone_passager?: string; depart_place?: DepartPlace; billet?: { id: number; numero_billet: string; qr_code_uuid: string; statut: string } | null }>
}
