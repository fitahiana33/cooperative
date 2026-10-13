<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import ListToolbar from '../../components/ui/ListToolbar.vue'
import PaginationControls from '../../components/ui/PaginationControls.vue'
import { notificationService } from '../../services/notification/service'
import type { NotificationItem } from '../../models/notification/model'
import { userError } from '../../utils/errors'
const items = ref<NotificationItem[]>([]); const search = ref(''); const unreadOnly = ref(false); const sortBy = ref('date_envoi'); const sortOrder = ref<'asc' | 'desc'>('desc'); const loading = ref(true); const error = ref('')
const page = ref(1); const pages = ref(1); const total = ref(0)
async function load() { loading.value = true; try { const result = await notificationService.list({ page: page.value, page_size: 20, search: search.value || undefined, unread_only: unreadOnly.value, sort_by: sortBy.value, sort_order: sortOrder.value }); items.value = result.items; total.value = result.total || items.value.length; pages.value = Math.max(result.pages || 1, 1) } catch (value: unknown) { error.value = userError(value, 'Impossible de charger les notifications.', 'NOTIFICATIONS_ERROR') } finally { loading.value = false } }
function changePage(next: number) { if (next >= 1 && next <= pages.value) { page.value = next; void load() } }
function toggleSort() { sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'; page.value = 1; void load() }
async function read(item: NotificationItem) { if (item.est_lue) return; try { Object.assign(item, await notificationService.read(item.id)) } catch (value: unknown) { error.value = userError(value, 'Impossible de marquer la notification.', 'NOTIFICATION_READ_ERROR') } }
onMounted(load)
</script>
<template><AppLayout><template #title>Notifications</template><div class="page-intro"><div><p class="eyebrow">INFORMATIONS</p><h2>Notifications</h2><p>Confirmations, rappels, retards, annulations, paiements et embarquements.</p></div></div><BaseCard><ListToolbar v-model='search' :loading='loading' placeholder='Titre, message ou type' :sort-label="sortOrder === 'asc' ? 'Tri croissant ↑' : 'Tri décroissant ↓'" @search='page = 1; load()' @sort='toggleSort' /><div class='filter-row'><label class='inline-filter'><input v-model='unreadOnly' type='checkbox' @change='page = 1; load()' /> Non lues uniquement</label><select v-model='sortBy' aria-label='Colonne de tri' @change='page = 1; load()'><option value='date_envoi'>Date d’envoi</option><option value='titre'>Titre</option><option value='type_notification'>Type</option></select></div><p v-if="loading" class="status-msg">Chargement…</p><p v-else-if="error" class="error-banner">{{ error }}</p><div v-else class="notification-list"><article v-for="item in items" :key="item.id" class="notification-item" :class="{ unread: !item.est_lue }" @click="read(item)"><div><strong>{{ item.titre }}</strong><p>{{ item.message }}</p><small>{{ new Date(item.date_envoi).toLocaleString('fr-FR') }}</small></div><span v-if="!item.est_lue" class="status-badge active">Nouveau</span></article><p v-if="!items.length" class="empty-state">Aucune notification.</p></div><PaginationControls v-if="!loading && !error" :page="page" :pages="pages" :total="total" item-label="notification(s)" @change="changePage" /></BaseCard></AppLayout></template>
