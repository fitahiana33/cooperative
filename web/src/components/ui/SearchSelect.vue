<script setup lang="ts" generic="T extends string | number | null | undefined">
import { computed, nextTick, onBeforeUnmount, ref, shallowRef, useAttrs, useId, watch } from "vue";
import AppIcon from "./AppIcon.vue";
defineOptions({ inheritAttrs: false });
const props = defineProps<{
  modelValue: T;
  options: Array<{ value: T; label: string }>;
  loadOptions?: (query: string) => Promise<Array<{ value: T; label: string }>>;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  emptyValue?: T;
  modelModifiers?: Record<string, boolean>;
}>();
const emit = defineEmits<{
  "update:modelValue": [value: T];
  change: [value: T];
}>();
const attrs = useAttrs();
const id = useId();
const open = ref(false);
const query = ref("");
const searching = ref(false);
const active = ref(0);
const input = ref<HTMLInputElement>();
const root = ref<HTMLElement>();
const remoteOptions = shallowRef<Array<{ value: T; label: string }>>([]);
const remoteSelected = shallowRef<{ value: T; label: string }>();
const remoteBusy = ref(false);
const remoteError = ref("");
let version = 0;
let debounce: ReturnType<typeof setTimeout> | undefined;
async function fetchOptions(term: string) {
  if (!props.loadOptions) return;
  const current = ++version;
  remoteBusy.value = true; remoteError.value = "";
  try {
    const options = await props.loadOptions(term);
    if (current === version) remoteOptions.value = options;
  } catch {
    if (current === version) { remoteOptions.value = []; remoteError.value = "Recherche indisponible. Réessayez."; }
  } finally { if (current === version) remoteBusy.value = false; }
}
onBeforeUnmount(() => { version++; clearTimeout(debounce); });
const empty = computed(() =>
  props.emptyValue !== undefined
    ? props.emptyValue
    : ((typeof props.modelValue === "number" ? 0 : "") as T),
);
const selected = computed(() =>
  props.options.find((option) => option.value === props.modelValue) || remoteOptions.value.find((option) => option.value === props.modelValue) || (remoteSelected.value?.value === props.modelValue ? remoteSelected.value : undefined),
);
const normalize = (value: string) =>
  value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("fr");
