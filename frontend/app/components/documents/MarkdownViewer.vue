<script setup lang="ts">
import { marked } from 'marked'

const props = defineProps<{
  markdown: string
  selectable?: boolean
}>()

const emit = defineEmits<{
  select: [selectedText: string]
}>()

const renderedHtml = computed(() => {
  if (!props.markdown) return ''
  return marked(props.markdown, { async: false, breaks: true })
})

const containerRef = ref<HTMLElement | null>(null)

const handleTextSelection = () => {
  if (!props.selectable) return

  const selection = window.getSelection()
  if (!selection || selection.isCollapsed) return

  const selectedText = selection.toString().trim()
  if (selectedText) {
    emit('select', selectedText)
  }
}
</script>

<template>
  <div
    ref="containerRef"
    class="markdown-viewer prose prose-sm dark:prose-invert max-w-none"
    :class="{ 'cursor-text': selectable }"
    @mouseup="handleTextSelection"
  >
    <div v-html="renderedHtml" />
  </div>
</template>

<style scoped>
.markdown-viewer {
  line-height: 1.6;
}

.markdown-viewer :deep(h1) {
  font-size: 1.875rem;
  font-weight: 700;
  margin-top: 2rem;
  margin-bottom: 1rem;
}

.markdown-viewer :deep(h2) {
  font-size: 1.5rem;
  font-weight: 600;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}

.markdown-viewer :deep(h3) {
  font-size: 1.25rem;
  font-weight: 600;
  margin-top: 1.25rem;
  margin-bottom: 0.5rem;
}

.markdown-viewer :deep(p) {
  margin-bottom: 1rem;
}

.markdown-viewer :deep(ul),
.markdown-viewer :deep(ol) {
  margin-left: 1.5rem;
  margin-bottom: 1rem;
}

.markdown-viewer :deep(li) {
  margin-bottom: 0.5rem;
}

.markdown-viewer :deep(code) {
  background-color: rgba(var(--ui-gray-100), 0.5);
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-size: 0.875em;
}

.markdown-viewer :deep(pre) {
  background-color: rgba(var(--ui-gray-100), 0.5);
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin-bottom: 1rem;
}

.markdown-viewer :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.markdown-viewer :deep(blockquote) {
  border-left: 4px solid rgba(var(--ui-primary-500), 1);
  padding-left: 1rem;
  margin-left: 0;
  margin-bottom: 1rem;
  font-style: italic;
}

.markdown-viewer :deep(a) {
  color: rgba(var(--ui-primary-500), 1);
  text-decoration: underline;
}

.markdown-viewer :deep(a:hover) {
  color: rgba(var(--ui-primary-600), 1);
}

.markdown-viewer :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1rem;
}

.markdown-viewer :deep(th),
.markdown-viewer :deep(td) {
  border: 1px solid rgba(var(--ui-gray-200), 1);
  padding: 0.5rem;
  text-align: left;
}

.markdown-viewer :deep(th) {
  background-color: rgba(var(--ui-gray-50), 1);
  font-weight: 600;
}

.markdown-viewer :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 0.5rem;
}

.markdown-viewer :deep(hr) {
  border: none;
  border-top: 1px solid rgba(var(--ui-gray-200), 1);
  margin: 2rem 0;
}
</style>
