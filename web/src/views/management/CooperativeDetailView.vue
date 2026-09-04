<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import { managementService } from '../../services/management/service'
import { chauffeurService } from '../../services/chauffeur/service'
import { vehiculeService } from '../../services/vehicule/service'
import { useAuthenticationStore } from '../../stores/authentication/store'
import { userError } from '../../utils/errors'
import type { Cooperative } from '../../models/cooperative/model'
import type { Chauffeur } from '../../models/chauffeur/model'
import type { Gare } from '../../models/gare/model'
import type { User } from '../../models/user/model'
import type { Vehicule } from '../../models/vehicule/model'

interface GareAssociation {
  id_gare: number
  gare?: { id: number; nom: string; ville: string; is_active: boolean }
  date_debut?: string
  date_fin?: string
  is_active: boolean
}

interface CooperativeMember {
  id_user: number
  user?: { id: number; name: string; first_name?: string; email: string }
  fonction?: string
  date_adhesion?: string
  date_fin?: string
  is_active: boolean
}

const route = useRoute()
const auth = useAuthenticationStore()
const id = computed(() => Number(route.params.id))
const cooperative = ref<Cooperative | null>(null)
const gares = ref<GareAssociation[]>([])
const members = ref<CooperativeMember[]>([])
const vehicules = ref<Vehicule[]>([])
const chauffeurs = ref<Chauffeur[]>([])
const availableGares = ref<Gare[]>([])
const eligibleMembers = ref<User[]>([])
const selectedGare = ref<number | null>(null)
const selectedMember = ref<number | null>(null)
const memberFunction = ref('MEMBRE')
const loading = ref(true)
const relationLoading = ref(false)
const relationSubmitting = ref(false)
const error = ref('')
const relationError = ref('')
const success = ref('')

const canEdit = computed(() => auth.hasPermission('COOPERATIVE_UPDATE'))
const canManageRelations = computed(() => auth.hasPermission('COOPERATIVE_UPDATE'))

function formatDate(value?: string | null) {
  return value ? new Date(value).toLocaleDateString('fr-FR') : '-'
}

function displayResponsible() {
  if (!cooperative.value) return 'Non designe'
  if (cooperative.value.responsable) {
    return `${cooperative.value.responsable.first_name || ''} ${cooperative.value.responsable.name}`.trim()
  }
  return cooperative.value.responsable_id ? `Utilisateur #${cooperative.value.responsable_id}` : 'Non designe'
}

function displayUser(member: CooperativeMember) {
  return member.user
    ? `${member.user.first_name || ''} ${member.user.name}`.trim()
    : `Utilisateur #${member.id_user}`
}

function displayDriver(chauffeur: Chauffeur) {
  return chauffeur.user
    ? `${chauffeur.user.first_name || ''} ${chauffeur.user.name}`.trim()
    : `Utilisateur #${chauffeur.id_user}`
}

async function loadRelations() {
  relationLoading.value = true
  relationError.value = ''
  const requests: Promise<unknown>[] = [
    managementService.listGareAssociations(id.value),
    managementService.listCooperativeMembers(id.value),
    vehiculeService.listVehicules({
      page: 1,
      page_size: 100,
      id_cooperative: id.value,
      sort_by: 'immatriculation',
      sort_order: 'asc',
    }),
    chauffeurService.listChauffeurs({
      page: 1,
      page_size: 100,
      id_cooperative: id.value,
      sort_by: 'created_at',
      sort_order: 'desc',
    }),
  ]
  if (canManageRelations.value) {
    requests.push(
      managementService.listAvailableGares(id.value),
      managementService.listEligibleMembers(id.value),
    )
  }

  const results = await Promise.allSettled(requests)
  if (results[0].status === 'fulfilled') gares.value = results[0].value as GareAssociation[]
  if (results[1].status === 'fulfilled') members.value = results[1].value as CooperativeMember[]
  if (results[2].status === 'fulfilled') vehicules.value = (results[2].value as { items: Vehicule[] }).items || []
  if (results[3].status === 'fulfilled') chauffeurs.value = (results[3].value as { items: Chauffeur[] }).items || []
  if (canManageRelations.value && results[4]?.status === 'fulfilled') availableGares.value = results[4].value as Gare[]
  if (canManageRelations.value && results[5]?.status === 'fulfilled') eligibleMembers.value = results[5].value as User[]
  if (results.some(result => result.status === 'rejected')) {
    relationError.value = 'Certaines informations associees ne sont pas disponibles pour ce compte.'
  }
  relationLoading.value = false
}

