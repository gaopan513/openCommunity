<script setup>
/**
 * 家政服务 - 服务商入驻申请对话框
 *
 * 商家角色用户申请成为家政服务提供者，等待管理员审核。
 */
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { applyProvider } from '@/api/housekeeping'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'created'])

const visible = ref(props.modelValue)
watch(() => props.modelValue, (v) => { visible.value = v })
watch(visible, (v) => emit('update:modelValue', v))

const loading = ref(false)
const formRef = ref(null)
const qualificationFile = ref(null)

const form = reactive({
  name: '',
  service_area: '',
  phone: '',
  description: '',
})

const rules = {
  name: [{ required: true, message: '请输入服务名称', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入联系电话', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' },
  ],
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const fd = new FormData()
    fd.append('name', form.name)
    fd.append('service_area', form.service_area)
    fd.append('phone', form.phone)
    fd.append('description', form.description)
    if (qualificationFile.value?.raw) {
      fd.append('qualification_image', qualificationFile.value.raw)
    }

    await applyProvider(fd)
    emit('created')
    resetForm()
  } catch (e) {
    // 错误已由请求层统一提示
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.name = ''
  form.service_area = ''
  form.phone = ''
  form.description = ''
  qualificationFile.value = null
  formRef.value?.resetFields()
}
</script>

<template>
  <el-dialog v-model="visible" title="家政服务入驻申请" width="560px" :close-on-click-modal="false" :append-to-body="true">
    <el-alert
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 18px"
      title="提交后由管理员审核，通过后可发布服务项目、接收邻居预约。"
    />

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="服务名称" prop="name">
        <el-input v-model="form.name" placeholder="如：张师傅家电维修" maxlength="100" />
      </el-form-item>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="联系电话" prop="phone">
            <el-input v-model="form.phone" placeholder="11 位手机号" maxlength="11" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="服务区域">
            <el-input v-model="form.service_area" placeholder="如：阳光花园小区及周边" maxlength="200" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="服务描述">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="擅长领域、从业经验、服务范围..."
          maxlength="1000"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="资质图片（选填）">
        <el-upload
          :auto-upload="false"
          :limit="1"
          accept="image/*"
          list-type="picture-card"
          :on-change="(file) => (qualificationFile = file)"
          :on-remove="() => (qualificationFile = null)"
        >
          <el-icon><Plus /></el-icon>
        </el-upload>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">提交申请</el-button>
    </template>
  </el-dialog>
</template>
