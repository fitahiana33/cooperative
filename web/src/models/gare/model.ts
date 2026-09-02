export interface Quai {
  id: number
  id_gare: number
  numero: string
  nom?: string
  description?: string
  is_active: boolean
  created_at: string
}

export interface Emplacement {
  id: number
  id_zone: number
  code: string
  nom?: string
  type_emplacement?: string
  description?: string
  is_available: boolean
  is_active: boolean
  created_at: string
}

export interface Zone {
  id: number
  id_gare: number
  nom: string
  type_zone?: string
  description?: string
  is_active: boolean
  created_at: string
  emplacements: Emplacement[]
}

export interface Gare {
  id: number
  nom: string
  adresse: string
  ville: string
  region?: string
  telephone?: string
  email?: string
  description?: string
  latitude?: number
  longitude?: number
  is_active: boolean
  created_at: string
  updated_at?: string
  quais: Quai[]
  zones: Zone[]
}

export interface GareCreate {
  nom: string
  adresse: string
  ville: string
  region?: string
  telephone?: string
  email?: string
  description?: string
  latitude?: number
  longitude?: number
}