async function attachGare() {
  if (!selectedGare.value || relationSubmitting.value) return
  relationSubmitting.value = true
  relationError.value = ''
  success.value = ''
  try {
    await managementService.attachToGare(id.value, selectedGare.value)
    selectedGare.value = null
    success.value = 'La gare a ete rattachee a la cooperative.'
    await loadRelations()
  } catch (errorValue: unknown) {
    relationError.value = userError(errorValue, 'Impossible de rattacher cette gare.', 'COOPERATIVE_GARE_ATTACH_ERROR')
  } finally {
    relationSubmitting.value = false
  }
}

async function detachGare(gareId: number) {
  if (relationSubmitting.value || !window.confirm('Retirer cette gare de la cooperative ?')) return
  relationSubmitting.value = true
  relationError.value = ''
  try {
    await managementService.removeFromGare(id.value, gareId)
    success.value = 'Le rattachement de la gare a ete desactive.'
    await loadRelations()
  } catch (errorValue: unknown) {
    relationError.value = userError(errorValue, 'Impossible de retirer cette gare.', 'COOPERATIVE_GARE_REMOVE_ERROR')
  } finally {
    relationSubmitting.value = false
  }
}

async function addMember() {
  if (!selectedMember.value || relationSubmitting.value) return
  relationSubmitting.value = true
  relationError.value = ''
  success.value = ''
  try {
    await managementService.addMember(id.value, {
      id_user: selectedMember.value,
      fonction: memberFunction.value.trim() || 'MEMBRE',
    })
    selectedMember.value = null
    memberFunction.value = 'MEMBRE'
    success.value = 'Le membre a ete rattache a la cooperative.'
    await loadRelations()
  } catch (errorValue: unknown) {
    relationError.value = userError(errorValue, 'Impossible d ajouter ce membre.', 'COOPERATIVE_MEMBER_ADD_ERROR')
  } finally {
    relationSubmitting.value = false
  }
}

async function removeMember(userId: number) {
  if (relationSubmitting.value || !window.confirm('Retirer cet utilisateur de la cooperative ?')) return
  relationSubmitting.value = true
  relationError.value = ''
  try {
    await managementService.removeMember(id.value, userId)
    success.value = 'Le membre a ete desactive dans cette cooperative.'
    await loadRelations()
  } catch (errorValue: unknown) {
    relationError.value = userError(errorValue, 'Impossible de retirer ce membre.', 'COOPERATIVE_MEMBER_REMOVE_ERROR')
  } finally {
    relationSubmitting.value = false
  }
}

