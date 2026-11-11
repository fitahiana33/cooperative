<script setup lang="ts">
import UserAvatar from "../../../components/ui/UserAvatar.vue";
import { computed, onMounted, ref } from "vue";
import { RouterLink, useRoute } from "vue-router";
import AppLayout from "../../../components/layout/AppLayout.vue";
import BaseCard from "../../../components/ui/BaseCard.vue";
import ListToolbar from "../../../components/ui/ListToolbar.vue";
import PaginationControls from "../../../components/ui/PaginationControls.vue";
import { userService } from "../../../services/user/service";
import { roleService } from "../../../services/role/service";
import { userError } from "../../../utils/errors";
import type { User } from "../../../models/user/model";
import type { Role } from "../../../models/role/model";
import { useSessionFilters } from "../../../composables/useSessionFilters";

const users = ref<User[]>([]);
const route = useRoute();
const total = ref(0);
const page = ref(1);
const pages = ref(1);
const search = ref("");
const role = ref("");
const active = ref<"" | "true" | "false">("");
const createdFrom = ref("");
const createdTo = ref("");
const roles = ref<Role[]>([]);
const sortBy = ref("created_at");
const sortOrder = ref<"asc" | "desc">("desc");
const loading = ref(true);
const error = ref("");
const success = ref("");
const busyAction = ref<string | null>(null);
const hasFilters = computed(
  () => Boolean(search.value || role.value || active.value || createdFrom.value || createdTo.value),
);
useSessionFilters("users", { search, role, active, createdFrom, createdTo });

function roleLabel(user: User) {
  return user.roles?.length
    ? user.roles.map((role) => role.libelle.toUpperCase()).join(", ")
    : user.role.toUpperCase();
}

function showError(errorValue: unknown, fallback: string) {
  error.value = userError(errorValue, fallback, "USERS_ERROR");
  success.value = "";
}

async function load() {
  loading.value = true;
  error.value = "";
  success.value = "";
  try {
    const result = await userService.list({
      page: page.value,
      page_size: 20,
      search: search.value || undefined,
      role: role.value || undefined,
      is_active: active.value === "" ? undefined : active.value === "true",
      created_from: createdFrom.value || undefined,
      created_to: createdTo.value || undefined,
      sort_by: sortBy.value,
      sort_order: sortOrder.value,
    });
    users.value = result.items;
    total.value = result.total;
    pages.value = result.pages || 1;
  } catch (errorValue: unknown) {
    showError(errorValue, "Impossible de charger les utilisateurs.");
  } finally {
    loading.value = false;
  }
}

async function loadRoles() {
  try {
    roles.value = (await roleService.listRoles({ page: 1, page_size: 100, sort_by: "libelle", sort_order: "asc" })).items;
  } catch {
    // User filtering remains available by status and dates if roles cannot load.
  }
}

function applyFilters() {
  page.value = 1;
  void load();
}

function resetFilters() {
  search.value = "";
  role.value = "";
  active.value = "";
  createdFrom.value = "";
  createdTo.value = "";
  applyFilters();
}

async function toggle(user: User) {
  const key = `toggle-${user.id}`;
  if (busyAction.value) return;
  busyAction.value = key;
  error.value = "";
  try {
    Object.assign(user, await userService.toggle(user.id));
    success.value = "Statut utilisateur mis à jour.";
  } catch (errorValue: unknown) {
    showError(errorValue, "Modification du statut impossible.");
  } finally {
    busyAction.value = null;
  }
}

async function remove(user: User) {
  if (
    !window.confirm(
      `Supprimer l’utilisateur « ${user.first_name || ""} ${user.name} » ?`,
    )
  )
    return;
  const key = `delete-${user.id}`;
  if (busyAction.value) return;
  busyAction.value = key;
  error.value = "";
  try {
    await userService.delete(user.id);
    users.value = users.value.filter((item) => item.id !== user.id);
    total.value = Math.max(0, total.value - 1);
    success.value = "Utilisateur supprimé.";
  } catch (errorValue: unknown) {
    showError(errorValue, "Suppression de l’utilisateur impossible.");
  } finally {
    busyAction.value = null;
  }
}

function changeSort(column: string) {
  sortOrder.value =
    sortBy.value === column && sortOrder.value === "asc" ? "desc" : "asc";
  sortBy.value = column;
  page.value = 1;
  void load();
}

function changePage(next: number) {
  if (next >= 1 && next <= pages.value) {
    page.value = next;
    void load();
  }
}

onMounted(async () => {
  await Promise.all([load(), loadRoles()]);
  if (typeof route.query.success === "string")
    success.value = route.query.success;
});
</script>

