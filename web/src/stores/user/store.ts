import { defineStore } from 'pinia'
import { userController } from '../../controllers/user/controller'
import type { User, UserCreate } from '../../models/user/model'

export const useUserStore = defineStore('users', {
  state: () => ({ items: [] as User[], total: 0, page: 1, pages: 0, pageSize: 20, search: '', sortBy: 'created_at', sortOrder: 'desc' as 'asc' | 'desc', loading: false, error: '', success: '' }),
  actions: {
    async fetchAll(page = this.page) { this.loading = true; this.error = ''; try { const result = await userController.list({ page, page_size: this.pageSize, search: this.search || undefined, sort_by: this.sortBy, sort_order: this.sortOrder }); this.items = result.items; this.total = result.total; this.page = result.page; this.pages = result.pages } catch (error) { console.error('[USERS_LOAD_ERROR]', error); this.error = 'Impossible de charger les utilisateurs. Vérifiez votre connexion.' } finally { this.loading = false } },
    async add(payload: UserCreate) { this.loading = true; this.error = ''; this.success = ''; try { await userController.create(payload); this.success = 'Utilisateur créé avec succès.'; await this.fetchAll(1) } catch (error) { console.error('[USER_CREATE_ERROR]', error); this.error = 'Impossible de créer cet utilisateur.' } finally { this.loading = false } },
    setSort(column: string) { this.sortOrder = this.sortBy === column && this.sortOrder === 'asc' ? 'desc' : 'asc'; this.sortBy = column; this.fetchAll(1) },
  },
})


