<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import { notificationService } from '../../services/notification/service'
import type { NotificationItem } from '../../models/notification/model'
import { userError } from '../../utils/errors'
const items = ref<NotificationItem[]>([]); const loading = ref(true); const error = ref('')
async function load() { try { const result = await notificationService.list({ page: 1, page_size: 50 }); items.value = result.items } catch (value: unknown) { error.value = userError(value, 'Impossible de charger les notifications.', 'NOTIFICATIONS_ERROR') } finally { loading.value = false } }
async function read(item: NotificationItem) { if (item.est_lue) return; try { Object.assign(item, await notificationService.read(item.id)) } catch (value: unknown) { error.value = userError(value, 'Impossible de marquer la notification.') } }
onMounted(load)
</script>
<template><AppLayout><template #title>Notifications</template><div class="page-intro"><div><p class="eyebrow">INFORMATIONS</p><h2>Notifications</h2><p>Confirmations, rappels, retards, annulations, paiements et embarquements.</p></div></div><BaseCard><p v-if="loading" class="status-msg">Chargement…</p><p v-else-if="error" class="error-banner">{{ error }}</p><div v-else class="notification-list"><article v-for="item in items" :key="item.id" class="notification-item" :class="{ unread: !item.est_lue }" @click="read(item)"><div><strong>{{ item.titre }}</strong><p>{{ item.message }}</p><small>{{ new Date(item.date_envoi).toLocaleString('fr-FR') }}</small></div><span v-if="!item.est_lue" class="status-badge active">Nouveau</span></article><p v-if="!items.length" class="empty-state">Aucune notification.</p></div></BaseCard></AppLayout></template>
