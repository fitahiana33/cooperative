<script setup lang="ts">
import { ref } from 'vue'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import { api } from '../../services/api'
import { userError } from '../../utils/errors'
const code = ref(''); const busy = ref(false); const error = ref(''); const result = ref<{ id: number; statut: string; motif_refus?: string | null } | null>(null)
async function control() { if (!code.value.trim()) { error.value = 'Saisissez le numéro du billet ou le QR Code.'; return }; busy.value = true; error.value = ''; result.value = null; try { result.value = (await api.post('/embarquement/controle', { code: code.value.trim() })).data } catch (value: unknown) { error.value = userError(value, 'Billet non autorisé à l’embarquement.', 'BOARDING_CONTROL_ERROR') } finally { busy.value = false } }
</script>
<template><AppLayout><template #title>Embarquement</template><div class="page-intro"><div><p class="eyebrow">CONTRÔLE</p><h2>Contrôle d’embarquement</h2><p>Recherchez un billet par numéro ou scannez sa valeur QR.</p></div></div><BaseCard><form class="inline-form" @submit.prevent="control"><label class="form-field"><span>Numéro billet ou QR Code *</span><input v-model="code" :disabled="busy" autofocus placeholder="BIL-… ou UUID" /></label><button class="primary-button" :disabled="busy">{{ busy ? 'Contrôle…' : 'Contrôler' }}</button></form><p v-if="error" class="error-banner" role="alert">{{ error }}</p><div v-if="result" class="result-panel" :class="result.statut === 'VALIDE' ? 'result-success' : 'result-error'"><strong>{{ result.statut === 'VALIDE' ? 'Embarquement enregistré' : 'Embarquement refusé' }}</strong><span>{{ result.motif_refus || 'Le billet, la réservation, la date et la place ont été validés.' }}</span></div></BaseCard></AppLayout></template>
