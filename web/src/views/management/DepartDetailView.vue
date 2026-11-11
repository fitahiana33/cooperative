<script setup lang="ts">
import PageTabs from "../../components/ui/PageTabs.vue";
import PageTabPanel from "../../components/ui/PageTabPanel.vue";
import DepartureIncidents from "../../components/ui/DepartureIncidents.vue";
import { allPages } from "../../services/pagination";
import SearchSelect from "../../components/ui/SearchSelect.vue";
import { onMounted, ref } from "vue";
import { RouterLink, useRoute } from "vue-router";
import AppLayout from "../../components/layout/AppLayout.vue";
import BaseCard from "../../components/ui/BaseCard.vue";
import type { Caisse } from "../../models/finance/model";
import type { Depart, DepartStatus } from "../../models/depart/model";
import { departService } from "../../services/depart/service";
import { financeService } from "../../services/finance/service";
import { useAuthenticationStore } from "../../stores/authentication/store";
import { userError } from "../../utils/errors";

const route = useRoute();
const auth = useAuthenticationStore();
const item = ref<Depart | null>(null);
const caisses = ref<Caisse[]>([]);
const cancelCaisseId = ref<number | null>(null);
const loading = ref(true);
const error = ref("");
const success = ref("");
const busy = ref(false);
const activeTab = ref("overview");
const labels: Record<DepartStatus, string> = {
  PROGRAMME: "Programmé",
  EMBARQUEMENT: "Embarquement",
  RETARDE: "Retardé",
  PARTI: "Parti",
  TERMINE: "Terminé",
  ANNULE: "Annulé",
};
const canUpdate = () => auth.hasPermission("DEPART_UPDATE");
const canCancel = () => auth.hasPermission("DEPART_CANCEL");
const canProcessRefund = () => auth.hasPermission("PAIEMENT_REFUND");
function routeName(value: Depart) {
  return `${value.itineraire?.destination_depart?.nom || `#${value.id_itineraire}`} → ${value.itineraire?.destination_arrivee?.nom || ""}`;
}
function formatDate(value: string) {
  return new Date(`${value}T00:00:00`).toLocaleDateString("fr-FR");
}
function showError(value: unknown, fallback: string) {
  error.value = userError(value, fallback, "DEPART_DETAIL_ERROR");
  success.value = "";
}
async function loadCaisses() {
  if (!canProcessRefund()) return;
  const result = await allPages((params) => financeService.caisses(params), {
    page: 1,
    page_size: 100,
  });
  caisses.value = (result.items || result).filter(
    (caisse: Caisse) => caisse.statut === "OUVERTE",
  );
}
async function load() {
  try {
    item.value = await departService.get(Number(route.params.id));
    await loadCaisses();
  } catch (value: unknown) {
    showError(value, "Impossible de charger ce départ.");
  } finally {
    loading.value = false;
  }
}
async function changeStatus(statut: DepartStatus) {
  if (!item.value || busy.value) return;
  busy.value = true;
  try {
    item.value = await departService.updateStatus(item.value.id, statut);
    success.value = "Statut mis à jour avec succès.";
  } catch (value: unknown) {
    showError(value, "Impossible de modifier le statut.");
  } finally {
    busy.value = false;
  }
}
async function cancel() {
  if (
    !item.value ||
    busy.value ||
    !window.confirm(
      "Annuler ce départ ? Les réservations seront annulées et les paiements remboursés si une caisse est sélectionnée.",
    )
  )
    return;
  busy.value = true;
  try {
    item.value = await departService.cancel(
      item.value.id,
      cancelCaisseId.value || undefined,
    );
    success.value = "Départ annulé avec succès.";
  } catch (value: unknown) {
    showError(
      value,
      "Impossible d’annuler ce départ. Si des réservations sont payées, sélectionnez une caisse ouverte.",
    );
  } finally {
    busy.value = false;
  }
}
onMounted(load);
</script>

