<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import { departService } from '../../services/depart/service'
import { reservationService } from '../../services/reservation/service'
import type { Depart } from '../../models/depart/model'
import type { DepartPlace, Reservation, ReservationStatus } from '../../models/reservation/model'
import { userError } from '../../utils/errors'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => route.name === 'reservation-edit')
const editId = computed(() => (isEdit.value ? Number(route.params.id) : null))

const labels: Record<ReservationStatus, string> = { EN_ATTENTE: 'En attente', CONFIRMEE: 'Confirmée', PAYEE: 'Payée', ANNULEE: 'Annulée', EXPIREE: 'Expirée', EMBARQUEE: 'Embarquée', TERMINEE: 'Terminée' }

const departures = ref<Depart[]>([])
const places = ref<DepartPlace[]>([])
const departId = ref<number | null>(null)
const selected = ref<number[]>([])
const passengerDetails = reactive<Record<number, { nom: string; telephone: string }>>({})
const loading = ref(true)
const loadingPlaces = ref(false)
const submitting = ref(false)
const busy = ref(false)
const error = ref('')
const success = ref('')
const today = new Date().toISOString().slice(0, 10)
const reservation = ref<Reservation | null>(null)

const selectedDepart = computed(() => departures.value.find((item) => item.id === departId.value))
const selectedPlaces = computed(() => places.value.filter((place) => selected.value.includes(place.id)).sort((a, b) => a.numero_place - b.numero_place))
const pricePerPlace = computed(() => Number(selectedDepart.value?.tarif?.prix || 0))
const totalAmount = computed(() => selected.value.length * pricePerPlace.value)
const seatColumns = computed(() => {
  const capacity = places.value.length
  if (capacity <= 8) return 2
  if (capacity <= 12) return 3
  return 4
})
const frontPlaces = computed(() => {
  const items = [...places.value].sort((a, b) => a.numero_place - b.numero_place)
  return items.slice(0, 2)
})
const seatRows = computed(() => {
  const items = [...places.value].sort((a, b) => a.numero_place - b.numero_place)
  const rowSize = seatColumns.value
  const rows: DepartPlace[][] = []
  for (let index = 2; index < items.length; index += rowSize) {
    rows.push(items.slice(index, index + rowSize))
  }
  return rows
})

function seatClass(place: DepartPlace) {
  if (selected.value.includes(place.id)) return 'selected'
  if (place.statut === 'RESERVEE') return 'reserved'
  if (place.statut === 'OCCUPEE') return 'occupied'
  if (place.statut === 'BLOQUEE') return 'blocked'
  return 'available'
}

function passengerFor(placeId: number) {
  return passengerDetails[placeId] ||= { nom: '', telephone: '' }
}

function showError(value: unknown, fallback = 'Une erreur est survenue.') { error.value = userError(value, fallback, 'RESERVATION_FORM_ERROR'); success.value = '' }

async function loadDepartures() {
  loading.value = true
  try { const result = await departService.list({ page: 1, page_size: 100, date_from: today, statut: 'PROGRAMME', sort_by: 'date_depart', sort_order: 'asc' }); departures.value = result.items } catch (value: unknown) { showError(value, 'Impossible de charger les départs disponibles.') } finally { loading.value = false }
}

async function loadReservation() {
  if (!editId.value) return
  try {
    reservation.value = await reservationService.get(editId.value)
    departId.value = reservation.value.id_depart
    selected.value = reservation.value.places.map((p) => p.id_depart_place)
    reservation.value.places.forEach((place) => {
      passengerDetails[place.id_depart_place] = { nom: place.nom_passager, telephone: place.telephone_passager || '' }
    })
    places.value = await reservationService.places(reservation.value.id_depart, false)
  } catch (value: unknown) { showError(value, 'Impossible de charger la réservation.') }
}

async function chooseDepart() {
  selected.value = []; places.value = []; Object.keys(passengerDetails).forEach((key) => delete passengerDetails[Number(key)]); if (!departId.value) return
  loadingPlaces.value = true; error.value = ''
  try { places.value = await reservationService.places(departId.value, false) } catch (value: unknown) { showError(value, 'Impossible de charger les places.') } finally { loadingPlaces.value = false }
}

function togglePlace(id: number) {
  if (isEdit.value) return
  if (selected.value.includes(id)) {
    selected.value = selected.value.filter((value) => value !== id)
    delete passengerDetails[id]
  } else {
    selected.value.push(id)
    passengerFor(id)
  }
}

