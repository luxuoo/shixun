import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [
    vue({
      // aora-bot 是框架无关的 Web Component，交给浏览器解析
      template: {
        compilerOptions: {
          isCustomElement: (tag) => tag === 'aora-bot'
        }
      }
    })
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/uploads': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    // 关键依赖体积较大，但都是长期不变的第三方库，单独分块利于浏览器长期缓存
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          if (!id.includes('node_modules')) return
          if (id.includes('monaco-editor')) return 'monaco'
          if (id.includes('marked')) return 'markdown'
          if (
            id.includes('naive-ui') ||
            id.includes('vueuc') ||
            id.includes('css-render') ||
            id.includes('seemly') ||
            id.includes('treemate') ||
            id.includes('vdirs') ||
            id.includes('vooks') ||
            id.includes('evtd') ||
            id.includes('date-fns')
          ) {
            return 'naive-ui'
          }
          if (
            id.includes('vue-router') ||
            id.includes('pinia') ||
            id.includes('@vue/') ||
            id.includes('vue-demi')
          ) {
            return 'vue-vendor'
          }
          return 'vendor'
        }
      }
    }
  }
})
