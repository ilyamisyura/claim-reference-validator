<script setup lang="ts">
import { useQueryClient } from '@tanstack/vue-query'
import {
  useGetProject,
  useDeleteProject
} from '@lib/api/v1/endpoints/projects'
import {
  useListProjectDocuments
} from '@lib/api/v1/endpoints/documents'

const route = useRoute()
const router = useRouter()
const toast = useToast()

const projectId = computed(() => Number(route.params.id))

const projectQuery = useGetProject(projectId)

const deleteMutation = useDeleteProject({
  mutation: {
    onSuccess: async () => {
      await router.push('/projects')
    }
  }
})

// Document management
const documentsQuery = useListProjectDocuments(projectId)
const selectedDocumentId = ref<number | null>(null)
const selectedText = ref<string>('')
const showMarkdownViewer = ref(false)
const showReplaceConfirmation = ref(false)
const pendingFile = ref<File | null>(null)
const uploadComponentRef = ref<any>(null)

const selectedDocument = computed(() => {
  if (!selectedDocumentId.value || !documentsQuery.data.value) return null
  const docs = (documentsQuery.data.value as any)?.data
  if (!Array.isArray(docs)) return null

  return docs.find((d: any) => d.id === selectedDocumentId.value)
})

const handleDocumentUploaded = (documentId: number) => {
  selectedDocumentId.value = documentId
  showMarkdownViewer.value = true
  toast.add({
    title: 'Document processed',
    description: 'You can now view the markdown and select reference sections',
    color: 'success'
  })
}

const handleConfirmReplace = (file: File) => {
  pendingFile.value = file
  showReplaceConfirmation.value = true
}

const handleConfirmReplaceAccept = async () => {
  showReplaceConfirmation.value = false
  if (pendingFile.value && uploadComponentRef.value) {
    await uploadComponentRef.value.performUpload(pendingFile.value)
    pendingFile.value = null
  }
}

const handleConfirmReplaceCancel = () => {
  showReplaceConfirmation.value = false
  pendingFile.value = null
  toast.add({
    title: 'Upload cancelled',
    description: 'No changes were made',
    color: 'neutral'
  })
}

const handleTextSelection = (text: string) => {
  selectedText.value = text
  toast.add({
    title: 'Text selected',
    description: `${text.length} characters selected. Ready to process.`,
    color: 'primary'
  })
}

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
      <UDashboardNavbar :title="(projectQuery.data.value as any)?.data?.name || 'Project'">
        <template #leading>
          <UDashboardSidebarCollapse />
        </template>
        <template #right>
          <div class="flex items-center gap-2">
            <UBadge variant="subtle" color="neutral" :label="(projectQuery.data.value as any)?.data?.status" />
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
                <DocumentsDocumentUpload
                  ref="uploadComponentRef"
                  :project-id="projectId"
                  @uploaded="handleDocumentUploaded"
                  @confirm-replace="handleConfirmReplace"
                />
              </div>
            </template>

            <div v-if="!(documentsQuery.data.value as any)?.data || (documentsQuery.data.value as any).data.length === 0" class="text-sm text-muted">
              No document uploaded yet. Upload a PDF to extract claims and references.
            </div>

            <div v-else class="space-y-3">
              <!-- Show only the first/latest document -->
              <div class="flex items-start justify-between">
                <div class="space-y-1">
                  <div class="font-medium text-sm">
                    {{ (documentsQuery.data.value as any).data[0].filename }}
                  </div>
                  <div class="text-xs text-muted">
                    {{ (documentsQuery.data.value as any).data[0].document_title || 'No title' }}
                  </div>
                  <div class="text-xs text-muted">
                    {{ (documentsQuery.data.value as any).data[0].page_count ?
                       `${(documentsQuery.data.value as any).data[0].page_count} pages` :
                       'Unknown pages' }}
                  </div>
                  <div class="text-xs text-muted">
                    Uploaded {{ new Date((documentsQuery.data.value as any).data[0].created_at).toLocaleDateString() }}
                  </div>
                </div>
                <UButton
                  size="xs"
                  variant="ghost"
                  icon="i-lucide-eye"
                  label="View"
                  @click="selectedDocumentId = (documentsQuery.data.value as any).data[0].id; showMarkdownViewer = true"
                />
              </div>

              <!-- Replace Document Button -->
              <div class="pt-2 border-t">
                <DocumentsDocumentUpload
                  :project-id="projectId"
                  @uploaded="handleDocumentUploaded"
                  @confirm-replace="handleConfirmReplace"
                />
                <p class="text-xs text-muted mt-1">
                  Uploading a new document will replace the current one and delete all claims.
                </p>
              </div>
            </div>
          </UCard>

          <!-- Markdown Viewer -->
          <UCard v-if="showMarkdownViewer && selectedDocument">
            <template #header>
              <div class="flex items-center justify-between">
                <span class="font-medium">Document Content (Select text to extract references)</span>
                <UButton
                  size="xs"
                  variant="ghost"
                  icon="i-lucide-x"
                  @click="showMarkdownViewer = false"
                />
              </div>
            </template>

            <div class="max-h-[600px] overflow-y-auto">
              <DocumentsMarkdownViewer
                :markdown="selectedDocument.markdown_content"
                :selectable="true"
                @select="handleTextSelection"
              />
            </div>

            <template #footer v-if="selectedText">
              <div class="flex items-center justify-between">
                <div class="text-sm">
                  <span class="font-medium">Selected text:</span>
                  <span class="text-muted ml-2">{{ selectedText.substring(0, 100) }}{{ selectedText.length > 100 ? '...' : '' }}</span>
                </div>
                <UButton
                  icon="i-lucide-wand-2"
                  label="Process with LM Studio"
                  color="primary"
                  @click="() => { toast.add({ title: 'Coming soon', description: 'LM Studio processing will be implemented next' }) }"
                />
              </div>
            </template>
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
                <span class="font-medium">{{ (projectQuery.data.value as any)?.data?.name }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-muted">Status</span>
                <span class="capitalize">{{ (projectQuery.data.value as any)?.data?.status }}</span>
              </div>
              <div v-if="(projectQuery.data.value as any)?.data?.description" class="pt-2">
                <div class="text-muted mb-1">Description</div>
                <div>{{ (projectQuery.data.value as any)?.data?.description }}</div>
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

  <!-- Confirmation Modal -->
  <UModal v-model:open="showReplaceConfirmation">
    <template #content>
      <div class="p-6 space-y-4">
        <div class="flex items-center gap-2">
          <UIcon name="i-lucide-alert-triangle" class="text-warning-500 w-6 h-6" />
          <h3 class="text-lg font-semibold">Replace Existing Document?</h3>
        </div>

        <div class="space-y-3">
          <p class="text-sm">
            This project already has a document. Uploading a new document will:
          </p>
          <ul class="text-sm space-y-1 list-disc list-inside text-muted">
            <li>Delete the existing document</li>
            <li>Delete all extracted claims</li>
            <li>Delete all claim-reference links</li>
          </ul>
          <p class="text-sm font-medium">
            This action cannot be undone. Are you sure you want to continue?
          </p>
        </div>

        <div class="flex justify-end gap-2 pt-2">
          <UButton
            color="neutral"
            variant="ghost"
            label="Cancel"
            @click="handleConfirmReplaceCancel"
          />
          <UButton
            color="error"
            label="Replace Document"
            @click="handleConfirmReplaceAccept"
          />
        </div>
      </div>
    </template>
  </UModal>
</template>
