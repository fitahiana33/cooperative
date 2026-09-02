import axios from 'axios'

/**
 * Logs the technical error for developers and returns a short message for users.
 * API internals must never be rendered directly in the interface.
 */
export function userError(error: unknown, fallback: string, context: string): string {
  console.error(`[${context}]`, error)

  if (!axios.isAxiosError(error)) return fallback

  const status = error.response?.status
  if (!error.response) return 'Le serveur est momentanément indisponible. Vérifiez votre connexion puis réessayez.'
  if (status === 401) return context === 'LOGIN_ERROR' ? fallback : 'Votre session a expiré. Reconnectez-vous puis réessayez.'
  if (status === 403) return 'Vous n’avez pas l’autorisation d’effectuer cette action.'
  if (status === 404) return 'La ressource demandée est introuvable.'
  if (status === 409) return 'Cette donnée existe déjà ou ne peut pas être supprimée car elle est utilisée.'
  if (status === 422) return 'Vérifiez les champs saisis puis réessayez.'
  if (status >= 500) return 'Une erreur est survenue. Veuillez réessayer.'

  if (status === 400) return 'Les informations saisies sont invalides. VÃ©rifiez les champs puis rÃ©essayez.'
  return fallback
}
