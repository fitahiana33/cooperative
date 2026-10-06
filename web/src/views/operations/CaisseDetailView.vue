<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink, useRoute } from "vue-router";
import AppLayout from "../../components/layout/AppLayout.vue";
import BaseCard from "../../components/ui/BaseCard.vue";
import { financeService } from "../../services/finance/service";
import { cooperativeService } from "../../services/cooperative/service";
import type { Caisse } from "../../models/finance/model";
import type { Cooperative } from "../../models/cooperative/model";
import type { OperationCaisse } from "../../services/finance/service";
import { userError } from "../../utils/errors";
const route = useRoute();
const caisse = ref<Caisse | null>(null);
const operations = ref<OperationCaisse[]>([]);
const cooperatives = ref<Cooperative[]>([]);
const depenseMontant = ref("");
const depenseCooperative = ref<number | null>(null);
const depenseDescription = ref("");
const busy = ref(false);
const loading = ref(true);
const error = ref("");
const success = ref("");
function showError(value: unknown, fallback = "Opération caisse impossible.") {
  error.value = userError(value, fallback, "CAISSE_DETAIL_ERROR");
  success.value = "";
}
async function load() {
  loading.value = true;
  try {
    const id = Number(route.params.id);
    const [cash, ops, cooperativePage] = await Promise.all([
      financeService.getCaisse(id),
      financeService.listOperations(id, { page: 1, page_size: 100 }),
      cooperativeService.listCooperatives({
        page: 1,
        page_size: 100,
        sort_by: "nom",
        sort_order: "asc",
      }),
    ]);
    caisse.value = cash;
    operations.value = ops.items || ops;
    cooperatives.value = cooperativePage.items || [];
  } catch (value: unknown) {
    showError(value, "Impossible de charger la caisse.");
  } finally {
    loading.value = false;
  }
}
async function close() {
  if (!caisse.value || !window.confirm("Clôturer cette caisse ?")) return;
  busy.value = true;
  try {
    await financeService.close(caisse.value.id);
    success.value = "Caisse clôturée.";
    await load();
  } catch (value: unknown) {
    showError(value);
  } finally {
    busy.value = false;
  }
}
async function addDepense() {
  if (!caisse.value) return;
  busy.value = true;
  error.value = "";
  try {
    const data: Record<string, unknown> = {
      type_operation: "DEPENSE",
      montant: Number(depenseMontant.value),
      description: depenseDescription.value || null,
    };
    if (depenseCooperative.value)
      data.id_cooperative = depenseCooperative.value;
    await financeService.addOperation(caisse.value.id, data);
    success.value = "Dépense enregistrée.";
    depenseMontant.value = "";
    depenseCooperative.value = null;
    depenseDescription.value = "";
    await load();
  } catch (value: unknown) {
    showError(value);
  } finally {
    busy.value = false;
  }
}
function operationClass(type: string) {
  if (type === "RECETTE") return "op-recette";
  if (type === "DEPENSE") return "op-depense";
  if (type === "COMMISSION") return "op-commission";
  return "";
}
onMounted(load);
</script>
<template>
  <AppLayout
    ><template #title>Détail caisse</template>
    <div class="page-intro">
      <div>
        <p class="eyebrow">FINANCES</p>
        <h2>Détail de la caisse #{{ route.params.id }}</h2>
        <p>Suivi des opérations et solde de la caisse.</p>
      </div>
      <RouterLink class="secondary-button" to="/finance"
        >Retour aux finances</RouterLink
      >
    </div>
    <p v-if="error" class="error-banner">{{ error }}</p>
    <p v-if="loading" class="status-msg">Chargement…</p>
    <template v-if="caisse && !loading"
      ><p v-if="success" class="success-banner">{{ success }}</p>
      <BaseCard
        ><div class="card-heading">
          <div>
            <h2>Informations caisse</h2>
            <p>État actuel et soldes calculés.</p>
          </div>
          <span
            :class="[
              'status-badge',
              caisse.statut === 'OUVERTE' ? 'active' : '',
            ]"
            >{{ caisse.statut }}</span
          >
        </div>
        <div class="detail-grid">
          <div class="detail-item">
            <span class="detail-label">ID gare</span
            ><strong>#{{ caisse.id_gare }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">Date ouverture</span
            ><strong>{{
              caisse.date_ouverture
                ? new Date(caisse.date_ouverture).toLocaleString("fr-FR")
                : "—"
            }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">Montant ouverture</span
            ><strong>{{ caisse.montant_ouverture }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">Date clôture</span
            ><strong>{{
              caisse.date_cloture
                ? new Date(caisse.date_cloture).toLocaleString("fr-FR")
                : "—"
            }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">Montant clôture</span
            ><strong>{{ caisse.montant_cloture ?? "—" }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">Statut</span
            ><strong>{{ caisse.statut }}</strong>
          </div>
        </div>
        <h3 class="section-title">Totaux</h3>
        <div class="detail-grid">
          <div class="detail-item">
            <span class="detail-label">Total recettes</span
            ><strong class="op-recette">{{ caisse.total_recettes }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">Total dépenses</span
            ><strong class="op-depense">{{ caisse.total_depenses }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">Total commissions</span
            ><strong class="op-commission">{{
              caisse.total_commissions
            }}</strong>
          </div>
          <div class="detail-item">
            <span class="detail-label">Solde</span
            ><strong>{{ caisse.solde }}</strong>
          </div>
        </div></BaseCard
      ><BaseCard v-if="caisse.statut === 'OUVERTE'"
        ><div class="card-heading">
          <div>
            <h2>Ajouter une dépense</h2>
            <p>Enregistrer une sortie d'espèces.</p>
          </div>
        </div>
        <div class="form-grid">
          <label class="form-field"
            ><span>Montant *</span
            ><input
              v-model="depenseMontant"
              type="number"
              min="0.01"
              step="0.01" /></label
          ><label class="form-field"
            ><span>Coopérative</span
            ><select v-model="depenseCooperative">
              <option :value="null">Aucune coopérative</option>
              <option
                v-for="cooperative in cooperatives"
                :key="cooperative.id"
                :value="cooperative.id"
              >{{ cooperative.nom }}</option>
            </select></label
          ><label class="form-field full"
            ><span>Description</span
            ><input
              v-model="depenseDescription"
              type="text"
              placeholder="Motif de la dépense"
          /></label>
        </div>
        <div class="form-actions">
          <button
            class="primary-button"
            :disabled="busy || !depenseMontant"
            @click="addDepense"
          >
            Enregistrer la dépense</button
          ><button
            class="secondary-button danger-action"
            :disabled="busy"
            @click="close"
          >
            Clôturer la caisse
          </button>
        </div></BaseCard
      ><BaseCard
        ><div class="card-heading">
          <div>
            <h2>Opérations</h2>
            <p>Historique des mouvements de la caisse.</p>
          </div>
        </div>
        <div class="table-scroll">
          <table class="data-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Montant</th>
                <th>Description</th>
                <th>Coopérative</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="op in operations" :key="op.id">
                <td>
                  <span
                    :class="['op-type', operationClass(op.type_operation)]"
                    >{{ op.type_operation }}</span
                  >
                </td>
                <td>{{ op.montant }}</td>
                <td>{{ op.description || "—" }}</td>
                <td>{{ op.id_cooperative ? `#${op.id_cooperative}` : "—" }}</td>
                <td>
                  {{
                    op.date_operation
                      ? new Date(op.date_operation).toLocaleString("fr-FR")
                      : "—"
                  }}
                </td>
              </tr>
              <tr v-if="!operations.length">
                <td colspan="5" class="empty-state">Aucune opération.</td>
              </tr>
            </tbody>
          </table>
        </div></BaseCard
      ></template
    ></AppLayout
  >
</template>
<style>
.op-recette {
  color: #16a34a;
  font-weight: 600;
}
.op-depense {
  color: #dc2626;
  font-weight: 600;
}
.op-commission {
  color: #ca8a04;
  font-weight: 600;
}
.op-type {
  padding: 0.25rem 0.5rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.form-field.full {
  grid-column: 1 / -1;
}
.form-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
  flex-wrap: wrap;
}
</style>
