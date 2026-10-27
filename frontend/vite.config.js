import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import path from 'path'
import fs from 'fs'

// 启动时统一预打包 Element Plus 各组件的样式，避免 dev 运行时才发现新依赖、
// 触发 "optimized dependencies changed. reloading" 整页重载。
// 直接读取已安装的 element-plus，凡带 style/css.mjs 的组件都预先声明，
// 后续新增组件也无需手工维护该列表。
const elementPlusStyleDeps = (() => {
  const dir = path.resolve(__dirname, 'node_modules/element-plus/es/components')
  if (!fs.existsSync(dir)) return []
  return fs
    .readdirSync(dir)
    .filter((name) => fs.existsSync(path.join(dir, name, 'style', 'css.mjs')))
    .map((name) => `element-plus/es/components/${name}/style/css`)
})()

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    // Element Plus 按需引入：模板中的 el-xxx 组件自动按需加载对应 JS 与样式
    AutoImport({
      resolvers: [ElementPlusResolver()],
      dts: false,
    }),
    Components({
      resolvers: [ElementPlusResolver()],
      dts: false,
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  optimizeDeps: {
    include: elementPlusStyleDeps,
  },
  server: {
    port: 3000,
    proxy: {
      // 开发环境代理 API 请求到 Django 后端
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/media': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
