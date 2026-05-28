<template>
  <div class="step-nav-container">
    <n-steps :current="current" :status="status" :vertical="vertical">
      <n-step
        v-for="step in steps"
        :key="step.id"
        :title="step.title"
        :description="getStepDescription(step)"
        :disabled="disabled"
        @click="handleClick(step)"
      />
    </n-steps>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Step {
  id: number
  step_order: number
  title: string
  description?: string
}

const props = defineProps<{
  steps: Step[]
  current: number
  vertical?: boolean
  disabled?: boolean
  status?: 'process' | 'finish' | 'error'
}>()

const emit = defineEmits<{
  (e: 'click', step: Step): void
}>()

function getStepDescription(step: Step) {
  return `步骤 ${step.step_order}`
}

function handleClick(step: Step) {
  if (!props.disabled) {
    emit('click', step)
  }
}
</script>

<style scoped>
.step-nav-container {
  width: 100%;
}

.step-nav-container :deep(.n-step) {
  cursor: pointer;
}

.step-nav-container :deep(.n-step:hover) {
  opacity: 0.8;
}
</style>
