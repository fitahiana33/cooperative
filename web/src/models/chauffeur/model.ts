export interface Chauffeur {
  id: number
  id_user: number
  id_cooperative: number
  numero_permis: string
  categorie_permis: string
  date_expiration_permis: string
  disponibilite: boolean
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface ChauffeurCreate {
  id_user: number
  id_cooperative: number
  numero_permis: string
  categorie_permis: string
  date_expiration_permis: string
  disponibilite?: boolean
}

export interface VehiculeChauffeurAssign {
  id_vehicule: number
  date_debut: string
  date_fin?: string
}
