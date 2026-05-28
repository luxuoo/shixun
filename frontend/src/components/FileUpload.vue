<template>
  <div class="file-upload-container">
    <n-upload
      :action="uploadUrl"
      :headers="headers"
      :data="uploadData"
      :multiple="multiple"
      :max="maxCount"
      :accept="accept"
      :default-upload="false"
      @change="handleChange"
      @finish="handleFinish"
      @error="handleError"
      ref="uploadRef"
    >
      <n-button>
        <template #icon>
          <n-icon><svg viewBox="0 0 24 24"><path fill="currentColor" d="M9 16h6v-6h4l-7-7-7 7h4zm-4 2h14v2H5z"/></svg></n-icon>
        </template>
        选择文件
      </n-button>
    </n-upload>
    <n-space v-if="showTip" style="margin-top: 8px;">
      <n-text depth="3" style="font-size: 12px;">
        {{ tip || `支持 ${accept} 格式，单个文件不超过 ${maxSize}MB` }}
      </n-text>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMessage } from 'naive-ui'
import type { UploadFileInfo } from 'naive-ui'
import { useUserStore } from '@/stores/user'

const props = defineProps<{
  action?: string
  accept?: string
  maxSize?: number
  maxCount?: number
  multiple?: boolean
  showTip?: boolean
  tip?: string
}>()

const emit = defineEmits<{
  (e: 'change', fileList: UploadFileInfo[]): void
  (e: 'finish', file: UploadFileInfo): void
  (e: 'error', file: UploadFileInfo): void
  (e: 'upload', urls: string[]): void
}>()

const message = useMessage()
const userStore = useUserStore()
const uploadRef = ref<any>(null)

const uploadUrl = computed(() => props.action || '/api/upload')
const maxSize = computed(() => props.maxSize || 10)

const headers = computed(() => ({
  Authorization: `Bearer ${userStore.token}`
}))

const uploadData = computed(() => ({}))

function handleChange({ fileList }: { fileList: UploadFileInfo[] }) {
  emit('change', fileList)
}

function handleFinish({ file }: { file: UploadFileInfo }) {
  emit('finish', file)
  message.success(`${file.name} 上传成功`)
}

function handleError({ file }: { file: UploadFileInfo }) {
  emit('error', file)
  message.error(`${file.name} 上传失败`)
}

function handleBeforeUpload({ file }: { file: UploadFileInfo }) {
  if (file.file && file.file.size > maxSize.value * 1024 * 1024) {
    message.error(`文件大小不能超过 ${maxSize.value}MB`)
    return false
  }
  return true
}

defineExpose({
  upload: () => uploadRef.value?.submit(),
  clear: () => uploadRef.value?.clear()
})
</script>

<style scoped>
.file-upload-container {
  width: 100%;
}
</style>
