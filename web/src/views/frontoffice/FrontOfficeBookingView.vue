<script setup lang="ts">
import { formatMoney } from "../../utils/money";
import PublicLayout from "../../components/layout/PublicLayout.vue";
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { departService } from "../../services/depart/service";
import {
  reservationService,
  type BookingPolicy,
} from "../../services/reservation/service";
import type {
  DepartPlace,
  PublicReservationCreate,
} from "../../models/reservation/model";
import type { PublicProgramme } from "../../models/depart/model";
import { userError } from "../../utils/errors";

const route = useRoute();
const departId = Number(route.query.depart_id);
const depart = ref<PublicProgramme | null>(null);
const places = ref<DepartPlace[]>([]);
const selected = ref<number[]>([]);
const name = ref("");
const phone = ref("");
const email = ref("");
const provider = ref<PublicReservationCreate["fournisseur"]>("MVOLA");
const paymentPhone = ref("");
const advance = ref(0);
const loading = ref(true);
const submitting = ref(false);
const error = ref("");
const createdReservation = ref("");
const reservationMinimum = ref<number | null>(null);
const accessToken = ref("");
const checkoutUrl = ref("");
const storageWarning = ref("");
const policy = ref<BookingPolicy | null>(null);
const commandKey = ref<string>(crypto.randomUUID());
const draftKey = `reservation-draft:${departId}`;
const paymentKey = ref("");
const previousReservation = ref("");
const step = ref(1);
const furthestStep = ref(1);
const stepTitles = [
  "Choisissez vos places",
  "Vos coordonnées",
  "Règlement",
  "Suivi de la réservation",
];
function validContact() {
  if (name.value.trim().length < 2 || phone.value.trim().length < 8) {
    error.value = "Renseignez le nom du réservataire et un téléphone valide.";
    return false;
  }
  if (
    email.value.trim() &&
    !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())
  ) {
    error.value = "Renseignez une adresse e-mail valide.";
    return false;
  }
  return true;
}
async function goStep(next: number) {
  if (submitting.value || createdReservation.value) return;
  error.value = "";
  if (next > 1 && !selected.value.length) {
    error.value = "Sélectionnez au moins une place.";
    return;
  }
  if (next > 2 && !validContact()) {
    step.value = 2;
    return;
  }
  step.value = next;
  furthestStep.value = Math.max(next, furthestStep.value);
  await nextTick();
  const heading = document.getElementById(`booking-step-${next}`);
  heading?.focus({ preventScroll: true });
  heading?.scrollIntoView({ block: "nearest" });
}

