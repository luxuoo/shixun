<template>
  <div class="task-detail-container">
    <n-spin :show="loading">
      <!-- 任务头部 -->
      <n-card style="margin-bottom: 24px;">
        <n-space align="center" :size="24">
          <div style="flex: 1;">
            <n-space align="center" style="margin-bottom: 12px;">
              <n-tag :type="getCategoryType(task.category)">{{ task.category || '未分类' }}</n-tag>
              <n-tag :type="getDifficultyType(task.difficulty)">{{ task.difficulty }}星难度</n-tag>
            </n-space>
            <h2 style="margin: 0 0 8px 0;">{{ task.title }}</h2>
            <p style="color: #666; margin: 0;">{{ task.description }}</p>
            <n-space style="margin-top: 16px;">
              <n-statistic label="总步骤" :value="task.total_steps" />
              <n-statistic label="预计时长" :value="task.estimated_hours || '未知'" suffix="小时" />
              <n-statistic label="当前进度" :value="currentStep" :suffix="`/ ${task.total_steps}`" />
            </n-space>
          </div>
        </n-space>
      </n-card>

      <!-- 步骤导航和内容 -->
      <n-grid :cols="24" :x-gap="16">
        <!-- 左侧步骤导航 -->
        <n-gi :span="6">
          <n-card title="步骤导航" style="position: sticky; top: 24px;">
            <n-steps vertical :current="currentStep" :status="stepStatus">
              <n-step
                v-for="step in steps"
                :key="step.id"
                :title="step.title"
                :description="`步骤 ${step.step_order}`"
                @click="selectStep(step)"
                style="cursor: pointer;"
              />
            </n-steps>
          </n-card>
        </n-gi>

        <!-- 右侧内容区 -->
        <n-gi :span="18">
          <!-- 当前步骤详情 -->
          <n-card v-if="currentStepData" :title="`步骤 ${currentStepData.step_order}: ${currentStepData.title}`" style="margin-bottom: 16px;">
            <n-space vertical :size="16">
              <div>
                <h4 style="margin: 0 0 8px 0;">步骤说明</h4>
                <p style="color: #666; margin: 0; white-space: pre-wrap;">{{ currentStepData.description }}</p>
              </div>
              <div v-if="currentStepData.requirements">
                <h4 style="margin: 0 0 8px 0;">具体要求</h4>
                <n-card embedded>
                  <p style="margin: 0; white-space: pre-wrap;">{{ currentStepData.requirements }}</p>
                </n-card>
              </div>
              <div v-if="currentStepData.expected_output">
                <h4 style="margin: 0 0 8px 0;">预期输出</h4>
                <n-card embedded>
                  <p style="margin: 0; white-space: pre-wrap;">{{ currentStepData.expected_output }}</p>
                </n-card>
              </div>
            </n-space>
          </n-card>

          <!-- 代码编辑器 -->
          <n-card title="代码编辑器" style="margin-bottom: 16px;">
            <div ref="editorContainer" style="height: 400px; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;"></div>
            <n-space justify="space-between" style="margin-top: 16px;">
              <n-space>
                <n-button @click="resetCode">重置代码</n-button>
              </n-space>
              <n-space>
                <n-button type="info" @click="openAiChat" :disabled="!aiChatEnabled" :title="aiChatEnabled ? '打开 AI 助手' : 'AI 对话功能已被管理员禁用'">
                  AI 助手
                </n-button>
                <n-button type="primary" @click="submitCode" :loading="submitting">
                  提交代码
                </n-button>
              </n-space>
            </n-space>
          </n-card>

          <!-- 提交记录 -->
          <n-card title="提交记录">
            <n-data-table
              :columns="submissionColumns"
              :data="submissions"
              :bordered="false"
            />
          </n-card>
        </n-gi>
      </n-grid>
    </n-spin>

    <!-- AI 助手弹窗 -->
    <n-modal v-model:show="showAiModal" preset="card" title="AI 助手" style="width: 840px">
      <n-space vertical :size="16">
        <!-- AI 对话区 -->
        <div class="ai-chat-area" ref="chatArea">
          <div v-for="(msg, index) in aiMessages" :key="index" :class="['chat-msg', msg.role]">
            <div class="chat-avatar">
              <n-icon v-if="msg.role === 'ai'" size="20" color="#6366f1"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"/></svg></n-icon>
              <n-icon v-else size="20" color="#fff"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg></n-icon>
            </div>
            <div class="chat-bubble" :class="msg.role">
              <div v-if="msg.role === 'ai'" class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
              <div v-else style="white-space: pre-wrap; word-break: break-word;">{{ msg.content }}</div>
            </div>
          </div>

          <!-- AI 加载气泡 -->
          <div v-if="isAiTyping" class="chat-msg ai">
            <div class="chat-avatar">
              <n-icon size="20" color="#6366f1"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"/></svg></n-icon>
            </div>
            <div class="chat-bubble ai typing-bubble">
              <div class="typing-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>

          <n-empty v-if="aiMessages.length === 0 && !isAiTyping" description="点击下方按钮获取 AI 帮助" />
        </div>

        <!-- AI 操作按钮 -->
        <n-space>
          <n-button @click="getHint" :loading="hintLoading" :disabled="hintsRemaining <= 0 || isAiTyping" type="warning">
            获取提示 ({{ hintsRemaining }}次)
          </n-button>
          <n-button @click="analyzeCode" :loading="analyzeLoading" :disabled="isAiTyping" type="info">
            分析代码
          </n-button>
        </n-space>

        <!-- 提问输入 -->
        <n-input-group>
          <n-input
            v-model:value="aiQuestion"
            placeholder="输入你的问题..."
            @keyup.enter="askQuestion"
            :disabled="isAiTyping"
            style="flex: 1;"
          />
          <n-button type="primary" @click="askQuestion" :loading="questionLoading" :disabled="isAiTyping">
            提问
          </n-button>
        </n-input-group>
      </n-space>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, h } from 'vue'
