import type { Destination } from '../destination/model'

export interface ItineraireCooperative {
  id_itineraire: number
  id_cooperative: number
  date_debut: string
  date_fin?: string | null
  is_active: boolean
  cooperative?: { id: number; nom: string; ville?: string | null; is_active: boolean } | null
}

export interface Itineraire {
  id: number
  id_destination_depart: number
  id_destination_arrivee: number
  distance_km?: number | null
  duree_estimee_minutes?: number | null
  description?: string | null
  is_active: boolean
  created_at: string
  updated_at?: string | null
  destination_depart?: Destination | null
  destination_arrivee?: Destination | null
  cooperatives?: ItineraireCooperative[]
}

export interface ItineraireCreate {
  id_destination_depart: number
  id_destination_arrivee: number
  distance_km?: number | null
  duree_estimee_minutes?: number | null
  description?: string
}