async function submit() {
  if (isEdit.value) return
  error.value = ''
  const missingPassenger = selectedPlaces.value.some((place) => passengerFor(place.id).nom.trim().length < 2)
  if (!departId.value || !selected.value.length || missingPassenger) { error.value = 'Sélectionnez un départ, puis renseignez le nom de chaque passager sélectionné.'; return }
  submitting.value = true
  try {
    const created = await reservationService.create({ id_depart: departId.value, places: selectedPlaces.value.map((place) => ({ id_depart_place: place.id, nom_passager: passengerFor(place.id).nom.trim(), telephone_passager: passengerFor(place.id).telephone.trim() || undefined })) })
    await reservationService.confirm(created.id)
    await router.push({ name: 'reservation-detail', params: { id: created.id }, query: { created: '1' } })
  } catch (value: unknown) { showError(value, 'La réservation n’a pas pu être confirmée.') } finally { submitting.value = false }
}

async function change(action: 'confirm' | 'cancel') {
  if (!reservation.value || busy.value) return
  if (action === 'cancel' && !window.confirm(`Annuler la réservation ${reservation.value.numero_reservation} ? Cette action libérera les places.`)) return
  busy.value = true; error.value = ''
  try {
    reservation.value = action === 'confirm' ? await reservationService.confirm(reservation.value.id) : await reservationService.cancel(reservation.value.id)
    success.value = action === 'confirm' ? 'Réservation confirmée et billets générés.' : 'Réservation annulée.'
  } catch (value: unknown) { showError(value, 'Opération impossible.') } finally { busy.value = false }
}

async function load() {
  if (isEdit.value) {
    await loadReservation()
    loading.value = false
  } else {
    await loadDepartures()
  }
}

onMounted(load)
</script>

