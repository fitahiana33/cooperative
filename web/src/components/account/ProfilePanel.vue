<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthenticationStore } from "../../stores/authentication/store";
import { userService } from "../../services/user/service";
import { userError } from "../../utils/errors";
import { roleLabels } from "../layout/navigation";
import UserAvatar from "../ui/UserAvatar.vue";
import PageTabs from "../ui/PageTabs.vue";
import PageTabPanel from "../ui/PageTabPanel.vue";

defineProps<{ publicPage?: boolean }>();
const auth = useAuthenticationStore();
const router = useRouter();
const tab = ref("information");
const profile = reactive({
  name: auth.user?.name || "",
  first_name: auth.user?.first_name || "",
  telephone: auth.user?.telephone || "",
  address: auth.user?.address || "",
});
const passwords = reactive({
  current_password: "",
  new_password: "",
  confirmation: "",
});
const busy = ref(false);
const error = ref("");
const success = ref("");
const photoInput = ref<HTMLInputElement>();
const role = computed(
  () => roleLabels[auth.user?.role || ""] || "Compte utilisateur",
);
async function perform(action: () => Promise<void>, message: string) {
  if (busy.value) return;
  busy.value = true;
  error.value = "";
  success.value = "";
  try {
    await action();
    success.value = message;
  } catch (value) {
    error.value = userError(
      value,
      "La modification n’a pas pu être enregistrée.",
      "PROFILE_ERROR",
    );
  } finally {
    busy.value = false;
  }
}
async function uploadPhoto(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  if (
    file.size > 4 * 1024 * 1024 ||
    !["image/jpeg", "image/png", "image/webp"].includes(file.type)
  ) {
    error.value = "Choisissez une photo JPEG, PNG ou WebP de 4 Mo maximum.";
    success.value = "";
    input.value = "";
    return;
  }
  await perform(async () => {
    auth.user = await userService.uploadPhoto(file);
  }, "Votre photo a été mise à jour.");
  input.value = "";
}
function save() {
  return perform(async () => {
    auth.user = await userService.updateMe(profile);
    Object.assign(profile, {
      name: auth.user.name,
      first_name: auth.user.first_name || "",
      telephone: auth.user.telephone || "",
      address: auth.user.address || "",
    });
  }, "Vos informations ont été enregistrées.");
}
function removePhoto() {
  return perform(async () => {
    auth.user = await userService.removePhoto();
  }, "Votre photo a été supprimée.");
}
async function changePassword() {
  if (passwords.new_password !== passwords.confirmation) {
    error.value = "Les deux nouveaux mots de passe doivent être identiques.";
    success.value = "";
    return;
  }
  await perform(async () => {
    await userService.changePassword({
      current_password: passwords.current_password,
      new_password: passwords.new_password,
    });
    passwords.current_password = "";
    passwords.new_password = "";
    passwords.confirmation = "";
    await auth.logout(false);
    auth.infoMessage =
      "Mot de passe modifié. Reconnectez-vous avec votre nouveau mot de passe.";
    await router.replace({ name: "login" });
  }, "");
}
</script>
<template>
  <section class="personal-profile" aria-labelledby="personal-profile-title">
    <div class="personal-intro">
      <p class="eyebrow">MON COMPTE</p>
      <component :is="publicPage ? 'h1' : 'h2'" id="personal-profile-title"
        >Mon profil</component
      >
      <p>Gérez vos informations personnelles et la sécurité de votre compte.</p>
    </div>
    <p v-if="error" class="error-banner" role="alert">{{ error }}</p>
    <p v-if="success" class="personal-success" role="status">{{ success }}</p>
    <div class="personal-grid">
      <aside
        v-if="auth.user"
        class="personal-identity"
        :class="{ 'personal-identity-security': tab === 'security' }"
        aria-label="Identité du compte"
      >
        <UserAvatar :user="auth.user" :size="96" />
        <h3>{{ auth.user.first_name }} {{ auth.user.name }}</h3>
        <span class="personal-role">{{ role }}</span>
        <p class="personal-email">{{ auth.user.email }}</p>
        <input
          id="profile-photo"
          ref="photoInput"
          class="sr-only"
          type="file"
          tabindex="-1"
          accept="image/jpeg,image/png,image/webp"
          :disabled="busy"
          aria-label="Choisir une photo de profil"
          @change="uploadPhoto"
        />
        <button
          class="secondary-button"
          type="button"
          :disabled="busy"
          @click="photoInput?.click()"
        >
          {{
            busy
              ? "Traitement…"
              : auth.user.photo_version
                ? "Changer la photo"
                : "Ajouter une photo"
          }}
        </button>
        <button
          v-if="auth.user.photo_version"
          class="personal-remove"
          type="button"
          :disabled="busy"
          @click="removePhoto"
        >
          Supprimer la photo
        </button>
        <small
          >JPEG, PNG ou WebP · 4 Mo maximum<br />10 millions de pixels
          maximum</small
        >
      </aside>
      <div class="personal-details" :aria-busy="busy">
        <PageTabs
          v-model="tab"
          :tabs="[
            { id: 'information', label: 'Informations' },
            { id: 'security', label: 'Sécurité' },
          ]"
          panel-prefix="profile"
          aria-label="Rubriques du profil"
        />
        <PageTabPanel
          prefix="profile"
          name="information"
          :active="tab === 'information'"
        >
          <form class="personal-form" @submit.prevent="save">
            <h3>Informations personnelles</h3>
            <div class="personal-fields">
              <label
                >Prénom<input
                  v-model.trim="profile.first_name"
                  required
                  maxlength="100"
                  autocomplete="given-name"
                  :disabled="busy"
              /></label>
              <label
                >Nom<input
                  v-model.trim="profile.name"
                  required
                  maxlength="100"
                  autocomplete="family-name"
                  :disabled="busy"
              /></label>
              <label class="personal-wide"
                >Adresse email<input
                  :value="auth.user?.email"
                  readonly
                  type="email"
                  autocomplete="email"
                  aria-describedby="profile-email-note"
                /><small id="profile-email-note"
                  >Pour changer votre adresse de connexion, contactez votre
                  administrateur.</small
                ></label
              >
              <label
                >Téléphone<input
                  v-model.trim="profile.telephone"
                  type="tel"
                  maxlength="30"
                  autocomplete="tel"
                  :disabled="busy"
              /></label>
              <label
                >Adresse<input
                  v-model.trim="profile.address"
                  maxlength="255"
                  autocomplete="street-address"
                  :disabled="busy"
              /></label>
            </div>
            <div class="personal-actions">
              <button class="primary-button" type="submit" :disabled="busy">
                Enregistrer les modifications
              </button>
            </div>
          </form>
        </PageTabPanel>
        <PageTabPanel
          prefix="profile"
          name="security"
          :active="tab === 'security'"
        >
          <form
            class="personal-form personal-security"
            @submit.prevent="changePassword"
          >
            <h3>Changer mon mot de passe</h3>
            <p>
              Après la modification, reconnectez-vous avec votre nouveau mot de
              passe sur chacun de vos appareils.
            </p>
            <label
              >Mot de passe actuel<input
                v-model="passwords.current_password"
                type="password"
                required
                maxlength="128"
                autocomplete="current-password"
                :disabled="busy"
            /></label>
            <label
              >Nouveau mot de passe<input
                v-model="passwords.new_password"
                type="password"
                required
                minlength="8"
                maxlength="128"
                autocomplete="new-password"
                :disabled="busy"
                aria-describedby="profile-password-note"
            /></label>
            <small id="profile-password-note"
              >Au moins 8 caractères, une lettre et un chiffre.</small
            >
            <label
              >Confirmer le nouveau mot de passe<input
                v-model="passwords.confirmation"
                type="password"
                required
                minlength="8"
                maxlength="128"
                autocomplete="new-password"
                :disabled="busy"
            /></label>
            <div class="personal-actions">
              <button class="primary-button" type="submit" :disabled="busy">
                Modifier le mot de passe
              </button>
            </div>
          </form>
        </PageTabPanel>
      </div>
    </div>
  </section>
