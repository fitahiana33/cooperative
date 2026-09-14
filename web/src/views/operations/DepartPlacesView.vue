<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import { departService } from '../../services/depart/service'
import { reservationService } from '../../services/reservation/service'
import type { Depart, DepartStatus } from '../../models/depart/model'
import type { DepartPlace, PlaceStatus } from '../../models/reservation/model'
import { userError } from '../../utils/errors'

const route = useRoute()
const departId = Number(route.params.id)
const depart = ref<Depart | null>(null)
const places = ref<DepartPlace[]>([])
const loading = ref(true)
const loadingPlaces = ref(false)
const error = ref('')
const busy = ref(false)
const editingPlaceId = ref<number | null>(null)
const newStatut = ref<PlaceStatus>('DISPONIBLE')

const labels: Record<DepartStatus, string> = { PROGRAMME: 'Programmé', EMBARQUEMENT: 'Embarquement', RETARDE: 'Retardé', PARTI: 'Parti', TERMINE: 'Terminé', ANNULE: 'Annulé' }
const placeLabels: Record<PlaceStatus, string> = { DISPONIBLE: 'Disponible', RESERVEE: 'Réservée', BLOQUEE: 'Bloquée', OCCUPEE: 'Occupée' }
const seatColumns = computed(() => 4)
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

function formatDate(value: string) { return new Date(`${value}T00:00:00`).toLocaleDateString('fr-FR') }
function showError(value: unknown, fallback: string) { error.value = userError(value, fallback, 'DEPART_PLACES_ERROR') }

async function load() {
  loading.value = true
  try {
    depart.value = await departService.get(departId)
    await loadPlaces()
  } catch (value: unknown) {
    showError(value, 'Impossible de charger ce départ.')
  } finally {
    loading.value = false
  }
}

async function loadPlaces() {
  loadingPlaces.value = true
  try {
    places.value = await reservationService.places(departId, false)
  } catch (value: unknown) {
    showError(value, 'Impossible de charger les places.')
  } finally {
    loadingPlaces.value = false
  }
}

function startEdit(place: DepartPlace) {
  if (busy.value) return
  editingPlaceId.value = place.id
  newStatut.value = place.statut
}

function cancelEdit() {
  editingPlaceId.value = null
}

