<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthenticationStore } from '../../stores/authentication/store'

const router = useRouter()
const auth = useAuthenticationStore()

const email = ref('')
const token = ref('')
const newPassword = ref('')
const showNewPassword = ref(false)
const isResetStep = ref(false)
const successMessage = ref('')

async function requestToken() {
  try {
    const res = await auth.forgotPassword({ email: email.value })
    successMessage.value = res.message || 'Jeton de réinitialisation généré avec succès.'
    isResetStep.value = true
  } catch {
    /* error captured by store */
  }
}

async function submitReset() {
  try {
    const res = await auth.resetPassword({
      token: token.value,
      new_password: newPassword.value,
    })
    successMessage.value = res.message || 'Mot de passe réinitialisé. Vous pouvez vous connecter.'
    setTimeout(() => {
      router.push({ name: 'login' })
    }, 2000)
  } catch {
    /* error captured by store */
  }
}
</script>

<template>
  <main class="forgot-page">
    <div class="forgot-card">
      <div class="brand">
        <span class="brand-mark">C</span>
        <span>Coopérative</span>
      </div>

      <h2>Mot de passe oublié</h2>
      <p class="subtitle">
        {{
          isResetStep
            ? 'Entrez le jeton reçu et votre nouveau mot de passe.'
            : 'Saisissez votre adresse email pour réinitialiser votre accès.'
        }}
      </p>

      <p v-if="successMessage" class="form-success">{{ successMessage }}</p>
      <p v-if="auth.error" class="form-error">{{ auth.error }}</p>

      <!-- Step 1: Email Request -->
      <form v-if="!isResetStep" @submit.prevent="requestToken">
        <label for="email">Adresse Email</label>
        <input
          id="email"
          v-model="email"
          type="email"
          placeholder="admin@cooperative.com"
          required
        />

        <button class="primary-button" type="submit" :disabled="auth.loading">
          {{ auth.loading ? 'Envoi en cours…' : 'Envoyer les instructions' }} <span>→</span>
        </button>
      </form>

      <!-- Step 2: Reset Token & Password -->
      <form v-else @submit.prevent="submitReset">
        <label for="token">Jeton de réinitialisation</label>
        <input
          id="token"
          v-model="token"
          type="text"
          placeholder="Entrez le jeton JWT"
          required
        />

        <label for="newPassword">Nouveau mot de passe</label>
        <div class="password-field">
          <input
            id="newPassword"
            v-model="newPassword"
            :type="showNewPassword ? 'text' : 'password'"
            placeholder="Au moins 8 caractères"
            required
          />
          <button type="button" class="toggle-pwd" @click="showNewPassword = !showNewPassword">
            {{ showNewPassword ? 'Masquer' : 'Afficher' }}
          </button>
        </div>

        <button class="primary-button" type="submit" :disabled="auth.loading">
          {{ auth.loading ? 'Réinitialisation…' : 'Réinitialiser le mot de passe' }} <span>→</span>
        </button>
      </form>

      <div class="login-footer">
        <router-link to="/login" class="login-link">← Retour à la connexion</router-link>
      </div>
    </div>
  </main>
</template>

<style scoped>
.forgot-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  color: #f8fafc;
  padding: 2rem 1rem;
}

.forgot-card {
  width: 100%;
  max-width: 440px;
  background: rgba(30, 41, 59, 0.85);
  padding: 2.5rem;
  border-radius: 1.25rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.35);
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 700;
  font-size: 1.2rem;
  margin-bottom: 1.5rem;
}

.brand-mark {
  background: #3b82f6;
  color: white;
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

h2 {
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0;
}

.subtitle {
  color: #94a3b8;
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
}

label {
  display: block;
  font-size: 0.85rem;
  font-weight: 600;
  color: #cbd5e1;
  margin-top: 1rem;
  margin-bottom: 0.4rem;
}

input {
  width: 100%;
  padding: 0.75rem 1rem;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 0.5rem;
  color: white;
  font-size: 0.95rem;
  outline: none;
  transition: border-color 0.2s;
}

input:focus {
  border-color: #3b82f6;
}

.password-field {
  position: relative;
  display: flex;
  align-items: center;
}

.toggle-pwd {
  position: absolute;
  right: 0.75rem;
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 0.8rem;
  cursor: pointer;
}

.form-error {
  color: #f87171;
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
  padding: 0.6rem 0.8rem;
  border-radius: 0.5rem;
  font-size: 0.85rem;
  margin-top: 1rem;
}

.form-success {
  color: #34d399;
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.3);
  padding: 0.6rem 0.8rem;
  border-radius: 0.5rem;
  font-size: 0.85rem;
  margin-top: 1rem;
}

.primary-button {
  width: 100%;
  padding: 0.85rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  margin-top: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: background 0.2s;
}

.primary-button:hover:not(:disabled) {
  background: #1d4ed8;
}

.login-footer {
  margin-top: 1.5rem;
  text-align: center;
  font-size: 0.9rem;
}

.login-link {
  color: #60a5fa;
  font-weight: 600;
  text-decoration: none;
}

.login-link:hover {
  text-decoration: underline;
}
</style>
