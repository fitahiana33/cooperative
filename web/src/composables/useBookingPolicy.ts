import { computed, onMounted, ref } from "vue";
import {
  reservationService,
  type BookingPolicy,
} from "../services/reservation/service";

/** Load per page: an administrator may have changed the policy since the last visit. */
export function useBookingPolicy() {
  const policy = ref<BookingPolicy | null>(null);
  const policyError = ref(false);
  const depositLabel = computed(() =>
    policy.value
      ? `${new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 2 }).format(policy.value.deposit_rate * 100)} %`
      : null,
  );
  async function loadPolicy() {
    policyError.value = false;
    try {
      policy.value = await reservationService.policy();
    } catch {
      policy.value = null;
      policyError.value = true;
    }
  }
  onMounted(loadPolicy);
  return { policy, policyError, depositLabel, loadPolicy };
}
