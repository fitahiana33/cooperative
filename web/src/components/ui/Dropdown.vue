<script setup lang="ts">
import { nextTick, onMounted, onBeforeUnmount, ref, useId } from "vue";
import AppIcon from "./AppIcon.vue";
const open = ref(false);
const root = ref<HTMLElement>();
const trigger = ref<HTMLButtonElement>();
const menuId = useId();
function close(restore = false) {
  open.value = false;
  if (restore) trigger.value?.focus();
}
async function toggle() {
  open.value = !open.value;
  if (open.value) {
    await nextTick();
    root.value
      ?.querySelector<HTMLElement>(".dropdown-menu button, .dropdown-menu a")
      ?.focus();
  }
}
function outside(e: PointerEvent) {
  if (!root.value?.contains(e.target as Node)) close();
}
function keyboard(e: KeyboardEvent) {
  if (e.key === "Escape") {
    e.preventDefault();
    close(true);
  }
  if (!open.value || !["ArrowDown", "ArrowUp", "Home", "End"].includes(e.key))
    return;
  const items = Array.from(
    root.value?.querySelectorAll<HTMLElement>(
      ".dropdown-menu button, .dropdown-menu a",
    ) || [],
  );
  if (!items.length) return;
  e.preventDefault();
  const index = items.indexOf(document.activeElement as HTMLElement);
  const next =
    e.key === "Home"
      ? 0
      : e.key === "End"
        ? items.length - 1
        : (index + (e.key === "ArrowDown" ? 1 : -1) + items.length) %
          items.length;
  items[next]?.focus();
}
function focusOut(e: FocusEvent) {
  if (!root.value?.contains(e.relatedTarget as Node)) close();
}
onMounted(() => document.addEventListener("pointerdown", outside));
onBeforeUnmount(() => document.removeEventListener("pointerdown", outside));
</script>
<template>
  <div ref="root" class="dropdown" @keydown="keyboard" @focusout="focusOut">
    <button
      ref="trigger"
      class="dropdown-trigger"
      type="button"
      :aria-expanded="open"
      :aria-controls="menuId"
      aria-label="Menu du compte"
      @click="toggle"
    >
      <slot name="trigger" /><AppIcon name="down" :size="15" />
    </button>
    <div v-if="open" :id="menuId" class="dropdown-menu" @click="close()">
      <slot />
    </div>
  </div>
</template>
