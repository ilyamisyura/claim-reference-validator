<script setup lang="ts">
import { useQueryClient } from '@tanstack/vue-query'
import {
  useGetProjectApiV1ProjectsProjectIdGet,
  useUpdateProjectApiV1ProjectsProjectIdPut
} from '@lib/api/v1/endpoints/projects'

const route = useRoute()
const router = useRouter()
const queryClient = useQueryClient()

const projectId = computed(() => Number(route.params.id))

const projectQuery = useGetProjectApiV1ProjectsProjectIdGet(projectId)

const form = reactive({
  name: '',
  description: '',
  status: 'draft' as 'draft' | 'processing' | 'ready'
})

watchEffect(() => {
  const p = projectQuery.data?.data
  if (p) {
    form.name = p.name
    form.description = p.description || ''
    form.status = (p.status as any) || 'draft'
  }
})

const updateMutation = useUpdateProjectApiV1ProjectsProjectIdPut({
  mutation: {
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: projectQuery.queryKey })
      await router.push(`/projects/${projectId.value}`)
    }
  }
})

function handleSubmit() {
  updateMutation.mutate({
    projectId: projectId.value,
    data: {
      name: form.name,
      description: form.description || undefined,
      status: form.status
    }
  })
}
</script>

<template>
  <UDashboardPanel>
    <template #header>
      <UDashboardNavbar :title="`Edit: ${projectQuery.data?.data?.name || 'Project'}`">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="max-w-2xl mx-auto py-8">
        <UCard v-if="projectQuery.isLoading.value">
          <div class="text-center py-8">Loading...</div>
        </UCard>

        <UCard v-else>
          <template #header>
            <h2 class="text-lg font-semibold">Edit Project</h2>
          </template>

          <ProjectsProjectForm v-model="form" :loading="updateMutation.isPending.value" />

          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton
                color="neutral"
                variant="ghost"
                :to="`/projects/${projectId}`"
              >
                Cancel
              </UButton>
              <UButton
                :loading="updateMutation.isPending.value"
                :disabled="!form.name"
                color="primary"
                @click="handleSubmit"
              >
                Save Changes
              </UButton>
            </div>
          </template>
        </UCard>
      </div>
    </template>
  </UDashboardPanel>
</template>
