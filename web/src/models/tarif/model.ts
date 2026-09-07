export interface Tarif {
  id: number
  id_itineraire: number
  id_cooperative?: number | null
  prix: number
  devise: string
  date_debut: string
  date_fin?: string | null
  is_active: boolean
  created_at: string
  updated_at?: string | null
  itineraire?: { id: number; id_destination_depart: number; id_destination_arrivee: number } | null
  cooperative?: { id: number; nom: string } | null
}

export interface TarifCreate {
  id_itineraire: number
  id_cooperative?: number | null
  prix: number
  devise?: string
  date_debut?: string
  date_fin?: string | null
}
