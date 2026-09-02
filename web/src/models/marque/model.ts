export interface Marque {
  id: number
  nom: string
  description?: string
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface MarqueCreate {
  nom: string
  description?: string
}
