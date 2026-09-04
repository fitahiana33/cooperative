export type VehiculeEtat = 'BON_ETAT' | 'MOYEN' | 'A_REPARER' | 'HORS_SERVICE'
export type DocumentType = 'CARTE_GRISE' | 'ASSURANCE' | 'VISITE_TECHNIQUE' | 'AUTRE_DOCUMENT'

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

export interface VehiculeModele {
  id: number
  id_marque: number
  nom: string
}

export interface VehiculeCooperative {
  id: number
  nom: string
  is_active: boolean
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
  modele?: VehiculeModele
  cooperative?: VehiculeCooperative
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
