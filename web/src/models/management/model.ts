export interface Gare {
  id: number
  nom: string
  adresse: string
  ville: string
  region?: string
  telephone?: string
  email?: string
  description?: string
  latitude?: float
  longitude?: float
  is_active: boolean
  created_at: string
}

export interface Cooperative {
  id: number
  nom: string
  sigle?: string
  numero_agrement?: string
  adresse?: string
  ville?: string
  telephone?: string
  email?: string
  logo_url?: string
  description?: string
  responsable_id?: number
  is_active: boolean
  created_at: string
}

export interface Role {
  id: number
  libelle: string
  description?: string
  is_active: boolean
  created_at: string
}

export interface Permission {
  id: number
  libelle: string
  code: string
  module: string
  description?: string
  is_active: boolean
  created_at: string
}
