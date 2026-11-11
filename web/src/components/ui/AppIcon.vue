<script setup lang="ts">
withDefaults(defineProps<{ name: string; size?: number }>(), { size: 20 });
const paths: Record<string, string> = {
  grid: "M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z",
  bus: "M5 17h14V5a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v12Z M5 10h14 M8 3v7 M16 3v7 M7 17v3 M17 17v3 M8 14h.01 M16 14h.01",
  calendar:
    "M8 2v4 M16 2v4 M3 10h18 M5 4h14a2 2 0 0 1 2 2v14H3V6a2 2 0 0 1 2-2Z M7 14h2 M13 14h4 M7 18h2",
  ticket:
    "M3 7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v3a2 2 0 0 0 0 4v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-3a2 2 0 0 0 0-4V7Z M15 5v3 M15 11v2 M15 16v3",
  check: "m5 12 4 4L19 6",
  scan: "M8 3H3v5 M16 3h5v5 M3 16v5h5 M21 16v5h-5 M7 12h10 M9 8h6v8H9z",
  pin: "M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z M15 10a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z",
  users:
    "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M13 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z M17 3a4 4 0 0 1 0 8 M22 21v-2a4 4 0 0 0-3-3.87",
  user: "M20 21v-2a6 6 0 0 0-6-6h-4a6 6 0 0 0-6 6v2 M16 6a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z",
  building:
    "M4 21V7l8-4 8 4v14 M2 21h20 M9 21v-6h6v6 M8 9h1 M15 9h1 M8 12h1 M15 12h1",
  route:
    "M6 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z M18 22a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z M6 8v7a4 4 0 0 0 4 4h5 M9 5h5a4 4 0 0 1 4 4v7",
  wallet:
    "M21 8H5a3 3 0 0 1 0-6h13v6 M3 5v14a2 2 0 0 0 2 2h16V8 M21 12h-5v5h5 M17 14.5h.01",
  chart: "M3 3v18h18 M7 16v-5 M12 16V7 M17 16v-9",
  file: "M14 2H4v20h16V8l-6-6Z M14 2v6h6 M8 12h8 M8 16h8",
  shield: "m12 2 9 4v6c0 6-9 10-9 10S3 18 3 12V6l9-4Z m-4 10 3 3 5-6",
  settings:
    "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z M12 2v3 M12 19v3 M2 12h3 M19 12h3 M5 5l2 2 M17 17l2 2 M19 5l-2 2 M7 17l-2 2",
  bell: "M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9 M10 21h4",
  search: "M21 21l-5-5 M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0Z",
  filter: "M3 5h18 M6 12h12 M10 19h4",
  arrow: "M4 12h16 m-6-6 6 6-6 6",
  back: "M20 12H4 m6-6-6 6 6 6",
  chevron: "m9 5 7 7-7 7",
  down: "m6 9 6 6 6-6",
  menu: "M3 6h18 M3 12h18 M3 18h18",
  close: "m6 6 12 12 M6 18 18 6",
  logout: "M9 3H3v18h6 M9 12h12 m-5-5 5 5-5 5",
  external: "M15 3h6v6 M21 3 10 14 M10 3H3v18h18v-7",
  clock: "M12 8v5l3 2 M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0Z",
  refresh:
    "M20 7v5h-5 M4 17v-5h5 M6 6a8 8 0 0 1 13 2l1 4 M4 12l1 4a8 8 0 0 0 13 2",
  plus: "M12 5v14 M5 12h14",
  help: "M9 9a3 3 0 1 1 5 2c-2 1-2 2-2 3 M12 17h.01 M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0Z",
  warning: "m12 3 10 18H2L12 3Z M12 9v4 M12 17h.01",
  sun: "M12 2v2 M12 20v2 M2 12h2 M20 12h2 M5 5l2 2 M17 17l2 2 M5 19l2-2 M17 7l2-2 M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z",
};
</script>
<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.65"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    class="app-icon"
  >
    <path :d="paths[name] || paths.grid" />
  </svg>
</template>
