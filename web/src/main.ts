import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import ElementAiVue from 'element-ai-vue'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import 'element-ai-vue/dist/index.css'
import App from './App.vue'
import './style.css'

const app = createApp(App)
app.use(ElementPlus)
app.use(ElementAiVue)
app.mount('#app')
