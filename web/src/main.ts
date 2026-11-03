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
    const currentRoute = router.currentRoute.value
    if (currentRoute.meta.layout === 'frontoffice' || !currentRoute.meta.requiresAuth) {
      if (currentRoute.name !== 'frontoffice') void router.push({ name: 'frontoffice' })
      return
    }
    if (currentRoute.name !== 'login') void router.push({ name: 'login', query: { expired: '1' } })
  })
})
auth.loadUser().finally(() => createApp(App).use(pinia).use(router).mount('#app'))
