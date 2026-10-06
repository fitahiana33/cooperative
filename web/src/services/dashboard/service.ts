import { api } from '../api'

export const dashboardService = {
  async summary() { return (await api.get('/dashboard/summary')).data },
  async statistics(params?: Record<string, unknown>) { return (await api.get('/statistiques', { params })).data },
}
