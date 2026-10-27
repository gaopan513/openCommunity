/**
 * 应用入口文件
 * 
 * 配置 Vue 3 + Router + Pinia。
 * Element Plus 按需引入（unplugin-vue-components 自动加载模板中的 el-xxx 组件），
 * 此处仅注册实际用到的图标与函数式组件样式。
 */
import { createApp } from 'vue'
import {
  ArrowLeft, ArrowRight, Briefcase, Calendar, ChatDotRound, ChatDotSquare,
  CircleCheckFilled, Clock, Delete, Edit, EditPen, Goods, Location, Phone,
  Picture, Plus, Present, QuestionFilled, Search, Shop, Star, Tickets, View,
  WarningFilled,
} from '@element-plus/icons-vue'
// 函数式调用组件（ElMessage / ElMessageBox / ElLoading）不走模板解析，
// 需手动引入样式
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/message-box/style/css'
import 'element-plus/es/components/loading/style/css'

import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import './style.css'
import './styles/community.css'

const app = createApp(App)

// 按需注册实际用到的 Element Plus 图标（避免全量注册数百个图标）
const icons = {
  ArrowLeft, ArrowRight, Briefcase, Calendar, ChatDotRound, ChatDotSquare,
  CircleCheckFilled, Clock, Delete, Edit, EditPen, Goods, Location, Phone,
  Picture, Plus, Present, QuestionFilled, Search, Shop, Star, Tickets, View,
  WarningFilled,
}
for (const [key, component] of Object.entries(icons)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)

app.mount('#app')
