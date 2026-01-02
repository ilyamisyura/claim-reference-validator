<script setup lang="ts">
import { useQueryClient } from '@tanstack/vue-query'
import {
  useGetProjectApiV1ProjectsProjectIdGet,
  useDeleteProjectApiV1ProjectsProjectIdDelete
} from '@lib/api/v1/endpoints/projects'

const route = useRoute()
const router = useRouter()
const queryClient = useQueryClient()

const projectId = computed(() => Number(route.params.id))

const projectQuery = useGetProjectApiV1ProjectsProjectIdGet(projectId)

const deleteMutation = useDeleteProjectApiV1ProjectsProjectIdDelete({
  mutation: {
    onSuccess: async () => {
      await router.push('/projects')
    }
  }
})

const documentInfo = ref<null | { filename: string; type: string; size: string }>(null)

const references = ref([
  { id: 'R1', title: 'Smith et al. (2020)', source: 'Journal of Medicine' },
  { id: 'R2', title: 'WHO Guidance 2021', source: 'World Health Organization' },
  { id: 'R3', title: 'Miller & Zhou (2019)', source: 'Clinical Trials' }
])

const claims = ref([
  { id: 101, text: 'The drug reduces blood pressure by 15%.', referenceId: 'R1' },
  { id: 102, text: 'No significant adverse events reported.', referenceId: 'R2' }
])

const refColumns = [
  { accessorKey: 'id', header: 'Ref ID' },
  { accessorKey: 'title', header: 'Title' },
  { accessorKey: 'source', header: 'Source' }
]

const claimColumns = [
  { accessorKey: 'id', header: 'ID' },
  { accessorKey: 'text', header: 'Claim' },
  { header: 'Reference', cell: ({ row }: any) => {
    const ref = references.value.find(r => r.id === row.original.referenceId)
    return ref ? `${row.original.referenceId} — ${ref.title}` : row.original.referenceId
  } }
]
</script>

<template>
  <UDashboardPanel :id="`project-${projectId}`">
    <template #header>
      <UDashboardNavbar :title="projectQuery.data?.data?.name || 'Project'">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
        <template #right>
          <div class="flex items-center gap-2">
            <UBadge variant="subtle" color="neutral" :label="projectQuery.data?.data?.status" />
            <UButton icon="i-lucide-upload" label="Upload Document" color="neutral" variant="outline" />
            <UButton icon="i-lucide-cog" label="Process" color="primary" />
          </div>
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="grid gap-4 lg:grid-cols-3">
        <div class="lg:col-span-2 space-y-4">
          <!-- Document -->
          <UCard>
            <template #header>
              <div class="flex items-center justify-between">
                <span class="font-medium">Document</span>
                <UButton size="xs" variant="outline" icon="i-lucide-upload" label="Upload" />
              </div>
            </template>

            <div v-if="!documentInfo" class="text-sm text-muted">
              No document uploaded yet. Supported: PDF, DOCX.
            </div>
            <div v-else class="text-sm">
              <div class="font-medium">{{ documentInfo.filename }}</div>
              <div class="text-muted">{{ documentInfo.type }} • {{ documentInfo.size }}</div>
            </div>
          </UCard>

          <!-- Reference List -->
          <UCard>
            <template #header>
              <div class="flex items-center justify-between">
                <span class="font-medium">Reference List</span>
                <div class="flex items-center gap-2">
                  <UButton size="xs" variant="outline" icon="i-lucide-quote" label="Paste References" />
                  <UButton size="xs" icon="i-lucide-plus" label="Add Reference" />
                </div>
              </div>
            </template>

            <UTable :data="references" :columns="refColumns" />
          </UCard>

          <!-- Claims -->
          <UCard>
            <template #header>
              <div class="flex items-center justify-between">
                <span class="font-medium">Claims</span>
                <UButton size="xs" icon="i-lucide-plus" label="Add Claim" />
              </div>
            </template>

            <UTable :data="claims" :columns="claimColumns" />
          </UCard>
        </div>

        <!-- Right rail -->
        <div class="space-y-4">
          <UCard>
            <template #header>
              <span class="font-medium">Project Info</span>
            </template>
            <div class="space-y-3 text-sm">
              <div class="flex items-center justify-between">
                <span class="text-muted">Project ID</span>
                <span>{{ projectId }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-muted">Name</span>
                <span class="font-medium">{{ projectQuery.data?.data?.name }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-muted">Status</span>
                <span class="capitalize">{{ projectQuery.data?.data?.status }}</span>
              </div>
              <div v-if="projectQuery.data?.data?.description" class="pt-2">
                <div class="text-muted mb-1">Description</div>
                <div>{{ projectQuery.data?.data?.description }}</div>
              </div>
              <div class="flex gap-2 justify-end pt-3">
                <UButton color="error" variant="subtle" :loading="deleteMutation.isPending.value" @click="deleteMutation.mutate({ projectId: projectId as number })">Delete</UButton>
                <UButton color="primary" :to="`/projects/${projectId}/edit`">Edit</UButton>
              </div>
            </div>
          </UCard>

          <UCard>
            <template #header>
              <span class="font-medium">Quick Actions</span>
            </template>
            <div class="flex flex-col gap-2">
              <UButton variant="outline" icon="i-lucide-wand-2" label="Extract References" />
              <UButton variant="outline" icon="i-lucide-wand-2" label="Extract Claims" />
              <UButton color="primary" icon="i-lucide-link" label="Link Claims to References" />
            </div>
          </UCard>
        </div>
      </div>
    </template>
  </UDashboardPanel>
</template>