</template>
<style scoped>
.personal-profile {
  max-width: 1120px;
  margin: 0 auto;
  color: var(--ink);
}
.personal-profile input.sr-only {
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  border: 0;
}
.personal-intro {
  margin-bottom: 24px;
}
.personal-intro :is(h1, h2) {
  margin: 6px 0;
  font-size: clamp(24px, 3vw, 32px);
  color: var(--ink-strong);
}
.personal-intro p {
  margin: 6px 0;
}
.personal-grid {
  display: grid;
  grid-template-columns: 270px minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}
.personal-identity,
.personal-details {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 16px;
  min-width: 0;
}
.personal-identity {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 28px 20px;
  text-align: center;
  gap: 12px;
}
.personal-identity h3 {
  margin: 2px 0;
  overflow-wrap: anywhere;
}
.personal-role {
  background: var(--brand-soft);
  color: var(--brand-dark);
  border-radius: 20px;
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 700;
}
.personal-email {
  font-size: 13px;
  overflow-wrap: anywhere;
  margin: 0 0 6px;
  max-width: 100%;
}
.personal-identity small {
  color: var(--ink-muted);
  line-height: 1.7;
  font-size: 11px;
}
.personal-remove {
  color: #a63830;
  background: none;
  border: 0;
  padding: 6px;
  font-size: 13px;
}
.personal-details {
  overflow: hidden;
}
.personal-details :deep(.page-tabs) {
  position: static;
  margin: 0;
  padding: 0 24px;
  display: flex;
  gap: 12px;
  overflow-x: auto;
  border-bottom: 1px solid var(--line);
}
.personal-details :deep(.page-tab) {
  flex-shrink: 0;
  padding: 16px 18px;
  border: 0;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--ink-muted);
  font-size: 13px;
  cursor: pointer;
}
.personal-details :deep(.page-tab.active) {
  color: var(--brand-dark);
  border-bottom-color: var(--brand);
  font-weight: 700;
}
.personal-profile .primary-button,
.personal-profile .secondary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 42px;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 10px 16px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  background: white;
  color: var(--ink-strong);
}
.personal-profile .primary-button {
  background: var(--brand);
  color: white;
  border-color: var(--brand);
}
.personal-profile .primary-button:hover:not(:disabled) {
  background: var(--brand-dark);
}
.personal-profile .secondary-button:hover:not(:disabled) {
  background: var(--canvas);
}
.personal-profile .error-banner {
  padding: 14px 18px;
  border: 1px solid #efc5bd;
  background: #fff1ee;
  border-radius: 8px;
  color: #9a3226;
}
.personal-form {
  padding: 24px;
}
.personal-form h3 {
  margin: 0 0 20px;
  color: var(--ink-strong);
}
.personal-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
.personal-wide {
  grid-column: 1 / -1;
}
.personal-form label {
  display: flex;
  flex-direction: column;
  gap: 7px;
  font-size: 13px;
  font-weight: 600;
}
.personal-form input {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid #cbd7d0;
  border-radius: 8px;
  padding: 11px 12px;
  font: inherit;
  color: var(--ink-strong);
  background: white;
  min-width: 0;
}
.personal-form input[readonly] {
  background: var(--canvas);
  color: var(--ink-muted);
}
.personal-form small {
  font-weight: 400;
  color: var(--ink-muted);
  font-size: 12px;
}
.personal-actions {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--line);
  display: flex;
  justify-content: flex-end;
}
.personal-success {
  padding: 14px 18px;
  background: var(--brand-soft);
  border-radius: 8px;
  color: var(--brand-dark);
}
.personal-security {
  max-width: 620px;
}
.personal-security label {
  margin-top: 18px;
}
.personal-security > p {
  font-size: 13px;
  margin-bottom: 20px;
}
@media (max-width: 760px) {
  .personal-grid {
    grid-template-columns: 1fr;
    gap: 18px;
  }
  .personal-identity {
    display: grid;
    grid-template-columns: 64px minmax(0, 1fr);
    text-align: left;
    padding: 20px;
    gap: 8px 14px;
  }
  .personal-identity :deep(.account-avatar) {
    width: 64px !important;
    height: 64px !important;
    grid-column: 1;
    grid-row: 1 / 4;
  }
  .personal-identity h3,
  .personal-identity .personal-role,
  .personal-identity .personal-email {
    grid-column: 2;
    margin: 0;
  }
  .personal-identity .personal-role {
    justify-self: start;
  }
  .personal-identity button,
  .personal-identity small {
    grid-column: 1 / -1;
    text-align: center;
  }
  .personal-identity-security .secondary-button,
  .personal-identity-security .personal-remove,
  .personal-identity-security small {
    display: none;
  }
  .personal-form {
    padding: 20px;
  }
  .personal-fields {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  .personal-intro {
    margin-bottom: 18px;
  }
  .personal-actions button {
    width: 100%;
  }
}
</style>
