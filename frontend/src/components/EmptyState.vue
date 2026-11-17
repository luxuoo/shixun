<!--
  EmptyState — 角色空状态（替代 n-empty 千篇一律的图标）
  <EmptyState text="还没有提交记录" shape="mochi" state="idle" :sizePx="64" />

  color 不传时按主题自动选：亮色用墨黑（深色身体在白卡上对比最强），
  暗色用青色（黑色身体在深色卡片上会隐形）。
-->
<template>
  <div class="empty-state">
    <AoraBot
      :shape="shape"
      :color="resolvedColor"
      :state="state"
      :face="face"
      :sizePx="sizePx"
      :lineWeight="1.1"
      :seed="seed || `empty:${text}`"
    />
    <p class="empty-text">{{ text }}</p>
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AoraBot from './AoraBot'
import { useThemeStore } from '@/stores/theme'

const props = withDefaults(defineProps<{
  text: string
  shape?: string
  color?: string
  state?: string
  face?: string
  sizePx?: number
  seed?: string
}>(), {
  shape: 'blob',
  color: '',
  state: 'idle',
  face: 'cute',
  sizePx: 64
})

const themeStore = useThemeStore()
const resolvedColor = computed(() => props.color || (themeStore.isDark ? 'cyan' : 'black'))
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 28px 0 20px;
}

.empty-text {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--t3);
}
</style>