<template>
  <AppLayout
    ><template #title>Détail du départ</template>
    <div class="page-intro">
      <div>
        <p class="eyebrow">PLANIFICATION</p>
        <h2>Détail du départ</h2>
        <p>
          Consultez le planning, les affectations et les places disponibles.
        </p>
      </div>
      <div class="form-actions">
        <RouterLink class="secondary-button" to="/departs"
          >Retour à la liste</RouterLink
        ><RouterLink
          v-if="
            item &&
            canUpdate() &&
            ['PROGRAMME', 'RETARDE'].includes(item.statut)
          "
          class="primary-button compact-button"
          :to="`/departs/${item.id}/edit`"
          >Modifier</RouterLink
        >
      </div>
    </div>
    <p v-if="loading" class="status-msg">Chargement…</p>
    <p v-else-if="error" class="error-banner" role="alert">{{ error }}</p>
    <template v-if="item"
      ><p v-if="success" class="success-banner" role="status">{{ success }}</p>
      <div class="record-summary">
        <div>
          <strong>{{ routeName(item) }}</strong
          ><small
            >{{ formatDate(item.date_depart) }} à
            {{ item.heure_depart.slice(0, 5) }}</small
          >
        </div>
        <div>
          <small>Places disponibles</small
          ><strong
            >{{ item.places_disponibles }} / {{ item.nombre_places }}</strong
          >
        </div>
        <span
          class="status-badge"
          :class="item.statut === 'ANNULE' ? 'inactive' : 'active'"
          >{{ labels[item.statut] }}</span
        >
      </div>
      <PageTabs
        v-model="activeTab"
        panel-prefix="departure-detail"
        aria-label="Sections du départ"
        :tabs="[
          { id: 'overview', label: 'Informations' },
          { id: 'operations', label: 'Opérations' },
          { id: 'incidents', label: 'Incidents' },
        ]"
      />
      <PageTabPanel
        prefix="departure-detail"
        name="overview"
        :active="activeTab === 'overview'"
      >
        <BaseCard
          ><h2>Informations et ressources</h2>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-label">Date</span
              ><strong>{{ formatDate(item.date_depart) }}</strong>
            </div>
            <div class="detail-item">
              <span class="detail-label">Heure</span
              ><strong>{{ item.heure_depart.slice(0, 5) }}</strong>
            </div>
            <div class="detail-item">
              <span class="detail-label">Itinéraire</span
              ><strong>{{ routeName(item) }}</strong>
            </div>
            <div class="detail-item">
              <span class="detail-label">Coopérative</span
              ><strong>{{
                item.cooperative?.nom || `#${item.id_cooperative}`
              }}</strong>
            </div>
            <div class="detail-item">
              <span class="detail-label">Véhicule</span
              ><strong>{{
                item.vehicule?.immatriculation || `#${item.id_vehicule}`
              }}</strong>
            </div>
            <div class="detail-item">
              <span class="detail-label">Chauffeur</span
              ><strong
                >Permis
                {{
                  item.chauffeur?.numero_permis || `#${item.id_chauffeur}`
                }}</strong
              >
            </div>
            <div class="detail-item">
              <span class="detail-label">Tarif</span
              ><strong
                >{{ item.tarif?.prix || "—" }}
                {{ item.tarif?.devise || "" }}</strong
              >
            </div>
            <div class="detail-item">
              <span class="detail-label">Places disponibles</span
              ><strong
                >{{ item.places_disponibles }} /
                {{ item.nombre_places }}</strong
              >
            </div>
            <div class="detail-item">
              <span class="detail-label">Taux de remplissage</span
              ><strong>{{ item.taux_remplissage }} %</strong>
            </div>
          </div>
        </BaseCard>
      </PageTabPanel>
      <PageTabPanel
        prefix="departure-detail"
        name="operations"
        :active="activeTab === 'operations'"
      >
        <BaseCard
          ><h2>Gestion du départ</h2>
          <div
            v-if="canCancel() && canProcessRefund()"
            class="form-grid cancellation-cash"
          >
            <label class="form-field"
              ><span>Caisse de remboursement (si nécessaire)</span
              ><SearchSelect
                aria-label="Annulation sans remboursement"
                v-model="cancelCaisseId"
                :options="
                  caisses.map((caisse) => ({
                    value: caisse.id,
                    label: `Gare #${caisse.id_gare} · solde ${caisse.solde}`,
                  }))
                "
                placeholder="Annulation sans remboursement"
                :empty-value="null"
            /></label>
          </div>
          <div class="form-actions">
            <RouterLink
              class="secondary-button compact-button"
              :to="`/departs/${item.id}/places`"
              >Gérer les places</RouterLink
            ><button
              v-if="canUpdate() && item.statut === 'PROGRAMME'"
              class="table-action"
              :disabled="busy"
              @click="changeStatus('EMBARQUEMENT')"
            >
              Embarquement</button
            ><button
              v-if="
                canUpdate() &&
                ['PROGRAMME', 'EMBARQUEMENT'].includes(item.statut)
              "
              class="table-action"
              :disabled="busy"
              @click="changeStatus('RETARDE')"
            >
              Retardé</button
            ><button
              v-if="
                canUpdate() &&
                ['PROGRAMME', 'EMBARQUEMENT', 'RETARDE'].includes(item.statut)
              "
              class="table-action"
              :disabled="busy"
              @click="changeStatus('PARTI')"
            >
              Parti</button
            ><button
              v-if="canUpdate() && item.statut === 'PARTI'"
              class="table-action"
              :disabled="busy"
              @click="changeStatus('TERMINE')"
            >
              Terminé</button
            ><button
              v-if="
                canCancel() &&
                !['ANNULE', 'PARTI', 'TERMINE'].includes(item.statut)
              "
              class="table-action danger-action"
              :disabled="busy"
              @click="cancel"
            >
              Annuler le départ
            </button>
          </div></BaseCard
        >
      </PageTabPanel>
      <PageTabPanel
        prefix="departure-detail"
        name="incidents"
        :active="activeTab === 'incidents'"
      >
        <DepartureIncidents :depart-id="item.id" :can-manage="canUpdate()" />
      </PageTabPanel> </template
  ></AppLayout>
</template>

<style scoped>
.cancellation-cash {
  max-width: 420px;
  margin: 1rem 0;
}
</style>