async function confirmEdit(place: DepartPlace) {
  if (busy.value) return
  busy.value = true
  error.value = ''
  try {
    const updated = await reservationService.updatePlace(place.id, newStatut.value)
    const idx = places.value.findIndex((p) => p.id === place.id)
    if (idx !== -1) places.value[idx] = updated
    editingPlaceId.value = null
  } catch (value: unknown) {
    showError(value, 'Impossible de modifier le statut de la place.')
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>

<template>
  <AppLayout>
    <template #title>Gestion des places</template>
    <div class="page-intro">
      <div>
        <p class="eyebrow">OPÉRATIONS</p>
        <h2>Places du départ</h2>
        <p>Consultez et gérez le statut de chaque place du départ.</p>
      </div>
      <div class="form-actions">
        <RouterLink class="secondary-button" :to="`/departs/${departId}`">Retour au détail</RouterLink>
        <RouterLink class="secondary-button" to="/departs">Liste des départs</RouterLink>
      </div>
    </div>
    <p v-if="loading" class="status-msg">Chargement…</p>
    <p v-else-if="error" class="error-banner" role="alert">{{ error }}</p>
    <template v-if="depart && !loading">
      <BaseCard>
        <div class="card-heading">
          <div>
            <h2>Départ #{{ depart.id }}</h2>
            <p>
              <span :class="['status-badge', depart.statut === 'ANNULE' ? 'inactive' : 'active']">{{ labels[depart.statut] }}</span>
            </p>
          </div>
        </div>
        <div class="detail-grid">
          <div class="detail-item"><span class="detail-label">Date</span><strong>{{ formatDate(depart.date_depart) }}</strong></div>
          <div class="detail-item"><span class="detail-label">Heure</span><strong>{{ depart.heure_depart.slice(0, 5) }}</strong></div>
          <div class="detail-item"><span class="detail-label">Véhicule</span><strong>{{ depart.vehicule?.immatriculation || `#${depart.id_vehicule}` }}</strong></div>
          <div class="detail-item"><span class="detail-label">Chauffeur</span><strong>Permis {{ depart.chauffeur?.numero_permis || `#${depart.id_chauffeur}` }}</strong></div>
          <div class="detail-item"><span class="detail-label">Places disponibles</span><strong>{{ depart.places_disponibles }} / {{ depart.nombre_places }}</strong></div>
          <div class="detail-item"><span class="detail-label">Places réservées</span><strong>{{ depart.places_reservees }} / {{ depart.nombre_places }}</strong></div>
        </div>
      </BaseCard>
      <BaseCard>
        <h3 class="section-title">Grille des places</h3>
        <p v-if="loadingPlaces" class="status-msg">Chargement des places…</p>
        <div v-if="!loadingPlaces" class="seat-layout">
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
                :class="{
                  available: place.statut === 'DISPONIBLE',
                  reserved: place.statut === 'RESERVEE',
                  occupied: place.statut === 'OCCUPEE',
                  blocked: place.statut === 'BLOQUEE'
                }"
                :disabled="place.statut === 'BLOQUEE' || busy"
                :title="placeLabels[place.statut]"
                @click="startEdit(place)"
              >
                {{ place.numero_place }}
              </button>
            </div>
            <div v-for="(row, rowIndex) in seatRows" :key="row[0]?.id || rowIndex" class="seat-row" :style="{ '--seat-columns': seatColumns }">
              <template v-for="place in row" :key="place.id">
                <div v-if="editingPlaceId === place.id" class="seat-edit">
                  <select v-model="newStatut" :disabled="busy">
                    <option value="DISPONIBLE">Disponible</option>
                    <option value="RESERVEE">Réservée</option>
                    <option value="BLOQUEE">Bloquée</option>
                    <option value="OCCUPEE">Occupée</option>
                  </select>
                  <div class="seat-edit-actions">
                    <button class="primary-button compact-button" :disabled="busy" @click="confirmEdit(place)">OK</button>
                    <button class="secondary-button compact-button" :disabled="busy" @click="cancelEdit">×</button>
                  </div>
                </div>
                <button
                  v-else
                  type="button"
                  class="seat-button real-seat"
                  :class="{
                    available: place.statut === 'DISPONIBLE',
                    reserved: place.statut === 'RESERVEE',
                    occupied: place.statut === 'OCCUPEE',
                    blocked: place.statut === 'BLOQUEE'
                  }"
                  :disabled="place.statut === 'BLOQUEE' || busy"
                  :title="placeLabels[place.statut]"
                  @click="startEdit(place)"
                >
                  {{ place.numero_place }}
                </button>
              </template>
            </div>
          </div>
          <p v-if="!places.length" class="status-msg">Aucune place configurée pour ce départ.</p>
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

.bus-cabin {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  width: min(100%, 460px);
  margin: 0 auto;
  padding: 1rem 0.75rem 0.75rem;
  border: 1px solid var(--border-color, #d1d5db);
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
  font-weight: 700;
  font-size: 0.82rem;
}

.real-seat.available {
  background: #ffffff;
  border-color: #22c55e;
  color: #166534;
}

.real-seat.reserved {
  background: #e5e7eb;
  border-color: #94a3b8;
  color: #475569;
}

.real-seat.occupied {
  background: #f59e0b;
  border-color: #f59e0b;
  color: #fff;
}

.real-seat.blocked {
  background: #ef4444;
  border-color: #ef4444;
  color: #fff;
}

.occupied {
  background-color: var(--color-warning, #f59e0b);
  color: #fff;
  border-color: var(--color-warning, #f59e0b);
}
.seat-edit {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem;
}
.seat-edit select {
  width: 100%;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  border-radius: 6px;
  border: 1px solid var(--border-color, #d1d5db);
  background: #fff;
}
.seat-edit-actions {
  display: flex;
  gap: 0.25rem;
  width: 100%;
}
.seat-edit-actions .compact-button {
  flex: 1;
  padding: 0.125rem 0.25rem;
  font-size: 0.7rem;
  min-height: 24px;
}
</style>
