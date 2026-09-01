<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthenticationStore } from '../../stores/authentication/store'

const router = useRouter()
const auth = useAuthenticationStore()

const name = ref('')
const firstName = ref('')
const email = ref('')
const telephone = ref('')
const address = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const localError = ref('')

async function submit() {
  localError.value = ''
  if (password.value !== confirmPassword.value) {
    localError.value = 'Les mots de passe ne correspondent pas.'
    return
  }
  if (password.value.length < 8) {
    localError.value = 'Le mot de passe doit contenir au moins 8 caractères.'
    return
  }

  try {
    await auth.register({
      name: name.value,
      first_name: firstName.value,
      email: email.value,
      telephone: telephone.value,
      address: address.value,
      password: password.value,
    })
    await router.push({ name: 'home' })
  } catch (error) {
    console.error('[REGISTER_ERROR]', error)
  }
}
</script>

<template>
  <main class="register-page">
    <div class="register-card">
      <div class="brand">
        <span class="brand-mark">C</span>
        <span>Coopérative</span>
      </div>

      <h2>Créer un compte</h2>
      <p class="subtitle">Rejoignez la plateforme et gérez vos réservations.</p>

      <form @submit.prevent="submit">
        <div class="form-row">
          <div>
            <label for="name">Nom</label>
            <input id="name" v-model="name" type="text" placeholder="Dupont" required />
          </div>
          <div>
            <label for="firstName">Prénom</label>
            <input id="firstName" v-model="firstName" type="text" placeholder="Jean" required />
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
            <input id="telephone" v-model="telephone" type="tel" placeholder="034 12 345 67" />
          </div>
          <div>
            <label for="address">Adresse / Ville</label>
            <input id="address" v-model="address" type="text" placeholder="Antananarivo" />
          </div>
        </div>

        <label for="password">Mot de passe</label>
        <div class="password-field">
          <input
            id="password"
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="Au moins 8 caractères"
            required
          />
          <button type="button" class="toggle-pwd" @click="showPassword = !showPassword">
            {{ showPassword ? 'Masquer' : 'Afficher' }}
          </button>
        </div>

        <label for="confirmPassword">Confirmer le mot de passe</label>
        <input
          id="confirmPassword"
          v-model="confirmPassword"
          :type="showPassword ? 'text' : 'password'"
          placeholder="Répétez le mot de passe"
          required
        />

        <p v-if="localError || auth.error" class="form-error">
          {{ localError || auth.error }}
        </p>

        <button class="primary-button" type="submit" :disabled="auth.loading">
          {{ auth.loading ? 'Inscription…' : 'Créer mon compte' }} <span>→</span>
        </button>
      </form>

      <div class="login-footer">
        <span>Déjà un compte ?</span>
        <router-link to="/login" class="login-link">Se connecter</router-link>
      </div>
    </div>
  </main>
</template>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  color: #f8fafc;
  padding: 2rem 1rem;
}

.register-card {
  width: 100%;
  max-width: 520px;
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

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
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
  color: #94a3b8;
  display: flex;
  gap: 0.5rem;
  justify-content: center;
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
