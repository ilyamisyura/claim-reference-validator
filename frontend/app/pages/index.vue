<script setup lang="ts">
</script>

<template>
  <UDashboardPanel id="dashboard">
    <template #header>
      <UDashboardNavbar title="Dashboard">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <UCard>
        <template #header>
          <span class="font-medium">Welcome</span>
        </template>
        <div class="flex items-center justify-between gap-3">
          <div class="text-sm text-muted">Manage your projects: upload a document, review the reference list, and track claims linked to references.</div>
          <UButton to="/projects" icon="i-lucide-folder" label="Go to Projects" color="primary" />
        </div>
      </UCard>
    </template>
  </UDashboardPanel>
</template>
