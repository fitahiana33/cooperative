import { defineStore } from 'pinia'
import { userController } from '../../controllers/user/controller'
import type { User, UserCreate } from '../../models/user/model'

export const useUserStore = defineStore('users', {
  state: () => ({ items: [] as User[], loading: false, error: '' }),
  actions: {
    async fetchAll() { this.loading = true; this.error = ''; try { this.items = await userController.list() } catch { this.error = 'Impossible de charger les utilisateurs.' } finally { this.loading = false } },
    async add(payload: UserCreate) { this.items.push(await userController.create(payload)) },
  },
})



