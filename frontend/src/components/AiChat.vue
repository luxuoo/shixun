<template>
  <div class="ai-chat-container">
    <n-card :title="title" :bordered="false">
      <template #header-extra>
        <n-space>
          <n-tag type="info" size="small">
            剩余提示: {{ hintsRemaining }}
          </n-tag>
        </n-space>
      </template>

      <!-- 消息区域 -->
      <div class="messages-area" ref="messagesRef">
        <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
          <div class="message-avatar">
            <n-avatar :size="36" round :color="msg.role === 'ai' ? '#2080f0' : '#18a058'">
              {{ msg.role === 'ai' ? 'AI' : '我' }}
            </n-avatar>
          </div>
          <div class="message-content">
            <n-card :type="msg.role === 'ai' ? 'info' : 'default'" size="small">
              <p style="margin: 0; white-space: pre-wrap; word-break: break-word;">{{ msg.content }}</p>
            </n-card>
            <span class="message-time">{{ msg.time }}</span>
          </div>
        </div>
        <n-empty v-if="messages.length === 0" description="点击下方按钮获取 AI 帮助" style="margin-top: 40px;" />
      </div>

      <!-- 操作区域 -->
      <div class="actions-area">
        <n-space vertical :size="12">
          <n-space>
            <n-button
              type="primary"
              @click="$emit('hint')"
              :loading="hintLoading"
              :disabled="hintsRemaining <= 0"
            >
              <template #icon>
                <n-icon><svg viewBox="0 0 24 24"><path fill="currentColor" d="M9 21c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1H9v1zm3-19C8.14 2 5 5.14 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.86-3.14-7-7-7z"/></svg></n-icon>
              </template>
              获取提示
            </n-button>
            <n-button @click="$emit('analyze')" :loading="analyzeLoading">
              <template #icon>
                <n-icon><svg viewBox="0 0 24 24"><path fill="currentColor" d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z"/></svg></n-icon>
              </template>
              分析代码
            </n-button>
            <n-button @click="$emit('score')" :loading="scoreLoading">
              <template #icon>
                <n-icon><svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg></n-icon>
              </template>
              评分
            </n-button>
          </n-space>
          <n-input
            v-model:value="question"
            type="textarea"
            placeholder="输入你的问题..."
            :rows="2"
            @keyup.ctrl.enter="handleAsk"
          />
          <n-button type="primary" block @click="handleAsk" :loading="questionLoading" :disabled="!question.trim()">
            提问 (Ctrl + Enter)
          </n-button>
        </n-space>
      </div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'

interface Message {
  role: 'user' | 'ai'
  content: string
  time: string
}

const props = defineProps<{
  title?: string
  messages: Message[]
  hintsRemaining: number
  hintLoading?: boolean
  analyzeLoading?: boolean
  scoreLoading?: boolean
  questionLoading?: boolean
}>()

const emit = defineEmits<{
  (e: 'hint'): void
  (e: 'analyze'): void
  (e: 'score'): void
  (e: 'ask', question: string): void
}>()

const messagesRef = ref<HTMLElement | null>(null)
const question = ref('')

function handleAsk() {
  if (question.value.trim()) {
    emit('ask', question.value)
    question.value = ''
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

watch(() => props.messages.length, () => {
  scrollToBottom()
})
</script>

<style scoped>
.ai-chat-container {
  height: 100%;
}

.messages-area {
  max-height: 400px;
  overflow-y: auto;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
  margin-bottom: 16px;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-content {
  max-width: 80%;
}

.message-time {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
  display: block;
}

.message.user .message-time {
  text-align: right;
}

.actions-area {
  border-top: 1px solid #e0e0e0;
  padding-top: 16px;
}
</style>
