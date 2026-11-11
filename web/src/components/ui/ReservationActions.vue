<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import type { Reservation } from "../../models/reservation/model";
import { reservationService } from "../../services/reservation/service";
import { financeService } from "../../services/finance/service";
import { formatMoney } from "../../utils/money";
import { userError } from "../../utils/errors";

const props = defineProps<{ reservation: Reservation; accessToken?: string }>();
const emit = defineEmits<{ updated: [reservation: Reservation] }>();
const busy = ref(false);
const confirming = ref(false);
const message = ref("");
const error = ref("");
const amount = ref(Number(props.reservation.minimum_a_payer || props.reservation.montant_restant));
const provider = ref("MVOLA");
const paymentPhone = ref(props.reservation.telephone_reservataire || "");
watch(() => props.reservation.id, () => {
  confirming.value = false;
  amount.value = Number(props.reservation.minimum_a_payer || props.reservation.montant_restant);
});
onMounted(async () => {
  if (!props.reservation.peut_payer) return;
  try {
    const payment = props.accessToken ? await reservationService.publicPendingOnline(props.reservation.numero_reservation, props.accessToken) : await financeService.pendingOnline(props.reservation.id);
    if (payment) { amount.value = Number(payment.montant); message.value = payment.message; }
  } catch { /* The payment action reports an unavailable status endpoint explicitly. */ }
});
async function refresh() {
  const item = props.accessToken
    ? await reservationService.publicGet(props.reservation.numero_reservation, props.accessToken)
    : await reservationService.get(props.reservation.id);
  emit("updated", item);
}
async function pay() {
  if (busy.value) return;
  busy.value = true; error.value = ""; message.value = "";
  try {
    const storageKey = `payment-command:${props.reservation.id}:${amount.value}:${provider.value}`;
    let key: string = crypto.randomUUID();
    try {
      key = sessionStorage.getItem(storageKey) || key;
      sessionStorage.setItem(storageKey, key);
    } catch { /* The server still rejects competing payment attempts. */ }
    const digits = paymentPhone.value.replace(/\D/g, "");
    const validPhone =
      (digits.length === 10 && digits.startsWith("0")) ||
      (digits.length === 12 && digits.startsWith("261"));
    if (!validPhone) {
      error.value = "Renseignez un numéro Mobile Money malgache valide.";
      return;
    }
    const data = { montant: amount.value, fournisseur: provider.value, cle_idempotence: key, telephone_paiement: paymentPhone.value.trim() };
    const payment = props.accessToken
      ? await reservationService.publicPay(props.reservation.numero_reservation, props.accessToken, data)
      : await financeService.online({ ...data, id_reservation: props.reservation.id });
    message.value = payment.message;
    if (payment.statut === "ECHOUE") {
      try { sessionStorage.removeItem(storageKey); } catch { /* The failure remains visible. */ }
    }
    if (props.accessToken) {
      try { localStorage.setItem(`reservation-payment:${payment.reference_paiement}`, JSON.stringify({ reservationNumber: props.reservation.numero_reservation, token: props.accessToken })); } catch { /* Reference and access code remain on screen. */ }
    }
    if (payment.checkout_url) window.location.assign(payment.checkout_url);
    else await refresh();
  } catch (value) {
    error.value = userError(value, "Le paiement n’a pas pu être préparé. Consultez son état avant de réessayer.", "PAYMENT_RESUME_ERROR");
  } finally { busy.value = false; }
}
async function cancel() {
  if (busy.value) return;
  busy.value = true; error.value = "";
  try {
    const item = props.accessToken
      ? await reservationService.publicCancel(props.reservation.numero_reservation, props.accessToken)
      : await reservationService.cancel(props.reservation.id);
    confirming.value = false;
    message.value = Number(item.montant_a_rembourser) > 0
      ? "Réservation annulée. Le remboursement est à traiter par la gare."
      : "Réservation annulée.";
    emit("updated", item);
  } catch (value) { error.value = userError(value, "L’annulation n’a pas pu être effectuée.", "RESERVATION_CANCEL_ERROR"); }
  finally { busy.value = false; }
}
</script>

<template>
  <div class="reservation-actions" :aria-busy="busy">
    <details>
      <summary>Détails et actions de la réservation</summary>
      <p>État du règlement : <strong>{{ reservation.etat_paiement === 'REGLE' ? 'Réglé intégralement' : reservation.etat_paiement === 'ACOMPTE_RECU' ? 'Acompte reçu, solde restant' : reservation.etat_paiement === 'A_REMBOURSER' ? 'Remboursement à traiter' : reservation.etat_paiement === 'REMBOURSE' ? 'Remboursé' : 'Non réglé' }}</strong></p>
      <ul><li v-for="place in reservation.places" :key="place.id">Place {{ place.depart_place?.numero_place }} · {{ place.nom_passager }}</li></ul>
      <form v-if="reservation.peut_payer" class="reservation-payment-form" @submit.prevent="pay">
        <label>Moyen de paiement<select v-model="provider" :disabled="busy"><option value="MVOLA">MVola</option><option value="ORANGE_MONEY">Orange Money</option><option value="AIRTEL_MONEY">Airtel Money</option></select></label>
        <label>Numéro Mobile Money<input v-model.trim="paymentPhone" type="tel" inputmode="tel" autocomplete="tel" placeholder="034 00 000 00" minlength="10" maxlength="30" :disabled="busy" required /></label>
        <label>Montant en ariary<input v-model.number="amount" type="number" step="1" :min="Number(reservation.minimum_a_payer)" :max="Number(reservation.montant_restant)" :disabled="busy" required /></label>
        <button type="submit" :disabled="busy">{{ busy ? 'Préparation…' : `Payer ${formatMoney(amount)}` }}</button>
      </form>
      <p v-if="reservation.peut_annuler && reservation.date_limite_annulation && Number(reservation.montant_paye) > 0">Annulation possible jusqu’au {{ new Date(reservation.date_limite_annulation).toLocaleString('fr-FR') }}.</p>
      <button v-if="reservation.peut_annuler && !confirming" type="button" :disabled="busy" @click="confirming = true">Annuler la réservation</button>
      <div v-if="confirming" role="group" aria-label="Confirmation de l’annulation">
        <p>Les places seront libérées. Le remboursement éventuel sera suivi par la gare.</p>
        <button type="button" :disabled="busy" @click="cancel">Confirmer l’annulation</button>
        <button type="button" :disabled="busy" @click="confirming = false">Conserver ma réservation</button>
      </div>
    </details>
    <p v-if="message" role="status">{{ message }}</p>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
  </div>
</template>

<style scoped>
.reservation-actions { margin-top: 1rem; border-top: 1px solid var(--line); padding-top: 1rem; }
summary { cursor: pointer; color: var(--brand); font-weight: 700; min-height: 44px; }
.reservation-payment-form { display: flex; gap: .75rem; align-items: end; flex-wrap: wrap; margin: 1rem 0; }
label { display: grid; gap: .4rem; font-size: .875rem; }
input, select { min-height: 44px; border: 1px solid var(--line); border-radius: 8px; padding: .5rem; background: var(--surface); color: var(--ink-strong); max-width: 100%; }
button { min-height: 44px; margin: .25rem .5rem .25rem 0; border: 1px solid var(--brand); border-radius: 8px; padding: .5rem 1rem; background: var(--surface); color: var(--brand); cursor: pointer; }
button[type=submit] { background: var(--brand); color: white; }
button:disabled { opacity: .6; cursor: wait; }
.error { color: #9d3030; }
@media (max-width: 480px) { .reservation-payment-form, label { width: 100%; } }
</style>
