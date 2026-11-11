<script setup lang="ts">
import AuthLayout from "../../components/layout/AuthLayout.vue";
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthenticationStore } from "../../stores/authentication/store";
document.title = "Créer un compte | Coopérative";

const router = useRouter();
const route = useRoute();
const auth = useAuthenticationStore();

const name = ref("");
const firstName = ref("");
const email = ref("");
const telephone = ref("");
const address = ref("");
const password = ref("");
const confirmPassword = ref("");
const showPassword = ref(false);
const localError = ref("");

async function submit() {
  localError.value = "";
  if (password.value !== confirmPassword.value) {
    localError.value = "Les mots de passe ne correspondent pas.";
    return;
  }
  if (password.value.length < 8) {
    localError.value = "Le mot de passe doit contenir au moins 8 caractères.";
    return;
  }

  try {
    await auth.register({
      name: name.value,
      first_name: firstName.value,
      email: email.value,
      telephone: telephone.value,
      address: address.value,
      password: password.value,
    });
    const redirect =
      typeof route.query.redirect === "string" &&
      route.query.redirect.startsWith("/")
        ? route.query.redirect
        : { name: "client-space" };
    await router.push(redirect);
  } catch (error) {
    if (import.meta.env.DEV) console.error("[REGISTER_ERROR]", error);
  }
}
</script>

<template>
  <AuthLayout>
    <div>
      <h1>Créer un compte</h1>
      <p class="auth-lead">
        Créez votre espace client pour retrouver vos réservations et vos
        billets.
      </p>

      <form @submit.prevent="submit">
        <div class="form-row">
          <div>
            <label for="name">Nom</label>
            <input
              id="name"
              v-model="name"
              type="text"
              placeholder="Dupont"
              required
            />
          </div>
          <div>
            <label for="firstName">Prénom</label>
            <input
              id="firstName"
              v-model="firstName"
              type="text"
              placeholder="Jean"
              required
            />
          </div>
        </div>

        <label for="email">Adresse Email</label>
        <input
          id="email"
          v-model="email"
          type="email"
          placeholder="jean.dupont@example.com"
          required
        />

        <div class="form-row">
          <div>
            <label for="telephone">Téléphone (optionnel)</label>
            <input
              id="telephone"
              v-model="telephone"
              type="tel"
              placeholder="034 12 345 67"
            />
          </div>
          <div>
            <label for="address">Adresse / Ville</label>
            <input
              id="address"
              v-model="address"
              type="text"
              placeholder="Antananarivo"
            />
          </div>
        </div>

        <label for="password">Mot de passe</label>
        <div class="password-field">
          <input
            id="password"
            autocomplete="new-password"
            minlength="8"
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="Au moins 8 caractères"
            required
          />
          <button
            type="button"
            class="toggle-pwd"
            @click="showPassword = !showPassword"
          >
            {{ showPassword ? "Masquer" : "Afficher" }}
          </button>
        </div>

        <label for="confirmPassword">Confirmer le mot de passe</label>
        <input
          id="confirmPassword"
          autocomplete="new-password"
          v-model="confirmPassword"
          :type="showPassword ? 'text' : 'password'"
          placeholder="Répétez le mot de passe"
          required
        />

        <p v-if="localError || auth.error" class="form-error" role="alert">
          {{ localError || auth.error }}
        </p>

        <button class="primary-button" type="submit" :disabled="auth.loading">
          {{ auth.loading ? "Inscription…" : "Créer mon compte" }}
          <span>→</span>
        </button>
      </form>

      <div class="auth-switch">
        <span>Déjà un compte ?</span>
        <router-link to="/login" class="login-link">Se connecter</router-link>
      </div>
    </div>
  </AuthLayout>
</template>
