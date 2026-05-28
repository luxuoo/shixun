<template>
  <div class="code-editor-container">
    <div class="editor-header">
      <n-space align="center">
        <n-tag type="info" size="small">{{ language }}</n-tag>
        <n-button size="small" @click="handleCopy">
          复制代码
        </n-button>
        <n-button size="small" @click="handleReset">
          重置
        </n-button>
      </n-space>
    </div>
    <div ref="editorRef" class="editor-body" :style="{ height: height }"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as monaco from 'monaco-editor'
import { useMessage } from 'naive-ui'

const props = defineProps<{
  modelValue: string
  language?: string
  height?: string
  readOnly?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const message = useMessage()
const editorRef = ref<HTMLElement | null>(null)
let editor: monaco.editor.IStandaloneCodeEditor | null = null

function initEditor() {
  if (!editorRef.value) return

  editor = monaco.editor.create(editorRef.value, {
    value: props.modelValue,
    language: props.language || 'python',
    theme: 'vs-dark',
    minimap: { enabled: false },
    fontSize: 14,
    lineNumbers: 'on',
    roundedSelection: true,
    scrollBeyondLastLine: false,
    automaticLayout: true,
    readOnly: props.readOnly || false,
    tabSize: 4,
    wordWrap: 'on'
  })

  editor.onDidChangeModelContent(() => {
    if (editor) {
      emit('update:modelValue', editor.getValue())
    }
  })
}

function handleCopy() {
  if (editor) {
    navigator.clipboard.writeText(editor.getValue())
    message.success('代码已复制到剪贴板')
  }
}

function handleReset() {
  if (editor) {
    editor.setValue(props.modelValue)
  }
}

watch(() => props.modelValue, (newValue) => {
  if (editor && editor.getValue() !== newValue) {
    editor.setValue(newValue)
  }
})

onMounted(() => {
  initEditor()
})

onBeforeUnmount(() => {
  if (editor) {
    editor.dispose()
  }
})
</script>

<style scoped>
.code-editor-container {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

.editor-header {
  padding: 8px 12px;
  background: #1e1e1e;
  border-bottom: 1px solid #333;
}

.editor-body {
  min-height: 300px;
}
</style>
