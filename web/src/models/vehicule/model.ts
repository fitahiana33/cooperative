export type VehiculeEtat = 'BON_ETAT' | 'MOYEN' | 'A_REPARER' | 'HORS_SERVICE'
export type DocumentType = 'CARTE_GRISE' | 'ASSURANCE' | 'VISITE_TECHNIQUE'

export interface VehiculeDocument {
  id: number
  id_vehicule: number
  type_document: DocumentType
  numero_document?: string
  date_delivrance?: string
  date_expiration?: string
  fichier_path?: string
  is_valid: boolean
  is_active: boolean
  is_expired: boolean
  created_at: string
  updated_at?: string
}

export interface Vehicule {
  id: number
  id_modele: number
  id_cooperative: number
  immatriculation: string
  chevaux?: number
  nombre_places: number
  disponibilite: boolean
  etat: VehiculeEtat
  description?: string
  is_active: boolean
  created_at: string
  updated_at?: string
  documents: VehiculeDocument[]
}

export interface VehiculeCreate {
  id_modele: number
  id_cooperative: number
  immatriculation: string
  chevaux?: number
  nombre_places: number
  disponibilite?: boolean
  etat?: VehiculeEtat
  description?: string
}
