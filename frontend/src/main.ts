import { createApp } from 'vue'
import { createPinia } from 'pinia'
import naive from 'naive-ui'
import { defineAoraBot } from '@aora-bot/element'
import App from './App.vue'
import './styles/theme.css'
import './styles/boardui.css'
import router from './router'
import HelpIcon from './components/HelpIcon.vue'
import AoraBot from './components/AoraBot'
import BotAvatar from './components/BotAvatar'
import EmptyState from './components/EmptyState.vue'
import BoardUI from './components/BoardUI.vue'

// 注册 <aora-bot> 卡通角色组件（Web Component，框架无关）
defineAoraBot()

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(naive)

// 全局注册：帮助图标 / 卡通角色 / 角色头像 / 角色空状态
app.component('HelpIcon', HelpIcon)
app.component('AoraBot', AoraBot)
app.component('BotAvatar', BotAvatar)
app.component('EmptyState', EmptyState)
app.component('BoardUI', BoardUI)

app.mount('#app')