onMounted(async () => {
  try {
    cooperative.value = await managementService.getCooperative(id.value)
    document.title = `${cooperative.value.nom} - Cooperative`
    await loadRelations()
  } catch (errorValue: unknown) {
    error.value = userError(errorValue, 'Impossible de charger les details de la cooperative.', 'COOPERATIVE_DETAIL_LOAD_ERROR')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <AppLayout>
    <template #title>Detail de la cooperative</template>

    <div class="page-intro">
      <div>
        <p class="eyebrow">GESTION DES COOPERATIVES</p>
        <h2>Detail de la cooperative</h2>
        <p>Consultez les informations, gares, membres, vehicules et chauffeurs associes.</p>
      </div>
      <div class="form-actions">
        <RouterLink class="secondary-button" to="/cooperatives">Retour a la liste</RouterLink>
        <RouterLink v-if="cooperative && canEdit" class="primary-button compact-button" :to="`/cooperatives/${id}/edit`">Modifier</RouterLink>
      </div>
    </div>

    <p v-if="loading" class="status-msg" role="status">Chargement des details en cours...</p>
    <p v-else-if="error" class="error-banner" role="alert">{{ error }}</p>
    <p v-if="relationError && cooperative" class="error-banner" role="status">{{ relationError }}</p>
    <p v-if="success" class="success-banner" role="status">{{ success }}</p>

    <template v-if="cooperative && !error">
      <BaseCard>
        <div class="card-heading">
          <div>
            <h2>{{ cooperative.nom }}</h2>
            <p><span :class="['status-badge', cooperative.is_active ? 'active' : 'inactive']">{{ cooperative.is_active ? 'Active' : 'Inactive' }}</span></p>
          </div>
        </div>
        <div class="detail-grid">
          <div class="detail-item"><span class="detail-label">Nom</span><strong>{{ cooperative.nom }}</strong></div>
          <div class="detail-item"><span class="detail-label">Sigle</span><strong>{{ cooperative.sigle || '-' }}</strong></div>
          <div class="detail-item"><span class="detail-label">Numero d agrement</span><strong>{{ cooperative.numero_agrement || '-' }}</strong></div>
          <div class="detail-item"><span class="detail-label">Ville</span><strong>{{ cooperative.ville || '-' }}</strong></div>
          <div class="detail-item detail-wide"><span class="detail-label">Adresse</span><strong>{{ cooperative.adresse || '-' }}</strong></div>
          <div class="detail-item"><span class="detail-label">Telephone</span><strong>{{ cooperative.telephone || '-' }}</strong></div>
          <div class="detail-item"><span class="detail-label">Email</span><strong>{{ cooperative.email || '-' }}</strong></div>
          <div class="detail-item"><span class="detail-label">Responsable</span><strong>{{ displayResponsible() }}</strong></div>
          <div class="detail-item"><span class="detail-label">Creee le</span><strong>{{ formatDate(cooperative.created_at) }}</strong></div>
          <div class="detail-item"><span class="detail-label">Modifiee le</span><strong>{{ formatDate(cooperative.updated_at) }}</strong></div>
          <div class="detail-item detail-wide"><span class="detail-label">Description</span><strong>{{ cooperative.description || 'Aucune description.' }}</strong></div>
        </div>
      </BaseCard>

      <BaseCard>
        <div class="card-heading">
          <div><h2>Gares associees ({{ gares.length }})</h2><p>Gares auxquelles cette cooperative est rattachee.</p></div>
        </div>
        <div v-if="canManageRelations" class="inline-form">
          <select v-model="selectedGare" :disabled="relationSubmitting || relationLoading">
            <option :value="null">Selectionner une gare a rattacher</option>
            <option v-for="gare in availableGares" :key="gare.id" :value="gare.id">{{ gare.nom }} - {{ gare.ville }}</option>
          </select>
          <button class="primary-button compact-button" type="button" :disabled="!selectedGare || relationSubmitting" @click="attachGare">{{ relationSubmitting ? 'Traitement...' : 'Rattacher' }}</button>
        </div>
        <div v-if="gares.length" class="table-scroll">
          <table class="data-table"><caption>Liste des gares associees</caption><thead><tr><th>Gare</th><th>Debut</th><th>Fin</th><th>Statut</th><th v-if="canManageRelations">Actions</th></tr></thead>
            <tbody><tr v-for="gare in gares" :key="gare.id_gare"><td><RouterLink class="table-link" :to="`/gares/${gare.gare?.id || gare.id_gare}`"><strong>{{ gare.gare?.nom || `Gare #${gare.id_gare}` }}</strong></RouterLink><small v-if="gare.gare">{{ gare.gare.ville }}</small></td><td>{{ formatDate(gare.date_debut) }}</td><td>{{ formatDate(gare.date_fin) }}</td><td><span :class="['status-badge', gare.is_active ? 'active' : 'inactive']">{{ gare.is_active ? 'Active' : 'Inactive' }}</span></td><td v-if="canManageRelations"><button class="table-action danger-action" type="button" :disabled="relationSubmitting || !gare.is_active" @click="detachGare(gare.id_gare)">Retirer</button></td></tr></tbody>
          </table>
        </div>
        <div v-else class="empty-state">Aucune gare associee.</div>
      </BaseCard>

      <BaseCard>
        <div class="card-heading">
          <div><h2>Membres ({{ members.length }})</h2><p>Utilisateurs rattaches a cette cooperative.</p></div>
        </div>
        <div v-if="canManageRelations" class="inline-form">
          <select v-model="selectedMember" :disabled="relationSubmitting || relationLoading">
            <option :value="null">Selectionner un utilisateur</option>
            <option v-for="user in eligibleMembers" :key="user.id" :value="user.id">{{ user.first_name || '' }} {{ user.name }} - {{ user.email }}</option>
          </select>
          <input v-model="memberFunction" placeholder="Fonction (ex. MEMBRE)" :disabled="relationSubmitting" />
          <button class="primary-button compact-button" type="button" :disabled="!selectedMember || relationSubmitting" @click="addMember">{{ relationSubmitting ? 'Traitement...' : 'Ajouter' }}</button>
        </div>
        <div v-if="members.length" class="table-scroll">
          <table class="data-table"><caption>Liste des membres</caption><thead><tr><th>Utilisateur</th><th>Fonction</th><th>Adhesion</th><th>Fin</th><th>Statut</th><th v-if="canManageRelations">Actions</th></tr></thead>
            <tbody><tr v-for="member in members" :key="member.id_user"><td><strong>{{ displayUser(member) }}</strong><small v-if="member.user">{{ member.user.email }}</small></td><td>{{ member.fonction || 'Membre' }}</td><td>{{ formatDate(member.date_adhesion) }}</td><td>{{ formatDate(member.date_fin) }}</td><td><span :class="['status-badge', member.is_active ? 'active' : 'inactive']">{{ member.is_active ? 'Actif' : 'Inactif' }}</span></td><td v-if="canManageRelations"><button class="table-action danger-action" type="button" :disabled="relationSubmitting || !member.is_active" @click="removeMember(member.id_user)">Retirer</button></td></tr></tbody>
          </table>
        </div>
        <div v-else class="empty-state">Aucun membre enregistre.</div>
      </BaseCard>

      <BaseCard>
        <div class="card-heading"><div><h2>Vehicules ({{ vehicules.length }})</h2><p>Vehicules appartenant a cette cooperative.</p></div><RouterLink class="card-link" to="/vehicules">Voir la flotte <span>-&gt;</span></RouterLink></div>
        <div v-if="vehicules.length" class="table-scroll"><table class="data-table"><caption>Vehicules de la cooperative</caption><thead><tr><th>Immatriculation</th><th>Modele</th><th>Places</th><th>Disponibilite</th><th>Etat</th></tr></thead><tbody><tr v-for="vehicule in vehicules" :key="vehicule.id"><td><RouterLink class="table-link" :to="`/vehicules/${vehicule.id}`"><strong>{{ vehicule.immatriculation }}</strong></RouterLink></td><td>{{ vehicule.modele?.nom || `Modele #${vehicule.id_modele}` }}</td><td>{{ vehicule.nombre_places }}</td><td>{{ vehicule.disponibilite ? 'Disponible' : 'Indisponible' }}</td><td>{{ vehicule.etat }}</td></tr></tbody></table></div>
        <div v-else class="empty-state">Aucun vehicule enregistre.</div>
      </BaseCard>

      <BaseCard>
        <div class="card-heading"><div><h2>Chauffeurs ({{ chauffeurs.length }})</h2><p>Chauffeurs rattaches a cette cooperative.</p></div><RouterLink class="card-link" to="/chauffeurs">Voir les chauffeurs <span>-&gt;</span></RouterLink></div>
        <div v-if="chauffeurs.length" class="table-scroll"><table class="data-table"><caption>Chauffeurs de la cooperative</caption><thead><tr><th>Utilisateur</th><th>Permis</th><th>Expiration</th><th>Disponibilite</th><th>Statut</th></tr></thead><tbody><tr v-for="chauffeur in chauffeurs" :key="chauffeur.id"><td><RouterLink class="table-link" :to="`/chauffeurs/${chauffeur.id}`"><strong>{{ displayDriver(chauffeur) }}</strong></RouterLink></td><td>{{ chauffeur.numero_permis }}</td><td>{{ formatDate(chauffeur.date_expiration_permis) }}</td><td>{{ chauffeur.disponibilite ? 'Disponible' : 'Indisponible' }}</td><td><span :class="['status-badge', chauffeur.is_active ? 'active' : 'inactive']">{{ chauffeur.is_active ? 'Actif' : 'Inactif' }}</span></td></tr></tbody></table></div>
        <div v-else class="empty-state">Aucun chauffeur enregistre.</div>
      </BaseCard>
    </template>
  </AppLayout>
</template>
