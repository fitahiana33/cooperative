export interface Role {
  id: number
  libelle: string
  description?: string
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface RoleCreate {
  libelle: string
  description?: string
}
