import { defineStore } from 'pinia'
import { authenticationController } from '../../controllers/authentication/controller'
import type {
  ForgotPasswordPayload,
  LoginPayload,
  RegisterPayload,
  ResetPasswordPayload,
} from '../../models/authentication/model'
import type { User } from '../../models/user/model'
import { REFRESH_TOKEN_KEY, TOKEN_KEY } from '../../services/authentication/constants'
import { userError } from '../../utils/errors'

export const useAuthenticationStore = defineStore('authentication', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY) || '',
    user: null as User | null,
    initialized: false,
    loading: false,
    error: '',
    infoMessage: '',
  }),

  getters: {
    isAuthenticated: (state) => Boolean(state.token),
    userRole: (state) => state.user?.role || '',
  },

  actions: {
    async login(payload: LoginPayload) {
      this.loading = true
      this.error = ''
      this.infoMessage = ''
      try {
        const response = await authenticationController.login(payload)
        this.token = response.access_token
        this.refreshToken = response.refresh_token
        localStorage.setItem(TOKEN_KEY, this.token)
        localStorage.setItem(REFRESH_TOKEN_KEY, this.refreshToken)
        if (response.user) {
          this.user = response.user
        } else {
          this.user = await authenticationController.me()
        }
      } catch (error: unknown) {
        this.error = userError(error, 'Email ou mot de passe incorrect.', 'LOGIN_ERROR')
        await this.logout()
        throw error
      } finally {
        this.loading = false
      }
    },

    async register(payload: RegisterPayload) {
      this.loading = true
      this.error = ''
      this.infoMessage = ''
      try {
        const response = await authenticationController.register(payload)
        this.token = response.access_token
        this.refreshToken = response.refresh_token
        localStorage.setItem(TOKEN_KEY, this.token)
        localStorage.setItem(REFRESH_TOKEN_KEY, this.refreshToken)
        if (response.user) {
          this.user = response.user
        } else {
          this.user = await authenticationController.me()
        }
      } catch (error: unknown) {
        this.error = userError(error, 'Une erreur est survenue lors de la création de votre compte.', 'REGISTER_ERROR')
        throw error
      } finally {
        this.loading = false
      }
    },

    async forgotPassword(payload: ForgotPasswordPayload) {
      this.loading = true
      this.error = ''
      this.infoMessage = ''
      try {
        const response = await authenticationController.forgotPassword(payload)
        this.infoMessage = response.message
        return response
      } catch (error: unknown) {
        this.error = userError(error, 'Impossible d’envoyer la demande de réinitialisation.', 'FORGOT_PASSWORD_ERROR')
        throw error
      } finally {
        this.loading = false
      }
    },

    async resetPassword(payload: ResetPasswordPayload) {
      this.loading = true
      this.error = ''
      this.infoMessage = ''
      try {
        const response = await authenticationController.resetPassword(payload)
        this.infoMessage = response.message
        return response
      } catch (error: unknown) {
        this.error = userError(error, 'Code ou jeton de réinitialisation invalide ou expiré.', 'RESET_PASSWORD_ERROR')
        throw error
      } finally {
        this.loading = false
      }
    },

    async loadUser() {
      if (!this.token) { this.initialized = true; return }
      try { this.user = await authenticationController.me() }
      catch (error) { console.error('[LOAD_USER_ERROR]', error); await this.logout() }
      finally { this.initialized = true }
    },

    async logout() {
      if (this.token) {
        try { await authenticationController.logout({ refresh_token: this.refreshToken }) } catch (error) { console.error('[LOGOUT_ERROR]', error) }
      }
      this.token = ''
      this.refreshToken = ''
      this.user = null
      this.initialized = true
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
    },
  },
})

export { REFRESH_TOKEN_KEY, TOKEN_KEY }