const matches = computed(() =>
  props.loadOptions ? (remoteBusy.value ? [] : remoteOptions.value) : props.options.filter(
    (option) =>
      !searching.value ||
      normalize(option.label).includes(normalize(query.value)),
  ),
);
const visible = computed(() => [
  ...(!props.required && (!searching.value || !query.value)
    ? [{ value: empty.value, label: props.placeholder || "Aucun" }]
    : []),
  ...matches.value.slice(0, 60),
]);
function show() {
  query.value = selected.value?.label || "";
  searching.value = false;
  active.value = 0;
  open.value = true;
  void fetchOptions("");
  void nextTick(() => input.value?.select());
}
function toggle() {
  if (open.value) {
    open.value = false;
    query.value = "";
  } else {
    input.value?.focus();
    show();
  }
}
function choose(value: T) {
  if (remoteBusy.value) return;
  remoteSelected.value = remoteOptions.value.find(option => option.value === value);
  emit("update:modelValue", value);
  emit("change", value);
  open.value = false;
  query.value = "";
}
function nativeChange(event: Event) {
  const value = (event.target as HTMLSelectElement).value;
  choose(
    props.options.find((option) => String(option.value) === value)?.value ??
      empty.value,
  );
}
function search(event: Event) {
  query.value = (event.target as HTMLInputElement).value;
  searching.value = true;
  if (props.loadOptions) {
    clearTimeout(debounce);
    version++;
    remoteBusy.value = true;
    debounce = setTimeout(() => void fetchOptions(query.value), 200);
  }
  active.value = 0;
  open.value = true;
}
function blur(event: FocusEvent) {
  if (!root.value?.contains(event.relatedTarget as Node)) {
    open.value = false;
    query.value = "";
  }
}
async function move(event: KeyboardEvent) {
  if (event.key === "Escape") {
    open.value = false;
    query.value = "";
    return;
  }
  if (event.key === "Enter" && open.value) {
    event.preventDefault();
    const option = visible.value[active.value];
    if (option) choose(option.value);
    return;
  }
  if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) return;
  event.preventDefault();
  open.value = true;
  active.value =
    event.key === "Home"
      ? 0
      : event.key === "End"
        ? visible.value.length - 1
        : Math.max(
            0,
            Math.min(
              active.value + (event.key === "ArrowDown" ? 1 : -1),
              visible.value.length - 1,
            ),
          );
  await nextTick();
  document
    .getElementById(`${id}-${active.value}`)
    ?.scrollIntoView({ block: "nearest" });
}
watch([() => props.required, selected, input], () => {
  input.value?.setCustomValidity(
    props.required && !selected.value
      ? "Choisissez une option dans la liste."
      : "",
  );
});
watch(
  () => props.disabled,
  (disabled) => {
    if (disabled) open.value = false;
  },
);
</script>
<template>
  <select
    v-if="!loadOptions && options.length <= 20"
    v-bind="attrs"
    :value="modelValue ?? ''"
    :disabled="disabled"
    :required="required"
    @change="nativeChange"
  >
    <option :value="empty ?? ''" :disabled="required">
      {{ placeholder || "Choisir…" }}
    </option>
    <option
      v-for="option in options"
      :key="String(option.value)"
      :value="option.value"
    >
      {{ option.label }}
    </option>
  </select>
  <div v-else ref="root" class="search-select" @focusout="blur">
    <div class="search-select-control">
      <input
        v-bind="attrs"
        ref="input"
        type="text"
        role="combobox"
        autocomplete="off"
        :value="open ? query : selected?.label || ''"
        :placeholder="open ? 'Rechercher…' : placeholder || 'Choisir…'"
        :disabled="disabled"
        :required="required"
        :aria-expanded="open"
        :aria-controls="id"
        :aria-activedescendant="
          open && visible.length ? `${id}-${active}` : undefined
        "
        aria-autocomplete="list"
        @focus="show"
        @input="search"
        @keydown="move"
      /><button
        type="button"
        tabindex="-1"
        :disabled="disabled"
        aria-label="Afficher les options"
        @mousedown.prevent="toggle"
      >
        <AppIcon name="down" :size="16" />
      </button>
    </div>
    <div v-if="open" class="search-select-popover">
      <ul :id="id" role="listbox">
        <li
          v-for="(option, index) in visible"
          :id="`${id}-${index}`"
          :key="String(option.value)"
          role="option"
          :aria-selected="option.value === modelValue"
          :class="{
            highlighted: active === index,
            selected: option.value === modelValue,
          }"
          @mousemove="active = index"
          @mousedown.prevent="choose(option.value)"
        >
          {{ option.label
          }}<AppIcon
            v-if="option.value === modelValue"
            name="check"
            :size="15"
          />
        </li>
      </ul>
      <p v-if="remoteBusy" role="status">Recherche en cours…</p>
      <p v-else-if="remoteError" role="alert">{{ remoteError }}</p>
      <p v-else-if="!visible.length">Aucun résultat. Essayez un autre terme.</p>
      <p v-else-if="matches.length > 60">
        {{ Math.min(matches.length, 60) }} sur {{ matches.length }} résultats.
        Précisez la recherche.
      </p>
    </div>
  </div>
</template>
<style scoped>
.search-select {
  position: relative;
  min-width: 0;
  width: 100%;
}
.search-select-control {
  position: relative;
}
.search-select-control input {
  padding-right: 38px !important;
}
.search-select-control button {
  position: absolute;
  top: 0;
  right: 0;
  display: grid;
  place-items: center;
  width: 38px;
  height: 100%;
  padding: 0;
  color: #61745b;
  background: transparent;
}
.search-select-popover {
  position: absolute;
  z-index: 25;
  top: calc(100% + 5px);
  right: 0;
  left: 0;
  min-width: 180px;
  max-height: 310px;
  overflow: auto;
  border: 1px solid #d9e3d2;
  border-radius: 9px;
  background: #fff;
  box-shadow: 0 8px 28px #23422e1a;
}
.search-select-popover ul {
  margin: 0;
  padding: 5px;
  list-style: none;
}
.search-select-popover li {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  padding: 11px;
  border-radius: 5px;
  color: #425d39;
  font: 400 13px/1.5 var(--font-body);
  cursor: pointer;
}
.search-select-popover li.highlighted,
.search-select-popover li:hover {
  background: #f0f5e8;
}
.search-select-popover li.selected {
  color: #245b3c;
  font-weight: 600;
}
.search-select-popover p {
  padding: 12px;
  margin: 0;
  color: #6d805c;
  font-size: 12px;
}
</style>
