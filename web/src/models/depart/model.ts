export type DepartStatus = 'PROGRAMME' | 'EMBARQUEMENT' | 'RETARDE' | 'PARTI' | 'TERMINE' | 'ANNULE'

export interface PublicProgramme {
  id: number
  id_itineraire: number
  id_cooperative: number
  id_gare?: number | null
  date_depart: string
  heure_depart: string
  nombre_places: number
  places_reservees: number
  places_disponibles: number
  taux_remplissage: number
  statut: Extract<DepartStatus, 'PROGRAMME' | 'EMBARQUEMENT' | 'RETARDE'>
  itineraire?: {
    destination_depart?: { id: number; nom: string }
    destination_arrivee?: { id: number; nom: string }
  }
  cooperative?: { id: number; nom: string }
  gare?: { id: number; nom: string; ville: string; adresse?: string | null }
  vehicule?: { id: number; nombre_places: number }
  tarif?: { id: number; prix: number; devise: string }
}

export interface Depart {
  id: number
  id_itineraire: number
  id_cooperative: number
  id_gare?: number | null
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
  gare?: { id: number; nom: string; ville: string; adresse?: string | null }
  vehicule?: { id: number; immatriculation: string; nombre_places: number; places_avant?: number; places_par_rangee?: number }
  chauffeur?: { id: number; id_user: number; numero_permis: string }
  tarif?: { id: number; prix: number; devise: string }
}

export interface DepartCreate {
  id_itineraire: number
  id_cooperative: number
  id_gare: number
  id_vehicule: number
  id_chauffeur: number
  id_tarif: number
  date_depart: string
  heure_depart: string
  nombre_places?: number
}
