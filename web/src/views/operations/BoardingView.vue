<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref } from "vue";
import AppLayout from "../../components/layout/AppLayout.vue";
import BaseCard from "../../components/ui/BaseCard.vue";
import { api } from "../../services/api";
import { departService } from "../../services/depart/service";
import { reservationService } from "../../services/reservation/service";
import type { Depart } from "../../models/depart/model";
import { userError } from "../../utils/errors";
const code = ref("");
const busy = ref(false);
const error = ref("");
const result = ref<{
  id: number;
  statut: string;
  motif_refus?: string | null;
} | null>(null);
const video = ref<HTMLVideoElement | null>(null);
const scanning = ref(false);
const scannerError = ref("");
const departures = ref<Depart[]>([]);
const departureId = ref<number | null>(null);
let cameraStream: MediaStream | null = null;
let scanFrame = 0;

type Detector = { detect(source: HTMLVideoElement): Promise<Array<{ rawValue: string }>> };
type DetectorConstructor = new (options?: { formats: string[] }) => Detector;

async function scanFrameLoop() {
  if (!scanning.value || !video.value) return;
  const BarcodeDetector = (window as Window & { BarcodeDetector?: DetectorConstructor }).BarcodeDetector;
  if (BarcodeDetector) {
    try {
      const detected = await new BarcodeDetector({ formats: ["qr_code"] }).detect(video.value);
      if (detected[0]?.rawValue) {
        code.value = detected[0].rawValue;
        stopScanner();
        await control();
        return;
      }
    } catch {
      scannerError.value = "Le QR Code n’a pas pu être lu.";
    }
  }
  scanFrame = window.requestAnimationFrame(scanFrameLoop);
}

async function startScanner() {
  scannerError.value = "";
  const BarcodeDetector = (window as Window & { BarcodeDetector?: DetectorConstructor }).BarcodeDetector;
  if (!BarcodeDetector) {
    scannerError.value = "Le scan caméra n’est pas pris en charge par ce navigateur. Saisissez le code manuellement.";
    return;
  }
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" } }, audio: false });
    scanning.value = true;
    await nextTick();
    if (!video.value) return;
    video.value.srcObject = cameraStream;
    await video.value.play();
    scanFrame = window.requestAnimationFrame(scanFrameLoop);
  } catch {
    scannerError.value = "Accès caméra refusé ou indisponible.";
    stopScanner();
  }
}

function stopScanner() {
  scanning.value = false;
  if (scanFrame) window.cancelAnimationFrame(scanFrame);
  cameraStream?.getTracks().forEach((track) => track.stop());
  cameraStream = null;
  if (video.value) video.value.srcObject = null;
}
async function control() {
  if (!code.value.trim()) {
    error.value = "Saisissez le numéro du billet ou le QR Code.";
    return;
  }
  busy.value = true;
  error.value = "";
  result.value = null;
  try {
    result.value = (
      await api.post("/embarquement/controle", { code: code.value.trim() })
    ).data;
  } catch (value: unknown) {
    error.value = userError(
      value,
      "Billet non autorisé à l’embarquement.",
      "BOARDING_CONTROL_ERROR",
    );
  } finally {
    busy.value = false;
  }
}
async function loadDepartures() {
  try {
    const result = await departService.list({ page: 1, page_size: 100, date_from: new Date().toISOString().slice(0, 10) });
    departures.value = result.items || [];
  } catch (value: unknown) {
    error.value = userError(value, "Impossible de charger les départs.", "MANIFEST_LOAD_ERROR");
  }
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
  <AppLayout
    ><template #title>Embarquement</template>
    <div class="page-intro">
      <div>
        <p class="eyebrow">CONTRÔLE</p>
        <h2>Contrôle d’embarquement</h2>
        <p>Recherchez un billet par numéro ou scannez sa valeur QR.</p>
      </div>
    </div>
    <BaseCard class="manifest-card">
      <div class="card-heading"><div><h2>Manifeste du départ</h2><p>Exportez la liste des passagers, des places, des billets et du pointage d’embarquement.</p></div></div>
      <div class="inline-form"><label class="form-field"><span>Départ *</span><select v-model="departureId"><option :value="null">Choisir un départ</option><option v-for="depart in departures" :key="depart.id" :value="depart.id">#{{ depart.id }} · {{ depart.date_depart }} {{ depart.heure_depart.slice(0, 5) }}</option></select></label><button class="secondary-button" type="button" :disabled="!departureId" @click="generateManifest">Générer le manifeste CSV</button></div>
    </BaseCard>
    <BaseCard
      ><form class="inline-form" @submit.prevent="control">
        <label class="form-field"
          ><span>Numéro billet ou QR Code *</span
          ><input
            v-model="code"
            :disabled="busy"
            autofocus
            placeholder="BIL-… ou UUID" /></label
        ><button class="primary-button" :disabled="busy">
          {{ busy ? "Contrôle…" : "Contrôler" }}
        </button>
      </form>
      <div class="scanner-actions">
        <button class="secondary-button" type="button" :disabled="scanning || busy" @click="startScanner">{{ scanning ? "Scan en cours…" : "Scanner avec la caméra" }}</button>
        <button v-if="scanning" class="secondary-button danger-action" type="button" @click="stopScanner">Arrêter le scan</button>
      </div>
      <video v-if="scanning" ref="video" class="qr-camera" autoplay muted playsinline aria-label="Caméra de scan QR"></video>
      <p v-if="scannerError" class="status-msg">{{ scannerError }}</p>
      <p v-if="error" class="error-banner" role="alert">{{ error }}</p>
      <div
        v-if="result"
        class="result-panel"
        :class="result.statut === 'VALIDE' ? 'result-success' : 'result-error'"
      >
        <strong>{{
          result.statut === "VALIDE"
            ? "Embarquement enregistré"
            : "Embarquement refusé"
        }}</strong
        ><span>{{
          result.motif_refus ||
          "Le billet, la réservation, la date et la place ont été validés."
        }}</span>
      </div></BaseCard
    ></AppLayout
  >
</template>
