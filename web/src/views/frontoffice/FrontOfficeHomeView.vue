<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthenticationStore } from '../../stores/authentication/store'
import { departService } from '../../services/depart/service'
import { destinationService } from '../../services/destination/service'
import { gareService } from '../../services/gare/service'
import type { PublicProgramme } from '../../models/depart/model'
import type { PublicDestination } from '../../models/destination/model'
import type { PublicGare, PublicGareCooperative } from '../../models/gare/model'
import { localIsoDate } from '../../utils/date'

const document = globalThis.document
document.title = 'Voyagez avec Coopérative'

const router = useRouter()
const auth = useAuthenticationStore()
const today = localIsoDate()
const loading = ref(false)
const loadingDestinations = ref(false)
const loadingGares = ref(false)
const mobileMenuOpen = ref(false)
const error = ref('')
const programme = ref<PublicProgramme[]>([])
const destinations = ref<PublicDestination[]>([])
const gares = ref<PublicGare[]>([])
const total = ref(0)
const filters = reactive({ search: '', date_from: today, date_to: '', id_destination_depart: '', id_destination_arrivee: '', id_gare: '', id_cooperative: '', passagers: '1' })
const hasResults = computed(() => programme.value.length > 0)
const cooperativeOptions = computed<PublicGareCooperative[]>(() => {
  const source = filters.id_gare ? gares.value.filter((item) => item.id === Number(filters.id_gare)) : gares.value
  const unique = new Map<number, PublicGareCooperative>()
  source.flatMap((item) => item.cooperatives).forEach((item) => unique.set(item.id, item))
  return [...unique.values()].sort((left, right) => left.nom.localeCompare(right.nom))
})

function displayDate(value: string) {
  return new Intl.DateTimeFormat('fr-FR', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(`${value}T00:00:00`))
}
function displayPrice(item: PublicProgramme) {
  if (!item.tarif) return 'Tarif à confirmer'
  return `${Number(item.tarif.prix).toLocaleString('fr-FR')} ${item.tarif.devise}`
}
function statusLabel(status: PublicProgramme['statut']) {
  return { PROGRAMME: 'Programmé', EMBARQUEMENT: 'Embarquement', RETARDE: 'Retardé' }[status]
}
function statusClass(status: PublicProgramme['statut']) { return status.toLowerCase() }

async function loadDestinations() {
  loadingDestinations.value = true
  try {
    const result = await destinationService.publicList({ page: 1, page_size: 200 })
    destinations.value = result.items || []
  } catch (value) {
    console.error('[PUBLIC_DESTINATIONS_ERROR]', value)
  } finally { loadingDestinations.value = false }
}

async function loadGares() {
  loadingGares.value = true
  try {
    const result = await gareService.publicList({ page: 1, page_size: 100 })
    gares.value = result.items || []
  } catch (value) {
    console.error('[PUBLIC_GARES_ERROR]', value)
  } finally { loadingGares.value = false }
}

async function loadProgramme() {
  loading.value = true
  error.value = ''
  try {
    const result = await departService.publicProgramme({
      page: 1,
      page_size: 50,
      search: filters.search.trim() || undefined,
      date_from: filters.date_from || undefined,
      date_to: filters.date_to || undefined,
      id_destination_depart: filters.id_destination_depart ? Number(filters.id_destination_depart) : undefined,
      id_destination_arrivee: filters.id_destination_arrivee ? Number(filters.id_destination_arrivee) : undefined,
      id_gare: filters.id_gare ? Number(filters.id_gare) : undefined,
      id_cooperative: filters.id_cooperative ? Number(filters.id_cooperative) : undefined,
      passagers: Number(filters.passagers),
    })
    programme.value = result.items || []
    total.value = result.total || 0
  } catch (value: unknown) {
    console.error('[PUBLIC_PROGRAMME_ERROR]', value)
    error.value = 'Le programme est momentanément indisponible. Réessayez dans quelques instants.'
  } finally { loading.value = false }
}

function resetFilters() {
  filters.search = ''
  filters.date_from = today
  filters.date_to = ''
  filters.id_destination_depart = ''
  filters.id_destination_arrivee = ''
  filters.id_gare = ''
  filters.id_cooperative = ''
  filters.passagers = '1'
  void loadProgramme()
}

function selectGare(id: number) {
  filters.id_gare = String(id)
  filters.id_cooperative = ''
  void loadProgramme()
  document.getElementById('programme')?.scrollIntoView({ behavior: 'smooth' })
}

