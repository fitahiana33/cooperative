<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import AppLayout from "../../components/layout/AppLayout.vue";
import PageTabs from "../../components/ui/PageTabs.vue";
import PageTabPanel from "../../components/ui/PageTabPanel.vue";
import PaginationControls from "../../components/ui/PaginationControls.vue";
import { api } from "../../services/api";
import { userError } from "../../utils/errors";
import { formatMoney } from "../../utils/money";
type Identity = {
  id_itineraire: number;
  id_cooperative: number;
  id_gare: number | null;
  libelle: string;
  cooperative?: string;
  gare?: string;
};
type Forecast = Identity & {
  qualite: string;
  observations: number;
  jours_actifs_30?: number;
  dernier_depart?: string;
  raison_qualite: string;
  passagers_7_jours: number | null;
  passagers_30_jours: number | null;
  remplissage_7_jours: number | null;
};
type Advice = Identity & {
  departs_recommandes: number;
  raison: string;
  horaires: { heure: string; departs_observes: number; remplissage: number }[];
  jours: {
    date: string;
    passagers: number;
    departs_planifies: number;
    places_planifiees: number;
    places_retenues: number;
    departs_supplementaires: number;
  }[];
};
type Anomaly = Identity & {
  date: string;
  type: string;
  valeur: number;
  moyenne: number;
  unite: string;
  raison: string;
};
type Popular = Identity & {
  passagers: number;
  departs: number;
  remplissage_observe: number;
};
type Analysis = {
  date_reference: string;
  periode_observee: { du: string; au: string };
  previsions: Forecast[];
  recommandations: Advice[];
  anomalies: Anomaly[];
  destinations_demandees: Popular[];
  limites: string;
  resume: {
    itineraires_exploitables: number;
    departs_a_etudier: number;
    itineraires_sous_tension: number;
    points_a_verifier: number;
  };
  priorites: Array<Identity & {
    type: "CAPACITE_A_ETUDIER" | "VERIFICATION_REQUISE";
    priorite: "HAUTE" | "NORMALE";
    valeur: number;
    message: string;
  }>;
};
const route = useRoute();
const data = ref<Analysis | null>(null);
const loading = ref(true),
  error = ref("");
const tab = ref("previsions"),
  search = ref(""),
  page = ref(1);
const tabs = computed(() => [
  {
    id: "previsions",
    label: "Prévisions",
    count: data.value?.previsions.length || 0,
  },
  {
    id: "planning",
    label: "Départs & horaires",
    count: data.value?.recommandations.length || 0,
  },
  { id: "popular", label: "Destinations demandées" },
  {
    id: "anomalies",
    label: "Points à vérifier",
    count: data.value?.anomalies.length || 0,
  },
  { id: "methode", label: "Méthode & limites" },
]);
const summary = computed(() =>
  data.value?.resume || {
    itineraires_exploitables: 0,
    departs_a_etudier: 0,
    itineraires_sous_tension: 0,
    points_a_verifier: 0,
  },
);
const priorities = computed(() => data.value?.priorites || []);
const rows = computed(() => {
  const source: Identity[] =
    tab.value === "planning"
      ? data.value?.recommandations || []
      : tab.value === "popular"
        ? data.value?.destinations_demandees || []
        : tab.value === "anomalies"
          ? data.value?.anomalies || []
          : data.value?.previsions || [];
  return source.filter((r) =>
    `${r.libelle} ${r.cooperative || ""} ${r.gare || ""}`
      .toLocaleLowerCase("fr")
      .includes(search.value.trim().toLocaleLowerCase("fr")),
  );
});
const visible = computed(() =>
  rows.value.slice((page.value - 1) * 6, page.value * 6),
);
const forecasts = computed(() =>
    tab.value === "previsions" ? (visible.value as Forecast[]) : [],
  ),
  advice = computed(() =>
    tab.value === "planning" ? (visible.value as Advice[]) : [],
  ),
  anomalies = computed(() =>
    tab.value === "anomalies" ? (visible.value as Anomaly[]) : [],
  ),
  popular = computed(() =>
    tab.value === "popular" ? (visible.value as Popular[]) : [],
  );
