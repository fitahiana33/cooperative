<script setup lang="ts">
import { useBookingPolicy } from "../../composables/useBookingPolicy";
import { formatMoney } from "../../utils/money";
import SearchSelect from "../../components/ui/SearchSelect.vue";
import PageTabs from "../../components/ui/PageTabs.vue";
import PageTabPanel from "../../components/ui/PageTabPanel.vue";
import AppIcon from "../../components/ui/AppIcon.vue";
import PassengerStepper from "../../components/ui/PassengerStepper.vue";
import PublicLayout from "../../components/layout/PublicLayout.vue";
import { computed, onMounted, reactive, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { departService } from "../../services/depart/service";
import { publicCatalog } from "../../services/publicCatalog";
import type { PublicProgramme } from "../../models/depart/model";
import type { PublicDestination } from "../../models/destination/model";
import type {
  PublicGare,
  PublicGareCooperative,
} from "../../models/gare/model";
import { validateTravelSearch } from "../../utils/travelSearch";
import { localIsoDate } from "../../utils/date";

const router = useRouter();
const { policy, depositLabel } = useBookingPolicy();
const today = localIsoDate();
const discoverTab = ref("destinations");
const discoverTabs = [
  { id: "destinations", label: "Destinations" },
  { id: "stations", label: "Gares de départ" },
];
let programmeRequest = 0;
const loading = ref(false);
const loadingReferences = ref(false);
const referenceError = ref("");
const error = ref("");
const programme = ref<PublicProgramme[]>([]);
const destinations = ref<PublicDestination[]>([]);
const gares = ref<PublicGare[]>([]);
const total = ref(0);
const filters = reactive({
  from: "",
  to: "",
  date: today,
  dateTo: "",
  gare: "",
  cooperative: "",
  passengers: "1",
  search: "",
});
const searchErrors = reactive({ from: "", to: "", date: "", passengers: "" });

const cooperativeOptions = computed<PublicGareCooperative[]>(() => {
  const source = filters.gare
    ? gares.value.filter((item) => item.id === Number(filters.gare))
    : gares.value;
  const unique = new Map<number, PublicGareCooperative>();
  source
    .flatMap((item) => item.cooperatives)
    .forEach((item) => unique.set(item.id, item));
  return [...unique.values()].sort((left, right) =>
    left.nom.localeCompare(right.nom),
  );
});
const featuredDepartures = computed(() => programme.value.slice(0, 3));
const passengerMax = computed(() =>
  Math.min(10, Math.max(1, policy.value?.max_seats || 10)),
);
const tomorrow = computed(() => {
  const day = new Date();
  day.setDate(day.getDate() + 1);
  return localIsoDate(day);
});

function displayDate(value: string) {
  return new Intl.DateTimeFormat("fr-FR", {
    weekday: "short",
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(`${value}T00:00:00`));
}
function displayPrice(item: PublicProgramme) {
  return item.tarif
    ? formatMoney(item.tarif.prix, item.tarif.devise)
    : "Tarif à confirmer";
}
function statusLabel(status: PublicProgramme["statut"]) {
  return {
    PROGRAMME: "Programmé",
    EMBARQUEMENT: "Embarquement",
    RETARDE: "Retardé",
  }[status];
}
function statusClass(status: PublicProgramme["statut"]) {
  return status.toLowerCase();
}
function setDate(value: "today" | "tomorrow") {
  filters.date = value === "today" ? today : tomorrow.value;
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
function clearSearchErrors() {
  searchErrors.from = "";
  searchErrors.to = "";
  searchErrors.date = "";
  searchErrors.passengers = "";
}
function validateSearch() {
  clearSearchErrors();
  if (!filters.from) searchErrors.from = "Choisissez une ville de départ.";
  if (!filters.to) searchErrors.to = "Choisissez une destination.";
  if (!filters.date) searchErrors.date = "Choisissez une date de départ.";
  if (!filters.passengers || Number(filters.passengers) < 1)
    searchErrors.passengers = "Indiquez le nombre de passagers.";
  const message = validateTravelSearch(filters, true);
  if (message && !Object.values(searchErrors).some(Boolean))
    searchErrors.date = message;
  return !Object.values(searchErrors).some(Boolean);
}
function swapLocations() {
  const from = filters.from;
  filters.from = filters.to;
  filters.to = from;
  clearSearchErrors();
}
function submitSearch() {
  if (!validateSearch()) {
    document
      .getElementById("search")
      ?.scrollIntoView({ behavior: "smooth", block: "center" });
    return;
  }
  void router.push({ name: "search-results", query: query() });
}
function reserve(item: PublicProgramme) {
  void router.push({
    name: "public-booking",
    query: { depart_id: String(item.id), passengers: filters.passengers },
  });
}
function resetFilters() {
  filters.from = "";
  filters.to = "";
  filters.date = today;
  filters.dateTo = "";
  filters.gare = "";
  filters.cooperative = "";
  filters.passengers = "1";
  filters.search = "";
  clearSearchErrors();
  void loadProgramme();
}
function chooseDestination(id: number) {
  filters.to = String(id);
  void loadProgramme();
  document.getElementById("departures")?.scrollIntoView({ behavior: "smooth" });
}
function selectGare(id: number) {
  filters.gare = String(id);
  filters.cooperative = "";
  void loadProgramme();
  document.getElementById("departures")?.scrollIntoView({ behavior: "smooth" });
}

async function loadReferences() {
  loadingReferences.value = true;
  referenceError.value = "";
  try {
    const catalog = await publicCatalog();
    destinations.value = catalog.destinations;
    gares.value = catalog.gares;
  } catch (value) {
    if (import.meta.env.DEV) console.error("[PUBLIC_REFERENCES_ERROR]", value);
    referenceError.value =
      "Impossible de charger les villes et les gares. Réessayez dans quelques instants.";
  } finally {
    loadingReferences.value = false;
  }
}
async function loadProgramme() {
  const request = ++programmeRequest;
  loading.value = true;
  error.value = "";
  try {
    const result = await departService.publicProgramme({
      page: 1,
      page_size: 50,
      search: filters.search.trim() || undefined,
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
    if (request !== programmeRequest) return;
    programme.value = result.items || [];
    total.value = result.total || 0;
  } catch (value) {
    if (request !== programmeRequest) return;
    if (import.meta.env.DEV) console.error("[PUBLIC_PROGRAMME_ERROR]", value);
    error.value = "Le programme est momentanément indisponible.";
  } finally {
    if (request === programmeRequest) loading.value = false;
  }
}
onMounted(() => {
  void Promise.all([loadReferences(), loadProgramme()]);
});
</script>

<template>
  <PublicLayout class="travel-home">
    <section class="travel-hero">
      <img
        class="travel-hero-photograph"
        src="/images/madagascar-journey-hero.png"
        alt=""
        width="1672"
        height="941"
        fetchpriority="high"
      />
      <div class="travel-hero-inner">
        <div class="travel-hero-copy">
          <p class="travel-eyebrow">MADAGASCAR COMMENCE ICI</p>
          <h1>
            Votre prochaine escale.<br /><em>Le voyage en plus simple.</em>
          </h1>
          <p>
            Une destination, le bon départ, votre place à bord. Retrouvez les
            trajets des coopératives et préparez votre voyage en quelques
            étapes.
          </p>
          <div class="travel-hero-points">
            <span
              ><AppIcon name="check" :size="16" /> Choisissez vos places</span
            ><span
              ><AppIcon name="check" :size="16" /> Réservez sans compte</span
            >
          </div>
        </div>
        >
      </div>
    </section>

    <section id="search" class="search-panel">
      <div class="search-tabs">
        <span class="active">Voyages</span
        ><RouterLink to="/ma-reservation">Mes réservations</RouterLink
        ><span>Avec ou sans compte</span>
      </div>
      <form @submit.prevent="submitSearch" novalidate>
        <p v-if="referenceError" class="error-banner" role="alert">
          {{ referenceError }}
          <button type="button" class="text-button" @click="loadReferences">
            Réessayer
          </button>
        </p>
        <div class="search-panel-heading">
          <div>
            <p class="travel-eyebrow">RÉSERVER UN TRAJET</p>
            <h2>Où souhaitez-vous aller ?</h2>
            <button class="swap-locations" type="button" @click="swapLocations">
              ↕ Inverser le trajet
            </button>
          </div>
          <span>{{
            depositLabel
              ? `Acompte minimum de ${depositLabel}, selon le montant du voyage.`
              : "Les conditions d’acompte sont précisées avant confirmation."
          }}</span>
        </div>
        <div class="search-fields">
          <label :class="{ 'has-error': searchErrors.from }"
            ><span>Départ <b>*</b></span
            ><SearchSelect
              aria-label="Ville de départ"
              v-model="filters.from"
              :disabled="loadingReferences"
              required
              :aria-invalid="Boolean(searchErrors.from)"
              aria-describedby="search-from-error"
              :options="
                destinations.map((item) => ({
                  value: String(item.id),
                  label: `${item.nom}`,
                }))
              "
              placeholder="Choisir une ville"
            /><small
              v-if="searchErrors.from"
              id="search-from-error"
              class="field-error"
              >{{ searchErrors.from }}</small
            ></label
          ><label :class="{ 'has-error': searchErrors.to }"
            ><span>Destination <b>*</b></span
            ><SearchSelect
              aria-label="Ville d’arrivée"
              v-model="filters.to"
              :disabled="loadingReferences"
              required
              :aria-invalid="Boolean(searchErrors.to)"
              aria-describedby="search-to-error"
              :options="
                destinations.map((item) => ({
                  value: String(item.id),
                  label: `${item.nom}`,
                }))
              "
              placeholder="Choisir une ville"
            /><small
              v-if="searchErrors.to"
              id="search-to-error"
              class="field-error"
              >{{ searchErrors.to }}</small
            ></label
          ><label :class="{ 'has-error': searchErrors.date }"
            ><span>Date de départ <b>*</b></span
            ><input
              v-model="filters.date"
              type="date"
              :min="today"
              required
              :aria-invalid="Boolean(searchErrors.date)"
              aria-describedby="search-date-error"
            /><small
              v-if="searchErrors.date"
              id="search-date-error"
              class="field-error"
              >{{ searchErrors.date }}</small
            ></label
          ><label :class="{ 'has-error': searchErrors.passengers }"
            ><span>Passagers <b>*</b></span
            ><PassengerStepper
              v-model="filters.passengers"
              :max="passengerMax"
              :aria-invalid="Boolean(searchErrors.passengers)"
              aria-describedby="search-passengers-error"
            />
            ><small
              v-if="searchErrors.passengers"
              id="search-passengers-error"
              class="field-error"
              >{{ searchErrors.passengers }}</small
            ></label
          ><button class="search-submit" type="submit" :disabled="loading">
            {{ loading ? "Recherche…" : "Rechercher" }} <b>→</b>
          </button>
        </div>
        <div class="quick-dates">
          <span>Date rapide :</span
          ><button
            type="button"
            :class="{ active: filters.date === today }"
            @click="setDate('today')"
          >
            Aujourd’hui</button
          ><button
            type="button"
            :class="{ active: filters.date === tomorrow }"
            @click="setDate('tomorrow')"
          >
            Demain
          </button>
          <details>
            <summary>Plus de filtres</summary>
            <div class="secondary-fields">
              <label
                ><span>Gare</span
                ><SearchSelect
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
                ><span>Coopérative</span
                ><SearchSelect
                  aria-label="Toutes les coopératives"
                  v-model="filters.cooperative"
                  :options="
                    cooperativeOptions.map((item) => ({
                      value: String(item.id),
                      label: `${item.nom}`,
                    }))
                  "
                  placeholder="Toutes les coopératives" /></label
              ><label
                ><span>Jusqu’au</span
                ><input
                  v-model="filters.dateTo"
                  type="date"
                  :min="filters.date || today" /></label
              ><label
                ><span>Mot-clé</span
                ><input
                  v-model="filters.search"
                  type="search"
                  placeholder="Ville ou coopérative" /></label
              ><button type="button" class="reset-button" @click="resetFilters">
                Réinitialiser
              </button>
            </div>
          </details>
        </div>
      </form>
    </section>

    <section id="departures" class="home-section departures-section">
      <div class="section-heading">
        <div>
          <p class="travel-eyebrow">DÉPARTS DISPONIBLES</p>
          <h2>Les prochains voyages</h2>
          <p>
            Comparez l’horaire, la gare, la coopérative, le tarif et les places.
          </p>
        </div>
        <RouterLink
          class="outline-button"
          :to="{ name: 'search-results', query: query() }"
          >Voir tous les départs <b>→</b></RouterLink
        >
      </div>
      <p v-if="error" class="home-alert" role="alert">
        {{ error }}
        <button type="button" @click="loadProgramme">Réessayer</button>
      </p>
      <div v-else-if="loading" class="departure-list">
        <div v-for="item in 3" :key="item" class="departure-skeleton">
          <i></i><i></i><i></i>
        </div>
      </div>
      <div v-else-if="!featuredDepartures.length" class="empty-panel">
        <strong>Aucun départ disponible pour ces critères.</strong
        ><span>Essayez une autre date ou élargissez votre recherche.</span
        ><button type="button" class="outline-button" @click="resetFilters">
          Réinitialiser la recherche
        </button>
      </div>
      <div v-else class="departure-list">
        <article
          v-for="item in featuredDepartures"
          :key="item.id"
          class="departure-offer"
        >
          <div class="offer-time">
            <strong>{{ item.heure_depart?.slice(0, 5) }}</strong
            ><span>{{ displayDate(item.date_depart) }}</span>
          </div>
          <div class="offer-route">
            <div>
              <strong>{{
                item.itineraire?.destination_depart?.nom || "Départ"
              }}</strong
              ><span>Ville de départ</span>
            </div>
            <b>→</b>
            <div>
              <strong>{{
                item.itineraire?.destination_arrivee?.nom || "Destination"
              }}</strong
              ><span>Destination</span>
            </div>
          </div>
          <div class="offer-context">
            <span
              ><small>Gare</small
              ><strong>{{ item.gare?.nom || "À confirmer" }}</strong
              ><em v-if="item.gare?.ville">{{ item.gare.ville }}</em></span
            ><span
              ><small>Coopérative</small
              ><strong>{{ item.cooperative?.nom || "À confirmer" }}</strong
              ><em
                ><i class="status-dot" :class="statusClass(item.statut)"></i
                >{{ statusLabel(item.statut) }}</em
              ></span
            ><span
              ><small>Disponibilité</small
              ><strong
                >{{ item.places_disponibles }} place{{
                  item.places_disponibles > 1 ? "s" : ""
                }}</strong
              ><em>sur {{ item.nombre_places }} places</em></span
            >
          </div>
          <div class="offer-price">
            <small>Tarif</small><strong>{{ displayPrice(item) }}</strong
            ><button type="button" @click="reserve(item)">
              Choisir ce départ <b>→</b>
            </button>
          </div>
        </article>
      </div>
    </section>

    <div class="home-section discover-network">
      <div class="section-heading">
        <div>
          <p class="travel-eyebrow">LE PLAISIR DE PRENDRE LA ROUTE</p>
          <h2>Un réseau, de nouvelles découvertes.</h2>
          <p>Explorez les destinations et retrouvez votre gare de départ.</p>
        </div>
      </div>
      <PageTabs
        v-model="discoverTab"
        :tabs="discoverTabs"
        panel-prefix="discover"
        aria-label="Explorer le réseau"
      />
      <PageTabPanel
        prefix="discover"
        name="destinations"
        :active="discoverTab === 'destinations'"
      >
        <section
          id="destinations"
          class="destination-section"
          aria-label="Destinations desservies"
        >
          <div class="destination-grid">
            <button
              v-for="item in destinations.slice(0, 6)"
              :key="item.id"
              type="button"
              class="destination-tile"
              @click="chooseDestination(item.id)"
            >
              <span class="destination-art"
                ><AppIcon name="pin" :size="28" /></span
              ><strong>{{ item.nom }}</strong
              ><small>{{ item.region || "Madagascar" }}</small
              ><b>Voir les départs →</b>
            </button>
            <div v-if="!destinations.length" class="empty-panel">
              Les destinations seront bientôt disponibles.
            </div>
          </div>
        </section>
      </PageTabPanel>
      <PageTabPanel
        prefix="discover"
        name="stations"
        :active="discoverTab === 'stations'"
      >
        <section
          id="stations"
          class="stations-section"
          aria-label="Gares de départ"
        >
          <div class="station-grid">
            <button
              v-for="item in gares.slice(0, 6)"
              :key="item.id"
              type="button"
              class="station-tile"
              @click="selectGare(item.id)"
            >
              <span class="station-icon">⌖</span
              ><span
                ><strong>{{ item.nom }}</strong
                ><small
                  >{{ item.ville }} ·
                  {{ item.adresse || "Adresse à confirmer" }}</small
                ></span
              ><b
                >{{ item.cooperatives.length }} coopérative{{
                  item.cooperatives.length > 1 ? "s" : ""
                }}
                →</b
              >
            </button>
            <div v-if="!gares.length" class="empty-panel">
              Les gares seront bientôt disponibles.
            </div>
          </div>
        </section>
      </PageTabPanel>
    </div>

    <section id="guide" class="travel-guide">
      <div class="guide-inner">
        <div>
          <p class="travel-eyebrow">VOYAGER EN CONFIANCE</p>
          <h2>Tout ce qu’il faut savoir avant le départ.</h2>
          <p>
            Nous affichons uniquement les informations disponibles dans le
            programme de chaque coopérative.
          </p>
        </div>
        <div class="guide-grid">
          <article>
            <span>01</span><strong>Comparez les horaires</strong>
            <p>Date, heure, trajet et gare sont visibles avant de choisir.</p>
          </article>
          <article>
            <span>02</span><strong>Réservez sans compte</strong>
            <p>Renseignez votre nom et votre téléphone pour réserver.</p>
          </article>
          <article>
            <span>03</span><strong>Payez une avance</strong>
            <p>
              {{
                depositLabel
                  ? `Un acompte minimum de ${depositLabel} confirme vos places après validation du paiement.`
                  : "L’acompte est précisé avant la confirmation."
              }}
            </p>
          </article>
          <article>
            <span>04</span><strong>Gardez votre référence</strong>
            <p>Votre billet est accessible après confirmation du paiement.</p>
          </article>
        </div>
      </div>
    </section>
    <section id="aide" class="home-section faq-section">
      <div>
        <p class="travel-eyebrow">BESOIN D’AIDE ?</p>
        <h2>Un doute avant de partir ?</h2>
      </div>
      <div class="faq-list">
        <details>
          <summary>Faut-il créer un compte pour réserver ?</summary>
          <p>
            Non. Vous pouvez réserver directement sur le site. Un compte permet
            de retrouver son historique et ses billets.
          </p>
        </details>
        <details>
          <summary>Quand la réservation devient-elle valide ?</summary>
          <p>
            La réservation est en attente tant que l’avance n’est pas confirmée.
            Elle devient valide après la confirmation du paiement. Les moyens
            disponibles sont indiqués dans votre réservation.
          </p>
        </details>
        <details>
          <summary>Combien de temps avant le départ faut-il arriver ?</summary>
          <p>
            Consultez les informations indiquées par la gare ou la coopérative
            dans votre confirmation.
          </p>
        </details>
      </div>
    </section>
  </PublicLayout>
</template>
