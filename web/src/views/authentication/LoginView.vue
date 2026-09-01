<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthenticationStore } from '../../stores/authentication/store'

const router = useRouter()
const auth = useAuthenticationStore()

const email = ref(import.meta.env.VITE_DEFAULT_ADMIN_EMAIL || '')
const password = ref(import.meta.env.VITE_DEFAULT_ADMIN_PASSWORD || '')
const showPassword = ref(false)

async function submit() {
  try {
    await auth.login({ email: email.value, password: password.value })
    await router.push({ name: 'home' })
  } catch {
    /* error exposed in auth.error */
  }
}
</script>

<template>
  <main class="login-page">
    <section class="login-visual">
      <div class="visual-content">
        <div class="brand brand-light">
          <span class="brand-mark">C</span>
          <span>Coopérative</span>
        </div>
        <div class="visual-copy">
          <p class="eyebrow-light">PLATEFORME DE GESTION</p>
          <h1>La gare routière,<br /><span>plus simple.</span></h1>
          <p>Centralisez vos opérations et offrez une expérience fluide à chaque passager.</p>
        </div>
        <div class="visual-footer">© 2026 Coopérative · Espace sécurisé</div>
      </div>
    </section>

    <section class="login-panel">
      <div class="login-card">
        <p class="eyebrow">BIENVENUE</p>
        <h2>Connectez-vous</h2>
        <p class="login-subtitle">Accédez à votre espace d’administration.</p>

        <form @submit.prevent="submit">
          <label for="email">Adresse email</label>
          <input
            id="email"
            v-model="email"
            type="email"
            autocomplete="username"
            placeholder="admin@cooperative.com"
            required
          />

          <div class="label-row">
            <label for="password">Mot de passe</label>
            <router-link to="/forgot-password" class="forgot-link">Mot de passe oublié ?</router-link>
          </div>

          <div class="password-field">
            <input
              id="password"
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="current-password"
              placeholder="Votre mot de passe"
              required
            />
            <button type="button" class="toggle-pwd" @click="showPassword = !showPassword">
              {{ showPassword ? 'Masquer' : 'Afficher' }}
            </button>
          </div>

          <p v-if="auth.error" class="form-error">{{ auth.error }}</p>

          <button class="primary-button" type="submit" :disabled="auth.loading">
            {{ auth.loading ? 'Connexion…' : 'Se connecter' }} <span>→</span>
          </button>
        </form>

        <div class="register-footer">
          <span>Pas encore de compte ?</span>
          <router-link to="/register" class="register-link">Créer un compte</router-link>
        </div>

        <p class="security-note">♢ Connexion protégée et sécurisée</p>
      </div>
    </section>
  </main>
</template>

<style scoped>
.login-page {
  display: flex;
  min-height: 100vh;
  background-color: #0f172a;
  color: #f8fafc;
  font-family: inherit;
}

.login-visual {
  flex: 1;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  padding: 3rem;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
}

.visual-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 700;
  font-size: 1.25rem;
}

.brand-mark {
  background: #3b82f6;
  color: white;
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.visual-copy h1 {
  font-size: 2.5rem;
  font-weight: 800;
  line-height: 1.2;
  margin: 1rem 0;
}

.visual-copy h1 span {
  color: #60a5fa;
}

.eyebrow-light {
  color: #94a3b8;
  font-size: 0.85rem;
  letter-spacing: 0.1em;
  font-weight: 600;
}

.login-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: rgba(30, 41, 59, 0.7);
  padding: 2.5rem;
  border-radius: 1.25rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.eyebrow {
  color: #3b82f6;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.1em;
}

.login-card h2 {
  font-size: 1.75rem;
  font-weight: 700;
  margin-top: 0.25rem;
}

.login-subtitle {
  color: #94a3b8;
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
}

label {
  display: block;
  font-size: 0.85rem;
  font-weight: 600;
  color: #cbd5e1;
  margin-bottom: 0.5rem;
  margin-top: 1rem;
}

.label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
}

.forgot-link {
  color: #60a5fa;
  font-size: 0.8rem;
  text-decoration: none;
}

.forgot-link:hover {
  text-decoration: underline;
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

.register-footer {
  margin-top: 1.5rem;
  text-align: center;
  font-size: 0.9rem;
  color: #94a3b8;
  display: flex;
  gap: 0.5rem;
  justify-content: center;
}

.register-link {
  color: #60a5fa;
  font-weight: 600;
  text-decoration: none;
}

.register-link:hover {
  text-decoration: underline;
}

.security-note {
  font-size: 0.75rem;
  color: #64748b;
  text-align: center;
  margin-top: 1.5rem;
}
</style>
