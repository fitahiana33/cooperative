import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { NotificationItem } from '../../models/notification/model'
import { notificationService } from '../../services/notification/service'
import { api } from '../../services/api'

export const useNotificationStore = defineStore('notification', () => {
  const notifications = ref<NotificationItem[]>([])
  const currentNotification = ref<NotificationItem | null>(null)
  const total = ref(0)
  const loading = ref(false)

  async function listNotifications(params?: Record<string, any>) {
    loading.value = true
    try {
      const res = await notificationService.list(params)
      notifications.value = res.items || res
      total.value = res.total || notifications.value.length
    } finally {
      loading.value = false
    }
  }

  async function getNotification(id: number) {
    loading.value = true
    try {
      if (notifications.value.length) {
        currentNotification.value = notifications.value.find((n) => n.id === id) || null
      }
      if (!currentNotification.value) {
        const res = await notificationService.list()
        const items = res.items || res
        currentNotification.value = items.find((n: NotificationItem) => n.id === id) || null
      }
    } finally {
      loading.value = false
    }
  }

  async function markAsRead(id: number) {
    loading.value = true
    try {
      const updated = await notificationService.read(id)
      const idx = notifications.value.findIndex((n) => n.id === id)
      if (idx !== -1) notifications.value[idx] = updated
      if (currentNotification.value?.id === id) currentNotification.value = updated
      return updated
    } finally {
      loading.value = false
    }
  }

  async function markAllAsRead() {
    loading.value = true
    try {
      const res = await api.patch('/notifications/read-all')
      const updated = res.data
      notifications.value = notifications.value.map((n) => ({ ...n, est_lue: true }))
      return updated
    } finally {
      loading.value = false
    }
  }

  async function deleteNotification(id: number) {
    loading.value = true
    try {
      await api.delete(`/notifications/${id}`)
      notifications.value = notifications.value.filter((n) => n.id !== id)
      if (currentNotification.value?.id === id) currentNotification.value = null
    } finally {
      loading.value = false
    }
  }

  return { notifications, currentNotification, total, loading, listNotifications, getNotification, markAsRead, markAllAsRead, deleteNotification }
})
