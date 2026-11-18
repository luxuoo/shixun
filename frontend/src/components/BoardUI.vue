<template>
  <div ref="host" class="boardui-host"></div>
</template>

<script setup lang="ts">
/**
 * React-island 桥：在 Vue 页面内挂载真实的 BoardUI（React）组件。
 * 用法：<BoardUI as="Button" :config="{ variant:'primary', onClick:fn, children:'文本' }" />
 * config 变化时通过 React root.render 复用同一根节点做协调更新，卸载时 unmount 释放。
 */
import { ref, onMounted, onBeforeUnmount, watch, type Component } from 'vue'
import { createElement } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { Button } from '@/boardui/components/base/buttons/button'

const registry: Record<string, Component> = {
  Button,
}

const props = defineProps<{
  as: string
  config?: Record<string, any>
}>()

const host = ref<HTMLElement | null>(null)
let root: Root | null = null

function render() {
  const Comp = registry[props.as]
  if (!Comp || !host.value) return
  if (!root) root = createRoot(host.value)
  root.render(createElement(Comp as any, props.config || {}))
}

onMounted(render)
watch(() => [props.as, props.config], render, { deep: true })
onBeforeUnmount(() => {
  root?.unmount()
  root = null
})
</script>