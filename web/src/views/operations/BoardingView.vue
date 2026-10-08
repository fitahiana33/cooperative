<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from "vue";
import { BrowserQRCodeReader, type IScannerControls } from "@zxing/browser";
import { localIsoDate } from "../../utils/date";
import AppLayout from "../../components/layout/AppLayout.vue";
import BaseCard from "../../components/ui/BaseCard.vue";
import { api } from "../../services/api";
import { departService } from "../../services/depart/service";
import { reservationService } from "../../services/reservation/service";
import type { Depart } from "../../models/depart/model";
import { userError } from "../../utils/errors";

interface PassengerRow {
  reservation: string;
  passager: string;
  telephone: string;
  place: number | string;
  billet: string;
  billet_statut: string;
  reservation_statut: string;
  embarque: boolean;
  date_pointage: string;
}

const code = ref("");
const busy = ref(false);
const error = ref("");
const result = ref<{ id: number; statut: string; motif_refus?: string | null } | null>(null);
const video = ref<HTMLVideoElement | null>(null);
const scanning = ref(false);
const scannerError = ref("");
const departures = ref<Depart[]>([]);
const departureId = ref<number | null>(null);
const passengers = ref<PassengerRow[]>([]);
const loadingPassengers = ref(false);
let scannerControls: IScannerControls | null = null;

const boarded = computed(() => passengers.value.filter((row) => row.embarque));
const waiting = computed(() => passengers.value.filter((row) => !row.embarque));

function departLabel(item: Depart) {
  const from = item.itineraire?.destination_depart?.nom || "?";
  const to = item.itineraire?.destination_arrivee?.nom || "?";
  return `${item.heure_depart.slice(0, 5)} · ${from} → ${to} · ${item.cooperative?.nom || "Coopérative #" + item.id_cooperative} · ${item.vehicule?.immatriculation || ""}`;
}

async function loadDepartures() {
  try {
    // Boarding happens on the day of the departure, for departures still open.
    const today = localIsoDate();
    const result = await departService.list({ page: 1, page_size: 100, date_from: today, date_to: today, sort_by: "heure_depart", sort_order: "asc" });
    departures.value = (result.items || []).filter((item: Depart) => ["PROGRAMME", "EMBARQUEMENT", "RETARDE"].includes(item.statut));
  } catch (value: unknown) {
    error.value = userError(value, "Impossible de charger les départs du jour.", "BOARDING_DEPARTURES_ERROR");
  }
}

async function loadPassengers() {
  if (!departureId.value) {
    passengers.value = [];
    return;
  }
  loadingPassengers.value = true;
  try {
    passengers.value = (await api.get<PassengerRow[]>(`/departs/${departureId.value}/passagers`)).data;
  } catch (value: unknown) {
    error.value = userError(value, "Impossible de charger la liste des passagers.", "BOARDING_PASSENGERS_ERROR");
  } finally {
    loadingPassengers.value = false;
  }
}

async function selectDeparture() {
  result.value = null;
  error.value = "";
  await loadPassengers();
}

async function control() {
  if (!departureId.value) {
    error.value = "Choisissez d’abord le départ en cours d’embarquement.";
    return;
  }
  if (!code.value.trim()) {
    error.value = "Saisissez le numéro du billet ou scannez son QR Code.";
    return;
  }
  busy.value = true;
  error.value = "";
  result.value = null;
  try {
    result.value = (await api.post("/embarquement/controle", { code: code.value.trim(), id_depart: departureId.value })).data;
    code.value = "";
    await loadPassengers();
  } catch (value: unknown) {
    error.value = userError(value, "Billet non autorisé à l’embarquement.", "BOARDING_CONTROL_ERROR");
  } finally {
    busy.value = false;
  }
}

async function startScanner() {
  scannerError.value = "";
  if (!departureId.value) {
    error.value = "Choisissez d’abord le départ en cours d’embarquement.";
    return;
  }
  scanning.value = true;
  await nextTick();
  if (!video.value) return;
  try {
    const reader = new BrowserQRCodeReader();
    scannerControls = await reader.decodeFromConstraints(
      { video: { facingMode: { ideal: "environment" } }, audio: false },
      video.value,
      (scan, _error, controls) => {
        if (!scan) return;
        controls.stop();
        scanning.value = false;
        code.value = scan.getText();
        void control();
      },
    );
  } catch {
    scannerError.value = "Accès à la caméra refusé ou indisponible. Saisissez le code manuellement.";
    stopScanner();
  }
}

function stopScanner() {
  scannerControls?.stop();
  scannerControls = null;
  scanning.value = false;
}

