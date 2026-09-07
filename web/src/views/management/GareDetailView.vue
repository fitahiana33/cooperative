<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import { gareService } from '../../services/gare/service'
import { useAuthenticationStore } from '../../stores/authentication/store'
import { userError } from '../../utils/errors'
import type { Emplacement, Gare, Quai, Zone } from '../../models/gare/model'

const route = useRoute()
const auth = useAuthenticationStore()
const id = computed(() => Number(route.params.id))
const gare = ref<Gare | null>(null)
const loading = ref(true)
const error = ref('')
const success = ref('')
const busyAction = ref<string | null>(null)
const canEdit = computed(() => auth.hasPermission('GARE_UPDATE'))
const quaiForm = reactive({ numero: '', nom: '', description: '' })
const zoneForm = reactive({ nom: '', type_zone: '', description: '' })
const emplacementForms = reactive<Record<number, { code: string; nom: string; type_emplacement: string }>>({})

function formatDate(value?: string | null) { return value ? new Date(value).toLocaleDateString('fr-FR') : '-' }
function formatCoordinate(value?: number) { return value === undefined || value === null ? '-' : String(value) }
function showError(errorValue: unknown, fallback: string) { error.value = userError(errorValue, fallback, 'GARE_DETAIL_ERROR'); success.value = '' }
function clearFeedback() { error.value = ''; success.value = '' }
function formForZone(zoneId: number) {
  return emplacementForms[zoneId] ||= { code: '', nom: '', type_emplacement: '' }
}

async function addQuai() {
  if (!gare.value || busyAction.value) return
  busyAction.value = 'quai-create'; clearFeedback()
  try {
    const item: Quai = await gareService.addQuai(gare.value.id, { numero: quaiForm.numero, nom: quaiForm.nom || undefined, description: quaiForm.description || undefined })
    gare.value.quais.push(item); Object.assign(quaiForm, { numero: '', nom: '', description: '' }); success.value = 'Quai ajoute avec succes.'
  } catch (errorValue: unknown) { showError(errorValue, 'Impossible d ajouter le quai.') }
  finally { busyAction.value = null }
}

async function addZone() {
  if (!gare.value || busyAction.value) return
  busyAction.value = 'zone-create'; clearFeedback()
  try {
    const item: Zone = await gareService.addZone(gare.value.id, { nom: zoneForm.nom, type_zone: zoneForm.type_zone || undefined, description: zoneForm.description || undefined })
    gare.value.zones.push(item); Object.assign(zoneForm, { nom: '', type_zone: '', description: '' }); success.value = 'Zone ajoutee avec succes.'
  } catch (errorValue: unknown) { showError(errorValue, 'Impossible d ajouter la zone.') }
  finally { busyAction.value = null }
}

async function addEmplacement(zone: Zone) {
  if (!gare.value || busyAction.value) return
  const form = formForZone(zone.id)
  busyAction.value = `emplacement-create-${zone.id}`; clearFeedback()
  try {
    const item: Emplacement = await gareService.addEmplacement(zone.id, { code: form.code, nom: form.nom || undefined, type_emplacement: form.type_emplacement || undefined })
    zone.emplacements.push(item); Object.assign(form, { code: '', nom: '', type_emplacement: '' }); success.value = 'Emplacement ajoute avec succes.'
  } catch (errorValue: unknown) { showError(errorValue, 'Impossible d ajouter l emplacement.') }
  finally { busyAction.value = null }
}

async function toggleQuai(item: Quai) {
  if (!gare.value || busyAction.value) return
  busyAction.value = `quai-toggle-${item.id}`; clearFeedback()
  try { Object.assign(item, await gareService.toggleQuai(gare.value.id, item.id)); success.value = 'Statut du quai mis a jour.' }
  catch (errorValue: unknown) { showError(errorValue, 'Impossible de modifier le quai.') }
  finally { busyAction.value = null }
}
async function toggleZone(item: Zone) {
  if (!gare.value || busyAction.value) return
  busyAction.value = `zone-toggle-${item.id}`; clearFeedback()
  try { Object.assign(item, await gareService.toggleZone(gare.value.id, item.id)); success.value = 'Statut de la zone mis a jour.' }
  catch (errorValue: unknown) { showError(errorValue, 'Impossible de modifier la zone.') }
  finally { busyAction.value = null }
}
async function toggleEmplacement(zone: Zone, item: Emplacement) {
  if (!gare.value || busyAction.value) return
  busyAction.value = `emplacement-toggle-${item.id}`; clearFeedback()
  try { Object.assign(item, await gareService.toggleEmplacement(gare.value.id, zone.id, item.id)); success.value = 'Statut de l emplacement mis a jour.' }
  catch (errorValue: unknown) { showError(errorValue, 'Impossible de modifier l emplacement.') }
  finally { busyAction.value = null }
}

