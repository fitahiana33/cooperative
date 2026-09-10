import { api } from '../api'
import type { NotificationItem } from '../../models/notification/model'

export const notificationService = {
  async list(params?: Record<string, unknown>) { return (await api.get('/notifications', { params })).data },
  async read(id: number): Promise<NotificationItem> { return (await api.patch(`/notifications/${id}/read`)).data },
}