function submitSearch() {
  void router.push({ name: 'search-results', query: {
    from: filters.id_destination_depart || undefined,
    to: filters.id_destination_arrivee || undefined,
    date: filters.date_from || undefined,
    passengers: filters.passagers,
    gare: filters.id_gare || undefined,
    cooperative: filters.id_cooperative || undefined,
  } })
}

function reserve(item: PublicProgramme) {
  void router.push({ name: 'public-booking', query: { depart_id: String(item.id) } })
}

function goToBackoffice() { void router.push({ name: auth.user?.role?.toLowerCase() === 'passenger' ? 'client-space' : 'home' }) }
onMounted(() => { void Promise.all([loadDestinations(), loadGares(), loadProgramme()]) })
</script>

<template>
  <main class="frontoffice-page">
    <header class="front-header">
      <router-link class="front-brand" to="/" aria-label="Accueil Coopérative"><span class="front-brand-mark">C</span><span>Coopérative</span></router-link>
      <nav class="front-nav" aria-label="Navigation publique"><a href="#programme">Réserver un voyage</a><a href="#gares">Gares et coopératives</a><a href="#destinations">Destinations</a><a href="#services">Nos services</a><a href="#aide">Aide</a></nav>
      <div class="front-actions">
        <button class="mobile-menu-toggle" type="button" :aria-label="mobileMenuOpen ? 'Fermer le menu' : 'Ouvrir le menu'" :aria-expanded="mobileMenuOpen" @click="mobileMenuOpen = !mobileMenuOpen">☰</button>
        <button v-if="auth.isAuthenticated" class="front-link-button" type="button" @click="goToBackoffice">Mon espace</button>
        <router-link v-else class="front-link-button" to="/login">Connexion</router-link>
        <router-link v-if="!auth.isAuthenticated" class="front-primary-button small" to="/register">Créer un compte</router-link>
      </div>
    </header>
    <nav v-if="mobileMenuOpen" class="mobile-front-nav" aria-label="Menu mobile"><a href="#programme" @click="mobileMenuOpen = false">Rechercher un voyage</a><a href="#gares" @click="mobileMenuOpen = false">Gares et coopératives</a><a href="#destinations" @click="mobileMenuOpen = false">Destinations</a><a href="#aide" @click="mobileMenuOpen = false">Aide</a></nav>

    <section class="front-hero">
      <div class="hero-copy"><p class="front-eyebrow">LE VOYAGE COMMENCE ICI</p><h1>Voyagez plus simplement à travers Madagascar.</h1><p class="hero-text">Consultez les départs des coopératives, trouvez votre itinéraire et préparez votre réservation en quelques clics.</p><div class="hero-points"><span>✓ Programme consultable</span><span>✓ Places affichées selon les disponibilités</span><span>✓ Réservation sécurisée</span></div></div>
      <div class="hero-illustration" aria-hidden="true"><div class="sun"></div><div class="road"></div><div class="bus">▰</div><span class="mountain mountain-one"></span><span class="mountain mountain-two"></span></div>
    </section>

    <section id="programme" class="search-section">
      <form class="trip-search" @submit.prevent="submitSearch">
        <div class="search-heading"><div><p class="front-eyebrow">TROUVER UN DÉPART</p><h2>Où souhaitez-vous aller ?</h2></div><span class="search-note">Consultation et réservation libres · acompte obligatoire</span></div>
        <div class="search-fields">
          <label><span>Départ</span><select v-model="filters.id_destination_depart" :disabled="loadingDestinations"><option value="">Toutes les villes</option><option v-for="item in destinations" :key="`from-${item.id}`" :value="String(item.id)">{{ item.nom }}</option></select></label>
          <label><span>Destination</span><select v-model="filters.id_destination_arrivee" :disabled="loadingDestinations"><option value="">Toutes les villes</option><option v-for="item in destinations" :key="`to-${item.id}`" :value="String(item.id)">{{ item.nom }}</option></select></label>
          <label><span>Nombre de passagers</span><select v-model="filters.passagers"><option v-for="count in 8" :key="count" :value="String(count)">{{ count }} {{ count === 1 ? 'passager' : 'passagers' }}</option></select></label>
          <label><span>Date du voyage</span><input v-model="filters.date_from" type="date" :min="today" /></label>
          <button class="front-primary-button" type="submit" :disabled="loading">{{ loading ? 'Recherche…' : 'Rechercher' }} <span>→</span></button>
        </div>
        <details class="advanced-search"><summary>Ajouter des filtres : gare, coopérative et options</summary><div><label><span>Gare de départ</span><select v-model="filters.id_gare" :disabled="loadingGares" @change="filters.id_cooperative = ''"><option value="">Toutes les gares</option><option v-for="item in gares" :key="item.id" :value="String(item.id)">{{ item.nom }} · {{ item.ville }}</option></select></label><label><span>Coopérative</span><select v-model="filters.id_cooperative" :disabled="loadingGares"><option value="">Toutes les coopératives</option><option v-for="item in cooperativeOptions" :key="item.id" :value="String(item.id)">{{ item.nom }}</option></select></label><label><span>Jusqu'au</span><input v-model="filters.date_to" type="date" :min="filters.date_from || today" /></label><label><span>Mot-clé</span><input v-model="filters.search" type="search" placeholder="Ville ou coopérative" /></label><button type="button" class="clear-button" @click="resetFilters">Réinitialiser</button></div></details>
      </form>
    </section>

    <section class="content-section programme-section">
      <div class="section-heading"><div><p class="front-eyebrow">DÉPARTS À VENIR</p><h2>Les prochains voyages</h2><p class="section-subtitle">Comparez les horaires, les tarifs et les places disponibles avant de réserver.</p></div><span v-if="total" class="result-count">{{ total }} départ(s)</span></div>
      <p v-if="error" class="front-error" role="alert">{{ error }}</p>
      <div v-else-if="loading" class="programme-state">Chargement du programme…</div>
      <div v-else-if="!hasResults" class="programme-state"><strong>Aucun départ trouvé</strong><span>Essayez une autre date ou une autre destination.</span><button type="button" class="clear-button" @click="resetFilters">Réinitialiser la recherche</button></div>
      <div v-else class="programme-grid">
        <article v-for="item in programme" :key="item.id" class="departure-card">
          <div class="departure-station" v-if="item.gare">{{ item.gare.nom }} · {{ item.gare.ville }}</div>
          <div class="departure-card-top"><span class="status-pill" :class="statusClass(item.statut)">{{ statusLabel(item.statut) }}</span><span class="departure-company">{{ item.cooperative?.nom || 'Coopérative' }}</span></div>
          <div class="route-line"><div><strong>{{ item.itineraire?.destination_depart?.nom || 'Départ' }}</strong><span>{{ displayDate(item.date_depart) }}</span></div><span class="route-arrow">→</span><div class="route-arrival"><strong>{{ item.itineraire?.destination_arrivee?.nom || 'Arrivée' }}</strong><span>{{ item.heure_depart.slice(0, 5) }}</span></div></div>
          <div class="departure-meta"><span><small>Tarif</small><strong>{{ displayPrice(item) }}</strong></span><span><small>Places disponibles</small><strong>{{ item.places_disponibles }} / {{ item.nombre_places }}</strong></span><span><small>Véhicule</small><strong>{{ item.vehicule?.nombre_places || item.nombre_places }} places</strong></span></div>
          <button class="reserve-button" type="button" @click="reserve(item)">Voir et réserver <span>→</span></button>
        </article>
      </div>
    </section>

    <section id="destinations" class="content-section destination-section"><div class="section-heading"><div><p class="front-eyebrow">NOS DESTINATIONS</p><h2>Partez depuis votre ville</h2><p class="section-subtitle">Les destinations sont alimentées par les itinéraires actifs de la gare.</p></div></div><div class="destination-grid"><button v-for="item in destinations.slice(0, 6)" :key="item.id" type="button" class="destination-card" @click="filters.id_destination_arrivee = String(item.id); document.getElementById('programme')?.scrollIntoView({ behavior: 'smooth' }); void loadProgramme()"><span class="destination-icon">⌖</span><strong>{{ item.nom }}</strong><small>{{ item.region || 'Madagascar' }}</small><span>Voir les départs →</span></button><div v-if="!destinations.length" class="programme-state">Les destinations seront bientôt disponibles.</div></div></section>

    <section id="gares" class="content-section station-section"><div class="section-heading"><div><p class="front-eyebrow">GARES ET COOPÉRATIVES</p><h2>Choisissez votre point de départ</h2><p class="section-subtitle">Consultez les gares actives et les coopératives présentes avant de choisir un départ.</p></div></div><div class="destination-grid station-grid"><button v-for="item in gares" :key="item.id" type="button" class="destination-card" @click="selectGare(item.id)"><span class="destination-icon">⌖</span><strong>{{ item.nom }}</strong><small>{{ item.ville }} · {{ item.adresse }}</small><span>{{ item.cooperatives.length }} coopérative(s) · Voir les départs →</span></button><div v-if="!gares.length" class="programme-state">Les gares seront bientôt disponibles.</div></div></section>

    <section id="services" class="content-section service-section"><div><p class="front-eyebrow">NOS SERVICES</p><h2>Un parcours simple pour chaque passager.</h2></div><div class="service-grid"><article><span>01</span><strong>Rechercher un voyage</strong><p>Filtrez par ville de départ, destination et date.</p></article><article><span>02</span><strong>Choisir sa place</strong><p>Sélectionnez vos places directement, sans créer de compte.</p></article><article><span>03</span><strong>Payer une avance</strong><p>La réservation devient valide après le paiement de l’avance minimale.</p></article></div></section>

    <section id="aide" class="content-section help-section"><div><p class="front-eyebrow">BESOIN D'AIDE ?</p><h2>Les réponses aux questions courantes.</h2><p class="section-subtitle">Les règles affichées restent celles de la gare et des coopératives.</p></div><div class="faq-list"><details><summary>Dois-je créer un compte pour consulter les départs ?</summary><p>Non. Le programme est consultable librement, comme la réservation. Un compte permet seulement de retrouver votre historique personnel.</p></details><details><summary>Comment réserver une place ?</summary><p>Choisissez un départ, sélectionnez une ou plusieurs places, renseignez le nom du réservataire puis payez l'avance demandée. Le compte n'est pas obligatoire.</p></details><details><summary>Où retrouver mon billet et mon QR Code ?</summary><p>Après confirmation du paiement, le billet est accessible dans votre espace si vous êtes connecté. Sans compte, conservez votre numéro de réservation et le lien de suivi.</p></details></div></section>

    <section class="contact-strip"><div><p class="front-eyebrow">UNE QUESTION ?</p><h2>La gare et les coopératives restent à votre écoute.</h2></div><div class="contact-items"><span>✉ Contactez la gare</span><span>⌖ Consultez les informations du voyage</span></div></section>
    <footer class="front-footer"><span>© 2026 Coopérative · Plateforme de réservation de taxi-brousse</span><nav><a href="#programme">Programme</a><a href="#services">Services</a><a href="#aide">Aide</a><router-link to="/conditions-voyage">Conditions</router-link><router-link to="/annulation">Annulation</router-link><router-link to="/confidentialite">Confidentialité</router-link></nav></footer>
  </main>
