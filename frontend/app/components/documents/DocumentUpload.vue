<script setup lang="ts">
import { useQueryClient } from '@tanstack/vue-query'
import axios from 'axios'
import { useListProjectDocuments } from '@lib/api/v1/endpoints/documents'

const props = defineProps<{
  projectId: number
}>()

const emit = defineEmits<{
  uploaded: [documentId: number]
  confirmReplace: [file: File]
}>()

const queryClient = useQueryClient()
const config = useRuntimeConfig()
const toast = useToast()

const uploading = ref(false)
const uploadProgress = ref(0)
const fileInputRef = ref<HTMLInputElement | null>(null)

// Query to check for existing documents
const documentsQuery = useListProjectDocuments(
  computed(() => props.projectId)
)

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const handleFileUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (!file) return

  if (!file.name.toLowerCase().endsWith('.pdf')) {
    toast.add({
      title: 'Invalid file type',
      description: 'Please upload a PDF file',
      color: 'error'
    })
    return
  }

  // Wait for query to load if it's still loading
  if (documentsQuery.isLoading.value) {
    toast.add({
      title: 'Loading...',
      description: 'Please wait while we check for existing documents',
      color: 'neutral'
    })
    return
  }

  // Check if documents already exist
  // Only check if query has successfully loaded
  if (documentsQuery.isSuccess.value) {
    const responseData = documentsQuery.data.value as any
    const existingDocs = responseData?.data

    if (Array.isArray(existingDocs) && existingDocs.length > 0) {
      // Emit event for parent to handle confirmation
      emit('confirmReplace', file)
      target.value = '' // Clear input
      return
    }
  }

  // No existing documents, proceed with upload
  await performUpload(file)
  target.value = ''
}

const performUpload = async (file: File) => {
  uploading.value = true
  uploadProgress.value = 0

  try {
    const formData = new FormData()
    formData.append('file', file)

    const response = await axios.post(
      `${config.public.apiBase}/api/v1/process/pdf`,
      formData,
      {
        params: { project_id: props.projectId },
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            uploadProgress.value = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            )
          }
        }
      }
    )

    toast.add({
      title: 'Success',
      description: 'Document uploaded and processed',
      color: 'success'
    })

    emit('uploaded', response.data.document_id)

    // Invalidate queries to refetch
    queryClient.invalidateQueries({ queryKey: ['project', props.projectId, 'documents'] })
  } catch (error: any) {
    console.error('Upload error:', error)
    toast.add({
      title: 'Upload failed',
      description: error.response?.data?.detail || 'Failed to upload document',
      color: 'error'
    })
  } finally {
    uploading.value = false
    uploadProgress.value = 0
  }
}

// Expose performUpload so parent can call it after confirmation
defineExpose({
  performUpload
})
</script>

<template>
  <div>
    <UButton
      icon="i-lucide-upload"
      :label="uploading ? `Uploading ${uploadProgress}%` : 'Upload PDF'"
      :loading="uploading"
      :disabled="uploading"
      @click="triggerFileInput"
    />

    <input
      ref="fileInputRef"
      type="file"
      accept=".pdf"
      class="hidden"
      :disabled="uploading"
      @change="handleFileUpload"
    />

    <div v-if="uploading" class="mt-2">
      <div class="w-full bg-gray-200 rounded-full h-2">
        <div
          class="bg-primary-500 h-2 rounded-full transition-all"
          :style="{ width: `${uploadProgress}%` }"
        />
      </div>
    </div>
  </div>
</template>
