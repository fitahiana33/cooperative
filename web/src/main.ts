import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './styles/main.css'
import { useAuthenticationStore } from './stores/authentication/store'

const pinia = createPinia()
const auth = useAuthenticationStore(pinia)
window.addEventListener('auth:session-expired', () => {
  void auth.logout(false).then(() => {
    if (router.currentRoute.value.name !== 'login') void router.push({ name: 'login', query: { expired: '1' } })
  })
})
auth.loadUser().finally(() => createApp(App).use(pinia).use(router).mount('#app'))
