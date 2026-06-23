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

function initStars(width: number, height: number) {
  stars = []
  const count = Math.floor((width * height) / 8000) // 密度：每 8000px 一颗星
  for (let i = 0; i < count; i++) {
    stars.push({
      x: Math.random() * width,
      y: Math.random() * height,
      r: Math.random() * 1.2 + 0.3,       // 半径 0.3 ~ 1.5
      a: Math.random() * 0.5 + 0.1,        // 透明度 0.1 ~ 0.6
      da: (Math.random() - 0.5) * 0.008    // 闪烁速度
    })
  }
}

function draw() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const w = canvas.width
  const h = canvas.height
  ctx.clearRect(0, 0, w, h)

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
  canvas.width = window.innerWidth * dpr
  canvas.height = window.innerHeight * dpr
  canvas.style.width = window.innerWidth + 'px'
  canvas.style.height = window.innerHeight + 'px'
  const ctx = canvas.getContext('2d')
  if (ctx) ctx.scale(dpr, dpr)
  initStars(window.innerWidth, window.innerHeight)
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
}

watch(() => themeStore.isDark, (dark) => {
  if (dark) {
    start()
  } else {
    stop()
  }
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
  width: 100vw;
  height: 100vh;
  pointer-events: none;
  z-index: 0;
}
</style>
