<script setup lang="ts">
import { useQueryClient } from '@tanstack/vue-query'
import {
  useListProjects,
  useDeleteProject
} from '@lib/api/v1/endpoints/projects'

const queryClient = useQueryClient()

const page = ref(1)
const pageSize = ref(20)

const list = useListProjects(
  computed(() => ({ page: page.value, pageSize: pageSize.value }))
)
const rows = computed(() => list.data.value?.data?.data ?? [])
const total = computed(() => list.data.value?.data?.total ?? 0)
const totalPages = computed(() => list.data.value?.data?.total_pages ?? 1)

const deleteMutation = useDeleteProject({
  mutation: {
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: list.queryKey })
    }
  }
})

function onDelete(row: any) {
  const p = row.original
  deleteMutation.mutate({ projectId: p.id })
}

const columns = [
  { accessorKey: 'name', header: 'Name' },
  { accessorKey: 'status', header: 'Status' },
  { accessorKey: 'updated_at', header: 'Updated' },
  { id: 'actions', header: '', cell: ({ row }: any) => h(
    'div',
    { class: 'flex justify-end gap-2' },
    [
      h(resolveComponent('UButton'), { label: 'Open', to: `/projects/${row.original.id}`, color: 'neutral', variant: 'outline', size: 'xs' }),
      h(resolveComponent('UButton'), { label: 'Edit', to: `/projects/${row.original.id}/edit`, color: 'neutral', variant: 'subtle', size: 'xs' }),
      h(resolveComponent('UButton'), { label: 'Delete', color: 'error', variant: 'subtle', size: 'xs', onClick: () => onDelete(row) })
    ]
  ) }
]
</script>

<template>
  <UDashboardPanel id="projects">
    <template #header>
      <UDashboardNavbar title="Projects">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>

        <template #right>
          <UButton label="New Project" icon="i-lucide-plus" color="primary" to="/projects/new" />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="space-y-4">
        <UTable :data="rows" :columns="columns" :loading="list.isLoading.value" />

        <div v-if="totalPages > 1" class="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-800">
          <div class="text-sm text-muted">
            Showing {{ ((page - 1) * pageSize) + 1 }} to {{ Math.min(page * pageSize, total) }} of {{ total }} projects
          </div>
          <div class="flex items-center gap-2">
            <UButton
              icon="i-lucide-chevron-left"
              color="neutral"
              variant="outline"
              size="xs"
              :disabled="page === 1"
              @click="page--"
            />
            <span class="text-sm">Page {{ page }} of {{ totalPages }}</span>
            <UButton
              icon="i-lucide-chevron-right"
              color="neutral"
              variant="outline"
              size="xs"
              :disabled="page >= totalPages"
              @click="page++"
            />
          </div>
        </div>
      </div>
    </template>
  </UDashboardPanel>
</template>
