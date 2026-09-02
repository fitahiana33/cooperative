export interface UserRole { id: number; libelle: string }
export interface User { id: number; name: string; first_name?: string; email: string; telephone?: string; address?: string; role: string; roles: UserRole[]; is_active: boolean; created_at: string }
export interface UserCreate { email: string; name: string; first_name: string; telephone?: string; address?: string; role?: string; password: string }
export interface UserUpdate { email?: string; name?: string; first_name?: string; telephone?: string; address?: string; password?: string; is_active?: boolean }
