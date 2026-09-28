<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import { financeService } from '../../services/finance/service'
import { gareService } from '../../services/gare/service'
import { reservationService } from '../../services/reservation/service'
		import { useAuthenticationStore } from '../../stores/authentication/store'
		import type { Caisse, Paiement } from '../../models/finance/model'
		import type { Gare } from '../../models/gare/model'
		import type { Reservation } from '../../models/reservation/model'
		import { userError } from '../../utils/errors'
    
		const caisses = ref<Caisse[]>([])
		const gares = ref<Gare[]>([])
		const reservations = ref<Reservation[]>([])
		const payments = ref<Paiement[]>([])
		const gareId = ref<number | null>(null)
		const ouverture = ref('0')
		const reservationId = ref<number | null>(null)
		const caisseId = ref<number | null>(null)
		const refundCaisseId = ref<number | null>(null)
		const busy = ref(false)
		const loading = ref(true)
		const error = ref('')
		const success = ref('')
		const auth = useAuthenticationStore()
		const canRefund = computed(() => auth.hasPermission('PAIEMENT_REFUND'))
    
		const caissesOuvertes = computed(() => caisses.value.filter((item) => item.statut === 'OUVERTE'))
		const selectedReservation = computed(() => reservations.value.find((item) => item.id === reservationId.value))
		const selectedCaisse = computed(() => caisses.value.find((item) => item.id === caisseId.value))
		const paymentAmount = computed(() => Number(selectedReservation.value?.montant_total || 0))
    
		function showError(value: unknown, fallback = 'Opération financière impossible.') {
			error.value = userError(value, fallback, 'FINANCE_ERROR')
			success.value = ''
		}
    
		function reservationLabel(item: Reservation) {
			const depart = item.depart
			const schedule = depart ? `${depart.date_depart} ${depart.heure_depart.slice(0, 5)}` : 'Départ non renseigné'
			const passengers = item.places?.map((place) => place.nom_passager).filter(Boolean).join(', ')
			return `${item.numero_reservation} · ${passengers || 'Passager'} · ${schedule}`
		}
    
		async function load() {
			loading.value = true
			try {
				const [cash, paid, stations, pendingReservations] = await Promise.all([
					financeService.caisses({ page: 1, page_size: 50 }),
					financeService.payments({ page: 1, page_size: 50 }),
					gareService.listGares({ page: 1, page_size: 100, sort_by: 'nom', sort_order: 'asc' }),
					reservationService.list({ page: 1, page_size: 100, statut: 'CONFIRMEE', date_from: new Date().toISOString().slice(0, 10) }),
				])
				caisses.value = cash.items || []
				payments.value = paid.items || []
				gares.value = stations.items || []
				reservations.value = pendingReservations.items || []
			} catch (value: unknown) {
				showError(value, 'Impossible de charger les données financières.')
			} finally {
				loading.value = false
			}
		}
    
		async function open() {
			if (!gareId.value) return
			busy.value = true
			try {
				await financeService.open({ id_gare: gareId.value, montant_ouverture: Number(ouverture.value) })
				success.value = 'Caisse ouverte.'
				gareId.value = null
				ouverture.value = '0'
				await load()
			} catch (value: unknown) {
				showError(value)
			} finally {
				busy.value = false
			}
		}
    
		async function close(item: Caisse) {
			if (!window.confirm('Clôturer cette caisse ?')) return
			busy.value = true
			try {
				await financeService.close(item.id)
				success.value = 'Caisse clôturée.'
				await load()
			} catch (value: unknown) {
				showError(value)
			} finally {
				busy.value = false
			}
		}
    
		async function pay() {
			if (!reservationId.value || !caisseId.value || !paymentAmount.value) return
			busy.value = true
			try {
				await financeService.pay({ id_reservation: reservationId.value, id_caisse: caisseId.value, montant: paymentAmount.value })
				success.value = 'Paiement en espèces enregistré et caisse mise à jour.'
				reservationId.value = null
				caisseId.value = null
				await load()
			} catch (value: unknown) {
				showError(value)
			} finally {
				busy.value = false
			}
		}

		async function refund(item: Paiement) {
			if (item.statut !== 'VALIDE' || !refundCaisseId.value) return
			if (!window.confirm(`Rembourser le paiement #${item.id} ? La réservation sera annulée.`)) return
			busy.value = true
			try {
				await financeService.refund(item.id, refundCaisseId.value)
				success.value = 'Paiement remboursé et réservation annulée.'
				await load()
			} catch (value: unknown) {
				showError(value, 'Impossible de rembourser ce paiement.')
			} finally {
				busy.value = false
			}
		}
    
		onMounted(load)
 </script>
 
 <template>
	 <AppLayout>
		 <template #title>Paiements & caisse</template>
		 <div class="page-intro">
			 <div><p class="eyebrow">FINANCES</p><h2>Paiements & caisse</h2><p>Encaissez les réservations confirmées en espèces sans saisir d’identifiant technique.</p></div>
		 </div>
		 <p v-if="error" class="error-banner">{{ error }}</p>
		 <p v-if="success" class="success-banner">{{ success }}</p>
		 <section class="content-grid">
			 <BaseCard>
				 <div class="card-heading"><div><h2>Ouvrir une caisse</h2><p>Choisissez la gare concernée.</p></div></div>
				 <div class="form-grid">
					 <label class="form-field"><span>Gare *</span><select v-model="gareId"><option :value="null">Choisir une gare</option><option v-for="gare in gares" :key="gare.id" :value="gare.id">{{ gare.nom }} · {{ gare.ville }}</option></select></label>
					 <label class="form-field"><span>Montant d’ouverture</span><input v-model="ouverture" type="number" min="0" step="0.01" /></label>
				 </div>
				 <button class="primary-button" :disabled="busy || !gareId" @click="open">Ouvrir la caisse</button>
			 </BaseCard>
			 <BaseCard>
				 <div class="card-heading"><div><h2>Encaisser une réservation</h2><p>Le montant restant est calculé automatiquement.</p></div></div>
				 <div class="form-grid">
					 <label class="form-field full"><span>Réservation confirmée *</span><select v-model="reservationId"><option :value="null">Choisir une réservation</option><option v-for="item in reservations" :key="item.id" :value="item.id">{{ reservationLabel(item) }}</option></select></label>
					 <label class="form-field full"><span>Caisse ouverte *</span><select v-model="caisseId"><option :value="null">Choisir une caisse</option><option v-for="item in caissesOuvertes" :key="item.id" :value="item.id">Caisse de la gare #{{ item.id_gare }} · solde {{ item.solde }}</option></select></label>
				 </div>
				 <div v-if="selectedReservation" class="payment-summary"><span>Montant à encaisser</span><strong>{{ paymentAmount.toLocaleString('fr-FR') }} MGA</strong><small>{{ selectedCaisse ? `Caisse sélectionnée · gare #${selectedCaisse.id_gare}` : 'Sélectionnez une caisse ouverte.' }}</small></div>
				 <button class="primary-button" :disabled="busy || !reservationId || !caisseId || !paymentAmount" @click="pay">Enregistrer le paiement en espèces</button>
				 <p v-if="!reservations.length && !loading" class="status-msg">Aucune réservation confirmée à encaisser.</p>
				 <p v-if="!caissesOuvertes.length && !loading" class="status-msg">Aucune caisse ouverte.</p>
			 </BaseCard>
		 </section>
		 <BaseCard>
			 <div class="card-heading"><div><h2>Historique des caisses</h2><p>Ouvertures, clôtures et soldes calculés à partir des opérations.</p></div></div>
			 <p v-if="loading" class="status-msg">Chargement…</p>
			 <div v-else class="table-scroll"><table class="data-table"><thead><tr><th>Gare</th><th>Ouverture</th><th>Recettes</th><th>Dépenses</th><th>Solde</th><th>Statut</th><th>Actions</th></tr></thead><tbody><tr v-for="item in caisses" :key="item.id"><td>Gare #{{ item.id_gare }}</td><td>{{ item.montant_ouverture }}</td><td>{{ item.total_recettes }}</td><td>{{ item.total_depenses }}</td><td>{{ item.solde }}</td><td>{{ item.statut }}</td><td><RouterLink class="secondary-button compact-button" :to="`/finance/caisses/${item.id}`">Détail</RouterLink><button v-if="item.statut === 'OUVERTE'" class="table-action danger-action" :disabled="busy" @click="close(item)">Clôturer</button></td></tr><tr v-if="!caisses.length"><td colspan="7" class="empty-state">Aucune caisse.</td></tr></tbody></table></div>
		 </BaseCard>
		 <BaseCard>
			 <div class="card-heading"><div><h2>Paiements récents</h2><p>Un remboursement est enregistré dans une caisse ouverte et annule la réservation associée.</p></div></div>
			 <div v-if="canRefund" class="form-grid refund-toolbar"><label class="form-field"><span>Caisse de remboursement *</span><select v-model="refundCaisseId"><option :value="null">Choisir une caisse ouverte</option><option v-for="item in caissesOuvertes" :key="item.id" :value="item.id">Caisse de la gare #{{ item.id_gare }} · solde {{ item.solde }}</option></select></label></div>
			 <div class="table-scroll"><table class="data-table"><thead><tr><th>Réservation</th><th>Montant</th><th>Méthode</th><th>Référence</th><th>Statut</th><th v-if="canRefund">Action</th></tr></thead><tbody><tr v-for="item in payments" :key="item.id"><td>Réservation #{{ item.id_reservation }}</td><td>{{ item.montant }}</td><td>{{ item.methode }}</td><td>{{ item.reference_paiement || '—' }}</td><td>{{ item.statut }}</td><td v-if="canRefund"><button v-if="item.statut === 'VALIDE'" class="table-action danger-action" :disabled="busy || !refundCaisseId" @click="refund(item)">Rembourser</button><span v-else>—</span></td></tr><tr v-if="!payments.length"><td :colspan="canRefund ? 6 : 5" class="empty-state">Aucun paiement.</td></tr></tbody></table></div>
		 </BaseCard>
	 </AppLayout>
 </template>
 
 <style scoped>
 .form-field.full { grid-column: 1 / -1; }
 .payment-summary { display: grid; gap: 0.25rem; margin: 1rem 0; padding: 1rem; border: 1px solid var(--border-color, #d1d5db); border-radius: 10px; background: #f8fafc; }
 .payment-summary strong { color: #166534; font-size: 1.35rem; }
.payment-summary small { color: #64748b; }
.refund-toolbar { max-width: 420px; margin-bottom: 1rem; }
</style>
