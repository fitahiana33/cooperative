<script setup lang="ts">
import { ref } from 'vue'
import AppLayout from '../../components/layout/AppLayout.vue'
import BaseCard from '../../components/ui/BaseCard.vue'
import { systemService } from '../../services/system/service'
import { userError } from '../../utils/errors'

const confirmation = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')
const result = ref<{ tables_cleared: number; users_deleted: number } | null>(null)

async function resetData() {
  if (confirmation.value !== 'RESET' || loading.value) return
  loading.value = true
  error.value = ''
  success.value = ''
  result.value = null
  try {
    const response = await systemService.resetBusinessData()
    result.value = response
    success.value = response.message
    confirmation.value = ''
  } catch (value: unknown) {
    error.value = userError(value, 'La réinitialisation n’a pas pu être effectuée.', 'SYSTEM_RESET_ERROR')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AppLayout>
    <template #title>Réinitialisation</template>
    <section class="page-intro">
      <div><p class="eyebrow">ADMINISTRATION SYSTÈME</p><h2>Réinitialiser les données</h2><p>Supprime les données métier de l’environnement de développement.</p></div>
    </section>
    <p v-if="error" class="error-banner" role="alert">{{ error }}</p>
    <p v-if="success" class="success-banner" role="status">{{ success }}</p>
    <BaseCard class="reset-card">
      <div class="warning-mark">!</div>
      <div class="reset-copy">
        <h2>Action irréversible</h2>
        <p>Cette action supprimera les coopératives, gares, véhicules, chauffeurs, départs, réservations, billets, paiements, caisses, notifications et les utilisateurs non administrateurs.</p>
        <p class="protected-note"><strong>Conservés :</strong> votre compte administrateur, les autres comptes administrateurs, les rôles et les permissions.</p>
      </div>
      <div class="reset-confirmation">
        <label for="reset-confirmation">Tapez <strong>RESET</strong> pour confirmer</label>
        <input id="reset-confirmation" v-model="confirmation" autocomplete="off" spellcheck="false" placeholder="RESET" :disabled="loading" @keyup.enter="resetData">
        <button class="danger-button" type="button" :disabled="confirmation !== 'RESET' || loading" @click="resetData">{{ loading ? 'Réinitialisation…' : 'Réinitialiser les données' }}</button>
      </div>
      <div v-if="result" class="reset-result"><span>{{ result.tables_cleared }} tables métier vidées</span><span>{{ result.users_deleted }} utilisateur(s) supprimé(s)</span></div>
    </BaseCard>
  </AppLayout>
</template>

<style scoped>
.reset-card { display: grid; grid-template-columns: auto 1fr; gap: 1rem 1.25rem; max-width: 820px; padding: 1.5rem; border-color: #fecaca; }
.warning-mark { display: grid; width: 42px; height: 42px; place-items: center; border-radius: 50%; color: #991b1b; background: #fee2e2; font-size: 1.4rem; font-weight: 800; }
.reset-copy h2 { margin: 0; color: #991b1b; font-size: 1.1rem; }
.reset-copy p { margin: 0.6rem 0 0; color: #475569; line-height: 1.55; }
.protected-note { padding: 0.75rem; border-left: 3px solid #16a34a; background: #f0fdf4; }
.reset-confirmation { display: grid; grid-column: 1 / -1; gap: 0.5rem; max-width: 480px; }
.reset-confirmation label { color: #334155; font-size: 0.85rem; }
.reset-confirmation input { min-height: 40px; padding: 0.6rem 0.75rem; border: 1px solid #cbd5e1; border-radius: 6px; font-family: monospace; }
.reset-confirmation input:focus { outline: 2px solid #fecaca; border-color: #ef4444; }
.danger-button { min-height: 40px; padding: 0.65rem 1rem; border: 0; border-radius: 6px; color: #fff; background: #dc2626; font-weight: 700; cursor: pointer; }
.danger-button:disabled { opacity: 0.45; cursor: not-allowed; }
.reset-result { display: flex; grid-column: 1 / -1; flex-wrap: wrap; gap: 0.75rem; color: #166534; font-size: 0.85rem; }
.reset-result span { padding: 0.5rem 0.7rem; border-radius: 6px; background: #f0fdf4; }
@media (max-width: 600px) { .reset-card { grid-template-columns: 1fr; } }
</style>