async function generateManifest() {
  if (!departureId.value) return;
  try {
    const blob = await reservationService.exportManifest(departureId.value);
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `manifeste-depart-${departureId.value}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  } catch (value: unknown) {
    error.value = userError(value, "Impossible de générer le manifeste.", "MANIFEST_EXPORT_ERROR");
  }
}

onMounted(loadDepartures);
onUnmounted(stopScanner);
</script>

<template>
  <AppLayout>
    <template #title>Embarquement</template>
    <div class="page-intro">
      <div>
        <p class="eyebrow">CONTRÔLE</p>
        <h2>Contrôle d’embarquement</h2>
        <p>Choisissez le départ, puis scannez le QR Code ou saisissez le numéro de chaque billet.</p>
      </div>
    </div>

    <BaseCard>
      <div class="card-heading"><div><h2>Départ à embarquer</h2><p>Un billet d’un autre départ sera refusé.</p></div></div>
      <div class="inline-form">
        <label class="form-field">
          <span>Départ du jour *</span>
          <select v-model="departureId" :disabled="busy" @change="selectDeparture">
            <option :value="null">{{ departures.length ? "Choisir un départ" : "Aucun départ à embarquer aujourd’hui" }}</option>
            <option v-for="depart in departures" :key="depart.id" :value="depart.id">{{ departLabel(depart) }}</option>
          </select>
        </label>
        <button class="secondary-button" type="button" :disabled="!departureId" @click="generateManifest">Exporter le manifeste (CSV)</button>
      </div>
    </BaseCard>

    <BaseCard>
      <form class="control-form" @submit.prevent="control">
        <label class="form-field">
          <span>Numéro du billet ou valeur du QR Code *</span>
          <input v-model="code" :disabled="busy || !departureId" placeholder="TKT-… ou identifiant du QR" />
        </label>
        <button class="primary-button" :disabled="busy || !departureId">{{ busy ? "Contrôle…" : "Contrôler" }}</button>
      </form>
      <div class="scanner-actions">
        <button class="secondary-button" type="button" :disabled="scanning || busy || !departureId" @click="startScanner">
          {{ scanning ? "Scan en cours…" : "Scanner avec la caméra" }}
        </button>
        <button v-if="scanning" class="secondary-button danger-action" type="button" @click="stopScanner">Arrêter le scan</button>
      </div>
      <video v-if="scanning" ref="video" class="qr-camera" muted playsinline aria-label="Caméra de scan QR"></video>
      <p v-if="scannerError" class="status-msg">{{ scannerError }}</p>
      <p v-if="error" class="error-banner" role="alert">{{ error }}</p>
      <div v-if="result" class="result-panel" :class="result.statut === 'VALIDE' ? 'result-success' : 'result-error'" role="status">
        <strong>{{ result.statut === "VALIDE" ? "Embarquement enregistré" : "Embarquement refusé" }}</strong>
        <span>{{ result.motif_refus || "Le billet, le départ, la date et la place ont été validés." }}</span>
      </div>
    </BaseCard>

    <BaseCard v-if="departureId">
      <div class="card-heading">
        <div>
          <h2>Passagers ({{ boarded.length }} / {{ passengers.length }} embarqués)</h2>
          <p>La liste se met à jour après chaque contrôle.</p>
        </div>
      </div>
      <p v-if="loadingPassengers" class="status-msg">Chargement des passagers…</p>
      <p v-else-if="!passengers.length" class="empty-state">Aucune réservation sur ce départ.</p>
      <div v-else class="table-scroll">
        <table class="data-table">
          <caption class="sr-only">Passagers du départ</caption>
          <thead><tr><th>Place</th><th>Passager</th><th>Billet</th><th>Réservation</th><th>Embarquement</th></tr></thead>
          <tbody>
            <tr v-for="row in [...waiting, ...boarded]" :key="row.billet || row.reservation + row.place">
              <td>{{ row.place }}</td>
              <td>{{ row.passager }}<br /><small>{{ row.telephone || "—" }}</small></td>
              <td><small>{{ row.billet || "Non émis" }}</small></td>
              <td>{{ row.reservation_statut }}</td>
              <td>
                <span :class="['status-badge', row.embarque ? 'active' : 'inactive']">
                  {{ row.embarque ? "Embarqué" : "Non embarqué" }}
                </span>
                <small v-if="row.embarque && row.date_pointage"> · {{ new Date(row.date_pointage).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" }) }}</small>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </BaseCard>
  </AppLayout>
</template>

<style scoped>
.control-form { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 0.75rem; align-items: end; }
.control-form input { width: 100%; }
@media (max-width: 640px) { .control-form { grid-template-columns: 1fr; } }
.scanner-actions { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.75rem; }
.qr-camera { display: block; width: 100%; max-width: 420px; aspect-ratio: 4 / 3; margin-top: 0.75rem; border-radius: 12px; background: #0f172a; object-fit: cover; }
.result-panel { display: grid; gap: 0.25rem; margin-top: 0.75rem; padding: 0.85rem 1rem; border-radius: 10px; }
.result-success { color: #14532d; background: #dcfce7; }
.result-error { color: #7f1d1d; background: #fee2e2; }
</style>
