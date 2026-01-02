<script setup lang="ts">
import { useQueryClient } from '@tanstack/vue-query'
import axios from 'axios'

const props = defineProps<{
  projectId: number
}>()

const emit = defineEmits<{
  uploaded: [documentId: number]
}>()

const queryClient = useQueryClient()
const config = useRuntimeConfig()
const toast = useToast()

const uploading = ref(false)
const uploadProgress = ref(0)
const fileInputRef = ref<HTMLInputElement | null>(null)

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

    // Invalidate project documents query to refetch
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
    target.value = ''
  }
}
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
