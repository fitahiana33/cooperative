<script setup lang="ts">
import ClientNavigation from "../../components/layout/ClientNavigation.vue";
import PublicLayout from "../../components/layout/PublicLayout.vue";
import ProfilePanel from "../../components/account/ProfilePanel.vue";
</script>
<template>
  <PublicLayout compact-footer
    ><ClientNavigation />
    <div class="client-personal-profile"><ProfilePanel public-page /></div
  ></PublicLayout>
</template>
<style scoped>
.client-personal-profile {
  max-width: 1160px;
  margin: 0 auto;
  padding: 28px 24px 48px;
}
@media (max-width: 600px) {
  .client-personal-profile {
    padding: 20px 16px 32px;
  }
}
</style>
