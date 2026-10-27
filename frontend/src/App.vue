<script setup>
/**
 * 根组件 — 邻里通讯式全局布局
 *
 * 顶部为社区通讯式报头（Masthead），含品牌标识、板块导航与用户区；
 * 底部为暖色页脚。
 */
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const navItems = [
  { path: '/', label: '首页', exact: true },
  { path: '/discussion', label: '自由发言' },
  { path: '/qa', label: '经验问答' },
  { path: '/secondhand', label: '二手市场' },
  { path: '/merchants', label: '周边商家' },
  { path: '/housekeeping', label: '家政服务' },
]

function isActive(item) {
  if (item.exact) return route.path === item.path
  return route.path === item.path || route.path.startsWith(item.path + '/')
}

async function handleLogout() {
  // 等待登出完成（含后端拉黑 refresh token）后再跳转
  await userStore.logout()
  router.push('/login')
}
</script>

<template>
  <!-- el-config-provider 提供中文 locale（按需引入模式下替代 app.use(ElementPlus, { locale })） -->
  <el-config-provider :locale="zhCn">
  <div id="app-layout">
    <!-- 顶部报头 Masthead -->
    <header class="oc-masthead">
      <div class="oc-masthead-inner">
        <router-link to="/" class="oc-brand">
          <span class="oc-brand-mark">邻</span>
          <span class="oc-brand-text">
            <span class="oc-brand-name">邻里通讯</span>
            <span class="oc-brand-tag">Neighborhood Gazette</span>
          </span>
        </router-link>

        <nav class="oc-nav">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="oc-nav-item"
            :class="{ 'router-link-active': isActive(item) }"
          >
            {{ item.label }}
          </router-link>
        </nav>

        <div class="user-area">
          <template v-if="userStore.isLoggedIn">
            <el-dropdown>
              <span class="user-name">
                {{ userStore.username }}
                <el-icon><arrow-down /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="router.push('/profile')">
                    个人中心
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="handleLogout">
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <template v-else>
            <el-button size="small" round @click="router.push('/login')">
              登录
            </el-button>
            <el-button type="primary" size="small" round @click="router.push('/register')">
              注册
            </el-button>
          </template>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="app-main">
      <router-view />
    </main>

    <!-- 底部 -->
    <footer class="oc-footer">
      <div class="oc-footer-rule"></div>
      <strong>邻里通讯</strong> · openCommunity 社区论坛 &copy; 2026
      <span style="opacity: 0.5; margin: 0 8px;">|</span>
      以小区为中心，连接邻里生活
    </footer>
  </div>
  </el-config-provider>
</template>

<style scoped>
.app-main {
  max-width: 1200px;
  margin: 28px auto;
  min-height: calc(100vh - 200px);
  padding: 0 20px;
}

.user-area {
  display: flex;
  align-items: center;
  gap: 10px;
  white-space: nowrap;
}

.user-name {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--oc-ink);
  font-weight: 600;
  font-size: 14px;
  padding: 6px 10px;
  border-radius: 8px;
  transition: background 0.2s ease;
}

.user-name:hover {
  background: var(--oc-primary-soft);
}

@media (max-width: 768px) {
  .oc-masthead-inner {
    height: auto;
    flex-wrap: wrap;
    padding: 10px 16px;
    gap: 12px;
  }
  .oc-nav {
    order: 3;
    width: 100%;
    overflow-x: auto;
    gap: 0;
  }
  .oc-nav-item {
    white-space: nowrap;
    padding: 6px 10px;
  }
  .app-main {
    margin: 16px auto;
    padding: 0 14px;
  }
}
</style>
