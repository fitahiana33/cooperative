export interface Cooperative {
  id: number
  nom: string
  sigle?: string
  numero_agrement?: string
  adresse?: string
  ville?: string
  telephone?: string
  email?: string
  description?: string
  responsable_id?: number
  is_active: boolean
  created_at: string
  updated_at?: string
  responsable?: { id: number; name: string; first_name?: string; email: string; telephone?: string; address?: string } | null
}

export interface CooperativeCreate {
  nom: string
  sigle?: string
  numero_agrement?: string
  adresse?: string
  ville?: string
  telephone?: string
  email?: string
  description?: string
  responsable_id?: number
}
