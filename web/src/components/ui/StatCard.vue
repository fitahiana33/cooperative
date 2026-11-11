<script setup lang="ts">
import BaseCard from "./BaseCard.vue";
import AppIcon from "./AppIcon.vue";
defineProps<{
  label: string;
  value: string;
  detail: string;
  icon: string;
  tone: string;
}>();
const iconNames: Record<string, string> = {
  "◷": "clock",
  "▤": "ticket",
  "▦": "grid",
  "◈": "wallet",
  "!": "warning",
  "✓": "check",
};
</script>
<template>
  <BaseCard
    ><div class="stat-card">
      <div class="stat-card-top">
        <span class="stat-icon" :class="tone"
          ><AppIcon :name="iconNames[icon] || 'chart'" :size="18" /></span
        ><span class="stat-label">{{ label }}</span>
      </div>
      <strong class="stat-value" :class="{ 'stat-value--long': value.length > 9 }" :title="value">{{ value }}</strong
      ><span class="stat-detail">{{ detail }}</span>
    </div></BaseCard
  >
</template>

<style scoped>
.stat-card {
  min-width: 0;
}
.stat-card-top {
  min-width: 0;
}
.stat-label {
  min-width: 0;
  line-height: 1.3;
}
.stat-value {
  display: block;
  max-width: 100%;
  white-space: normal;
  overflow-wrap: anywhere;
  letter-spacing: 0;
  font-size: clamp(1.35rem, 2vw, 1.8rem);
  line-height: 1.15;
}
.stat-value--long {
  font-size: clamp(1.15rem, 1.6vw, 1.5rem);
}
.stat-detail {
  display: block;
  min-height: 1.25rem;
  line-height: 1.35;
}
@media (max-width: 1100px) and (min-width: 768px) {
  .stat-card-top {
    align-items: flex-start;
  }
  .stat-label {
    font-size: 0.75rem;
  }
  .stat-value {
    font-size: 1.35rem;
  }
}
</style>