function startNewBooking() {
  if (submitting.value) return;
  previousReservation.value = createdReservation.value;
  try {
    sessionStorage.removeItem(draftKey);
  } catch {
    /* The current in-memory key is renewed. */
  }
  commandKey.value = crypto.randomUUID();
  paymentKey.value = "";
  createdReservation.value = "";
  reservationMinimum.value = null;
  accessToken.value = "";
  checkoutUrl.value = "";
  selected.value = [];
  error.value = "";
  step.value = 1;
  furthestStep.value = 1;
  void load();
}
const seatColumns = computed(
  () => depart.value?.vehicule?.places_par_rangee || 4,
);
const frontSeats = computed(() => depart.value?.vehicule?.places_avant || 0);
function seatStyle(number: number) {
  if (number <= frontSeats.value)
    return {
      gridRow: 1,
      gridColumn: seatColumns.value - frontSeats.value + number,
    };
  const index = number - frontSeats.value - 1;
  return {
    gridRow: Math.floor(index / seatColumns.value) + 2,
    gridColumn: (index % seatColumns.value) + 1,
  };
}
const requestedPassengers = computed(() =>
  Math.min(
    policy.value?.max_seats || 1,
    Math.max(1, Number(route.query.passengers) || 1),
  ),
);
const availablePlaces = computed(() =>
  places.value.filter((item) => item.statut === "DISPONIBLE"),
);
const total = computed(
  () => Number(depart.value?.tarif?.prix || 0) * selected.value.length,
);
const minimum = computed(
  () =>
    reservationMinimum.value ??
    Math.min(
      total.value,
      Math.max(
        policy.value?.minimum_deposit_amount || 0,
        Math.ceil(total.value * (policy.value?.deposit_rate || 0)),
      ),
    ),
);
const currency = computed(() => depart.value?.tarif?.devise || "MGA");
function price(value: number) {
  return formatMoney(value, currency.value);
}
function date(value?: string) {
  return value
    ? new Intl.DateTimeFormat("fr-FR", {
        weekday: "long",
        day: "2-digit",
        month: "long",
        year: "numeric",
      }).format(new Date(`${value}T00:00:00`))
    : "";
}
function togglePlace(id: number) {
  if (submitting.value || createdReservation.value) return;
  if (
    !selected.value.includes(id) &&
    selected.value.length >= (policy.value?.max_seats || 1)
  ) {
    error.value = `Vous pouvez réserver au maximum ${policy.value?.max_seats} places.`;
    return;
  }
  selected.value = selected.value.includes(id)
    ? selected.value.filter((item) => item !== id)
    : [...selected.value, id];
}
watch([minimum, total], () => {
  if (createdReservation.value) return;
  advance.value = total.value
    ? Math.min(total.value, Math.max(minimum.value, advance.value))
    : 0;
});
async function load() {
  if (!Number.isInteger(departId) || departId < 1) {
    error.value = "Le départ demandé est introuvable.";
    loading.value = false;
    return;
  }
  try {
    const [departure, available, rules] = await Promise.all([
      departService.publicGet(departId),
      reservationService.publicPlaces(departId),
      reservationService.policy(),
    ]);
    depart.value = departure;
    places.value = available;
    policy.value = rules;
    try {
      const draft = JSON.parse(
        sessionStorage.getItem(draftKey) || "null",
      ) as PublicReservationCreate | null;
      if (draft?.cle_idempotence) {
        commandKey.value = draft.cle_idempotence;
        name.value = draft.nom_reservataire;
        phone.value = draft.telephone_reservataire;
        paymentPhone.value = draft.telephone_reservataire;
        email.value = draft.email_reservataire || "";
        provider.value = draft.fournisseur;
        selected.value = draft.places.map((place) => place.id_depart_place);
        advance.value = draft.montant_avance;
        step.value = 3;
        furthestStep.value = 3;
      }
    } catch {
      /* Booking still works when session storage is unavailable. */
    }
  } catch (value) {
    if (import.meta.env.DEV) console.error("[PUBLIC_BOOKING_ERROR]", value);
    error.value = "Ce départ n’est plus disponible à la réservation.";
  } finally {
    loading.value = false;
  }
}
async function submit() {
  if (submitting.value) return;
  error.value = "";
  if (!selected.value.length) {
    error.value = "Sélectionnez au moins une place.";
    return;
  }
  if (name.value.trim().length < 2 || phone.value.trim().length < 8) {
    error.value = "Renseignez le nom du réservataire et un téléphone valide.";
    return;
  }
  if (
    email.value.trim() &&
    !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())
  ) {
    error.value = "Renseignez une adresse e-mail valide.";
    return;
  }
  if (
    !Number.isFinite(advance.value) ||
    advance.value < minimum.value ||
    advance.value > total.value
  ) {
    error.value = `L’avance doit être comprise entre ${price(minimum.value)} et ${price(total.value)}.`;
    return;
  }
  if (policy.value?.online_payment_enabled) {
    const digits = paymentPhone.value.replace(/\D/g, "");
    const valid =
      (digits.length === 10 && digits.startsWith("0")) ||
      (digits.length === 12 && digits.startsWith("261"));
    if (!valid) {
      error.value =
        "Renseignez le numéro Mobile Money qui autorisera le paiement.";
      return;
    }
  }
  submitting.value = true;
  try {
    const payload: PublicReservationCreate = {
      cle_idempotence: commandKey.value,
      id_depart: departId,
      places: selected.value.map((id) => ({
        id_depart_place: id,
        nom_passager: name.value.trim(),
      })),
      nom_reservataire: name.value.trim(),
      telephone_reservataire: phone.value.trim(),
      email_reservataire: email.value.trim() || undefined,
      montant_avance: advance.value,
      fournisseur: provider.value,
    };
    try {
      sessionStorage.setItem(draftKey, JSON.stringify(payload));
    } catch {
      /* Keep the in-memory retry key. */
    }
    const result = createdReservation.value
      ? {
          reservation: { numero_reservation: createdReservation.value },
          acompte_minimum: reservationMinimum.value,
          access_token: accessToken.value,
        }
      : await reservationService.publicCreate(payload);
    reservationMinimum.value = Number(result.acompte_minimum ?? minimum.value);
    createdReservation.value = result.reservation.numero_reservation;
    accessToken.value = result.access_token;
    step.value = 4;
    furthestStep.value = 4;
    try {
      localStorage.setItem(
        `reservation-access:${createdReservation.value}`,
        accessToken.value,
      );
    } catch {
      storageWarning.value =
        "Conservez la référence et le code d’accès affichés pour retrouver votre réservation.";
    }
    if (!policy.value?.online_payment_enabled) {
      error.value =
        "Réservation enregistrée. Réglez au guichet avant la fin du délai indiqué dans son suivi.";
      return;
    }
    if (advance.value < minimum.value) {
      advance.value = minimum.value;
      error.value = `Les conditions ont changé depuis votre estimation. L’acompte est de ${price(minimum.value)}. Vérifiez ce montant puis reprenez le paiement.`;
      return;
    }
    // The reservation and access code are available before any provider request.
    if (!paymentKey.value) paymentKey.value = `PAY-${commandKey.value}`;
    const payment = await reservationService.publicPay(
      createdReservation.value,
      accessToken.value,
      {
        montant: advance.value,
        fournisseur: provider.value,
        cle_idempotence: paymentKey.value,
        telephone_paiement: paymentPhone.value.trim(),
      },
    );
    checkoutUrl.value = payment.checkout_url || "";
    if (payment.statut === "ECHOUE") paymentKey.value = crypto.randomUUID();
    try {
      localStorage.setItem(
        `reservation-payment:${payment.reference_paiement}`,
        JSON.stringify({
          reservationNumber: createdReservation.value,
          token: accessToken.value,
        }),
      );
      // Keep the booking command until the customer explicitly starts another booking.
    } catch {
      /* The reference and token remain visible on this page. */
    }
    if (payment.checkout_url) window.location.assign(payment.checkout_url);
    else error.value = payment.message;
  } catch (value) {
    error.value = userError(
      value,
      "La réservation n’a pas pu être créée. Vérifiez les informations saisies.",
      "PUBLIC_BOOKING_ERROR",
    );
  } finally {
    submitting.value = false;
  }
}
watch(phone, (value, previous) => {
  if (!paymentPhone.value.trim() || paymentPhone.value === previous)
    paymentPhone.value = value;
});
onMounted(load);
</script>

