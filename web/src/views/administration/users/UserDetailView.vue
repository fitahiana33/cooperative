<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppLayout from '../../../components/layout/AppLayout.vue'
import BaseCard from '../../../components/ui/BaseCard.vue'
import { userService } from '../../../services/user/service'
import { userError } from '../../../utils/errors'
import type { User } from '../../../models/user/model'

const route = useRoute()
const id = computed(() => Number(route.params.id))
const user = ref<User | null>(null)
const loading = ref(true)
const error = ref('')

function formatDate(value?: string | null) {
  return value ? new Date(value).toLocaleDateString('fr-FR') : '—'
}

function displayName(value: User) {
  return `${value.first_name || ''} ${value.name}`.trim()
}

onMounted(async () => {
  try {
    user.value = await userService.get(id.value)
    document.title = `${displayName(user.value)} · Utilisateur`
  } catch (errorValue: unknown) {
    error.value = userError(errorValue, 'Impossible de charger les détails de l’utilisateur.', 'USER_DETAIL_LOAD_ERROR')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <AppLayout>
    <template #title>Détail de l’utilisateur</template>

    <div class="page-intro">
      <div>
        <p class="eyebrow">ADMINISTRATION</p>
        <h2>Détail de l’utilisateur</h2>
        <p>Consultez les informations du compte, ses rôles et ses permissions.</p>
      </div>
      <div class="form-actions">
        <RouterLink class="secondary-button" to="/users">Retour à la liste</RouterLink>
        <RouterLink v-if="user" class="primary-button compact-button" :to="`/users/${id}/edit`">Modifier</RouterLink>
      </div>
    </div>

    <p v-if="loading" class="status-msg">Chargement des détails en cours…</p>
    <p v-else-if="error" class="error-banner" role="alert">{{ error }}</p>

    <template v-if="user && !error">
      <BaseCard>
        <div class="card-heading">
          <div>
            <h2>{{ displayName(user) }}</h2>
            <p><span :class="['status-badge', user.is_active ? 'active' : 'inactive']">{{ user.is_active ? 'Actif' : 'Inactif' }}</span></p>
          </div>
        </div>
        <div class="detail-grid">
          <div class="detail-item"><span class="detail-label">Nom complet</span><strong>{{ displayName(user) }}</strong></div>
          <div class="detail-item"><span class="detail-label">Identifiant</span><strong>#{{ user.id }}</strong></div>
          <div class="detail-item"><span class="detail-label">Rôle principal</span><strong>{{ user.role.toUpperCase() }}</strong></div>
          <div class="detail-item"><span class="detail-label">Email</span><strong>{{ user.email }}</strong></div>
          <div class="detail-item"><span class="detail-label">Téléphone</span><strong>{{ user.telephone || '—' }}</strong></div>
          <div class="detail-item detail-wide"><span class="detail-label">Adresse</span><strong>{{ user.address || '—' }}</strong></div>
          <div class="detail-item"><span class="detail-label">Créé le</span><strong>{{ formatDate(user.created_at) }}</strong></div>
        </div>
      </BaseCard>

      <BaseCard>
        <div class="card-heading"><div><h2>Rôles ({{ user.roles?.length || 0 }})</h2><p>Rôles actuellement attribués à ce compte.</p></div></div>
        <div v-if="user.roles?.length" class="detail-list"><div v-for="role in user.roles" :key="role.id" class="detail-list-row"><strong>{{ role.libelle.toUpperCase() }}</strong><span>Rôle attribué</span><span>Identifiant #{{ role.id }}</span></div></div>
        <div v-else class="empty-state"><strong>Aucun rôle attribué.</strong><span>Ce compte utilise uniquement le rôle par défaut.</span></div>
      </BaseCard>

      <BaseCard>
        <div class="card-heading"><div><h2>Permissions effectives ({{ user.permissions?.length || 0 }})</h2><p>Permissions héritées des rôles actifs.</p></div></div>
        <div v-if="user.permissions?.length" class="permission-check-grid"><div v-for="permission in user.permissions" :key="permission" class="permission-check"><span><strong>{{ permission }}</strong><small>Permission effective</small></span></div></div>
        <div v-else class="empty-state"><strong>Aucune permission effective.</strong><span>Attribuez un rôle actif à cet utilisateur.</span></div>
      </BaseCard>
    </template>
  </AppLayout>
</template>