<template>
  <AppLayout>
    <template #title>Utilisateurs</template>

    <div class="page-intro">
      <div>
        <p class="eyebrow">ADMINISTRATION</p>
        <h2>Utilisateurs</h2>
        <p>Consultez et gérez les comptes utilisateurs.</p>
      </div>
      <RouterLink class="primary-button compact-button" to="/users/new"
        >+ Ajouter</RouterLink
      >
    </div>

    <BaseCard>
      <div class="card-heading">
        <div>
          <h2>Utilisateurs enregistrés ({{ total }})</h2>
          <p>Consultez les informations détaillées et gérez les comptes.</p>
        </div>
      </div>
      <ListToolbar
        v-model="search"
        :loading="loading"
        :show-sort="false"
        placeholder="Rechercher par nom ou email"
        @search="
          page = 1;
          load();
        "
      />
      <form class="user-filters" @submit.prevent="applyFilters">
        <div class="user-filters-heading">
          <div>
            <strong>Filtres avancés</strong>
            <small>Combinez un rôle, un statut et une période de création.</small>
          </div>
          <button v-if="hasFilters" type="button" class="text-button" @click="resetFilters">
            Réinitialiser
          </button>
        </div>
        <label>Rôle
          <select v-model="role">
            <option value="">Tous les rôles</option>
            <option v-for="item in roles" :key="item.id" :value="item.libelle">{{ item.libelle }}</option>
          </select>
        </label>
        <label>Statut
          <select v-model="active">
            <option value="">Actifs et inactifs</option>
            <option value="true">Actifs</option>
            <option value="false">Inactifs</option>
          </select>
        </label>
        <label>Créé à partir du<input v-model="createdFrom" type="date" :max="createdTo || undefined" /></label>
        <label>Créé jusqu’au<input v-model="createdTo" type="date" :min="createdFrom || undefined" /></label>
        <button type="submit" class="secondary-button" :disabled="loading">Appliquer</button>
      </form>
      <p v-if="loading" class="status-msg" role="status">
        Chargement des utilisateurs…
      </p>
      <p v-else-if="error" class="error-banner" role="alert">{{ error }}</p>
      <p v-if="success" class="success-banner" role="status">{{ success }}</p>

      <div v-if="!loading && !error" class="table-scroll">
        <table class="data-table">
          <caption>
            Liste des utilisateurs enregistrés
          </caption>
          <thead>
            <tr>
              <th>
                <button
                  class="sort-button"
                  type="button"
                  @click="changeSort('name')"
                >
                  Utilisateur ↕
                </button>
              </th>
              <th>Email</th>
              <th>Rôles</th>
              <th>
                <button
                  class="sort-button"
                  type="button"
                  @click="changeSort('is_active')"
                >
                  Statut ↕
                </button>
              </th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td>
                <span
                  style="display: inline-flex; align-items: center; gap: 10px"
                  ><UserAvatar :user="user" :size="34" /><strong
                    >{{ user.first_name }} {{ user.name }}</strong
                  ></span
                >
              </td>
              <td>{{ user.email }}</td>
              <td>
                <span class="module-badge">{{ roleLabel(user) }}</span>
              </td>
              <td>
                <span
                  :class="[
                    'status-badge',
                    user.is_active ? 'active' : 'inactive',
                  ]"
                  >{{ user.is_active ? "Actif" : "Inactif" }}</span
                >
              </td>
              <td>
                <RouterLink
                  class="table-action table-link"
                  :to="`/users/${user.id}`"
                  >Détails</RouterLink
                >
                <RouterLink
                  class="table-action table-link"
                  :to="`/users/${user.id}/edit`"
                  >Modifier</RouterLink
                >
                <button
                  class="table-action"
                  :disabled="busyAction !== null"
                  @click="toggle(user)"
                >
                  {{
                    busyAction === `toggle-${user.id}`
                      ? "Traitement…"
                      : user.is_active
                        ? "Désactiver"
                        : "Activer"
                  }}
                </button>
                <button
                  class="table-action danger-action"
                  :disabled="busyAction !== null"
                  @click="remove(user)"
                >
                  {{
                    busyAction === `delete-${user.id}`
                      ? "Suppression…"
                      : "Supprimer"
                  }}
                </button>
              </td>
            </tr>
            <tr v-if="!users.length">
              <td colspan="5">
                <div class="empty-state">Aucun utilisateur trouvé.</div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <PaginationControls
        v-if="!loading && !error"
        :page="page"
        :pages="pages || 1"
        :total="total"
        :disabled="busyAction !== null"
        item-label="utilisateur(s)"
        @change="changePage"
      />
    </BaseCard>
  </AppLayout>
</template>

<style scoped>
.user-filters { align-items: end; background: #f7faf8; border: 1px solid var(--border, #dce5de); border-radius: 12px; display: grid; gap: 12px; grid-template-columns: repeat(5, minmax(0, 1fr)) auto; margin: 14px 0 18px; padding: 14px; }
.user-filters-heading { align-items: center; display: flex; grid-column: 1 / -1; justify-content: space-between; }
.user-filters-heading small { color: var(--text-muted, #637267); display: block; margin-top: 3px; }
.user-filters label { color: var(--text-muted, #56675d); display: grid; font-size: .8rem; font-weight: 650; gap: 6px; }
.user-filters select, .user-filters input { background: white; border: 1px solid var(--border, #cfdad2); border-radius: 8px; min-height: 42px; padding: 0 10px; width: 100%; }
.user-filters .secondary-button { min-height: 42px; }
@media (max-width: 1000px) { .user-filters { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 580px) { .user-filters { grid-template-columns: 1fr; } .user-filters .secondary-button { width: 100%; } }
</style>