import { useRoute } from 'vue-router'
import { useMessage } from 'naive-ui'
import { NButton, NTag } from 'naive-ui'
import * as monaco from 'monaco-editor'
import { marked } from 'marked'
import { taskApi, submissionApi, aiApi, authApi } from '@/api'

// 配置 marked
marked.setOptions({ breaks: true, gfm: true } as any)

const route = useRoute()
const message = useMessage()

const loading = ref(false)
const submitting = ref(false)
const hintLoading = ref(false)
const analyzeLoading = ref(false)
const questionLoading = ref(false)
const showAiModal = ref(false)
const aiChatEnabled = ref(true)

const task = ref<any>({})
const steps = ref<any[]>([])
const currentStep = ref(1)
const currentStepData = ref<any>(null)
const stepStatus = ref<'process' | 'finish' | 'error'>('process')

const editorContainer = ref<HTMLElement | null>(null)
let editor: monaco.editor.IStandaloneCodeEditor | null = null

const aiMessages = ref<{ role: string; content: string }[]>([])
const aiQuestion = ref('')
const hintsRemaining = ref(3)
const chatArea = ref<HTMLElement | null>(null)
const isAiTyping = ref(false)

const submissions = ref<any[]>([])

const submissionColumns = [
  { title: '提交时间', key: 'submitted_at', render: (row: any) => new Date(row.submitted_at).toLocaleString() },
  {
    title: '状态', key: 'status', width: 100,
    render: (row: any) => {
      const map: Record<string, { label: string; type: string }> = {
        pending: { label: '待评分', type: 'warning' },
        ai_scored: { label: 'AI 已评分', type: 'success' },
        reviewed: { label: '已审核', type: 'info' }
      }
      const info = map[row.status] || { label: row.status, type: 'default' }
      return h(NTag, { type: info.type as any, size: 'small' }, { default: () => info.label })
    }
  },
  { title: 'AI评分', key: 'ai_score', width: 80, render: (row: any) => row.ai_score ? `${row.ai_score}分` : '-' },
  { title: '老师评分', key: 'teacher_score', width: 90, render: (row: any) => row.teacher_score ? `${row.teacher_score}分` : '-' },
  { title: '最终分数', key: 'final_score', width: 90, render: (row: any) => row.final_score ? `${row.final_score}分` : '-' }
]

