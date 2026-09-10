<script setup lang="ts">
import { onMounted, ref } from 'vue'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import ListToolbar from '../../components/ui/ListToolbar.vue'
import { billetService } from '../../services/billet/service'
import type { Billet } from '../../models/billet/model'
import { userError } from '../../utils/errors'
const items = ref<Billet[]>([]); const search = ref(''); const loading = ref(true); const error = ref(''); const total = ref(0)
function showError(value: unknown) { error.value = userError(value, 'Impossible de charger les billets.', 'BILLETS_LIST_ERROR') }
async function load() { loading.value = true; error.value = ''; try { const result = await billetService.list({ page: 1, page_size: 50, search: search.value || undefined }); items.value = result.items; total.value = result.total } catch (value: unknown) { showError(value) } finally { loading.value = false } }
onMounted(load)
</script>
<template><AppLayout><template #title>Billets & QR Code</template><div class="page-intro"><div><p class="eyebrow">RÉSERVATIONS</p><h2>Billets & QR Code</h2><p>Chaque place confirmée possède un billet et un QR Code unique.</p></div></div><BaseCard><div class="card-heading"><div><h2>Historique des billets ({{ total }})</h2><p>Recherchez par numéro de billet ou de réservation.</p></div></div><ListToolbar v-model="search" :loading="loading" placeholder="Numéro billet / réservation" @search="load" /><p v-if="loading" class="status-msg">Chargement des billets…</p><p v-else-if="error" class="error-banner">{{ error }}</p><div v-if="!loading && !error" class="table-scroll"><table class="data-table"><caption>Billets générés</caption><thead><tr><th>Billet</th><th>Passager</th><th>Départ</th><th>Place</th><th>Tarif</th><th>QR Code</th><th>Statut</th></tr></thead><tbody><tr v-for="item in items" :key="item.id"><td><strong>{{ item.numero_billet }}</strong><br><small>{{ item.numero_reservation }}</small></td><td>{{ item.nom_passager || '—' }}</td><td>{{ item.date_depart }} {{ item.heure_depart?.slice(0, 5) }}<br>{{ item.destination_depart || '—' }} → {{ item.destination_arrivee || '—' }}</td><td>{{ item.numero_place || '—' }}</td><td>{{ item.prix || '—' }} {{ item.devise || '' }}</td><td><code>{{ item.qr_code_uuid }}</code></td><td><span class="status-badge" :class="item.statut === 'VALIDE' ? 'active' : 'inactive'">{{ item.statut }}</span></td></tr><tr v-if="!items.length"><td colspan="7" class="empty-state">Aucun billet généré.</td></tr></tbody></table></div></BaseCard></AppLayout></template>
