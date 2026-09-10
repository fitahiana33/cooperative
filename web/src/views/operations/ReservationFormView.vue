<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import { departService } from '../../services/depart/service'
import { reservationService } from '../../services/reservation/service'
import type { Depart } from '../../models/depart/model'
import type { DepartPlace } from '../../models/reservation/model'
import { userError } from '../../utils/errors'

const router = useRouter()
const departures = ref<Depart[]>([])
const places = ref<DepartPlace[]>([])
const departId = ref<number | null>(null)
const selected = ref<number[]>([])
const nomPassager = ref('')
const telephone = ref('')
const loading = ref(true)
const loadingPlaces = ref(false)
const submitting = ref(false)
const error = ref('')
const today = new Date().toISOString().slice(0, 10)
const selectedDepart = computed(() => departures.value.find((item) => item.id === departId.value))
function showError(value: unknown, fallback = 'Une erreur est survenue.') { error.value = userError(value, fallback, 'RESERVATION_FORM_ERROR') }
async function load() {
  loading.value = true
  try { const result = await departService.list({ page: 1, page_size: 100, date_from: today, statut: 'PROGRAMME', sort_by: 'date_depart', sort_order: 'asc' }); departures.value = result.items } catch (value: unknown) { showError(value, 'Impossible de charger les départs disponibles.') } finally { loading.value = false }
}
async function chooseDepart() {
  selected.value = []; places.value = []; if (!departId.value) return
  loadingPlaces.value = true; error.value = ''
  try { places.value = await reservationService.places(departId.value, true) } catch (value: unknown) { showError(value, 'Impossible de charger les places disponibles.') } finally { loadingPlaces.value = false }
}
function togglePlace(id: number) { if (selected.value.includes(id)) selected.value = selected.value.filter((value) => value !== id); else selected.value.push(id) }
async function submit() {
  error.value = ''
  if (!departId.value || !selected.value.length || nomPassager.value.trim().length < 2) { error.value = 'Sélectionnez un départ, au moins une place et renseignez le nom du passager.'; return }
  submitting.value = true
  try {
    const reservation = await reservationService.create({ id_depart: departId.value, places: selected.value.map((id) => ({ id_depart_place: id, nom_passager: nomPassager.value.trim(), telephone_passager: telephone.value.trim() || undefined })) })
    await reservationService.confirm(reservation.id)
    await router.push({ name: 'reservation-detail', params: { id: reservation.id }, query: { created: '1' } })
  } catch (value: unknown) { showError(value, 'La réservation n’a pas pu être confirmée.') } finally { submitting.value = false }
}
onMounted(load)
</script>

<template>
  <AppLayout>
    <template #title>Nouvelle réservation</template>
    <div class="page-intro"><div><p class="eyebrow">VENTES & PLACES</p><h2>Créer une réservation</h2><p>Choisissez un départ puis une ou plusieurs places disponibles.</p></div><RouterLink class="secondary-button" to="/reservations">Retour à la liste</RouterLink></div>
    <p v-if="error" class="error-banner" role="alert">{{ error }}</p>
    <BaseCard>
      <div class="form-grid"><label class="form-field"><span>Départ *</span><select v-model="departId" :disabled="loading || submitting" @change="chooseDepart"><option :value="null">Choisir un départ</option><option v-for="item in departures" :key="item.id" :value="item.id">{{ item.date_depart }} {{ item.heure_depart.slice(0, 5) }} — #{{ item.id }} — {{ item.places_disponibles }} place(s)</option></select></label><label class="form-field"><span>Nom du passager *</span><input v-model="nomPassager" :disabled="submitting" placeholder="Nom complet" /></label><label class="form-field"><span>Téléphone</span><input v-model="telephone" :disabled="submitting" placeholder="Téléphone" /></label></div>
      <div v-if="selectedDepart" class="detail-grid"><div class="detail-item"><span class="detail-label">Coopérative</span><strong>#{{ selectedDepart.id_cooperative }}</strong></div><div class="detail-item"><span class="detail-label">Tarif</span><strong>{{ selectedDepart.tarif?.prix || '—' }} {{ selectedDepart.tarif?.devise || '' }}</strong></div><div class="detail-item"><span class="detail-label">Places sélectionnées</span><strong>{{ selected.length }}</strong></div></div>
      <h3 v-if="departId" class="section-title">Choisir les places</h3><p v-if="loadingPlaces" class="status-msg">Chargement des places…</p><div v-if="departId && !loadingPlaces" class="seat-grid"><button v-for="place in places" :key="place.id" type="button" class="seat-button" :class="{ selected: selected.includes(place.id) }" :disabled="place.statut !== 'DISPONIBLE' || submitting" @click="togglePlace(place.id)">{{ place.numero_place }}</button><p v-if="!places.length" class="status-msg">Aucune place disponible pour ce départ.</p></div>
      <div class="form-actions"><button class="primary-button" :disabled="submitting || loading || !selected.length" @click="submit">{{ submitting ? 'Confirmation…' : 'Confirmer la réservation' }}</button><RouterLink class="secondary-button" to="/reservations">Annuler</RouterLink></div>
    </BaseCard>
  </AppLayout>
</template>
