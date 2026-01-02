<script setup lang="ts">
const props = defineProps<{
  modelValue: {
    name: string
    description: string
    status: 'draft' | 'processing' | 'ready'
  }
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: typeof props.modelValue]
  'submit': []
}>()

const form = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const statusOptions = [
  { label: 'Draft', value: 'draft' },
  { label: 'Processing', value: 'processing' },
  { label: 'Ready', value: 'ready' }
]
</script>

<template>
  <div class="space-y-4">
    <UInput
      v-model="form.name"
      label="Name"
      placeholder="Project name"
      required
    />
    <UTextarea
      v-model="form.description"
      label="Description"
      placeholder="Optional description"
    />
    <USelect
      v-model="form.status"
      :items="statusOptions"
      label="Status"
    />
  </div>
</template>
