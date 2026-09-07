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
  permis_expire?: boolean
  user?: { id: number; name: string; first_name?: string; email: string; telephone?: string; address?: string }
  cooperative?: { id: number; nom: string; is_active: boolean }
  vehicule_actuel?: { id: number; id_modele: number; immatriculation: string; disponibilite: boolean; etat: string; is_active: boolean } | null
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
