<script setup>
/**
 * 注册页面 — 暖色分栏布局
 */
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const formRef = ref(null)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  phone: '',
  community_name: '',
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 30, message: '用户名长度 3-30 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== form.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

async function handleRegister() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    // 角色由服务端固定为 resident，商家身份需入驻审核通过后授予
    await userStore.register({
      username: form.username,
      password: form.password,
      phone: form.phone,
      community_name: form.community_name,
    })
    ElMessage.success('注册成功')
    router.push('/')
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
          <h2>加入邻里，<br />从一份通讯开始。</h2>
          <p>
            注册一个账号，便可在小区里发帖、提问、淘闲置、约服务。
            把陌生的人，连成熟悉的邻里。
          </p>
        </div>
        <div class="oc-auth-aside-foot">Neighborhood · Since 2026</div>
      </aside>

      <!-- 表单区 -->
      <main class="oc-auth-main">
        <h3>创建账号</h3>
        <p class="oc-auth-sub">填写信息，成为邻里的一员</p>
        <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" placeholder="3-30个字符" size="large" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" type="password" placeholder="至少6位" show-password size="large" />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input v-model="form.confirmPassword" type="password" placeholder="再次输入密码" show-password size="large" />
          </el-form-item>
          <el-form-item label="手机号（选填）">
            <el-input v-model="form.phone" placeholder="11位手机号" size="large" />
          </el-form-item>
          <el-form-item label="所属小区（选填）">
            <el-input v-model="form.community_name" placeholder="如：阳光花园小区" size="large" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="loading" size="large" style="width: 100%" @click="handleRegister">
              注册
            </el-button>
          </el-form-item>
        </el-form>
        <div class="oc-auth-footer">
          已有账号？
          <router-link to="/login">去登录</router-link>
        </div>
      </main>
    </div>
  </div>
</template>
