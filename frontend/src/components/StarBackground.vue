<template>
  <canvas ref="canvasRef" class="star-canvas" />
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useThemeStore } from '../stores/theme'

const themeStore = useThemeStore()
const canvasRef = ref<HTMLCanvasElement | null>(null)
let animId: number | null = null
let stars: { x: number; y: number; r: number; a: number; da: number }[] = []
let cssW = 0
let cssH = 0

function initStars() {
  stars = []
  const count = Math.floor((cssW * cssH) / 6000)
  for (let i = 0; i < count; i++) {
    stars.push({
      x: Math.random() * cssW,
      y: Math.random() * cssH,
      r: Math.random() * 1.2 + 0.3,
      a: Math.random() * 0.5 + 0.1,
      da: (Math.random() - 0.5) * 0.008
    })
  }
}

function draw() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  ctx.clearRect(0, 0, cssW, cssH)

  for (const s of stars) {
    s.a += s.da
    if (s.a <= 0.05 || s.a >= 0.6) s.da = -s.da
    s.a = Math.max(0.05, Math.min(0.6, s.a))

    ctx.beginPath()
    ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(200, 210, 255, ${s.a})`
    ctx.fill()
  }

  animId = requestAnimationFrame(draw)
}

function resize() {
  const canvas = canvasRef.value
  if (!canvas) return
  const dpr = window.devicePixelRatio || 1
  cssW = window.innerWidth
  cssH = window.innerHeight
  canvas.width = cssW * dpr
  canvas.height = cssH * dpr
  canvas.style.width = cssW + 'px'
  canvas.style.height = cssH + 'px'
  const ctx = canvas.getContext('2d')
  if (ctx) {
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  }
  initStars()
}

function start() {
  resize()
  draw()
  window.addEventListener('resize', resize)
}

function stop() {
  if (animId) cancelAnimationFrame(animId)
  animId = null
  window.removeEventListener('resize', resize)
  // 清空画布
  const canvas = canvasRef.value
  if (canvas) {
    const ctx = canvas.getContext('2d')
    if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height)
  }
}

watch(() => themeStore.isDark, (dark) => {
  if (dark) start()
  else stop()
})

onMounted(() => {
  if (themeStore.isDark) start()
})

onBeforeUnmount(() => {
  stop()
})
</script>

<style scoped>
.star-canvas {
  position: fixed;
  top: 0;
  left: 0;
  pointer-events: none;
  z-index: 0;
}
</style>