watch([tab, search], () => {
  page.value = 1;
});
watch(
  () => route.query.onglet,
  (value) => {
    if (typeof value === "string" && ["previsions", "planning", "popular", "anomalies", "methode"].includes(value)) {
      tab.value = value;
    }
  },
  { immediate: true },
);
function key(r: Identity) {
  return `${r.id_itineraire}-${r.id_cooperative}-${r.id_gare}`;
}
function day(d: string) {
  return new Date(`${d}T00:00:00`).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "short",
  });
}
function number(n: number | null) {
  return n == null
    ? "—"
    : n.toLocaleString("fr-FR", { maximumFractionDigits: 1 });
}
async function load() {
  loading.value = true;
  error.value = "";
  try {
    data.value = (await api.get<Analysis>("/aide-decision")).data;
  } catch (e) {
    error.value = userError(
      e,
      "Impossible de charger les analyses.",
      "DECISION_SUPPORT_ERROR",
    );
  } finally {
    loading.value = false;
  }
}
onMounted(load);
</script>
<template>
  <AppLayout>
    <template #title>Aide à la décision</template>
    <div class="page-header">
      <div>
        <h2>Aide à la décision</h2>
        <p>Préparer l’offre de transport à partir de l’activité observée.</p>
      </div>
      <button class="secondary-button" :disabled="loading" @click="load">
        {{ loading ? "Analyse…" : "Actualiser" }}
      </button>
    </div>
    <p v-if="error" class="error-banner" role="alert">{{ error }}</p>
    <p v-if="loading" role="status">Analyse de l’historique et du planning…</p>
    <template v-else-if="data">
      <p class="analysis-period">
        Historique du {{ day(data.periode_observee.du) }} au
        {{ day(data.periode_observee.au) }} · Projections des 7 et 30 jours
        suivant le {{ day(data.date_reference) }}.
      </p>
      <section class="decision-overview" aria-label="Priorités opérationnelles">
        <div class="decision-kpis">
          <article><small>Historique exploitable</small><strong>{{ summary.itineraires_exploitables }}</strong><span>trajet(s)</span></article>
          <article><small>Capacité à étudier</small><strong>{{ summary.departs_a_etudier }}</strong><span>départ(s) sur 7 jours</span></article>
          <article><small>Trajets sous tension</small><strong>{{ summary.itineraires_sous_tension }}</strong><span>à examiner</span></article>
          <article><small>Points à vérifier</small><strong>{{ summary.points_a_verifier }}</strong><span>signal(s)</span></article>
        </div>
        <article class="priority-panel">
          <div><p class="eyebrow">À DÉCIDER EN PREMIER</p><h2>Priorités fondées sur les données</h2></div>
          <p>Ce sont des recommandations à valider : l’application ne crée jamais un départ automatiquement.</p>
          <ul v-if="priorities.length">
            <li v-for="item in priorities" :key="`${item.type}-${key(item)}`">
              <span :class="['priority-kind', item.priorite.toLowerCase()]">{{ item.type === 'CAPACITE_A_ETUDIER' ? 'Capacité' : 'Vérification' }}</span>
              <div><strong>{{ item.libelle }}</strong><small>{{ item.cooperative }} · {{ item.gare }}</small><p>{{ item.message }}</p></div>
              <RouterLink :to="item.type === 'CAPACITE_A_ETUDIER' ? { name: 'planning-calendar' } : { name: 'aide-decision', query: { onglet: 'anomalies' } }">{{ item.type === 'CAPACITE_A_ETUDIER' ? 'Voir le planning' : 'Examiner' }} →</RouterLink>
            </li>
          </ul>
          <p v-else class="empty-priority">Aucune priorité chiffrée n’est disponible : poursuivez la collecte de données ou vérifiez le périmètre.</p>
        </article>
      </section>
      <PageTabs
        v-model="tab"
        :tabs="tabs"
        panel-prefix="decision"
        aria-label="Analyses de décision"
      />
      <label v-if="tab !== 'methode'" class="decision-search"
        >Filtrer par trajet, gare ou coopérative<input
          v-model="search"
          type="search"
          placeholder="Rechercher dans les analyses"
      /></label>
      <PageTabPanel
        prefix="decision"
        name="previsions"
        :active="tab === 'previsions'"
      >
        <div class="decision-grid">
          <article v-for="r in forecasts" :key="key(r)" class="decision-card">
            <div class="decision-card-head">
              <h2>{{ r.libelle }}</h2>
              <span
                class="quality-tag"
                :class="{ insufficient: r.qualite !== 'EXPLOITABLE' }"
                >{{
                  r.qualite === "EXPLOITABLE"
                    ? "Historique exploitable"
                    : "Données insuffisantes"
                }}</span
              >
            </div>
            <p>{{ r.cooperative }} · {{ r.gare }}</p>
            <dl class="decision-metrics">
              <div>
                <dt>Places confirmées estimées · 7 j</dt>
                <dd>{{ number(r.passagers_7_jours) }}</dd>
              </div>
              <div>
                <dt>Projection · 30 j</dt>
                <dd>{{ number(r.passagers_30_jours) }}</dd>
              </div>
              <div>
                <dt>Occupation de l’offre planifiée · 7 j</dt>
                <dd>
                  {{
                    r.remplissage_7_jours == null
                      ? r.qualite !== "EXPLOITABLE"
                        ? "Projection indisponible"
                        : "Aucune place planifiée"
                      : number(r.remplissage_7_jours) + " %"
                  }}
                </dd>
              </div>
            </dl>
            <small
              >{{ r.observations }} jours de service observés ·
              {{ r.jours_actifs_30 || 0 }} sur les 30 derniers jours<span
                v-if="r.dernier_depart"
              >
                · dernier départ le {{ day(r.dernier_depart) }}</span
              >.</small
            >
            <p v-if="r.qualite !== 'EXPLOITABLE'" class="quality-reason">
              {{ r.raison_qualite }}
            </p>
          </article>
        </div>
      </PageTabPanel>
      <PageTabPanel
        prefix="decision"
        name="planning"
        :active="tab === 'planning'"
      >
        <p class="info-banner">
          Conseils à valider dans le planning. Aucun départ n’est créé
          automatiquement. Une occupation supérieure à 100 % signale un manque
          de capacité estimé.
        </p>
        <article
          v-for="r in advice"
          :key="key(r)"
          class="decision-card advice-card"
        >
          <h2>{{ r.libelle }}</h2>
          <p>{{ r.cooperative }} · {{ r.gare }}</p>
          <strong
            >{{ r.departs_recommandes }} départ(s) supplémentaire(s) à étudier
            sur 7 jours</strong
          >
          <p>{{ r.raison }}</p>
          <div class="decision-table">
            <table>
              <caption>
                Comparaison quotidienne avec le planning
              </caption>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Estimation</th>
                  <th>Départs prévus</th>
                  <th>Places offertes</th>
                  <th>Places retenues</th>
                  <th>Ajouts à étudier</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="d in r.jours" :key="d.date">
                  <td>{{ day(d.date) }}</td>
                  <td>{{ number(d.passagers) }}</td>
                  <td>{{ d.departs_planifies }}</td>
                  <td>{{ d.places_planifiees }}</td>
                  <td>{{ d.places_retenues }}</td>
                  <td>
                    <strong>{{ d.departs_supplementaires }}</strong>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-if="r.horaires.length">
            <strong>Horaires à étudier :</strong>
            <span v-for="(h, i) in r.horaires" :key="h.heure"
              >{{ i ? " · " : "" }}{{ h.heure }} ({{ h.remplissage }} %,
              {{ h.departs_observes }} départs observés)</span
            >.
          </p>
          <p v-else>
            Historique insuffisant par horaire pour proposer un créneau.
          </p>
          <RouterLink to="/planning" class="text-link"
            >Examiner le planning →</RouterLink
          >
        </article>
      </PageTabPanel>
      <PageTabPanel
        prefix="decision"
        name="popular"
        :active="tab === 'popular'"
      >
        <p>
          Classement par nombre de places confirmées sur l’historique, à
          distinguer des recherches et de la demande non satisfaite.
        </p>
        <div class="decision-grid">
          <article v-for="r in popular" :key="key(r)" class="decision-card">
            <h2>{{ r.libelle }}</h2>
            <p>{{ r.cooperative }} · {{ r.gare }}</p>
            <strong>{{ number(r.passagers) }} places confirmées</strong>
            <p>
              {{ r.departs }} départs · {{ r.remplissage_observe }} % de
              remplissage observé.
            </p>
          </article>
        </div>
      </PageTabPanel>
      <PageTabPanel
        prefix="decision"
        name="anomalies"
        :active="tab === 'anomalies'"
      >
        <article
          v-for="(r, i) in anomalies"
          :key="key(r) + r.date + r.type + i"
          class="decision-card"
        >
          <h2>
            {{
              r.type === "RECETTES_INHABITUELLES"
                ? "Recettes inhabituelles"
                : "Réservations inhabituelles"
            }}
            · {{ r.libelle }}
          </h2>
          <p>
            {{ day(r.date) }} · Coopérative {{ r.id_cooperative }} · Gare
            {{ r.id_gare ?? "non renseignée" }}
          </p>
          <p>
            <strong>{{
              r.unite === "Ar"
                ? formatMoney(r.valeur, "MGA")
                : number(r.valeur) + " places"
            }}</strong>
            · Moyenne des jours observés :
            {{
              r.unite === "Ar"
                ? formatMoney(r.moyenne, "MGA")
                : number(r.moyenne)
            }}
          </p>
          <p>{{ r.raison }}</p>
        </article>
      </PageTabPanel>
      <PageTabPanel prefix="decision" name="methode" :active="tab === 'methode'"
        ><article class="decision-card">
          <h2>Comprendre les résultats</h2>
          <p>{{ data.limites }}</p>
          <p>
            La qualité « exploitable » signifie que le volume d’historique
            respecte les seuils techniques. Elle ne garantit pas la précision
            des prévisions. Mesurez les écarts avec les résultats réels avant
            d’engager des ressources.
          </p>
          <p>
            Les recettes représentent les paiements actuellement validés,
            regroupés par date de validation à Madagascar. Elles ne constituent
            pas un bénéfice net et ne remplacent pas le rapprochement de caisse.
          </p>
        </article></PageTabPanel
      >
      <p v-if="tab !== 'methode' && !rows.length" class="empty-panel">
        {{
          search
            ? "Aucune analyse ne correspond à cette recherche."
            : tab === "planning"
              ? "Aucun historique suffisant pour recommander des départs."
              : tab === "anomalies"
                ? "Aucun signal inhabituel détecté sur les données exploitables."
                : "Aucune donnée disponible dans votre périmètre."
        }}
      </p>
      <PaginationControls
        v-if="tab !== 'methode'"
        :page="page"
        :pages="Math.max(1, Math.ceil(rows.length / 6))"
        :total="rows.length"
        @change="page = $event"
      />
    </template>
  </AppLayout>