function getCategoryType(category: string) {
  const types: Record<string, string> = { 'Python': 'info', 'Web': 'success', 'YOLO': 'warning' }
  return types[category] as any || 'info'
}

function getDifficultyType(difficulty: number) {
  if (difficulty <= 2) return 'success'
  if (difficulty <= 3) return 'warning'
  return 'error'
}

function initEditor() {
  if (!editorContainer.value) return
  editor = monaco.editor.create(editorContainer.value, {
    value: '# 在这里编写你的代码\n\n',
    language: 'python',
    theme: 'vs-dark',
    minimap: { enabled: false },
    fontSize: 14,
    lineNumbers: 'on',
    roundedSelection: true,
    scrollBeyondLastLine: false,
    automaticLayout: true
  })
}

function selectStep(step: any) {
  currentStep.value = step.step_order
  currentStepData.value = step
  loadSubmissions()
}

function resetCode() {
  if (editor) editor.setValue('# 在这里编写你的代码\n\n')
}

function openAiChat() {
  showAiModal.value = true
  nextTick(() => {
    if (chatArea.value) chatArea.value.scrollTop = chatArea.value.scrollHeight
  })
}

function scrollChat() {
  nextTick(() => {
    if (chatArea.value) chatArea.value.scrollTop = chatArea.value.scrollHeight
  })
}

async function submitCode() {
  if (!editor || !currentStepData.value) return
  const code = editor.getValue()
  if (!code.trim()) {
    message.warning('请先编写代码')
    return
  }
  submitting.value = true
  try {
    await submissionApi.create({
      task_id: task.value.id,
      step_id: currentStepData.value.id,
      code: code,
      language: 'python'
    })
    message.success('代码提交成功，AI 正在自动评分...')
    // 等一下再刷新，让 AI 评分有时间处理
    setTimeout(() => loadSubmissions(), 2000)
  } catch (error: any) {
    message.error(error.detail || '提交失败')
  } finally {
    submitting.value = false
  }
}

function renderMarkdown(content: string): string {
  try {
    return marked.parse(content || '') as string
  } catch {
    return content
  }
}

async function getHint() {
  if (!currentStepData.value) return
  hintLoading.value = true
  isAiTyping.value = true
  scrollChat()
  try {
    const result = await aiApi.getHint({
      task_id: task.value.id,
      step_id: currentStepData.value.id,
      student_code: editor?.getValue()
    }) as any
    aiMessages.value.push({ role: 'ai', content: `**提示 - 级别${result.hint_level}**\n\n${result.content}` })
    hintsRemaining.value = result.remaining_hints
  } catch (error: any) {
    message.error(error.detail || '获取提示失败')
  } finally {
    hintLoading.value = false
    isAiTyping.value = false
    scrollChat()
  }
}

async function analyzeCode() {
  if (!editor || !currentStepData.value) return
  const code = editor.getValue()
  if (!code.trim()) {
    message.warning('请先编写代码')
    return
  }
  analyzeLoading.value = true
  isAiTyping.value = true
  scrollChat()
  try {
    const result = await aiApi.analyzeCode({
      task_id: task.value.id,
      step_id: currentStepData.value.id,
      code: code
    }) as any
    aiMessages.value.push({ role: 'ai', content: `**代码分析**\n\n${result.analysis}` })
  } catch (error: any) {
    message.error(error.detail || '分析失败')
  } finally {
    analyzeLoading.value = false
    isAiTyping.value = false
    scrollChat()
  }
}

