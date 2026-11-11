import { createApp } from "vue";
import { createPinia } from "pinia";
import router from "./router";
import App from "./App.vue";
import "./styles/main.css";
import "./styles/tokens.css";
import "./styles/workspace.css";
import "./styles/public.css";
import "./styles/public-home.css";
import "./styles/public-journey.css";
import "./styles/public-account.css";
import "./styles/auth.css";
import "./styles/sections.css";
import { useAuthenticationStore } from "./stores/authentication/store";

const pinia = createPinia();
const auth = useAuthenticationStore(pinia);
window.addEventListener("auth:session-expired", () => {
  void auth.logout(false).then(() => {
    if (router.currentRoute.value.name !== "frontoffice")
      void router.push({ name: "frontoffice" });
  });
});
async function bootstrap() {
  // Resolve the stored session before the first navigation guard runs, then
  // wait for the router's initial URL. This preserves a deep link on browser
  // refresh instead of briefly evaluating it with an empty user profile.
  await auth.loadUser();
  const app = createApp(App).use(pinia).use(router);
  await router.isReady();
  app.mount("#app");
}

void bootstrap();
