import { onBeforeUnmount, ref, watch, type UnwrapNestedRefs } from "vue";

export function useFormDraft<T extends Record<string, unknown>>(
  key: string,
  form: UnwrapNestedRefs<T>,
  enabled = true,
) {
  const restored = ref(false);
  const lastSaved = ref<Date | null>(null);
  const dirty = ref(false);
  let timer: ReturnType<typeof setTimeout> | undefined;
  const storageKey = `cooperative:draft:${key}`;

  if (enabled) {
    try {
      const saved = JSON.parse(localStorage.getItem(storageKey) || "null");
      if (saved?.values && typeof saved.values === "object") {
        Object.assign(form, saved.values);
        restored.value = true;
        lastSaved.value = saved.at ? new Date(saved.at) : null;
      }
    } catch { /* a damaged draft must never block the form */ }
  }

  const stop = watch(
    () => JSON.parse(JSON.stringify(form)) as T,
    (values) => {
      if (!enabled) return;
      dirty.value = true;
      clearTimeout(timer);
      timer = setTimeout(() => {
        const at = new Date();
        try { localStorage.setItem(storageKey, JSON.stringify({ at: at.toISOString(), values })); } catch { return; }
        lastSaved.value = at;
      }, 500);
    },
    { deep: true },
  );
  const warn = (event: BeforeUnloadEvent) => {
    if (!enabled || !dirty.value) return;
    event.preventDefault();
  };
  if (enabled) window.addEventListener("beforeunload", warn);
  onBeforeUnmount(() => { stop(); clearTimeout(timer); window.removeEventListener("beforeunload", warn); });

  function clear() {
    dirty.value = false;
    try { localStorage.removeItem(storageKey); } catch { /* optional storage */ }
  }
  return { restored, lastSaved, dirty, clear };
}
