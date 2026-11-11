<script setup lang="ts">
import AuthLayout from "../../components/layout/AuthLayout.vue";
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthenticationStore } from "../../stores/authentication/store";
document.title = "Mot de passe oublié | Coopérative";

const router = useRouter();
const route = useRoute();
const auth = useAuthenticationStore();

const email = ref("");
const token = ref("");
const newPassword = ref("");
const showNewPassword = ref(false);
const isResetStep = ref(false);
const successMessage = ref("");

async function requestToken() {
  try {
    const res = await auth.forgotPassword({ email: email.value });
    successMessage.value =
      res.message || "Code de réinitialisation généré avec succès.";
    if (res.reset_url) {
      const resetToken = new URL(res.reset_url).searchParams.get("token");
      if (resetToken) token.value = resetToken;
    }
    isResetStep.value = true;
  } catch (error) {
    if (import.meta.env.DEV) console.error("[FORGOT_PASSWORD_ERROR]", error);
  }
}

async function submitReset() {
  try {
    const res = await auth.resetPassword({
      token: token.value,
      new_password: newPassword.value,
    });
    successMessage.value =
      res.message || "Mot de passe réinitialisé. Vous pouvez vous connecter.";
    setTimeout(() => {
      router.push({ name: "login" });
    }, 2000);
  } catch (error) {
    if (import.meta.env.DEV) console.error("[RESET_PASSWORD_ERROR]", error);
  }
}

onMounted(() => {
  const queryToken =
    typeof route.query.token === "string" ? route.query.token : "";
  if (queryToken) {
    token.value = queryToken;
    isResetStep.value = true;
  }
});
</script>

<template>
  <AuthLayout>
    <div>
      <h1>Mot de passe oublié</h1>
      <p class="auth-lead">
        {{
          isResetStep
            ? "Entrez le code reçu et votre nouveau mot de passe."
            : "Saisissez votre adresse email pour réinitialiser votre accès."
        }}
      </p>

      <p v-if="successMessage" class="form-success" role="status">
        {{ successMessage }}
      </p>
      <p v-if="auth.error" class="form-error" role="alert">{{ auth.error }}</p>

      <!-- Step 1: Email Request -->
      <form v-if="!isResetStep" @submit.prevent="requestToken">
        <label for="email">Adresse Email</label>
        <input
          id="email"
          v-model="email"
          type="email"
          placeholder="vous@exemple.com"
          required
        />

        <button class="primary-button" type="submit" :disabled="auth.loading">
          {{ auth.loading ? "Envoi en cours…" : "Envoyer les instructions" }}
          <span>→</span>
        </button>
      </form>

      <!-- Step 2: Reset Token & Password -->
      <form v-else @submit.prevent="submitReset">
        <label for="token">Code de réinitialisation</label>
        <input
          id="token"
          v-model="token"
          type="text"
          placeholder="Collez le code reçu par e-mail"
          required
        />

        <label for="newPassword">Nouveau mot de passe</label>
        <div class="password-field">
          <input
            id="newPassword"
            autocomplete="new-password"
            minlength="8"
            v-model="newPassword"
            :type="showNewPassword ? 'text' : 'password'"
            placeholder="Au moins 8 caractères"
            required
          />
          <button
            type="button"
            class="toggle-pwd"
            @click="showNewPassword = !showNewPassword"
          >
            {{ showNewPassword ? "Masquer" : "Afficher" }}
          </button>
        </div>

        <button class="primary-button" type="submit" :disabled="auth.loading">
          {{
            auth.loading ? "Réinitialisation…" : "Réinitialiser le mot de passe"
          }}
          <span>→</span>
        </button>
      </form>

      <div class="auth-switch">
        <router-link to="/login" class="login-link"
          >← Retour à la connexion</router-link
        >
      </div>
    </div>
  </AuthLayout>
</template>