<template>
  <AppLayout>
    <template #title>{{ isEdit ? 'Modifier réservation' : 'Nouvelle réservation' }}</template>
    <div class="page-intro">
      <div>
        <p class="eyebrow">VENTES & PLACES</p>
        <h2>{{ isEdit ? 'Modifier la réservation' : 'Créer une réservation' }}</h2>
        <p>{{ isEdit ? 'Réservation ' + (reservation?.numero_reservation || '#' + editId) + ' — Les places confirmées ne peuvent pas être modifiées.' : 'Choisissez un départ puis une ou plusieurs places disponibles.' }}</p>
      </div>
      <RouterLink class="secondary-button" to="/reservations">Retour à la liste</RouterLink>
    </div>
    <p v-if="error" class="error-banner" role="alert">{{ error }}</p>
    <p v-else-if="success" class="success-banner">{{ success }}</p>

    <template v-if="isEdit">
      <BaseCard v-if="reservation">
        <div class="card-heading">
          <div>
            <h2>{{ reservation.numero_reservation }}</h2>
            <span class="status-badge" :class="reservation.statut === 'CONFIRMEE' || reservation.statut === 'PAYEE' ? 'active' : 'inactive'">{{ labels[reservation.statut] || reservation.statut }}</span>
          </div>
          <RouterLink class="secondary-button" :to="{ name: 'reservation-detail', params: { id: reservation.id } }">Voir le détail complet</RouterLink>
        </div>
        <div class="detail-grid">
          <div class="detail-item"><span class="detail-label">Départ</span><strong>#{{ reservation.id_depart }}</strong></div>
          <div class="detail-item"><span class="detail-label">Date & Heure</span><strong>{{ reservation.depart?.date_depart }} {{ reservation.depart?.heure_depart?.slice(0, 5) }}</strong></div>
          <div class="detail-item"><span class="detail-label">Montant total</span><strong>{{ reservation.montant_total }}</strong></div>
          <div class="detail-item"><span class="detail-label">Expiration</span><strong>{{ reservation.date_expiration ? new Date(reservation.date_expiration).toLocaleString('fr-FR') : '—' }}</strong></div>
        </div>
        <h3 class="section-title">Places réservées</h3>
        <div class="table-scroll">
          <table class="data-table">
            <thead><tr><th>Place</th><th>Passager</th><th>Téléphone</th><th>Billet</th><th>Statut</th></tr></thead>
            <tbody>
              <tr v-for="place in reservation.places" :key="place.id">
                <td>{{ place.depart_place?.numero_place || place.id_depart_place }}</td>
                <td>{{ place.nom_passager }}</td>
                <td>{{ place.telephone_passager || '—' }}</td>
                <td>{{ place.billet?.numero_billet || 'Non généré' }}</td>
                <td>{{ place.billet?.statut || reservation.statut }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="form-actions">
          <button v-if="reservation.statut === 'EN_ATTENTE'" class="primary-button" :disabled="busy" @click="change('confirm')">{{ busy ? 'Confirmation…' : 'Confirmer' }}</button>
          <RouterLink v-if="!['ANNULEE', 'TERMINEE', 'EMBARQUEE'].includes(reservation.statut)" class="secondary-button danger-action" :to="{ name: 'reservation-detail', params: { id: reservation.id } }">Gérer l’annulation</RouterLink>
          <RouterLink class="secondary-button" :to="{ name: 'places-depart', params: { id: reservation.id_depart } }">Gérer les places du départ</RouterLink>
        </div>
      </BaseCard>
      <p v-else-if="!loading" class="status-msg">Réservation introuvable.</p>
    </template>

    <template v-else>
      <BaseCard>
        <div class="form-grid">
          <label class="form-field"><span>Départ *</span>
            <select v-model="departId" :disabled="loading || submitting" @change="chooseDepart">
              <option :value="null">Choisir un départ</option>
              <option v-for="item in departures" :key="item.id" :value="item.id">{{ item.date_depart }} {{ item.heure_depart.slice(0, 5) }} — #{{ item.id }} — {{ item.nombre_places }} place(s), {{ item.places_disponibles }} disponible(s)</option>
            </select>
          </label>
        </div>
        <div v-if="selectedDepart" class="detail-grid">
          <div class="detail-item"><span class="detail-label">Coopérative</span><strong>#{{ selectedDepart.id_cooperative }}</strong></div>
          <div class="detail-item"><span class="detail-label">Capacité du véhicule</span><strong>{{ selectedDepart.nombre_places }} places</strong></div>
          <div class="detail-item"><span class="detail-label">Disponibles</span><strong>{{ selectedDepart.places_disponibles }} places</strong></div>
          <div class="detail-item"><span class="detail-label">Tarif</span><strong>{{ selectedDepart.tarif?.prix || '—' }} {{ selectedDepart.tarif?.devise || '' }}</strong></div>
          <div class="detail-item"><span class="detail-label">Places sélectionnées</span><strong>{{ selected.length }}</strong></div>
          <div class="detail-item total-detail"><span class="detail-label">Total à payer</span><strong>{{ totalAmount.toLocaleString('fr-FR') }} {{ selectedDepart.tarif?.devise || 'MGA' }}</strong></div>
        </div>
        <div v-if="departId" class="seat-heading">
          <div>
            <h3 class="section-title">Choisir les places</h3>
            <p class="seat-help">Cliquez sur une ou plusieurs places vertes pour les sélectionner.</p>
          </div>
          <strong class="seat-counter">{{ selected.length }} sélectionnée(s)</strong>
        </div>
        <p v-if="loadingPlaces" class="status-msg">Chargement des places…</p>
        <div v-if="departId && !loadingPlaces" class="seat-layout">
          <div class="seat-legend" aria-label="Légende des places">
            <span><i class="legend-swatch available"></i>Disponible</span>
            <span><i class="legend-swatch selected"></i>Sélectionnée</span>
            <span><i class="legend-swatch unavailable"></i>Indisponible</span>
          </div>
          <div class="bus-cabin">
            <div class="front-row">
              <div class="driver-seat" aria-label="Place du chauffeur non réservable">
                <span class="driver-icon">CH</span>
                <span>Chauffeur</span>
              </div>
              <button
                v-for="place in frontPlaces"
                :key="place.id"
                type="button"
                class="seat-button real-seat front-seat"
                :class="seatClass(place)"
                :disabled="place.statut !== 'DISPONIBLE' || submitting"
                @click="togglePlace(place.id)"
                :title="`Place ${place.numero_place}`"
              >
                {{ place.numero_place }}
              </button>
            </div>
            <div v-for="(row, rowIndex) in seatRows" :key="row[0]?.id || rowIndex" class="seat-row" :style="{ '--seat-columns': seatColumns }">
              <button
                v-for="place in row"
                :key="place.id"
                type="button"
                class="seat-button real-seat"
                :class="seatClass(place)"
                :disabled="place.statut !== 'DISPONIBLE' || submitting"
                @click="togglePlace(place.id)"
                :title="`Place ${place.numero_place}`"
              >
                {{ place.numero_place }}
              </button>
            </div>
          </div>
          <p v-if="!places.length" class="status-msg">Aucune place disponible pour ce départ.</p>
        </div>
        <div v-if="selectedPlaces.length" class="passenger-list">
          <div class="card-heading passenger-heading">
            <div><h3 class="section-title">Informations des passagers</h3><p>Un passager différent peut être associé à chaque place.</p></div>
            <strong class="seat-counter">{{ selectedPlaces.length }} passager(s)</strong>
          </div>
          <div v-for="place in selectedPlaces" :key="place.id" class="passenger-row">
            <div class="passenger-seat">Place {{ place.numero_place }}</div>
            <label class="form-field"><span>Nom complet *</span><input v-model="passengerFor(place.id).nom" :disabled="submitting" placeholder="Nom du passager" /></label>
            <label class="form-field"><span>Téléphone</span><input v-model="passengerFor(place.id).telephone" :disabled="submitting" placeholder="034 00 00 00" /></label>
          </div>
        </div>
        <div class="form-actions">
          <button class="primary-button" :disabled="submitting || loading || !selected.length" @click="submit">{{ submitting ? 'Confirmation…' : 'Confirmer la réservation' }}</button>
          <RouterLink class="secondary-button" to="/reservations">Annuler</RouterLink>
        </div>
      </BaseCard>
    </template>
  </AppLayout>
</template>

<style scoped>
.seat-layout {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
}

.seat-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 1rem;
  margin-top: 1.5rem;
}

