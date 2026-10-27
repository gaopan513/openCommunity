import App from './App'
import { createSSRApp } from 'vue'
import * as Pinia from 'pinia'

export function createApp() {
  const app = createSSRApp(App)
  // 全局状态：用户登录态（与 Web 端 stores/user.js 对齐）
  app.use(Pinia.createPinia())
  return {
    app,
    Pinia,
  }
}
