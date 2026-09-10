export interface Billet {
  id: number
  numero_billet: string
  id_reservation_place: number
  qr_code_uuid: string
  qr_code_path?: string | null
  statut: string
  date_emission: string
  date_utilisation?: string | null
  reservation_id?: number
  numero_reservation?: string
  nom_passager?: string
  telephone_passager?: string
  numero_place?: number
  id_depart?: number
  date_depart?: string
  heure_depart?: string
  statut_depart?: string
  prix?: number
  devise?: string
  destination_depart?: string
  destination_arrivee?: string
  immatriculation?: string
  nom_cooperative?: string
}
