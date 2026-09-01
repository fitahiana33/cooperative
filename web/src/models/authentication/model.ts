import type { User } from '../user/model'

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload {
  name: string
  first_name: string
  email: string
  telephone?: string
  address?: string
  password: string
}

export interface RefreshTokenPayload {
  refresh_token: string
}

export interface ForgotPasswordPayload {
  email: string
}

export interface ResetPasswordPayload {
  token: string
  new_password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user?: User
}

export interface MessageResponse {
  message: string
}
