<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import type { User } from "../../models/user/model";
import { userService } from "../../services/user/service";
import { useAuthenticationStore } from "../../stores/authentication/store";

const props = withDefaults(defineProps<{ user: User; size?: number }>(), {
  size: 38,
});
const auth = useAuthenticationStore();
const source = ref("");
const initials = computed(() =>
  `${props.user.first_name?.charAt(0) || ""}${props.user.name.charAt(0)}`.toLocaleUpperCase(
    "fr",
  ),
);
let generation = 0;
function clear() {
  if (source.value) URL.revokeObjectURL(source.value);
  source.value = "";
}
watch(
  () => [props.user.id, props.user.photo_version, auth.token],
  async () => {
    const request = ++generation;
    clear();
    if (!props.user.photo_version || !auth.token) return;
    try {
      const blob = await userService.photo(
        props.user.id === auth.user?.id ? undefined : props.user.id,
      );
      if (request === generation) source.value = URL.createObjectURL(blob);
    } catch {
      /* Initials remain readable when the image is unavailable. */
    }
  },
  { immediate: true },
);
onBeforeUnmount(() => {
  generation++;
  clear();
});
</script>
<template>
  <span
    class="account-avatar"
    :style="{
      width: `${size}px`,
      height: `${size}px`,
      fontSize: `${size * 0.32}px`,
    }"
    aria-hidden="true"
  >
    <img v-if="source" :src="source" alt="" @error="clear" />
    <span v-else>{{ initials }}</span>
  </span>
</template>
<style scoped>
.account-avatar {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--brand-soft);
  color: var(--brand-dark);
  font-weight: 700;
  overflow: hidden;
  border: 1px solid var(--line);
  vertical-align: middle;
}
.account-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>
