<script setup lang="ts">
import { useQueryClient } from '@tanstack/vue-query'
import { useCreateProject } from '@lib/api/v1/endpoints/projects'

const router = useRouter()
const queryClient = useQueryClient()

const form = reactive({
  name: '',
  description: '',
  status: 'draft' as 'draft' | 'processing' | 'ready'
})

const createMutation = useCreateProject({
  mutation: {
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['projects'] })
      await router.push('/projects')
    }
  }
})

function handleSubmit() {
  createMutation.mutate({
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
      <UDashboardNavbar title="New Project">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="max-w-2xl mx-auto py-8">
        <UCard>
          <template #header>
            <h2 class="text-lg font-semibold">Create Project</h2>
          </template>

          <ProjectsProjectForm v-model="form" :loading="createMutation.isPending.value" />

          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton
                color="neutral"
                variant="ghost"
                :to="'/projects'"
              >
                Cancel
              </UButton>
              <UButton
                :loading="createMutation.isPending.value"
                :disabled="!form.name"
                color="primary"
                @click="handleSubmit"
              >
                Create Project
              </UButton>
            </div>
          </template>
        </UCard>
      </div>
    </template>
  </UDashboardPanel>
</template>