.seat-help {
  margin: 0.25rem 0 0;
  color: #64748b;
  font-size: 0.9rem;
}

.seat-counter {
  color: #1d4ed8;
  white-space: nowrap;
}

.total-detail {
  border-color: #bfdbfe;
  background: #eff6ff;
}

.total-detail strong {
  color: #1d4ed8;
  font-size: 1.05rem;
}

.passenger-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.passenger-heading {
  margin: 0;
}

.passenger-row {
  display: grid;
  grid-template-columns: 100px minmax(0, 1fr) minmax(0, 1fr);
  align-items: end;
  gap: 0.75rem;
  padding: 0.9rem;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #f8fafc;
}

.passenger-seat {
  padding-bottom: 0.65rem;
  color: #1e3a8a;
  font-weight: 700;
}

@media (max-width: 700px) {
  .passenger-row {
    grid-template-columns: 1fr;
  }

  .passenger-seat {
    padding-bottom: 0;
  }
}

.seat-legend {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.75rem 1rem;
  color: #475569;
  font-size: 0.82rem;
}

.seat-legend span {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.legend-swatch {
  width: 0.8rem;
  height: 0.8rem;
  border: 1px solid transparent;
  border-radius: 4px;
}

.legend-swatch.available {
  border-color: #bbf7d0;
  background: #f0fdf4;
}

.legend-swatch.selected {
  border-color: #4d72e8;
  background: #4d72e8;
}

.legend-swatch.unavailable {
  border-color: #e5e7eb;
  background: #f3f4f6;
}

.bus-cabin {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  width: min(100%, 460px);
  margin: 0 auto;
  padding: 1rem 0.75rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.03), rgba(15, 23, 42, 0.08));
}

.front-row {
  position: relative;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.5rem;
  z-index: 1;
}

.driver-seat {
  display: flex;
  min-height: 42px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.2rem;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  background: #e2e8f0;
  color: #475569;
  font-size: 0.7rem;
  font-weight: 700;
  text-align: center;
}

.driver-icon {
  font-size: 0.78rem;
  font-weight: 800;
}

.front-seat {
  min-width: 0;
}

.bus-cabin::before {
  content: "";
  position: absolute;
  left: 50%;
  top: 0.75rem;
  bottom: 0.75rem;
  width: 16%;
  transform: translateX(-50%);
  border-left: 3px solid rgba(148, 163, 184, 0.7);
  border-right: 3px solid rgba(148, 163, 184, 0.7);
  border-radius: 999px;
  pointer-events: none;
}

.seat-row {
  position: relative;
  display: grid;
  grid-template-columns: repeat(var(--seat-columns), minmax(0, 1fr));
  gap: 0.5rem;
  z-index: 1;
}

.real-seat {
  min-height: 42px;
  border-radius: 12px;
  font-size: 0.82rem;
}
</style>
