<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import AppLayout from '../../../components/layout/AppLayout.vue'
import BaseCard from '../../../components/ui/BaseCard.vue'
import { userService } from '../../../services/user/service'
import { roleService } from '../../../services/role/service'
import type { User, UserCreate, UserUpdate } from '../../../models/user/model'
import type { Role } from '../../../models/role/model'
import { userError } from '../../../utils/errors'

const route = useRoute()
const router = useRouter()
const id = computed(() => route.params.id ? Number(route.params.id) : null)
const editing = computed(() => Boolean(id.value))
const title = computed(() => editing.value ? 'Modifier un utilisateur' : 'Ajouter un utilisateur')
const form = reactive({ name: '', first_name: '', email: '', telephone: '', address: '', password: '', role: 'passenger', is_active: true })
const roles = ref<Role[]>([])
const loading = ref(true)
const submitting = ref(false)
const error = ref('')

async function load() {
  try {
    const rolePage = await roleService.listRoles({ page: 1, page_size: 100, sort_by: 'libelle', sort_order: 'asc' })
    roles.value = rolePage.items
    if (id.value) {
      const user: User = await userService.get(id.value)
      Object.assign(form, { name: user.name, first_name: user.first_name || '', email: user.email, telephone: user.telephone || '', address: user.address || '', password: '', role: user.role, is_active: user.is_active })
    } else if (roles.value.length) form.role = roles.value.find(role => role.libelle === 'passenger')?.libelle || roles.value[0].libelle
  } catch (errorValue: unknown) { error.value = userError(errorValue, 'Impossible de charger les données du formulaire.', 'USER_FORM_LOAD_ERROR') }
  finally { loading.value = false }
}
async function submit() {
  if (submitting.value) return
  submitting.value = true; error.value = ''
  try {
    if (id.value) {
      const payload: UserUpdate = { name: form.name, first_name: form.first_name, email: form.email, telephone: form.telephone || undefined, address: form.address || undefined, is_active: form.is_active, ...(form.password ? { password: form.password } : {}) }
      await userService.update(id.value, payload)
    } else {
      const payload: UserCreate = { name: form.name, first_name: form.first_name, email: form.email, telephone: form.telephone || undefined, address: form.address || undefined, role: form.role, password: form.password }
      await userService.create(payload)
    }
    await router.push({ path: '/users', query: { success: id.value ? 'Utilisateur modifié avec succès.' : 'Utilisateur créé avec succès.' } })
  } catch (errorValue: unknown) { error.value = userError(errorValue, 'Enregistrement de l’utilisateur impossible.', 'USER_FORM_SAVE_ERROR') }
  finally { submitting.value = false }
}
onMounted(load)
</script>

<template>
  <AppLayout>
    <template #title>{{ title }}</template>
    <div class="page-intro"><div><p class="eyebrow">ADMINISTRATION</p><h2>{{ title }}</h2><p>Renseignez les informations du compte puis enregistrez.</p></div><RouterLink class="secondary-button" to="/users">Retour à la liste</RouterLink></div>
    <BaseCard><p v-if="loading" class="status-msg">Chargement des données en cours…</p><p v-else-if="error" class="error-banner">{{ error }}</p><form v-else class="management-form form-page user-form" @submit.prevent="submit"><div class="field-group"><label for="user-name">Nom <span>*</span></label><input id="user-name" v-model="form.name" required /></div><div class="field-group"><label for="user-first-name">Prénom <span>*</span></label><input id="user-first-name" v-model="form.first_name" required /></div><div class="field-group"><label for="user-email">Email <span>*</span></label><input id="user-email" v-model="form.email" type="email" required /></div><div class="field-group"><label for="user-phone">Téléphone</label><input id="user-phone" v-model="form.telephone" /></div><div class="field-group field-wide"><label for="user-address">Adresse</label><input id="user-address" v-model="form.address" /></div><div class="field-group"><label for="user-password">{{ editing ? 'Nouveau mot de passe' : 'Mot de passe' }} <span v-if="!editing">*</span></label><input id="user-password" v-model="form.password" type="password" :required="!editing" minlength="8" :placeholder="editing ? 'Laisser vide pour conserver' : ''" /></div><div v-if="!editing" class="field-group"><label for="user-role">Rôle initial <span>*</span></label><select id="user-role" v-model="form.role" required><option v-for="role in roles" :key="role.id" :value="role.libelle">{{ role.libelle }}</option></select></div><label v-if="editing" class="check-field"><input v-model="form.is_active" type="checkbox" /> Compte actif</label><p v-if="editing" class="field-hint field-wide">Pour attribuer plusieurs rôles, utilisez la page Rôles & permissions.</p><div class="form-actions"><button class="primary-button compact-button" type="submit" :disabled="submitting">{{ submitting ? 'Enregistrement…' : 'Enregistrer' }}</button><RouterLink class="secondary-button" to="/users">Annuler</RouterLink></div></form></BaseCard>
  </AppLayout>
</template>