</template>

<style scoped>
.frontoffice-page { min-height: 100vh; color: #17233f; background: #f8fbff; }
.front-header { display: flex; align-items: center; gap: 2rem; max-width: 1220px; margin: auto; padding: 1.2rem 1.5rem; }.front-brand { display: inline-flex; align-items: center; gap: .65rem; color: #17233f; font: 800 1.15rem Manrope, sans-serif; text-decoration: none; }.front-brand-mark { display: grid; place-items: center; width: 2.25rem; height: 2.25rem; border-radius: .7rem; color: white; background: #4268dc; box-shadow: 0 8px 18px #4268dc35; }.front-nav { display: flex; gap: 1.2rem; margin-left: auto; }.front-nav a, .front-link-button { color: #63708c; font-size: .78rem; font-weight: 700; text-decoration: none; background: transparent; }.front-nav a:hover, .front-link-button:hover { color: #4268dc; }.front-actions { display: flex; align-items: center; gap: .8rem; }
.front-primary-button, .reserve-button { border-radius: .65rem; color: white; background: #4268dc; font-weight: 700; box-shadow: 0 8px 16px #4268dc2b; }.front-primary-button { min-height: 44px; padding: 0 1.25rem; }.front-primary-button.small { display: inline-flex; align-items: center; min-height: 38px; font-size: .8rem; text-decoration: none; }.front-primary-button:disabled { opacity: .6; cursor: wait; }
.front-hero { display: flex; justify-content: space-between; align-items: center; gap: 2rem; max-width: 1220px; min-height: 430px; margin: 0 auto; padding: 4.5rem 1.5rem 6.5rem; }.hero-copy { position: relative; z-index: 1; max-width: 650px; }.front-eyebrow { margin: 0 0 .7rem; color: #5573d4; font-size: .7rem; font-weight: 800; letter-spacing: .16em; }h1, h2 { margin: 0; font-family: Manrope, sans-serif; letter-spacing: -.055em; }h1 { max-width: 650px; font-size: clamp(2.5rem, 5.5vw, 4.5rem); line-height: 1.04; }.hero-text { max-width: 560px; margin: 1.4rem 0; color: #67748f; font-size: 1.05rem; line-height: 1.7; }.hero-points { display: flex; flex-wrap: wrap; gap: 1rem; color: #4d6090; font-size: .78rem; font-weight: 700; }.hero-illustration { position: relative; width: 370px; height: 250px; overflow: hidden; border-radius: 1.6rem; background: linear-gradient(160deg, #dce9ff, #fdf7e9); box-shadow: 0 22px 50px #37558e1c; }.sun { position: absolute; top: 2.3rem; right: 3rem; width: 4rem; height: 4rem; border-radius: 50%; background: #f5bd6c; box-shadow: 0 0 0 1.2rem #f5bd6c22; }.mountain { position: absolute; bottom: 4rem; width: 0; height: 0; border-right: 130px solid transparent; border-bottom: 135px solid #9bb6c6; border-left: 130px solid transparent; }.mountain-one { left: 1rem; }.mountain-two { right: -2rem; border-bottom-color: #789caf; }.road { position: absolute; right: -30px; bottom: -70px; left: -30px; height: 150px; transform: rotate(-4deg); background: #718398; }.bus { position: absolute; bottom: 3.9rem; left: 8rem; display: grid; place-items: center; width: 7.5rem; height: 3.8rem; border: .35rem solid #23395d; border-radius: 1rem .9rem .5rem .5rem; color: #f4bc69; background: #4268dc; font-size: 2.4rem; box-shadow: 0 .5rem 0 #23395d; }
.search-section { position: relative; z-index: 2; max-width: 1120px; margin: -3.8rem auto 0; padding: 0 1.5rem; }.trip-search { padding: 1.4rem; border: 1px solid #e0e9f8; border-radius: 1rem; background: white; box-shadow: 0 18px 40px #334e8018; }.search-heading, .section-heading { display: flex; align-items: end; justify-content: space-between; gap: 1rem; }.search-heading h2, .section-heading h2, .service-section h2, .help-section h2 { font-size: 2rem; }.search-note, .section-subtitle { color: #75819a; font-size: .75rem; }.search-fields { display: grid; grid-template-columns: 1fr 1fr 1fr auto; align-items: end; gap: .7rem; margin-top: 1.2rem; }.search-fields label, .advanced-search label { margin: 0; }.search-fields label span, .advanced-search label span { display: block; margin-bottom: .4rem; color: #64708a; font-size: .7rem; font-weight: 700; }.search-fields select, .search-fields input, .advanced-search input { width: 100%; min-height: 42px; padding: 0 .75rem; border: 1px solid #dfe7f2; border-radius: .6rem; color: #17233f; background: #fbfdff; font: inherit; }.advanced-search { margin-top: 1rem; color: #5573d4; font-size: .75rem; font-weight: 700; }.advanced-search summary { cursor: pointer; }.advanced-search > div { display: flex; align-items: end; gap: .7rem; margin-top: .8rem; }.clear-button { min-height: 38px; padding: 0 .8rem; border: 1px solid #dfe7f2; border-radius: .6rem; color: #5573d4; background: white; font-weight: 700; }.content-section { max-width: 1180px; margin: auto; padding: 5rem 1.5rem 1rem; }.programme-section { padding-top: 5.5rem; }.result-count { color: #5573d4; font-size: .8rem; font-weight: 700; }.front-error { margin-top: 2rem; padding: .8rem 1rem; border-radius: .6rem; color: #a33a35; background: #fff2f0; }.programme-state { display: grid; min-height: 180px; place-items: center; gap: .5rem; margin-top: 2rem; border: 1px dashed #cfdaeb; border-radius: .9rem; color: #7c89a1; background: white; text-align: center; }.programme-state strong { color: #3f4e6d; }.programme-state .clear-button { margin-top: .3rem; }
.programme-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; margin-top: 2rem; }.departure-card { padding: 1.25rem; border: 1px solid #e0e9f8; border-radius: .9rem; background: white; box-shadow: 0 8px 25px #334e8010; }.departure-card-top, .route-line, .departure-meta { display: flex; justify-content: space-between; align-items: center; gap: .75rem; }.departure-company { color: #7a87a0; font-size: .75rem; }.status-pill { padding: .35rem .55rem; border-radius: 99px; font-size: .68rem; font-weight: 800; }.status-pill.programme { color: #256b4d; background: #e8f8ef; }.status-pill.embarquement { color: #9a6617; background: #fff5d9; }.status-pill.retarde { color: #a4483d; background: #fff0ee; }.route-line { justify-content: center; margin: 1.5rem 0; text-align: center; }.route-line div { display: grid; gap: .3rem; min-width: 110px; }.route-line strong { font: 800 1.1rem Manrope, sans-serif; }.route-line span:not(.route-arrow) { color: #7c89a1; font-size: .75rem; }.route-arrow { color: #5573d4; font-size: 1.4rem; }.route-arrival { text-align: left; }.departure-meta { padding: .9rem 0; border-top: 1px solid #edf1f7; }.departure-meta span { display: grid; gap: .3rem; }.departure-meta small { color: #8994a8; font-size: .7rem; }.departure-meta strong { color: #344466; font-size: .78rem; }.reserve-button { width: 100%; min-height: 40px; margin-top: .8rem; }.reserve-button span { margin-left: .4rem; }
.destination-section { padding-top: 5rem; }.destination-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 2rem; }.destination-card { display: grid; gap: .35rem; padding: 1.2rem; border: 1px solid #e0e9f8; border-radius: .85rem; color: #17233f; background: white; text-align: left; transition: transform .2s, box-shadow .2s; }.destination-card:hover { transform: translateY(-3px); box-shadow: 0 12px 25px #334e8014; }.destination-icon { color: #5573d4; font-size: 1.4rem; }.destination-card strong { font: 800 1rem Manrope, sans-serif; }.destination-card small, .destination-card span:last-child { color: #7c89a1; font-size: .75rem; }.destination-card span:last-child { margin-top: .7rem; color: #5573d4; font-weight: 700; }.service-section { display: grid; grid-template-columns: .65fr 1.35fr; gap: 2rem; padding-top: 6rem; }.service-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }.service-grid article { padding: 1rem; border-left: 2px solid #5573d4; }.service-grid span { color: #5573d4; font-size: .75rem; font-weight: 800; }.service-grid strong { display: block; margin: .7rem 0 .4rem; font: 800 1rem Manrope, sans-serif; }.service-grid p { margin: 0; color: #75819a; font-size: .8rem; line-height: 1.5; }.help-section { display: grid; grid-template-columns: .8fr 1.2fr; gap: 2rem; padding-top: 6rem; }.faq-list { display: grid; gap: .7rem; }.faq-list details { padding: 1rem; border: 1px solid #e0e9f8; border-radius: .7rem; background: white; }.faq-list summary { cursor: pointer; color: #344466; font-weight: 700; }.faq-list p { margin: .8rem 0 0; color: #75819a; font-size: .82rem; line-height: 1.6; }.contact-strip { display: flex; justify-content: space-between; align-items: center; gap: 2rem; max-width: 1180px; margin: 5rem auto 0; padding: 2.3rem 1.5rem; border-top: 1px solid #dfe8f5; border-bottom: 1px solid #dfe8f5; }.contact-strip h2 { max-width: 530px; font-size: 1.65rem; }.contact-items { display: grid; gap: .8rem; color: #5573d4; font-size: .82rem; font-weight: 700; }.front-footer { display: flex; justify-content: space-between; gap: 1rem; max-width: 1180px; margin: auto; padding: 2rem 1.5rem; color: #8a96aa; font-size: .75rem; }.front-footer nav { display: flex; gap: 1rem; }.front-footer a { color: #71809b; text-decoration: none; }
@media (max-width: 900px) { .front-nav a:nth-child(n+3) { display: none; }.front-hero { padding-top: 3rem; }.hero-illustration { width: 300px; }.search-fields { grid-template-columns: 1fr 1fr; }.search-fields .front-primary-button { grid-column: 1 / -1; }.programme-grid { grid-template-columns: 1fr; }.service-section, .help-section { grid-template-columns: 1fr; }.service-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 650px) { .front-header { justify-content: space-between; }.front-nav { display: none; }.front-actions .front-link-button { display: none; }.front-hero { flex-direction: column; align-items: stretch; padding-bottom: 5rem; }.hero-illustration { align-self: center; width: min(100%, 370px); }.search-section { padding: 0 1rem; }.search-heading, .section-heading, .contact-strip { align-items: start; flex-direction: column; }.search-note { line-height: 1.5; }.search-fields { grid-template-columns: 1fr; }.search-fields .front-primary-button { grid-column: auto; }.advanced-search > div { align-items: stretch; flex-direction: column; }.content-section { padding-right: 1rem; padding-left: 1rem; }.destination-grid, .service-grid { grid-template-columns: 1fr; }.contact-strip { margin-top: 3rem; padding-right: 1rem; padding-left: 1rem; }.front-footer { align-items: center; flex-direction: column; text-align: center; } }
.search-fields { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.search-fields .front-primary-button { grid-column: 1 / -1; }
.departure-station { margin-top: .6rem; color: #5573d4; font-size: .72rem; font-weight: 800; }
.station-section { padding-top: 4rem; }
.station-grid .destination-card { min-height: 150px; }
@media (max-width: 900px) { .search-fields { grid-template-columns: 1fr 1fr; } }
@media (max-width: 650px) { .search-fields { grid-template-columns: 1fr; } }

/* Visual language inspired by the reference booking platform: a strong
   travel banner, a floating search module and information-rich cards. */
.frontoffice-page { color: #18324b; background: #f4f7fb; font-family: Inter, system-ui, sans-serif; }
.front-header { position: sticky; top: 0; z-index: 10; max-width: none; padding: .85rem max(1.5rem, calc((100vw - 1240px) / 2)); border-bottom: 1px solid #e6edf4; background: rgba(255,255,255,.96); backdrop-filter: blur(14px); }
.front-brand { color: #0d2b4f; font-size: 1.05rem; letter-spacing: -.02em; }.front-brand-mark { width: 2.15rem; height: 2.15rem; border-radius: .55rem; background: #ef8d2f; box-shadow: none; }
.front-nav { gap: 1.45rem; }.front-nav a, .front-link-button { color: #5d7184; font-size: .76rem; }.front-nav a:hover, .front-link-button:hover { color: #ef7828; }
.front-primary-button, .reserve-button { border-radius: .45rem; background: #ef7828; box-shadow: 0 8px 18px #ef782833; }.front-primary-button.small { min-height: 36px; padding: 0 1rem; }
.front-hero { position: relative; isolation: isolate; max-width: none; min-height: 390px; padding: 5rem max(1.5rem, calc((100vw - 1180px) / 2)) 7.5rem; color: white; background: linear-gradient(115deg, #0b2c4b 0%, #164d74 63%, #d8752e 150%); overflow: hidden; }
.front-hero::before, .front-hero::after { position: absolute; z-index: -1; border-radius: 50%; content: ''; }.front-hero::before { right: -8rem; bottom: -12rem; width: 32rem; height: 32rem; background: #f29b4224; }.front-hero::after { top: -13rem; right: 22%; width: 25rem; height: 25rem; border: 1px solid #ffffff1f; }
.hero-copy { max-width: 690px; }.front-hero .front-eyebrow { color: #ffc270; }.front-hero h1 { max-width: 690px; font-size: clamp(2.45rem, 5vw, 4.25rem); letter-spacing: -.065em; }.front-hero .hero-text { color: #d5e1eb; }.front-hero .hero-points { color: #f4c788; }
.hero-illustration { width: 410px; height: 245px; border: 1px solid #ffffff26; background: linear-gradient(160deg, #f5bd7030, #ffffff12); box-shadow: 0 25px 60px #061c302b; }.sun { background: #ffc26e; }.mountain { border-bottom-color: #638da2; }.mountain-two { border-bottom-color: #436f88; }.road { background: #163b58; }.bus { border-color: #092b47; background: #ef7828; box-shadow: 0 .5rem 0 #092b47; }
.search-section { max-width: 1180px; margin: -4.4rem auto 0; padding: 0 1.5rem; }.trip-search { padding: 1.7rem 1.8rem; border: 0; border-radius: .8rem; box-shadow: 0 18px 45px #163b581c; }.search-heading h2, .section-heading h2, .service-section h2, .help-section h2 { color: #123452; font-size: clamp(1.55rem, 3vw, 2.1rem); letter-spacing: -.045em; }.front-eyebrow { color: #e9782a; letter-spacing: .14em; }.search-note { color: #738699; }
.search-fields { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .95rem; }.search-fields label span, .advanced-search label span { color: #536d81; }.search-fields select, .search-fields input, .advanced-search input { min-height: 46px; border-color: #d9e3eb; border-radius: .4rem; background: #fff; }.search-fields .front-primary-button { min-height: 46px; border-radius: .4rem; }
.content-section { max-width: 1240px; padding-right: max(1.5rem, calc((100vw - 1180px) / 2)); padding-left: max(1.5rem, calc((100vw - 1180px) / 2)); }.programme-section { padding-top: 5rem; }.section-subtitle { max-width: 600px; margin-top: .6rem; line-height: 1.6; }.result-count { padding: .45rem .7rem; border-radius: 99px; color: #d86521; background: #fff0e4; }
.programme-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1.2rem; }.departure-card { position: relative; padding: 1.35rem; border: 1px solid #e4ebf1; border-radius: .7rem; box-shadow: 0 12px 28px #18324b0c; }.departure-card::before { position: absolute; top: 0; right: 1.2rem; left: 1.2rem; height: 3px; border-radius: 0 0 99px 99px; background: #ef7828; content: ''; }.departure-station { color: #e9782a; }.departure-company { color: #718699; }.route-line { margin: 1.6rem 0; }.route-line strong { color: #173b59; }.route-arrow { color: #e9782a; }.departure-meta { border-color: #edf1f4; }.reserve-button { min-height: 42px; }
.destination-section, .station-section { padding-top: 5.5rem; }.destination-grid { gap: 1.1rem; }.destination-card { min-height: 145px; border: 1px solid #e1e9ef; border-radius: .7rem; box-shadow: 0 8px 20px #18324b08; }.destination-card:hover { border-color: #efb17d; box-shadow: 0 15px 30px #18324b16; }.destination-icon { color: #ef7828; }.destination-card strong { color: #173b59; }.destination-card span:last-child { color: #e9782a; }
.service-section { padding-top: 6.5rem; }.service-grid article { border-left-color: #ef7828; }.service-grid span { color: #e9782a; }.help-section { padding-top: 6.5rem; }.faq-list details { border-color: #e1e9ef; box-shadow: 0 5px 14px #18324b06; }.faq-list summary { color: #173b59; }.contact-strip { max-width: 1180px; border-color: #dce6ed; }.front-footer { max-width: 1180px; }
@media (max-width: 900px) { .front-hero { padding-right: 2rem; padding-left: 2rem; }.front-nav a:nth-child(n+3) { display: none; }.search-fields { grid-template-columns: 1fr 1fr; } }
@media (max-width: 650px) { .front-header { padding: .8rem 1rem; }.front-hero { min-height: 520px; padding: 3.5rem 1rem 7rem; }.hero-illustration { width: 100%; }.search-section { margin-top: -3.6rem; padding: 0 1rem; }.trip-search { padding: 1.2rem; }.search-fields { grid-template-columns: 1fr; }.content-section { padding-right: 1rem; padding-left: 1rem; }.section-heading h2 { font-size: 1.7rem; } }
.mobile-menu-toggle { display: none; min-height: 40px; padding: 0 .65rem; border: 1px solid #d9e3eb; border-radius: .4rem; color: #0d2b4f; background: white; font-size: 1.1rem; }
.mobile-front-nav { display: none; }
@media (max-width: 650px) { .mobile-menu-toggle { display: inline-flex; align-items: center; justify-content: center; }.mobile-front-nav { position: sticky; top: 4.1rem; z-index: 9; display: grid; gap: .2rem; padding: .75rem 1rem; border-bottom: 1px solid #e6edf4; background: white; box-shadow: 0 8px 18px #18324b14; }.mobile-front-nav a { padding: .7rem .5rem; color: #18324b; font-size: .82rem; font-weight: 800; text-decoration: none; }.front-actions .front-link-button { display: none; } }
.search-fields { grid-template-columns: repeat(4, minmax(0, 1fr)) auto; }.search-fields .front-primary-button { grid-column: auto; }.advanced-search select { width: 100%; min-height: 46px; padding: 0 .75rem; border: 1px solid #d9e3eb; border-radius: .4rem; color: #18324b; background: #fff; font: inherit; }
@media (max-width: 900px) { .search-fields { grid-template-columns: 1fr 1fr; }.search-fields .front-primary-button { grid-column: 1 / -1; } }
@media (max-width: 650px) { .search-fields { grid-template-columns: 1fr; }.search-fields .front-primary-button { grid-column: auto; } }
</style>
