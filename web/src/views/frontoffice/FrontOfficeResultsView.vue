<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthenticationStore } from '../../stores/authentication/store'
import { departService } from '../../services/depart/service'
import { destinationService } from '../../services/destination/service'
import { gareService } from '../../services/gare/service'
import type { PublicProgramme } from '../../models/depart/model'
import type { PublicDestination } from '../../models/destination/model'
import type { PublicGare, PublicGareCooperative } from '../../models/gare/model'
import { localIsoDate } from '../../utils/date'

const route = useRoute()
const router = useRouter()
const auth = useAuthenticationStore()
const today = localIsoDate()
const loading = ref(true)
const error = ref('')
const mobileMenuOpen = ref(false)
const programme = ref<PublicProgramme[]>([])
const destinations = ref<PublicDestination[]>([])
const gares = ref<PublicGare[]>([])
const total = ref(0)
const sortBy = ref<'time' | 'price' | 'availability'>('time')
const sortOrder = ref<'asc' | 'desc'>('asc')

function queryValue(name: string, fallback = '') {
  const value = route.query[name]
  return typeof value === 'string' ? value : fallback
}

const filters = reactive({
  from: queryValue('from'),
  to: queryValue('to'),
  date: queryValue('date', today),
  passengers: queryValue('passengers', '1'),
  gare: queryValue('gare'),
  cooperative: queryValue('cooperative'),
})

const cooperativeOptions = computed<PublicGareCooperative[]>(() => {
  const source = filters.gare ? gares.value.filter((item) => item.id === Number(filters.gare)) : gares.value
  const unique = new Map<number, PublicGareCooperative>()
  source.flatMap((item) => item.cooperatives).forEach((item) => unique.set(item.id, item))
  return [...unique.values()].sort((left, right) => left.nom.localeCompare(right.nom))
})

const sortedProgramme = computed(() => [...programme.value].sort((left, right) => {
  let comparison = 0
  if (sortBy.value === 'price') comparison = Number(left.tarif?.prix || 0) - Number(right.tarif?.prix || 0)
  else if (sortBy.value === 'availability') comparison = left.places_disponibles - right.places_disponibles
  else comparison = `${left.date_depart}T${left.heure_depart}`.localeCompare(`${right.date_depart}T${right.heure_depart}`)
  return sortOrder.value === 'asc' ? comparison : -comparison
}))

