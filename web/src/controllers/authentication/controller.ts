import { authenticationService } from '../../services/authentication/service'
import type {
  ForgotPasswordPayload,
  LoginPayload,
  RegisterPayload,
  ResetPasswordPayload,
  RefreshTokenPayload,
} from '../../models/authentication/model'

export const authenticationController = {
  login(payload: LoginPayload) {
    return authenticationService.login(payload)
  },

  register(payload: RegisterPayload) {
    return authenticationService.register(payload)
  },

  forgotPassword(payload: ForgotPasswordPayload) {
    return authenticationService.forgotPassword(payload)
  },

  resetPassword(payload: ResetPasswordPayload) {
    return authenticationService.resetPassword(payload)
  },

  me() {
    return authenticationService.me()
  },

  logout(payload?: RefreshTokenPayload) {
    return authenticationService.logout(payload)
  },
}