async function askQuestion() {
  if (!aiQuestion.value.trim() || !currentStepData.value) return
  const q = aiQuestion.value
  aiMessages.value.push({ role: 'user', content: q })
  aiQuestion.value = ''
  questionLoading.value = true
  isAiTyping.value = true
  scrollChat()
  try {
    const result = await aiApi.getHint({
      task_id: task.value.id,
      step_id: currentStepData.value.id,
      student_code: editor?.getValue(),
      question: q
    }) as any
    aiMessages.value.push({ role: 'ai', content: result.content })
    hintsRemaining.value = result.remaining_hints
  } catch (error: any) {
    message.error(error.detail || '提问失败')
  } finally {
    questionLoading.value = false
    isAiTyping.value = false
    scrollChat()
  }
}

async function loadTask() {
  const taskId = Number(route.params.id)
  if (!taskId) return
  loading.value = true
  try {
    const taskData = await taskApi.getDetail(taskId) as any
    task.value = taskData
    steps.value = taskData.steps || []
    if (steps.value.length > 0) selectStep(steps.value[0])
  } catch (error) {
    console.error('加载任务失败', error)
  } finally {
    loading.value = false
  }
}

async function loadSubmissions() {
  try {
    const data = await submissionApi.getList({ task_id: task.value.id, step_id: currentStepData.value?.id }) as any
    submissions.value = data
  } catch (error) {
    console.error('加载提交记录失败', error)
  }
}

async function loadSettings() {
  try {
    const data = await authApi.getSettings() as any
    aiChatEnabled.value = data.ai_chat_enabled !== false
  } catch {
    aiChatEnabled.value = true
  }
}

onMounted(async () => {
  await loadTask()
  initEditor()
  loadSettings()
})
</script>

<style scoped>
.task-detail-container {
  max-width: 1400px;
  margin: 0 auto;
}

.ai-chat-area {
  max-height: 480px;
  overflow-y: auto;
  padding: 20px;
  background: #f5f5f9;
  border-radius: 12px;
}

.chat-msg {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.chat-msg.user {
  flex-direction: row-reverse;
}

.chat-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.chat-msg.ai .chat-avatar {
  background: #eef2ff;
}

.chat-msg.user .chat-avatar {
  background: #6366f1;
}

.chat-bubble {
  max-width: 78%;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
}

.chat-bubble.ai {
  background: #fff;
  border: 1px solid #e8e8ec;
  border-top-left-radius: 4px;
  color: #1e1e2d;
}

.chat-bubble.user {
  background: #6366f1;
  color: white;
  border-top-right-radius: 4px;
}

/* Markdown 样式 */
.markdown-body :deep(p) {
  margin: 0 0 8px;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(code) {
  background: #f0f0f4;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  font-family: 'Consolas', 'Monaco', monospace;
}

.markdown-body :deep(pre) {
  background: #1e1e2d;
  color: #e0e0e0;
  padding: 12px 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
  color: inherit;
}

.markdown-body :deep(ul), .markdown-body :deep(ol) {
  padding-left: 20px;
  margin: 4px 0;
}

.markdown-body :deep(li) {
  margin: 2px 0;
}

.markdown-body :deep(strong) {
  font-weight: 600;
}

.markdown-body :deep(blockquote) {
  border-left: 3px solid #6366f1;
  padding-left: 12px;
  margin: 8px 0;
  color: #666;
}

/* 加载动画 */
.typing-bubble {
  padding: 14px 20px !important;
}

.typing-dots {
  display: flex;
  gap: 6px;
  align-items: center;
}

.typing-dots span {
  width: 8px;
  height: 8px;
  background: #6366f1;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
}

.typing-dots span:nth-child(1) { animation-delay: 0s; }
.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}
</style>