onMounted(async () => {
  try {
    gare.value = await gareService.getGare(id.value)
    document.title = `${gare.value.nom} - Gare`
  } catch (errorValue: unknown) { showError(errorValue, 'Impossible de charger les details de la gare.') }
  finally { loading.value = false }
})
</script>

<template>
  <AppLayout>
    <template #title>Detail de la gare</template>
    <div class="page-intro"><div><p class="eyebrow">GESTION DES GARES</p><h2>Detail de la gare</h2><p>Consultez et gerez les informations, quais, zones et emplacements.</p></div><div class="form-actions"><RouterLink class="secondary-button" to="/gares">Retour a la liste</RouterLink><RouterLink v-if="gare && canEdit" class="primary-button compact-button" :to="`/gares/${id}/edit`">Modifier</RouterLink></div></div>
    <p v-if="loading" class="status-msg">Chargement des details en cours...</p>
    <p v-else-if="error && !gare" class="error-banner" role="alert">{{ error }}</p>
    <p v-if="error && gare" class="error-banner" role="alert">{{ error }}</p><p v-if="success" class="success-banner" role="status">{{ success }}</p>

    <template v-if="gare && !loading">
      <BaseCard><div class="card-heading"><div><h2>{{ gare.nom }}</h2><p><span :class="['status-badge', gare.is_active ? 'active' : 'inactive']">{{ gare.is_active ? 'Active' : 'Inactive' }}</span></p></div></div><div class="detail-grid"><div class="detail-item"><span class="detail-label">Nom</span><strong>{{ gare.nom }}</strong></div><div class="detail-item"><span class="detail-label">Ville</span><strong>{{ gare.ville }}</strong></div><div class="detail-item"><span class="detail-label">Region</span><strong>{{ gare.region || '-' }}</strong></div><div class="detail-item detail-wide"><span class="detail-label">Adresse</span><strong>{{ gare.adresse }}</strong></div><div class="detail-item"><span class="detail-label">Telephone</span><strong>{{ gare.telephone || '-' }}</strong></div><div class="detail-item"><span class="detail-label">Email</span><strong>{{ gare.email || '-' }}</strong></div><div class="detail-item"><span class="detail-label">Latitude</span><strong>{{ formatCoordinate(gare.latitude) }}</strong></div><div class="detail-item"><span class="detail-label">Longitude</span><strong>{{ formatCoordinate(gare.longitude) }}</strong></div><div class="detail-item"><span class="detail-label">Creee le</span><strong>{{ formatDate(gare.created_at) }}</strong></div><div class="detail-item"><span class="detail-label">Modifiee le</span><strong>{{ formatDate(gare.updated_at) }}</strong></div><div class="detail-item detail-wide"><span class="detail-label">Description</span><strong>{{ gare.description || 'Aucune description.' }}</strong></div></div></BaseCard>

      <BaseCard><div class="card-heading"><div><h2>Quais ({{ gare.quais.length }})</h2><p>Quais rattaches a cette gare.</p></div></div><form v-if="canEdit && gare.is_active" class="management-form inline-form" @submit.prevent="addQuai"><input v-model="quaiForm.numero" required placeholder="Numero du quai" /><input v-model="quaiForm.nom" placeholder="Nom du quai" /><input v-model="quaiForm.description" placeholder="Description" /><button class="primary-button compact-button" type="submit" :disabled="busyAction !== null">{{ busyAction === 'quai-create' ? 'Ajout...' : 'Ajouter' }}</button></form><div v-if="gare.quais.length" class="table-scroll"><table class="data-table"><caption>Liste des quais</caption><thead><tr><th>Numero</th><th>Nom</th><th>Description</th><th>Statut</th><th>Action</th></tr></thead><tbody><tr v-for="quai in gare.quais" :key="quai.id"><td><strong>{{ quai.numero }}</strong></td><td>{{ quai.nom || '-' }}</td><td>{{ quai.description || '-' }}</td><td><span :class="['status-badge', quai.is_active ? 'active' : 'inactive']">{{ quai.is_active ? 'Actif' : 'Inactif' }}</span></td><td><button v-if="canEdit" class="table-action" type="button" :disabled="busyAction !== null" @click="toggleQuai(quai)">{{ busyAction === `quai-toggle-${quai.id}` ? 'Traitement...' : (quai.is_active ? 'Desactiver' : 'Activer') }}</button></td></tr></tbody></table></div><div v-else class="empty-state">Aucun quai enregistre.</div></BaseCard>

      <BaseCard><div class="card-heading"><div><h2>Zones et emplacements ({{ gare.zones.length }})</h2><p>Organisation interne de la gare.</p></div></div><form v-if="canEdit && gare.is_active" class="management-form inline-form" @submit.prevent="addZone"><input v-model="zoneForm.nom" required placeholder="Nom de la zone" /><input v-model="zoneForm.type_zone" placeholder="Type de zone" /><input v-model="zoneForm.description" placeholder="Description" /><button class="primary-button compact-button" type="submit" :disabled="busyAction !== null">{{ busyAction === 'zone-create' ? 'Ajout...' : 'Ajouter' }}</button></form><div v-if="!gare.zones.length" class="empty-state">Aucune zone enregistree.</div><div v-for="zone in gare.zones" :key="zone.id" class="detail-subsection"><div class="card-heading"><div><h3>{{ zone.nom }}</h3><p>{{ zone.type_zone || 'Zone non typee' }} - {{ zone.emplacements.length }} emplacement(s)</p></div><button v-if="canEdit" class="table-action" type="button" :disabled="busyAction !== null" @click="toggleZone(zone)">{{ busyAction === `zone-toggle-${zone.id}` ? 'Traitement...' : (zone.is_active ? 'Desactiver' : 'Activer') }}</button></div><form v-if="canEdit && zone.is_active && gare.is_active" class="management-form inline-form" @submit.prevent="addEmplacement(zone)"><input v-model="formForZone(zone.id).code" required placeholder="Code emplacement" /><input v-model="formForZone(zone.id).nom" placeholder="Nom" /><input v-model="formForZone(zone.id).type_emplacement" placeholder="Type" /><button class="primary-button compact-button" type="submit" :disabled="busyAction !== null">{{ busyAction === `emplacement-create-${zone.id}` ? 'Ajout...' : 'Ajouter' }}</button></form><div v-if="zone.emplacements.length" class="table-scroll"><table class="data-table"><caption>Emplacements de la zone {{ zone.nom }}</caption><thead><tr><th>Code</th><th>Nom</th><th>Type</th><th>Disponibilite</th><th>Statut</th><th>Action</th></tr></thead><tbody><tr v-for="emplacement in zone.emplacements" :key="emplacement.id"><td><strong>{{ emplacement.code }}</strong></td><td>{{ emplacement.nom || '-' }}</td><td>{{ emplacement.type_emplacement || '-' }}</td><td>{{ emplacement.is_available ? 'Disponible' : 'Occupe' }}</td><td><span :class="['status-badge', emplacement.is_active ? 'active' : 'inactive']">{{ emplacement.is_active ? 'Actif' : 'Inactif' }}</span></td><td><button v-if="canEdit" class="table-action" type="button" :disabled="busyAction !== null" @click="toggleEmplacement(zone, emplacement)">{{ busyAction === `emplacement-toggle-${emplacement.id}` ? 'Traitement...' : (emplacement.is_active ? 'Desactiver' : 'Activer') }}</button></td></tr></tbody></table></div><div v-else class="empty-state">Aucun emplacement dans cette zone.</div></div></BaseCard>
    </template>
  </AppLayout>
</template>