function displayDate(value: string) {
  return new Intl.DateTimeFormat('fr-FR', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' }).format(new Date(`${value}T00:00:00`))
}
function displayPrice(item: PublicProgramme) {
  return item.tarif ? `${Number(item.tarif.prix).toLocaleString('fr-FR')} ${item.tarif.devise}` : 'Tarif à confirmer'
}
function routeName(item: PublicProgramme) {
  return `${item.itineraire?.destination_depart?.nom || 'Départ'} → ${item.itineraire?.destination_arrivee?.nom || 'Arrivée'}`
}
function query() {
  return {
    from: filters.from || undefined,
    to: filters.to || undefined,
    date: filters.date || undefined,
    passengers: filters.passengers,
    gare: filters.gare || undefined,
    cooperative: filters.cooperative || undefined,
  }
}
async function loadReferences() {
  const [destinationResult, gareResult] = await Promise.allSettled([
    destinationService.publicList({ page: 1, page_size: 200 }),
    gareService.publicList({ page: 1, page_size: 100 }),
  ])
  if (destinationResult.status === 'fulfilled') destinations.value = destinationResult.value.items || []
  if (gareResult.status === 'fulfilled') gares.value = gareResult.value.items || []
}
async function loadProgramme() {
  loading.value = true
  error.value = ''
  try {
    const result = await departService.publicProgramme({
      page: 1,
      page_size: 100,
      date_from: filters.date || undefined,
      id_destination_depart: filters.from ? Number(filters.from) : undefined,
      id_destination_arrivee: filters.to ? Number(filters.to) : undefined,
      id_gare: filters.gare ? Number(filters.gare) : undefined,
      id_cooperative: filters.cooperative ? Number(filters.cooperative) : undefined,
      passagers: Number(filters.passengers),
    })
    programme.value = result.items || []
    total.value = result.total || 0
  } catch (value) {
    console.error('[PUBLIC_RESULTS_ERROR]', value)
    error.value = 'Les départs ne sont pas disponibles pour le moment.'
  } finally { loading.value = false }
}
async function search() {
  await router.replace({ name: 'search-results', query: query() })
  await loadProgramme()
}
function reset() {
  filters.from = ''
  filters.to = ''
  filters.date = today
  filters.passengers = '1'
  filters.gare = ''
  filters.cooperative = ''
  void search()
}
function reserve(item: PublicProgramme) {
  void router.push({ name: 'public-booking', query: { depart_id: String(item.id) } })
}
function goToClientSpace() {
  void router.push({ name: auth.user?.role?.toLowerCase() === 'passenger' ? 'client-space' : 'home' })
}
onMounted(async () => { await loadReferences(); await loadProgramme() })
</script>

<template>
  <main class="results-page">
    <header class="results-header">
      <RouterLink class="results-brand" to="/"><span class="results-brand-mark">C</span><span>Coopérative</span></RouterLink>
      <nav class="results-desktop-nav" aria-label="Navigation client"><RouterLink to="/">Accueil</RouterLink><a href="#resultats">Voyages</a><a href="#aide-resultats">Aide</a></nav>
      <div class="results-actions"><button class="results-menu-toggle" type="button" :aria-label="mobileMenuOpen ? 'Fermer le menu' : 'Ouvrir le menu'" :aria-expanded="mobileMenuOpen" @click="mobileMenuOpen = !mobileMenuOpen">☰</button><button v-if="auth.isAuthenticated" type="button" class="results-user-link" @click="goToClientSpace">Mon espace</button><RouterLink v-else class="results-user-link" to="/login">Connexion</RouterLink><RouterLink v-if="!auth.isAuthenticated" class="results-cta" to="/register">Créer un compte</RouterLink></div>
    </header>
    <nav v-if="mobileMenuOpen" class="results-mobile-nav" aria-label="Menu mobile"><RouterLink to="/" @click="mobileMenuOpen = false">Accueil</RouterLink><a href="#resultats" @click="mobileMenuOpen = false">Voyages</a><a href="#aide-resultats" @click="mobileMenuOpen = false">Aide</a></nav>

    <section class="results-intro"><div><RouterLink class="back-link" to="/">← Modifier la recherche</RouterLink><p class="results-kicker">VOYAGES DISPONIBLES</p><h1>Comparez les départs qui vous conviennent.</h1><p>Les résultats sont classés par horaire. Vérifiez la gare, le prix et les places avant de continuer.</p></div></section>

    <section class="results-search" aria-label="Modifier la recherche">
      <form @submit.prevent="search">
        <div class="essential-fields">
          <label><span>Départ</span><select v-model="filters.from"><option value="">Toutes les villes</option><option v-for="item in destinations" :key="`from-${item.id}`" :value="String(item.id)">{{ item.nom }}</option></select></label>
          <label><span>Destination</span><select v-model="filters.to"><option value="">Toutes les villes</option><option v-for="item in destinations" :key="`to-${item.id}`" :value="String(item.id)">{{ item.nom }}</option></select></label>
          <label><span>Date</span><input v-model="filters.date" type="date" :min="today" required /></label>
          <label><span>Passagers</span><select v-model="filters.passengers"><option v-for="count in 8" :key="count" :value="String(count)">{{ count }} {{ count === 1 ? 'passager' : 'passagers' }}</option></select></label>
          <button class="results-search-button" type="submit">Rechercher <span>→</span></button>
        </div>
        <details class="secondary-filters"><summary>Filtres secondaires : gare et coopérative</summary><div><label><span>Gare de départ</span><select v-model="filters.gare" @change="filters.cooperative = ''"><option value="">Toutes les gares</option><option v-for="item in gares" :key="item.id" :value="String(item.id)">{{ item.nom }} · {{ item.ville }}</option></select></label><label><span>Coopérative</span><select v-model="filters.cooperative"><option value="">Toutes les coopératives</option><option v-for="item in cooperativeOptions" :key="item.id" :value="String(item.id)">{{ item.nom }}</option></select></label><button type="button" class="reset-link" @click="reset">Réinitialiser</button></div></details>
      </form>
    </section>

    <section id="resultats" class="results-content" aria-live="polite">
      <div class="results-toolbar"><div><p class="results-kicker">RÉSULTATS</p><h2>{{ total }} départ{{ total > 1 ? 's' : '' }} trouvé{{ total > 1 ? 's' : '' }}</h2></div><div class="sort-controls"><label for="sort-by">Trier par</label><select id="sort-by" v-model="sortBy"><option value="time">Horaire de départ</option><option value="price">Prix</option><option value="availability">Places disponibles</option></select><button type="button" class="sort-direction" :aria-label="sortOrder === 'asc' ? 'Ordre croissant' : 'Ordre décroissant'" @click="sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'">{{ sortOrder === 'asc' ? '↑' : '↓' }}</button></div></div>
      <div v-if="loading" class="result-grid" aria-label="Chargement des résultats"><div v-for="index in 3" :key="index" class="result-skeleton"><span></span><span></span><span></span></div></div>
      <div v-else-if="error" class="result-empty"><strong>{{ error }}</strong><p>Vous pouvez modifier la date ou élargir les critères de recherche.</p><button type="button" class="results-search-button" @click="reset">Réinitialiser la recherche</button></div>
      <div v-else-if="!sortedProgramme.length" class="result-empty"><strong>Aucun départ ne correspond à votre recherche.</strong><p>Essayez une autre date, une autre ville ou moins de passagers.</p><button type="button" class="results-search-button" @click="reset">Voir tous les départs</button></div>
      <div v-else class="result-grid"><article v-for="item in sortedProgramme" :key="item.id" class="result-card"><div class="result-card-head"><span class="result-status">{{ item.statut === 'RETARDE' ? 'Départ retardé' : 'Départ programmé' }}</span><strong>{{ displayPrice(item) }}</strong></div><div class="result-date">{{ displayDate(item.date_depart) }}</div><div class="result-route"><div><strong>{{ item.itineraire?.destination_depart?.nom || 'Départ' }}</strong><span>Ville de départ</span></div><span class="result-arrow">→</span><div><strong>{{ item.itineraire?.destination_arrivee?.nom || 'Arrivée' }}</strong><span>Destination</span></div></div><div class="result-time"><strong>{{ item.heure_depart.slice(0, 5) }}</strong><span>Heure de départ</span></div><div class="result-context"><span><b>Gare</b>{{ item.gare?.nom || 'Gare à confirmer' }}<small v-if="item.gare?.adresse">{{ item.gare.adresse }}</small></span><span><b>Coopérative</b>{{ item.cooperative?.nom || 'À confirmer' }}</span><span><b>Disponibilité</b>{{ item.places_disponibles }} place{{ item.places_disponibles > 1 ? 's' : '' }}</span></div><button type="button" class="result-reserve" @click="reserve(item)">Voir et réserver <span>→</span></button></article></div>
    </section>

    <section id="aide-resultats" class="results-help"><strong>Besoin d’aide ?</strong><span>La réservation est créée en attente. Le règlement s’effectue au guichet de la gare dans le délai indiqué sur votre réservation.</span><RouterLink to="/#aide">Consulter l’aide</RouterLink></section>
  </main>
</template>

<style scoped>
.results-page { min-height: 100vh; color: #18324b; background: #f4f7fb; font-family: Inter, system-ui, sans-serif; }
.results-header { display: flex; align-items: center; gap: 2rem; padding: .85rem max(1rem, calc((100vw - 1240px) / 2)); border-bottom: 1px solid #e5edf3; background: #fff; }.results-brand { display: inline-flex; align-items: center; gap: .65rem; color: #0d2b4f; font-weight: 800; text-decoration: none; }.results-brand-mark { display: grid; place-items: center; width: 2.15rem; height: 2.15rem; border-radius: .55rem; color: #fff; background: #ef8d2f; }.results-header nav { display: flex; gap: 1.3rem; margin-left: auto; }.results-header nav a, .results-user-link { color: #607487; font-size: .8rem; font-weight: 700; text-decoration: none; background: none; }.results-header nav a:hover, .results-user-link:hover { color: #e9782a; }.results-actions { display: flex; align-items: center; gap: .8rem; }.results-cta, .results-search-button, .result-reserve { display: inline-flex; align-items: center; justify-content: center; gap: .4rem; min-height: 40px; padding: 0 1rem; border-radius: .4rem; color: white; background: #ef7828; font-weight: 800; text-decoration: none; box-shadow: 0 8px 18px #ef782833; }
.results-intro { padding: 3rem max(1rem, calc((100vw - 1180px) / 2)) 7rem; color: white; background: linear-gradient(115deg, #0b2c4b, #164d74 70%, #d8752e); }.results-intro > div { max-width: 720px; }.back-link { display: inline-block; margin-bottom: 2rem; color: #ffd18b; font-size: .8rem; font-weight: 700; text-decoration: none; }.results-kicker { margin: 0 0 .55rem; color: #e9782a; font-size: .7rem; font-weight: 900; letter-spacing: .15em; }.results-intro .results-kicker { color: #ffc270; }.results-intro h1 { margin: 0; font: 800 clamp(2rem, 4vw, 3.4rem)/1.08 Manrope, sans-serif; letter-spacing: -.06em; }.results-intro p:last-child { max-width: 620px; color: #d7e2eb; line-height: 1.6; }
.results-search { max-width: 1180px; margin: -4rem auto 0; padding: 0 1rem; }.results-search form { padding: 1.25rem; border-radius: .8rem; background: white; box-shadow: 0 18px 45px #18324b1c; }.essential-fields { display: grid; grid-template-columns: 1.1fr 1.1fr 1fr .8fr auto; align-items: end; gap: .7rem; }.essential-fields label, .secondary-filters label { display: grid; gap: .35rem; margin: 0; }.essential-fields label span, .secondary-filters label span { color: #536d81; font-size: .7rem; font-weight: 800; }.essential-fields select, .essential-fields input, .secondary-filters select { width: 100%; min-height: 44px; padding: 0 .7rem; border: 1px solid #d9e3eb; border-radius: .35rem; color: #18324b; background: white; font: inherit; }.secondary-filters { margin-top: 1rem; color: #e9782a; font-size: .78rem; font-weight: 800; }.secondary-filters summary { cursor: pointer; }.secondary-filters > div { display: flex; align-items: end; gap: .7rem; margin-top: .8rem; }.reset-link { min-height: 40px; border: 0; color: #e9782a; background: none; font-weight: 800; cursor: pointer; }
.results-content { max-width: 1180px; margin: auto; padding: 4.2rem 1rem 4rem; }.results-toolbar { display: flex; align-items: end; justify-content: space-between; gap: 1rem; }.results-toolbar h2 { margin: 0; color: #123452; font: 800 1.8rem Manrope, sans-serif; letter-spacing: -.05em; }.sort-controls { display: flex; align-items: center; gap: .55rem; color: #627789; font-size: .75rem; font-weight: 700; }.sort-controls select, .sort-direction { min-height: 38px; padding: 0 .65rem; border: 1px solid #d8e2ea; border-radius: .35rem; color: #18324b; background: #fff; font: inherit; }.sort-direction { min-width: 38px; color: #e9782a; cursor: pointer; }.result-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1.1rem; margin-top: 1.5rem; }.result-card { position: relative; padding: 1.3rem; border: 1px solid #e1e9ef; border-radius: .7rem; background: white; box-shadow: 0 10px 25px #18324b0b; }.result-card::before { position: absolute; top: 0; right: 1.2rem; left: 1.2rem; height: 3px; border-radius: 0 0 99px 99px; background: #ef7828; content: ''; }.result-card-head, .result-context, .result-route { display: flex; align-items: center; justify-content: space-between; gap: .7rem; }.result-card-head { padding-top: .2rem; }.result-status { color: #2c7b57; font-size: .7rem; font-weight: 800; }.result-card-head > strong { color: #e56822; font-size: 1.05rem; }.result-date { margin-top: 1.1rem; color: #536d81; font-size: .78rem; font-weight: 800; text-transform: capitalize; }.result-route { justify-content: center; margin: 1.1rem 0 .8rem; text-align: center; }.result-route div { display: grid; gap: .25rem; min-width: 125px; }.result-route strong { color: #123452; font: 800 1.15rem Manrope, sans-serif; }.result-route span:not(.result-arrow) { color: #8192a1; font-size: .68rem; }.result-arrow { color: #ef7828; font-size: 1.4rem; }.result-time { display: grid; justify-items: center; gap: .15rem; margin: .75rem 0 1.1rem; padding: .65rem; border-radius: .45rem; background: #f5f8fa; }.result-time strong { color: #0d2b4f; font-size: 1.6rem; letter-spacing: -.04em; }.result-time span { color: #687e90; font-size: .68rem; }.result-context { align-items: stretch; padding: .9rem 0; border-top: 1px solid #edf1f4; border-bottom: 1px solid #edf1f4; }.result-context span { display: grid; gap: .25rem; min-width: 0; color: #617789; font-size: .72rem; }.result-context small { overflow: hidden; color: #8192a1; font-size: .62rem; text-overflow: ellipsis; white-space: nowrap; }.result-context b { color: #9aa8b3; font-size: .62rem; text-transform: uppercase; }.result-reserve { width: 100%; margin-top: 1rem; border: 0; cursor: pointer; }.result-empty { display: grid; justify-items: center; gap: .45rem; margin-top: 1.5rem; padding: 3rem 1rem; border: 1px dashed #cbd9e3; border-radius: .7rem; color: #708494; background: white; text-align: center; }.result-empty strong { color: #18324b; }.result-empty p { margin: 0 0 .8rem; }.result-skeleton { display: grid; gap: .8rem; min-height: 300px; padding: 1.3rem; border-radius: .7rem; background: linear-gradient(90deg, #fff 25%, #edf3f6 37%, #fff 63%); background-size: 400% 100%; animation: skeleton 1.4s ease infinite; }.result-skeleton span { height: 16px; border-radius: .25rem; background: #dbe6ed99; }.result-skeleton span:nth-child(2) { width: 72%; height: 80px; margin: auto; }.results-help { display: flex; align-items: center; gap: 1rem; max-width: 1180px; margin: 0 auto 3rem; padding: 1.2rem 1rem; border-top: 1px solid #dce6ed; border-bottom: 1px solid #dce6ed; color: #607487; font-size: .8rem; }.results-help strong { color: #18324b; }.results-help a { margin-left: auto; color: #e9782a; font-weight: 800; text-decoration: none; }@keyframes skeleton { to { background-position: -400% 0; } }
@media (max-width: 900px) { .essential-fields { grid-template-columns: 1fr 1fr; }.essential-fields .results-search-button { grid-column: 1 / -1; }.result-grid { grid-template-columns: 1fr; } }
@media (max-width: 650px) { .results-header { gap: .6rem; }.results-desktop-nav { display: none; }.results-actions { margin-left: auto; }.results-cta { display: none; }.results-intro { padding: 2rem 1rem 6rem; }.results-intro h1 { font-size: 2.2rem; }.results-search { margin-top: -3.2rem; padding: 0 .75rem; }.results-search form { padding: 1rem; }.essential-fields { grid-template-columns: 1fr; }.essential-fields .results-search-button { grid-column: auto; }.secondary-filters > div { align-items: stretch; flex-direction: column; }.results-content { padding: 3rem .75rem; }.results-toolbar { align-items: start; flex-direction: column; }.sort-controls { width: 100%; }.sort-controls select { flex: 1; }.result-card { padding: 1rem; }.result-context { gap: .4rem; }.result-context span { font-size: .65rem; }.results-help { align-items: start; flex-direction: column; margin-right: .75rem; margin-left: .75rem; }.results-help a { margin-left: 0; } }
.results-menu-toggle { display: none; min-height: 38px; padding: 0 .65rem; border: 1px solid #d9e3eb; border-radius: .35rem; color: #0d2b4f; background: white; font-size: 1.1rem; }
.results-mobile-nav { display: none; }
@media (max-width: 650px) { .results-menu-toggle { display: inline-flex; align-items: center; justify-content: center; }.results-mobile-nav { display: grid; gap: .2rem; padding: .7rem 1rem; border-bottom: 1px solid #e5edf3; background: white; box-shadow: 0 8px 18px #18324b14; }.results-mobile-nav a { padding: .65rem .45rem; color: #18324b; font-size: .82rem; font-weight: 800; text-decoration: none; } }
</style>
