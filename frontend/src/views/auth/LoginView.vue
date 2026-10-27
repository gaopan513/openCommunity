<script setup>
/**
 * 登录页面 — 暖色分栏布局
 */
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const loading = ref(false)
const formRef = ref(null)

const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.login(form.username, form.password)
    ElMessage.success('登录成功')
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="oc-auth">
    <div class="oc-auth-wrap">
      <!-- 暖色品牌侧栏 -->
      <aside class="oc-auth-aside">
        <div class="oc-auth-aside-brand">
          <span class="oc-auth-aside-mark">邻</span>
          <span class="oc-auth-aside-name">邻里通讯</span>
        </div>
        <div class="oc-auth-aside-quote">
          <h2>楼栋之间，<br />一句问候的温度。</h2>
          <p>
            登录后，你可以发帖聊天、提问互助、淘闲置、约家政——
            把陌生的小区，过成熟络的邻里。
          </p>
        </div>
        <div class="oc-auth-aside-foot">Neighborhood · Since 2026</div>
      </aside>

      <!-- 表单区 -->
      <main class="oc-auth-main">
        <h3>欢迎回来</h3>
        <p class="oc-auth-sub">用账号回到邻里通讯</p>
        <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名" size="large" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              show-password
              size="large"
              @keyup.enter="handleLogin"
            />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              :loading="loading"
              size="large"
              style="width: 100%"
              @click="handleLogin"
            >
              登录
            </el-button>
          </el-form-item>
        </el-form>
        <div class="oc-auth-footer">
          还没有账号？
          <router-link to="/register">立即注册</router-link>
        </div>
      </main>
    </div>
  </div>
</template>
