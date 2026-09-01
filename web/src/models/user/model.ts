export interface User { id: number; name: string; first_name: string; email: string; telephone?: string; address?: string; role: string; is_active: boolean; created_at: string }
export interface UserCreate { email: string; name: string; first_name: string; password: string }

