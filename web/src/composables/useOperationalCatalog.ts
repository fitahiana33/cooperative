import { computed, ref } from "vue";
import type { Cooperative } from "../models/cooperative/model";
import type { Gare } from "../models/gare/model";
import type { Itineraire } from "../models/itineraire/model";
import { cooperativeService } from "../services/cooperative/service";
import { gareService } from "../services/gare/service";
import { itineraireService } from "../services/itineraire/service";
import { allPages } from "../services/pagination";

export function useOperationalCatalog() {
  const gares = ref<Gare[]>([]);
  const cooperatives = ref<Cooperative[]>([]);
  const itineraires = ref<Itineraire[]>([]);
  const loadingCatalog = ref(false);

  const gareOptions = computed(() =>
    gares.value.map((item) => ({ value: item.id, label: `${item.nom} · ${item.ville}` })),
  );
  const cooperativeOptions = computed(() =>
    cooperatives.value.map((item) => ({
      value: item.id,
      label: item.sigle ? `${item.sigle} · ${item.nom}` : item.nom,
    })),
  );
  const routeOptions = computed(() =>
    itineraires.value.map((item) => ({
      value: item.id,
      label: `${item.destination_depart?.nom || "Départ"} → ${item.destination_arrivee?.nom || "Destination"}`,
    })),
  );

  async function loadCatalog() {
    if (loadingCatalog.value || (gares.value.length && cooperatives.value.length && itineraires.value.length)) return;
    loadingCatalog.value = true;
    const [gareResult, cooperativeResult, routeResult] = await Promise.allSettled([
      allPages((params) => gareService.listGares(params), { page: 1, page_size: 100, sort_by: "nom", sort_order: "asc" }),
      allPages((params) => cooperativeService.listCooperatives(params), { page: 1, page_size: 100, sort_by: "nom", sort_order: "asc" }),
      allPages((params) => itineraireService.list(params), { page: 1, page_size: 100, sort_by: "created_at", sort_order: "asc" }),
    ]);
    if (gareResult.status === "fulfilled") gares.value = gareResult.value.items || [];
    if (cooperativeResult.status === "fulfilled") cooperatives.value = cooperativeResult.value.items || [];
    if (routeResult.status === "fulfilled") itineraires.value = routeResult.value.items || [];
    loadingCatalog.value = false;
  }

  return { gares, cooperatives, itineraires, gareOptions, cooperativeOptions, routeOptions, loadingCatalog, loadCatalog };
}
