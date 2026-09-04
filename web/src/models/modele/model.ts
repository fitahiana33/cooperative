export interface Modele {
  id: number
  id_marque: number
  nom: string
  description?: string
  is_active: boolean
  created_at: string
  updated_at?: string
  marque?: { id: number; nom: string; is_active: boolean }
}

export interface ModeleCreate {
  id_marque: number
  nom: string
  description?: string
}
