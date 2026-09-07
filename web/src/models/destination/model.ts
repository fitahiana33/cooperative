export interface Destination {
  id: number
  nom: string
  region?: string | null
  description?: string | null
  is_active: boolean
  created_at: string
  updated_at?: string | null
}

export interface DestinationCreate {
  nom: string
  region?: string
  description?: string
}