</template>
<style scoped>
.analysis-period {
  color: var(--text-muted, #637267);
  font-size: 0.9rem;
}
.decision-overview { display: grid; gap: 18px; margin: 20px 0; }
.decision-kpis { display: grid; gap: 12px; grid-template-columns: repeat(4, minmax(0, 1fr)); }
.decision-kpis article { background: var(--surface, white); border: 1px solid var(--border, #dce3dd); border-radius: 12px; display: grid; gap: 3px; padding: 16px; }
.decision-kpis small, .decision-kpis span { color: var(--text-muted, #637267); font-size: .78rem; }
.decision-kpis strong { font-size: 1.6rem; }
.priority-panel { background: #f4f8f5; border: 1px solid #d5e5da; border-radius: 14px; padding: 20px; }
.priority-panel h2, .priority-panel p { margin: 0; }
.priority-panel > p { color: var(--text-muted, #637267); margin-top: 8px; }
.priority-panel ul { display: grid; gap: 10px; list-style: none; margin: 16px 0 0; padding: 0; }
.priority-panel li { align-items: start; background: white; border-radius: 10px; display: grid; gap: 12px; grid-template-columns: auto minmax(0, 1fr) auto; padding: 14px; }
.priority-panel li small, .priority-panel li p { display: block; font-size: .83rem; }
.priority-panel li p { margin-top: 5px; }
.priority-panel li a { color: var(--primary, #166653); font-size: .85rem; font-weight: 700; white-space: nowrap; }
.priority-kind { background: #e7f3ea; border-radius: 999px; color: #1e603a; font-size: .72rem; font-weight: 750; padding: 5px 8px; }
.priority-kind.haute { background: #fff0d9; color: #985619; }
.empty-priority { padding-top: 12px; }
.decision-search {
  display: grid;
  gap: 8px;
  max-width: 460px;
  margin: 20px 0;
  font-size: 0.85rem;
}
.decision-search input {
  border: 1px solid var(--border, #cdd8d1);
  border-radius: 9px;
  padding: 12px;
  width: 100%;
}
.decision-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}
.decision-card {
  background: var(--surface, white);
  border: 1px solid var(--border, #dce3dd);
  border-radius: 14px;
  padding: 22px;
  margin-bottom: 16px;
  min-width: 0;
}
.decision-card h2 {
  font-size: 1.1rem;
  margin: 0 0 8px;
}
.decision-card p {
  line-height: 1.65;
}
.decision-card-head {
  display: flex;
  flex-wrap: wrap;
  align-items: start;
  gap: 10px;
  justify-content: space-between;
}
.quality-tag {
  padding: 5px 9px;
  background: #e8f4ed;
  color: #245b39;
  border-radius: 6px;
  font-size: 12px;
}
.quality-tag.insufficient {
  background: #fff2dd;
  color: #79501c;
}
.decision-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
  margin: 22px 0;
}
.decision-metrics dt {
  color: #5c6d63;
  font-size: 12px;
}
.decision-metrics dd {
  margin: 6px 0 0;
  font-size: 1.5rem;
  font-weight: 750;
}
.decision-metrics div:last-child {
  grid-column: 1/-1;
}
.decision-metrics div:last-child dd {
  font-size: 1.1rem;
}
.quality-reason {
  color: #79501c;
  font-size: 0.9rem;
}
.decision-table {
  overflow-x: auto;
  margin: 16px 0;
}
.decision-table table {
  width: 100%;
  border-collapse: collapse;
  white-space: nowrap;
}
.decision-table caption {
  text-align: left;
  margin-bottom: 10px;
  font-weight: 600;
}
.decision-table th,
.decision-table td {
  padding: 10px;
  border-bottom: 1px solid #e3e9e5;
  text-align: left;
}
@media (max-width: 900px) {
.decision-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .decision-grid {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 560px) { .decision-kpis { grid-template-columns: 1fr 1fr; } .priority-panel li { grid-template-columns: 1fr; } }
</style>
