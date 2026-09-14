<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink, useRoute } from "vue-router";
import AppLayout from "../../components/layout/AppLayout.vue";
import BaseCard from "../../components/ui/BaseCard.vue";
import { api } from "../../services/api";
import { billetService } from "../../services/billet/service";
import type { Billet } from "../../models/billet/model";
import { userError } from "../../utils/errors";
const route = useRoute();
const item = ref<Billet | null>(null);
const loading = ref(true);
const error = ref("");
function showError(value: unknown) {
  error.value = userError(
    value,
    "Impossible de charger le billet.",
    "BILLET_DETAIL_ERROR",
  );
}
function qrUrl(path?: string | null) {
  if (!path) return "";
  const apiRoot = (api.defaults.baseURL || "").replace(/\/api\/v1\/?$/, "");
  return `${apiRoot}${path}`;
}
async function load() {
  try {
    item.value = await billetService.get(Number(route.params.id));
  } catch (value: unknown) {
    showError(value);
  } finally {
    loading.value = false;
  }
}
onMounted(load);
</script>
<template>
  <AppLayout
    ><template #title>Détail billet</template>
    <div class="page-intro">
      <div>
        <p class="eyebrow">BILLETS & QR CODE</p>
        <h2>Détail du billet</h2>
        <p>Billet {{ item?.numero_billet || `#${route.params.id}` }}</p>
      </div>
      <RouterLink class="secondary-button" to="/billets"
        >Retour à la liste</RouterLink
      >
    </div>
    <p v-if="loading" class="status-msg">Chargement…</p>
    <p v-else-if="error" class="error-banner">{{ error }}</p>
    <template v-if="!loading && !error && item"
      ><BaseCard
        ><div class="card-heading">
          <div>
            <h2>{{ item.numero_billet }}</h2>
            <span
              class="status-badge"
              :class="item.statut === 'VALIDE' ? 'active' : 'inactive'"
              >{{ item.statut }}</span
            >
          </div>
        </div>
        <div v-if="item.qr_code_path" class="qr-panel">
          <img
            :src="qrUrl(item.qr_code_path)"
            :alt="`QR Code du billet ${item.numero_billet}`"
            class="qr-image"
          />
          <span>Présentez ce QR Code au contrôle d’embarquement.</span>
        </div>
        <div class="detail-grid">
          <div class="detail-item">
            <span class="detail-label">QR Code UUID</span
            ><strong
              ><code>{{ item.qr_code_uuid }}</code></strong
            >
          </div>
          <div class="detail-item">
            <span class="detail-label">Numéro réservation</span
            ><strong>{{ item.numero_reservation || "—" }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">Passager</span
            ><strong>{{ item.nom_passager || "—" }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">Téléphone</span
            ><strong>{{ item.telephone_passager || "—" }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">Trajet</span
            ><strong
              >{{ item.destination_depart || "—" }} →
              {{ item.destination_arrivee || "—" }}</strong
            >
          </div>
          <div class="detail-item">
            <span class="detail-label">Date départ</span
            ><strong>{{ item.date_depart || "—" }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">Heure départ</span
            ><strong>{{ item.heure_depart?.slice(0, 5) || "—" }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">Place</span
            ><strong>{{ item.numero_place || "—" }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">Prix</span
            ><strong>{{ item.prix || "—" }} {{ item.devise || "" }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">Véhicule</span
            ><strong>{{ item.immatriculation || "—" }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">Coopérative</span
            ><strong>{{ item.nom_cooperative || "—" }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">Date émission</span
            ><strong>{{
              item.date_emission
                ? new Date(item.date_emission).toLocaleString("fr-FR")
                : "—"
            }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">Date utilisation</span
            ><strong>{{
              item.date_utilisation
                ? new Date(item.date_utilisation).toLocaleString("fr-FR")
                : "—"
            }}</strong>
          </div>
        </div></BaseCard
      ></template
    >
    <p v-if="!loading && !error && !item" class="status-msg">
      Aucun billet trouvé.
    </p></AppLayout
  >
</template>
<style scoped>
.qr-panel {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 1.25rem 0;
  padding: 1rem;
  border: 1px solid var(--border-color, #d1d5db);
  border-radius: 12px;
  background: #fff;
}

.qr-image {
  width: 160px;
  height: 160px;
  object-fit: contain;
}
</style>
