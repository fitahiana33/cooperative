import { watch, type Ref } from "vue";
import { useAuthenticationStore } from "../stores/authentication/store";

/** Preserve list filters across navigation, refreshes and browser restarts. */
export function useSessionFilters<T extends Record<string, Ref<unknown>>>(
  module: string,
  fields: T,
) {
  const auth = useAuthenticationStore();
  const key = `cooperative:filters:${auth.user?.id ?? "guest"}:${module}`;

  function restore(field: Ref<unknown>, value: unknown) {
    if (field.value instanceof Date && typeof value === "string") {
      const parsed = new Date(value);
      if (!Number.isNaN(parsed.getTime())) field.value = parsed;
      return;
    }
    if (
      field.value === null &&
      (value === null ||
        (typeof value === "string" && value.length <= 200) ||
        (typeof value === "number" && Number.isFinite(value)) ||
        typeof value === "boolean")
    ) {
      field.value = value;
      return;
    }
    if (
      typeof value === typeof field.value &&
      (typeof value !== "string" || value.length <= 200) &&
      (typeof value !== "number" || Number.isFinite(value))
    )
      field.value = value;
  }

  try {
    // Migrate preferences written by previous releases in sessionStorage.
    const legacy = sessionStorage.getItem(key);
    if (!localStorage.getItem(key) && legacy) localStorage.setItem(key, legacy);
    const saved: unknown = JSON.parse(localStorage.getItem(key) || "null");
    if (saved && typeof saved === "object")
      for (const [name, field] of Object.entries(fields)) {
        const value = (saved as Record<string, unknown>)[name];
        restore(field, value);
      }
    // Drop obsolete fields left by a previous screen version.
    localStorage.setItem(
      key,
      JSON.stringify(
        Object.fromEntries(
          Object.entries(fields).map(([name, field]) => [name, field.value]),
        ),
      ),
    );
  } catch {
    if (import.meta.env.DEV)
      console.info(
        "Préférences de liste indisponibles ; les filtres restent utilisables.",
      );
  }
  watch(
    () =>
      Object.fromEntries(
        Object.entries(fields).map(([name, field]) => [name, field.value]),
      ),
    (values) => {
      try {
        localStorage.setItem(key, JSON.stringify(values));
      } catch {
        if (import.meta.env.DEV)
          console.info(
            "Les préférences de liste ne peuvent pas être mémorisées dans cet onglet.",
          );
      }
    },
    { flush: "sync" },
  );
}
