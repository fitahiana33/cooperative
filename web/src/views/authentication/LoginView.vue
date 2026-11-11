<script setup lang="ts">
import AuthLayout from "../../components/layout/AuthLayout.vue";
import AppIcon from "../../components/ui/AppIcon.vue";
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthenticationStore } from "../../stores/authentication/store";
document.title = "Connexion | Coopérative";

const router = useRouter();
const route = useRoute();
const sessionExpired = route.query.expired === "1";
const auth = useAuthenticationStore();

const email = ref("");
const password = ref("");
const showPassword = ref(false);

async function submit() {
  try {
    await auth.login({ email: email.value, password: password.value });
    const redirect =
      typeof route.query.redirect === "string" &&
      route.query.redirect.startsWith("/")
        ? route.query.redirect
        : {
            name:
              auth.user?.role?.toLowerCase() === "passenger"
                ? "client-space"
                : "home",
          };
    await router.push(redirect);
  } catch (error) {
    if (import.meta.env.DEV) console.error("[LOGIN_ERROR]", error);
  }
}
</script>

<template>
  <AuthLayout
    ><p class="auth-eyebrow">HEUREUX DE VOUS RETROUVER</p>
    <h1>Bienvenue à bord.</h1>
    <p class="auth-lead">
      Connectez-vous à votre espace voyageur ou à votre espace de gestion.
    </p>
    <form @submit.prevent="submit" :aria-busy="auth.loading">
      <label for="email">Adresse e-mail</label
      ><input
        id="email"
        v-model="email"
        type="email"
        autocomplete="username"
        placeholder="vous@exemple.com"
        required
      />
      <div class="auth-label-row">
        <label for="password">Mot de passe</label
        ><RouterLink to="/forgot-password">Mot de passe oublié ?</RouterLink>
      </div>
      <div class="password-field">
        <input
          id="password"
          v-model="password"
          :type="showPassword ? 'text' : 'password'"
          autocomplete="current-password"
          placeholder="Votre mot de passe"
          required
        /><button
          type="button"
          :aria-pressed="showPassword"
          aria-controls="password"
          @click="showPassword = !showPassword"
        >
          {{ showPassword ? "Masquer" : "Afficher" }}
        </button>
      </div>
      <p v-if="sessionExpired && !auth.error" class="form-error" role="status">
        Votre session a expiré. Reconnectez-vous.
      </p>
      <p
        v-if="auth.infoMessage && !auth.error"
        class="form-success"
        role="status"
      >
        {{ auth.infoMessage }}
      </p>
      <p v-if="auth.error" class="form-error" role="alert">{{ auth.error }}</p>
      <button class="primary-button" type="submit" :disabled="auth.loading">
        {{ auth.loading ? "Connexion…" : "Se connecter"
        }}<AppIcon name="arrow" :size="18" />
      </button>
    </form>
    <div class="auth-switch">
      <span>Votre première visite ?</span
      ><RouterLink to="/register">Créer un compte</RouterLink>
    </div>
  </AuthLayout>
</template>
