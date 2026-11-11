<script setup lang="ts">
import { nextTick, onMounted, ref } from "vue";
import type { Caisse, Paiement } from "../../models/finance/model";
import { financeService } from "../../services/finance/service";
import { formatMoney } from "../../utils/money";
import { userError } from "../../utils/errors";
const props = defineProps<{ payment: Paiement; caisses: Caisse[]; initialCaisseId?: number | null }>();
const emit = defineEmits<{ done: []; close: [] }>();
const method = ref("ESPECES");
const caisseId = ref<number | null>(props.initialCaisseId || null);
const reference = ref("");
const busy = ref(false);
const error = ref("");
const heading = ref<HTMLElement | null>(null);
async function submit() {
  if (busy.value) return;
  if (method.value === "ESPECES" && !caisseId.value) {
    error.value = props.caisses.length
      ? "Choisissez la caisse qui remettra les espèces."
      : "Aucune caisse ouverte n’est disponible dans votre périmètre.";
    return;
  }
  if (method.value !== "ESPECES" && reference.value.trim().length < 8) {
    error.value = "Renseignez la référence du remboursement réellement effectué.";
    return;
  }
  busy.value = true; error.value = "";
  try {
    await financeService.refund(props.payment.id, method.value === 'ESPECES' ? caisseId.value! : undefined,
      { methode: method.value, reference: method.value === 'ESPECES' ? undefined : reference.value.trim() });
    emit("done");
  } catch (value) { error.value = userError(value, "Le remboursement n’a pas pu être enregistré.", "REFUND_ERROR"); }
  finally { busy.value = false; }
}
onMounted(async () => {
  await nextTick();
  heading.value?.focus();
});
</script>
<template>
  <Teleport to="body">
  <div class="refund-overlay" @click.self="emit('close')">
  <section class="refund-form" role="dialog" aria-modal="true" aria-labelledby="refund-heading">
    <h2 id="refund-heading" ref="heading" tabindex="-1">Rembourser {{ formatMoney(Number(payment.montant)) }}</h2>
    <p>{{ payment.numero_reservation || payment.reference_paiement }}</p>
    <form novalidate @submit.prevent="submit">
      <label>Mode de remboursement<select v-model="method" :disabled="busy"><option value="ESPECES">Espèces au guichet</option><option value="MOBILE_MONEY">Mobile Money déjà effectué</option><option value="VIREMENT">Virement déjà effectué</option><option value="CARTE">Carte déjà effectué</option></select></label>
      <label v-if="method === 'ESPECES'">Caisse qui rend les espèces<select v-model.number="caisseId" required :disabled="busy"><option :value="null" disabled>Choisir une caisse ouverte</option><option v-for="caisse in caisses" :key="caisse.id" :value="caisse.id">Caisse {{ caisse.id }} · solde {{ formatMoney(Number(caisse.solde)) }}</option></select></label>
      <p v-if="method === 'ESPECES' && !caisses.length" class="refund-warning">Ouvrez d’abord une caisse autorisée pour cette gare, ou choisissez un remboursement externe déjà effectué.</p>
      <template v-if="method !== 'ESPECES'"><p>Enregistrez uniquement un remboursement déjà confirmé par votre prestataire. Cette action ne déclenche pas elle-même le transfert.</p><label>Référence du remboursement déjà effectué<input v-model="reference" required minlength="8" maxlength="150" :disabled="busy" /></label></template>
      <p v-if="error" role="alert">{{ error }}</p>
      <button type="submit" class="btn-primary" :disabled="busy">{{ busy ? 'Enregistrement…' : 'Confirmer le remboursement' }}</button>
      <button type="button" :disabled="busy" @click="emit('close')">Fermer</button>
    </form>
  </section>
  </div>
  </Teleport>
</template>
<style scoped>
.refund-overlay { align-items: center; background: rgb(15 30 24 / .55); display: flex; inset: 0; justify-content: center; padding: 20px; position: fixed; z-index: 1200; }
.refund-form { padding: 1.5rem; border: 1px solid var(--line); background: var(--surface); border-radius: 12px; box-shadow: 0 24px 70px rgb(0 0 0 / .22); max-height: calc(100vh - 40px); max-width: 720px; overflow-y: auto; width: 100%; }
form { display: flex; gap: 1rem; align-items: end; flex-wrap: wrap; }
label { display: grid; gap: .4rem; max-width: 100%; }
input, select, button { min-height: 44px; border: 1px solid var(--line); border-radius: 8px; padding: .5rem .75rem; max-width: 100%; }
p { flex-basis: 100%; } button { cursor: pointer; }
.refund-warning { background: #fff5df; border-radius: 8px; color: #79501c; padding: 10px; }
@media (max-width: 560px) { .refund-overlay { align-items: end; padding: 0; } .refund-form { border-radius: 16px 16px 0 0; max-height: 92vh; } form, label, button { width: 100%; } }
</style>
