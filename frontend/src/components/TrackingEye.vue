<template>
  <div
    ref="rootRef"
    class="t-eye"
    :style="{
      width: (showWhite ? size : pupilSize) + 'px',
      height: (showWhite ? size : pupilSize) + 'px',
      backgroundColor: showWhite ? eyeColor : 'transparent',
      overflow: showWhite ? 'hidden' : 'visible',
      transform: showWhite && blinking ? 'scaleY(0.06)' : 'scaleY(1)',
    }"
  >
    <div
      v-if="!(showWhite && blinking)"
      class="t-pupil"
      :style="{
        width: pupilSize + 'px',
        height: pupilSize + 'px',
        backgroundColor: pupilColor,
        transform: `translate(${off.x}px, ${off.y}px)`,
      }"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = withDefaults(defineProps<{
  size?: number
  pupilSize?: number
  maxDistance?: number
  eyeColor?: string
  pupilColor?: string
  blinking?: boolean
  showWhite?: boolean
  forceLookX?: number
  forceLookY?: number
  mouseX: number
  mouseY: number
}>(), {
  size: 48,
  pupilSize: 16,
  maxDistance: 10,
  eyeColor: '#ffffff',
  pupilColor: '#2D2D2D',
  blinking: false,
  showWhite: true,
})

const rootRef = ref<HTMLElement | null>(null)

const off = computed(() => {
  if (props.forceLookX !== undefined && props.forceLookY !== undefined) {
    return { x: props.forceLookX, y: props.forceLookY }
  }
  const el = rootRef.value
  if (!el) return { x: 0, y: 0 }
  const r = el.getBoundingClientRect()
  const cx = r.left + r.width / 2
  const cy = r.top + r.height / 2
  const dx = props.mouseX - cx
  const dy = props.mouseY - cy
  const dist = Math.min(Math.sqrt(dx * dx + dy * dy), props.maxDistance)
  const ang = Math.atan2(dy, dx)
  return { x: Math.cos(ang) * dist, y: Math.sin(ang) * dist }
})
</script>

<style scoped>
.t-eye {
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.15s, background-color 0.15s;
}
.t-pupil {
  border-radius: 50%;
  transition: transform 0.1s ease-out;
}
</style>