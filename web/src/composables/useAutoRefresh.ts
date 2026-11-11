import { onBeforeUnmount, onMounted } from "vue";

/** Refresh operational data while the screen is active, never in the background. */
export function useAutoRefresh(refresh: () => void | Promise<void>, intervalMs = 60_000) {
  let timer: ReturnType<typeof setInterval> | undefined;
  let lastRun = Date.now();

  const run = () => {
    if (document.hidden || !navigator.onLine) return;
    lastRun = Date.now();
    void refresh();
  };
  const onFocus = () => {
    if (Date.now() - lastRun > Math.min(intervalMs, 30_000)) run();
  };

  onMounted(() => {
    timer = setInterval(run, intervalMs);
    window.addEventListener("focus", onFocus);
    window.addEventListener("online", run);
    document.addEventListener("visibilitychange", onFocus);
  });
  onBeforeUnmount(() => {
    if (timer) clearInterval(timer);
    window.removeEventListener("focus", onFocus);
    window.removeEventListener("online", run);
    document.removeEventListener("visibilitychange", onFocus);
  });
}
