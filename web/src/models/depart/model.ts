export type DepartStatus = 'PROGRAMME' | 'EMBARQUEMENT' | 'RETARDE' | 'PARTI' | 'TERMINE' | 'ANNULE'

export interface Depart {
  id: number
  id_itineraire: number
  id_cooperative: number
  id_vehicule: number
  id_chauffeur: number
  id_tarif: number
  date_depart: string
  heure_depart: string
  nombre_places: number
  places_reservees: number
  places_disponibles: number
  taux_remplissage: number
  statut: DepartStatus
  created_at: string
  updated_at?: string
  itineraire?: {
    id: number
    destination_depart?: { id: number; nom: string }
    destination_arrivee?: { id: number; nom: string }
  }
  cooperative?: { id: number; nom: string }
  vehicule?: { id: number; immatriculation: string; nombre_places: number }
  chauffeur?: { id: number; id_user: number; numero_permis: string }
  tarif?: { id: number; prix: number; devise: string }
}

export interface DepartCreate {
  id_itineraire: number
  id_cooperative: number
  id_vehicule: number
  id_chauffeur: number
  id_tarif: number
  date_depart: string
  heure_depart: string
  nombre_places?: number
}