<template>
  <PublicLayout class="booking-refactored" compact-footer>
    <section v-if="loading" class="booking-state">
      <h1>Préparation de votre voyage</h1>
      <p>Chargement du départ…</p>
    </section>
    <section
      v-else-if="error && !depart"
      class="booking-state error"
      role="alert"
    >
      <h1>Réservation indisponible</h1>
      <p>{{ error }}</p>
      <RouterLink class="booking-outline" to="/recherche"
        >Retour aux départs</RouterLink
      >
    </section>
    <template v-else-if="depart"
      ><section class="booking-heading">
        <div>
          <p>RÉSERVER UN VOYAGE</p>
          <h1>Préparez votre réservation.</h1>
          <span
            >Choisissez vos places, renseignez le nom du réservataire et payez
            l’avance depuis votre mobile.</span
          >
        </div>
      </section>
      <nav
        class="booking-steps booking-step-navigation"
        aria-label="Étapes de réservation"
      >
        <ol>
          <li
            v-for="(label, index) in [
              'Places',
              'Coordonnées',
              'Règlement',
              'Suivi',
            ]"
            :key="label"
          >
            <button
              type="button"
              :class="{
                active: step === index + 1,
                complete: step > index + 1,
              }"
              :aria-current="step === index + 1 ? 'step' : undefined"
              :disabled="
                submitting ||
                (createdReservation
                  ? index !== 3
                  : index + 1 > Math.min(3, furthestStep))
              "
              @click="goStep(index + 1)"
            >
              <b>{{ index + 1 }}</b
              >{{ label }}
            </button>
          </li>
        </ol>
      </nav>
      <div class="booking-trip-summary">
        <div>
          <strong
            >{{ depart.itineraire?.destination_depart?.nom }} →
            {{ depart.itineraire?.destination_arrivee?.nom }}</strong
          ><span
            >{{ date(depart.date_depart) }} ·
            {{ depart.heure_depart?.slice(0, 5) }}</span
          >
        </div>
        <div>
          <small>{{ selected.length }} place(s)</small
          ><strong>{{ price(total) }}</strong>
        </div>
        <details class="booking-mobile-details">
          <summary>Détails du voyage</summary>
          <p>
            Gare : {{ depart.gare?.nom || "À confirmer" }} · Coopérative :
            {{ depart.cooperative?.nom || "À confirmer" }} ·
            {{ price(Number(depart.tarif?.prix || 0)) }} par place.
          </p>
        </details>
      </div>
      <section class="booking-layout">
        <div class="booking-main">
          <article
            v-if="step === 1"
            class="booking-card"
            aria-labelledby="booking-step-1"
          >
            <div class="card-heading">
              <div>
                <p class="booking-kicker">ÉTAPE 1</p>
                <h2 id="booking-step-1" tabindex="-1">Choisissez vos places</h2>
              </div>
              <span>{{ availablePlaces.length }} disponible(s)</span>
            </div>
            <p class="hint">
              Votre recherche : {{ requestedPassengers }} passager(s).
              Sélectionnez une place par passager.
            </p>
            <div class="seat-legend">
              <span>□ Disponible</span><span>■ Sélectionnée</span
              ><span>▨ Indisponible</span>
            </div>
            <div
              class="seat-grid"
              :style="{
                gridTemplateColumns: `repeat(${seatColumns}, minmax(0, 48px))`,
              }"
            >
              <button
                v-for="placeItem in places"
                :key="placeItem.id"
                :style="seatStyle(placeItem.numero_place)"
                type="button"
                :class="['seat', { selected: selected.includes(placeItem.id) }]"
                :disabled="
                  placeItem.statut !== 'DISPONIBLE' ||
                  submitting ||
                  Boolean(createdReservation)
                "
                :aria-label="`Place ${placeItem.numero_place}, ${placeItem.statut.toLowerCase()}`"
                :aria-pressed="selected.includes(placeItem.id)"
                @click="togglePlace(placeItem.id)"
              >
                {{ placeItem.numero_place }}
              </button>
            </div>
            <p class="hint">
              Les places sont retenues pendant le délai de paiement de la
              réservation.
            </p>
            <div class="booking-stage-actions">
              <button
                type="button"
                class="booking-next"
                :disabled="!selected.length"
                @click="goStep(2)"
              >
                Continuer vers les coordonnées →
              </button>
            </div>
          </article>
          <form
            v-if="step === 2"
            class="booking-card"
            aria-labelledby="booking-step-2"
            @submit.prevent="goStep(3)"
          >
            <div class="card-heading">
              <div>
                <p class="booking-kicker">ÉTAPE 2</p>
                <h2 id="booking-step-2" tabindex="-1">Vos coordonnées</h2>
              </div>
              <span>Pas de compte nécessaire</span>
            </div>
            <div class="fields">
              <label
                >Nom du réservataire<input
                  v-model="name"
                  minlength="2"
                  autocomplete="name"
                  placeholder="Votre nom complet"
                  required /></label
              ><label
                >Téléphone<input
                  v-model="phone"
                  minlength="8"
                  type="tel"
                  autocomplete="tel"
                  placeholder="034 00 000 00"
                  required /></label
              ><label class="wide"
                >E-mail <small>(facultatif)</small
                ><input
                  v-model="email"
                  type="email"
                  autocomplete="email"
                  placeholder="vous@exemple.com"
              /></label>
            </div>
            <p class="hint">
              Un seul nom est nécessaire. Les noms des autres passagers restent
              facultatifs.
            </p>
            <div class="booking-stage-actions">
              <button type="button" class="booking-back" @click="goStep(1)">
                Retour aux places</button
              ><button type="submit" class="booking-next">
                Continuer vers le règlement →
              </button>
            </div>
          </form>
          <form
            v-if="step === 3"
            class="booking-card"
            aria-labelledby="booking-step-3"
            @submit.prevent="submit"
          >
            <div class="card-heading">
              <div>
                <p class="booking-kicker">ÉTAPE 3</p>
                <h2 id="booking-step-3" tabindex="-1">
                  {{
                    policy?.online_payment_enabled
                      ? "Payez votre avance"
                      : "Règlement au guichet"
                  }}
                </h2>
              </div>
              <span>{{
                policy?.online_payment_enabled
                  ? "Mobile money sécurisé"
                  : "Selon le délai de réservation"
              }}</span>
            </div>
            <p v-if="!policy?.online_payment_enabled" class="hint">
              Le paiement en ligne est indisponible pour le moment. Retrouvez le
              délai de règlement dans le suivi de votre réservation. Au guichet,
              le montant restant est à régler intégralement.
            </p>
            <div v-else class="fields">
              <label
                >Moyen de paiement<select v-model="provider">
                  <option value="MVOLA">MVola</option>
                  <option value="ORANGE_MONEY">Orange Money</option>
                  <option value="AIRTEL_MONEY">Airtel Money</option>
                </select></label
              ><label
                >Numéro Mobile Money<input
                  v-model.trim="paymentPhone"
                  type="tel"
                  inputmode="tel"
                  autocomplete="tel"
                  placeholder="034 00 000 00"
                  minlength="10"
                  maxlength="30"
                  required
                /><small
                  >Le compte qui recevra la demande de paiement. Il peut être
                  différent du numéro de contact.</small
                ></label
              ><label
                >Montant de l’avance ({{ currency }})<input
                  v-model.number="advance"
                  type="number"
                  :min="minimum"
                  :max="total"
                  step="1"
                  required
              /></label>
            </div>
            <div class="advance-box">
              <strong
                >Minimum à payer :
                {{
                  price(policy?.online_payment_enabled ? minimum : total)
                }}</strong
              ><span
                >Total : {{ price(total) }} · Solde éventuel :
                {{
                  price(
                    policy?.online_payment_enabled
                      ? Math.max(0, total - advance)
                      : 0,
                  )
                }}</span
              >
            </div>
            <div class="booking-stage-actions">
              <button
                type="button"
                class="booking-back"
                :disabled="submitting"
                @click="goStep(2)"
              >
                Retour aux coordonnées</button
              ><button
                class="booking-submit"
                type="submit"
                :disabled="submitting || !selected.length"
              >
                {{
                  submitting
                    ? "Enregistrement…"
                    : policy?.online_payment_enabled
                      ? "Continuer vers le paiement"
                      : "Réserver et régler au guichet"
                }}
                →
              </button>
            </div>
          </form>
          <article
            v-if="step === 4"
            class="booking-card"
            aria-labelledby="booking-step-4"
          >
            <p class="booking-kicker">ÉTAPE 4</p>
            <h2 id="booking-step-4" tabindex="-1">{{ stepTitles[3] }}</h2>
            <p>
              Référence : <strong>{{ createdReservation }}</strong
              >. Votre réservation reste accessible depuis son suivi.
            </p>
            <p v-if="submitting" role="status">Préparation du paiement…</p>
            <div v-if="storageWarning" class="booking-error" role="alert">
              <p>{{ storageWarning }}</p>
              <p>
                Référence : <strong>{{ createdReservation }}</strong>
              </p>
              <label
                >Code d’accès<input
                  :value="accessToken"
                  readonly
                  aria-label="Code d’accès à conserver"
                  @focus="($event.target as HTMLInputElement).select()"
              /></label>
              <a
                v-if="checkoutUrl"
                :href="checkoutUrl"
                target="_blank"
                rel="noopener noreferrer"
                >Ouvrir le paiement ↗</a
              >
            </div>
            <RouterLink
              v-if="createdReservation"
              class="booking-outline"
              :to="{
                name: 'public-reservation-lookup',
                query: { reference: createdReservation },
              }"
              >Retrouver la réservation {{ createdReservation }} →</RouterLink
            >
            <button
              v-if="createdReservation && !storageWarning"
              class="booking-outline"
              type="button"
              @click="startNewBooking"
            >
              Commencer une autre réservation
            </button>
            <RouterLink
              v-if="previousReservation && !createdReservation"
              :to="{
                name: 'public-reservation-lookup',
                query: { reference: previousReservation },
              }"
              >Retrouver la précédente réservation
              {{ previousReservation }}</RouterLink
            >
            <button
              v-if="policy?.online_payment_enabled"
              class="booking-submit"
              type="button"
              :disabled="submitting"
              @click="submit"
            >
              {{ submitting ? "Préparation…" : "Reprendre le paiement" }} →
            </button>
          </article>
          <p v-if="error" class="booking-error" role="alert">{{ error }}</p>
          <RouterLink
            v-if="previousReservation && !createdReservation"
            :to="{
              name: 'public-reservation-lookup',
              query: { reference: previousReservation },
            }"
            >Retrouver la précédente réservation
            {{ previousReservation }}</RouterLink
          >
        </div>
        <aside class="booking-summary">
          <div class="summary-sticky">
            <p class="booking-kicker">RÉCAPITULATIF</p>
            <h2>Votre voyage</h2>
            <div class="summary-route">
              <strong>{{
                depart.itineraire?.destination_depart?.nom || "Départ"
              }}</strong
              ><b>→</b
              ><strong>{{
                depart.itineraire?.destination_arrivee?.nom || "Destination"
              }}</strong>
            </div>
            <dl>
              <div>
                <dt>Date</dt>
                <dd>{{ date(depart.date_depart) }}</dd>
              </div>
              <div>
                <dt>Heure</dt>
                <dd>{{ depart.heure_depart?.slice(0, 5) }}</dd>
              </div>
              <div>
                <dt>Places</dt>
                <dd>{{ selected.length || "Aucune" }}</dd>
              </div>
              <div>
                <dt>Gare</dt>
                <dd>{{ depart.gare?.nom || "À confirmer" }}</dd>
              </div>
              <div>
                <dt>Coopérative</dt>
                <dd>{{ depart.cooperative?.nom || "À confirmer" }}</dd>
              </div>
            </dl>
            <div class="summary-price">
              <span>Total sélectionné</span><strong>{{ price(total) }}</strong>
            </div>
            <div class="summary-trust">
              <strong>Après le paiement</strong
              ><span
                >Les billets sont disponibles après confirmation du
                paiement.</span
              >
            </div>
          </div>
        </aside>
      </section></template
    >
  </PublicLayout>
</template>
