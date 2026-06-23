import { createApp } from 'vue'
import { createPinia } from 'pinia'
import naive from 'naive-ui'
import App from './App.vue'
import router from './router'
import HelpIcon from './components/HelpIcon.vue'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(naive)

// 全局注册帮助图标组件
app.component('HelpIcon', HelpIcon)

app.mount('#app')
