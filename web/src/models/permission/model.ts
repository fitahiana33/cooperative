export interface Permission {
  id: number
  libelle: string
  code: string
  module: string
  description?: string
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface PermissionCreate {
  libelle: string
  code: string
  module: string
  description?: string
}
