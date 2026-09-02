import { api } from '../api'
import type {
  ForgotPasswordPayload,
  LoginPayload,
  MessageResponse,
  RefreshTokenPayload,
  RegisterPayload,
  ResetPasswordPayload,
  TokenResponse,
} from '../../models/authentication/model'
import type { User } from '../../models/user/model'

export const authenticationService = {
  async login(payload: LoginPayload): Promise<TokenResponse> {
    return (await api.post<TokenResponse>('/auth/login', payload)).data
  },

  async register(payload: RegisterPayload): Promise<TokenResponse> {
    return (await api.post<TokenResponse>('/auth/register', payload)).data
  },

  async refreshToken(payload: RefreshTokenPayload): Promise<TokenResponse> {
    return (await api.post<TokenResponse>('/auth/refresh', payload)).data
  },

  async forgotPassword(payload: ForgotPasswordPayload): Promise<MessageResponse> {
    return (await api.post<MessageResponse>('/auth/forgot-password', payload)).data
  },

  async resetPassword(payload: ResetPasswordPayload): Promise<MessageResponse> {
    return (await api.post<MessageResponse>('/auth/reset-password', payload)).data
  },

  async me(): Promise<User> {
    return (await api.get<User>('/auth/me')).data
  },

  async logout(payload?: RefreshTokenPayload): Promise<MessageResponse> {
    return (await api.post<MessageResponse>('/auth/logout', payload)).data
  },
}
