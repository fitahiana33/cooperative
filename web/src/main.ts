import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './styles/main.css'
import { useAuthenticationStore } from './stores/authentication/store'

const pinia = createPinia()
const auth = useAuthenticationStore(pinia)
auth.loadUser().finally(() => createApp(App).use(pinia).use(router).mount('#app'))
