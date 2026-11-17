<template>
  <div class="code-editor-container">
    <div class="editor-header">
      <n-space align="center">
        <n-tag type="info" size="small">{{ language }}</n-tag>
        <n-button size="small" :disabled="!ready" @click="handleCopy">
          复制代码
        </n-button>
        <n-button size="small" :disabled="!ready" @click="handleReset">
          重置
        </n-button>
      </n-space>
    </div>
    <div class="editor-body-wrap" :style="{ height: height }">
      <div v-if="!ready" class="editor-skeleton">
        <span class="spinner"></span>
        <span>编辑器加载中…</span>
      </div>
      <div ref="editorRef" class="editor-body"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useMessage } from 'naive-ui'
import type * as Monaco from 'monaco-editor'

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
const ready = ref(false)
let editor: Monaco.editor.IStandaloneCodeEditor | null = null
let disposed = false

// monaco 体积很大（约 3MB），动态导入让任务页先渲染出来再加载编辑器
async function initEditor() {
  if (!editorRef.value) return
  try {
    const monaco = await import('monaco-editor')
    if (disposed || !editorRef.value) return

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
    ready.value = true

    editor.onDidChangeModelContent(() => {
      if (editor) {
        emit('update:modelValue', editor.getValue())
      }
    })
  } catch (e) {
    console.error('代码编辑器加载失败', e)
    message.error('代码编辑器加载失败，请刷新页面重试')
  }
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

watch(() => props.readOnly, (val) => {
  editor?.updateOptions({ readOnly: val || false })
})

onMounted(() => {
  initEditor()
})

onBeforeUnmount(() => {
  disposed = true
  if (editor) {
    editor.dispose()
    editor = null
  }
})
</script>

<style scoped>
.code-editor-container {
  border: 1px solid var(--line);
  border-radius: 8px;
  overflow: hidden;
}

.editor-header {
  padding: 8px 12px;
  background: #1e1e1e;
  border-bottom: 1px solid #333;
}

.editor-body-wrap {
  position: relative;
  min-height: 300px;
}

.editor-body {
  width: 100%;
  height: 100%;
}

.editor-skeleton {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: #1e1e1e;
  color: #8a93a7;
  font-size: 13px;
  z-index: 1;
}

.spinner {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.18);
  border-top-color: #818cf8;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
