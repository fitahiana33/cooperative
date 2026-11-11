<script setup lang="ts">
import { useBookingPolicy } from "../../composables/useBookingPolicy";
import { formatMoney } from "../../utils/money";
import SearchSelect from "../../components/ui/SearchSelect.vue";
import PaginationControls from "../../components/ui/PaginationControls.vue";
import PassengerStepper from "../../components/ui/PassengerStepper.vue";
import { validateTravelSearch } from "../../utils/travelSearch";
import PublicLayout from "../../components/layout/PublicLayout.vue";
import { computed, onMounted, reactive, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import { departService } from "../../services/depart/service";
import { publicCatalog } from "../../services/publicCatalog";
import type { PublicProgramme } from "../../models/depart/model";
import type { PublicDestination } from "../../models/destination/model";
import type {
  PublicGare,
  PublicGareCooperative,
} from "../../models/gare/model";
import { localIsoDate } from "../../utils/date";

const route = useRoute();
const router = useRouter();
const { policy, depositLabel } = useBookingPolicy();
const today = localIsoDate();
const loading = ref(true);
const error = ref("");
const destinations = ref<PublicDestination[]>([]);
const gares = ref<PublicGare[]>([]);
const programme = ref<PublicProgramme[]>([]);
const total = ref(0);
const page = ref(1);
const pages = ref(1);
const validationError = ref("");
const referenceError = ref("");
let requestId = 0;
const sortBy = ref<"time" | "price" | "availability">("time");
const sortOrder = ref<"asc" | "desc">("asc");
const filters = reactive({
  from: value("from"),
  to: value("to"),
  date: value("date", today),
  dateTo: value("dateTo"),
  passengers: value("passengers", "1"),
  gare: value("gare"),
  cooperative: value("cooperative"),
  search: value("search"),
});

function value(name: string, fallback = "") {
  const item = route.query[name];
  return typeof item === "string" ? item : fallback;
}
const cooperativeOptions = computed<PublicGareCooperative[]>(() => {
  const source = filters.gare
    ? gares.value.filter((item) => item.id === Number(filters.gare))
    : gares.value;
  const map = new Map<number, PublicGareCooperative>();
  source
    .flatMap((item) => item.cooperatives)
    .forEach((item) => map.set(item.id, item));
  return [...map.values()].sort((a, b) => a.nom.localeCompare(b.nom));
});
const passengerMax = computed(() =>
  Math.min(10, Math.max(1, policy.value?.max_seats || 10)),
);
const sortedProgramme = computed(() =>
  [...programme.value].sort((left, right) => {
    const comparison =
      sortBy.value === "price"
        ? (left.tarif ? Number(left.tarif.prix) : Infinity) -
          (right.tarif ? Number(right.tarif.prix) : Infinity)
        : sortBy.value === "availability"
          ? left.places_disponibles - right.places_disponibles
          : `${left.date_depart}T${left.heure_depart}`.localeCompare(
              `${right.date_depart}T${right.heure_depart}`,
            );
    return sortOrder.value === "asc" ? comparison : -comparison;
  }),
);
function displayDate(value: string) {
  return new Intl.DateTimeFormat("fr-FR", {
    weekday: "long",
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(new Date(`${value}T00:00:00`));
}
function displayPrice(item: PublicProgramme) {
  return item.tarif
    ? formatMoney(item.tarif.prix, item.tarif.devise)
    : "Tarif à confirmer";
}
function query() {
  return {
    from: filters.from || undefined,
    to: filters.to || undefined,
    date: filters.date || undefined,
    dateTo: filters.dateTo || undefined,
    passengers: filters.passengers,
    gare: filters.gare || undefined,
    cooperative: filters.cooperative || undefined,
    search: filters.search || undefined,
  };
}
function swapLocations() {
  const from = filters.from;
  filters.from = filters.to;
  filters.to = from;
}
function reserve(item: PublicProgramme) {
  void router.push({
    name: "public-booking",
    query: { depart_id: String(item.id), passengers: filters.passengers },
  });
}
function reset() {
  filters.from = "";
  filters.to = "";
  filters.date = today;
  filters.dateTo = "";
  filters.passengers = "1";
  filters.gare = "";
  filters.cooperative = "";
  filters.search = "";
  void search();
}
async function loadReferences() {
  referenceError.value = "";
  try {
    const catalog = await publicCatalog();
    destinations.value = catalog.destinations;
    gares.value = catalog.gares;
  } catch {
    referenceError.value =
      "Les villes et les gares ne peuvent pas être chargées. Réessayez.";
  }
}
async function loadProgramme() {
  const currentRequest = ++requestId;
  loading.value = true;
  error.value = "";
  try {
    const result = await departService.publicProgramme({
      page: page.value,
      page_size: 10,
      search: filters.search || undefined,
      date_from: filters.date || undefined,
      date_to: filters.dateTo || undefined,
      id_destination_depart: filters.from ? Number(filters.from) : undefined,
      id_destination_arrivee: filters.to ? Number(filters.to) : undefined,
      id_gare: filters.gare ? Number(filters.gare) : undefined,
      id_cooperative: filters.cooperative
        ? Number(filters.cooperative)
        : undefined,
      passagers: Number(filters.passengers),
    });
    if (currentRequest !== requestId) return;
    programme.value = result.items || [];
    total.value = result.total || 0;
    pages.value = result.pages || 1;
  } catch (value) {
    if (currentRequest !== requestId) return;
    if (import.meta.env.DEV) console.error("[PUBLIC_RESULTS_ERROR]", value);
    error.value = "Les départs ne sont pas disponibles pour le moment.";
  } finally {
    if (currentRequest === requestId) loading.value = false;
  }
}
async function search() {
  validationError.value = validateTravelSearch(filters);
  if (validationError.value) return;
  page.value = 1;
  const previous = route.fullPath;
  await router.replace({ name: "search-results", query: query() });
  if (route.fullPath === previous) await loadProgramme();
}
async function changePage(next: number) {
  page.value = next;
  await loadProgramme();
  document.getElementById("results")?.scrollIntoView({ behavior: "smooth" });
}
watch(
  () => route.query,
  () => {
    Object.assign(filters, {
      from: value("from"),
      to: value("to"),
      date: value("date", today),
      dateTo: value("dateTo"),
      passengers: value("passengers", "1"),
      gare: value("gare"),
      cooperative: value("cooperative"),
      search: value("search"),
    });
    validationError.value = validateTravelSearch(filters);
    page.value = 1;
    if (!validationError.value) void loadProgramme();
  },
);
onMounted(async () => {
  await loadReferences();
  validationError.value = validateTravelSearch(filters);
  if (!validationError.value) await loadProgramme();
  else loading.value = false;
});
</script>

<template>
  <PublicLayout class="travel-results">
    <section class="results-hero">
      <div>
        <RouterLink class="results-back" to="/"
          >← Modifier la recherche</RouterLink
        >
        <p class="results-eyebrow">VOYAGES DISPONIBLES</p>
        <h1>Comparez les départs.</h1>
        <p>
          Les horaires, tarifs, gares, coopératives et places disponibles sont
          réunis dans chaque résultat.
        </p>
      </div>
    </section>
    <section class="results-query">
      <form @submit.prevent="search">
        <p v-if="referenceError" class="error-banner" role="alert">
          {{ referenceError }}
          <button type="button" class="text-button" @click="loadReferences">
            Réessayer
          </button>
        </p>
        <div class="query-heading">
          <strong>Modifier votre recherche</strong
          ><button class="swap-query" type="button" @click="swapLocations">
            ↕ Inverser le trajet
          </button>
        </div>
        <p v-if="validationError" class="error-banner" role="alert">
          {{ validationError }}
        </p>
        <div class="query-fields">
          <label
            ><span>Départ</span
            ><SearchSelect
              aria-label="Ville de départ"
              v-model="filters.from"
              :options="
                destinations.map((item) => ({
                  value: String(item.id),
                  label: `${item.nom}`,
                }))
              "
              placeholder="Toutes les villes" /></label
          ><label
            ><span>Destination</span
            ><SearchSelect
              aria-label="Ville d’arrivée"
              v-model="filters.to"
              :options="
                destinations.map((item) => ({
                  value: String(item.id),
                  label: `${item.nom}`,
                }))
              "
              placeholder="Toutes les villes" /></label
          ><label
            ><span>Date</span
            ><input v-model="filters.date" type="date" :min="today" /></label
          ><label
            ><span>Passagers</span
            ><PassengerStepper v-model="filters.passengers" :max="passengerMax" /></label
          ><button type="submit">Rechercher →</button>
        </div>
      </form>
    </section>
    <section id="results" class="results-body">
      <aside class="results-filters">
        <div>
          <p class="results-eyebrow">AFFINER</p>
          <h2>Votre recherche</h2>
        </div>
        <label
          >Gare<SearchSelect
            aria-label="Toutes les gares"
            v-model="filters.gare"
            @change="filters.cooperative = ''"
            :options="
              gares.map((item) => ({
                value: String(item.id),
                label: `${item.nom} · ${item.ville}`,
              }))
            "
            placeholder="Toutes les gares" /></label
        ><label
          >Coopérative<SearchSelect
            aria-label="Toutes les coopératives"
            v-model="filters.cooperative"
            :options="
              cooperativeOptions.map((item) => ({
                value: String(item.id),
                label: `${item.nom}`,
              }))
            "
            placeholder="Toutes les coopératives" /></label
        ><button class="filter-apply" type="button" @click="search">
          Appliquer les filtres</button
        ><button class="filter-reset" type="button" @click="reset">
          Réinitialiser
        </button>
        <div class="filter-note">
          <strong>Réservation sans compte</strong
          ><span
            >Vous pouvez réserver sans compte.
            {{
              depositLabel
                ? `Acompte minimum : ${depositLabel}.`
                : "Consultez l’acompte avant confirmation."
            }}</span
          >
        </div>
      </aside>
      <div class="results-list">
        <div class="results-heading">
          <div>
            <p class="results-eyebrow">RÉSULTATS</p>
            <h2>{{ total }} départ{{ total > 1 ? "s" : "" }}</h2>
          </div>
          <label class="sort-control"
            >Trier par<select v-model="sortBy">
              <option value="time">Horaire</option>
              <option value="price">Prix</option>
              <option value="availability">Disponibilité</option>
            </select></label
          ><button
            class="sort-order"
            type="button"
            @click="sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'"
          >
            {{ sortOrder === "asc" ? "↑" : "↓" }}
          </button>
        </div>
        <div v-if="loading" class="result-loading">
          <i v-for="item in 3" :key="item"></i>
        </div>
        <div v-else-if="error" class="result-empty" role="alert">
          <strong>{{ error }}</strong
          ><span>Modifiez vos critères puis relancez la recherche.</span
          ><button type="button" @click="reset">Réinitialiser</button>
        </div>
        <div v-else-if="!sortedProgramme.length" class="result-empty">
          <strong>Aucun départ ne correspond à votre recherche.</strong
          ><span
            >Essayez une autre date, une autre ville ou moins de
            passagers.</span
          ><button type="button" @click="reset">Voir tous les départs</button>
        </div>
        <div v-else class="result-cards">
          <article
            v-for="item in sortedProgramme"
            :key="item.id"
            class="result-offer"
          >
            <div class="result-time">
              <strong>{{ item.heure_depart?.slice(0, 5) }}</strong
              ><span>{{ displayDate(item.date_depart) }}</span>
            </div>
            <div class="result-trip">
              <div>
                <strong>{{
                  item.itineraire?.destination_depart?.nom || "Départ"
                }}</strong
                ><small>Ville de départ</small>
              </div>
              <b>→</b>
              <div>
                <strong>{{
                  item.itineraire?.destination_arrivee?.nom || "Destination"
                }}</strong
                ><small>Destination</small>
              </div>
            </div>
            <div class="result-details">
              <span
                ><small>Gare</small
                ><strong>{{ item.gare?.nom || "À confirmer" }}</strong></span
              ><span
                ><small>Coopérative</small
                ><strong>{{
                  item.cooperative?.nom || "À confirmer"
                }}</strong></span
              ><span
                ><small>Places</small
                ><strong
                  >{{ item.places_disponibles }} disponible{{
                    item.places_disponibles > 1 ? "s" : ""
                  }}</strong
                ></span
              >
            </div>
            <div class="result-price">
              <small>Tarif par place</small
              ><strong>{{ displayPrice(item) }}</strong
              ><button type="button" @click="reserve(item)">
                Voir et réserver →
              </button>
            </div>
          </article>
        </div>
        <PaginationControls
          :page="page"
          :pages="pages"
          :total="total"
          :loading="loading"
          item-label="départ(s)"
          @change="changePage"
        />
        <p v-if="pages > 1" class="pagination-note">
          Le tri s’applique aux départs de la page affichée.
        </p>
      </div>
    </section>
    <section id="help" class="results-help">
      <strong>Besoin d’aide ?</strong
      ><span
        >Les moyens de paiement disponibles sont indiqués après la réservation.
        Le billet est disponible lorsque le paiement est confirmé.</span
      ><RouterLink to="/conditions-voyage">Conditions de voyage →</RouterLink>
    </section>
  </PublicLayout>
</template>
