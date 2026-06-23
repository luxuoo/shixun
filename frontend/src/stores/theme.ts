import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { darkTheme } from 'naive-ui'

export const useThemeStore = defineStore('theme', () => {
  const isDark = ref(localStorage.getItem('theme') === 'dark')

  function toggle() {
    isDark.value = !isDark.value
    localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
    updateBodyClass()
  }

  function updateBodyClass() {
    if (isDark.value) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  const theme = ref(isDark.value ? darkTheme : null)

  watch(isDark, (val) => {
    theme.value = val ? darkTheme : null
    updateBodyClass()
  })

  // 初始化
  updateBodyClass()

  return { isDark, theme, toggle }
})
