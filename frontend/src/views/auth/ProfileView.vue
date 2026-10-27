<script setup>
/**
 * 个人中心页面
 */
import { ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { getProfile, updateProfile, changePassword } from '@/api/auth'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const activeTab = ref('profile')

// 资料表单
const profileForm = ref({})
const profileLoading = ref(false)

// 密码表单
const passwordForm = ref({ old_password: '', new_password: '', confirm: '' })
const passwordLoading = ref(false)

onMounted(async () => {
  try {
    const res = await getProfile()
    profileForm.value = res.data
  } catch (e) {
    // 错误已处理
  }
})

async function handleUpdateProfile() {
  profileLoading.value = true
  try {
    const res = await updateProfile(profileForm.value)
    userStore.updateUserInfo(res.data)
    ElMessage.success('资料更新成功')
  } catch (e) {
    // 错误已处理
  } finally {
    profileLoading.value = false
  }
}

async function handleChangePassword() {
  if (passwordForm.value.new_password !== passwordForm.value.confirm) {
    ElMessage.error('两次输入的密码不一致')
    return
  }
  passwordLoading.value = true
  try {
    await changePassword({
      old_password: passwordForm.value.old_password,
      new_password: passwordForm.value.new_password,
      // 携带当前 refresh token，后端拉黑使其无法续期，彻底踢出旧会话
      refresh_token: userStore.refreshToken,
    })
    ElMessage.success('密码修改成功，请重新登录')
    // refresh token 已随改密请求由后端拉黑，此处仅需清理本地登录态
    // （logout() 为异步且需再调后端，会被下面的整页跳转中断）
    userStore.clearLocalAuth()
    window.location.href = '/login'
  } catch (e) {
    // 错误已处理
  } finally {
    passwordLoading.value = false
  }
}
</script>

<template>
  <div class="oc-page profile-page">
    <div class="oc-page-head">
      <span class="oc-kicker">My Account</span>
      <h1>个人中心</h1>
      <p class="oc-sub">管理你在邻里通讯的资料与账号安全</p>
    </div>

    <div class="oc-panel">
      <div class="oc-panel-head">
        <h2>账号设置</h2>
      </div>
      <div class="oc-panel-body">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="基本资料" name="profile">
            <el-form :model="profileForm" label-width="100px" style="max-width: 520px">
              <el-form-item label="用户名">
                <el-input :value="profileForm.username" disabled />
              </el-form-item>
              <el-form-item label="角色">
                <el-input :value="profileForm.role_display" disabled />
              </el-form-item>
              <el-form-item label="手机号">
                <el-input v-model="profileForm.phone" placeholder="选填" />
              </el-form-item>
              <el-form-item label="所属小区">
                <el-input v-model="profileForm.community_name" placeholder="选填" />
              </el-form-item>
              <el-form-item label="详细地址">
                <el-input v-model="profileForm.address" placeholder="选填" />
              </el-form-item>
              <el-form-item label="邮箱">
                <el-input v-model="profileForm.email" placeholder="选填" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="profileLoading" @click="handleUpdateProfile">
                  保存修改
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="修改密码" name="password">
            <el-form :model="passwordForm" label-width="100px" style="max-width: 520px">
              <el-form-item label="旧密码">
                <el-input v-model="passwordForm.old_password" type="password" show-password />
              </el-form-item>
              <el-form-item label="新密码">
                <el-input v-model="passwordForm.new_password" type="password" show-password />
              </el-form-item>
              <el-form-item label="确认新密码">
                <el-input v-model="passwordForm.confirm" type="password" show-password />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="passwordLoading" @click="handleChangePassword">
                  修改密码
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-page {
  padding-bottom: 40px;
}
</style>
