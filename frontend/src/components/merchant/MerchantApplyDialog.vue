<script setup>
/**
 * 商家入驻申请对话框
 *
 * 商家角色用户填写店铺资料提交入驻申请，等待管理员审核。
 */
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { applyMerchant } from '@/api/merchants'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  categories: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue', 'created'])

const visible = ref(props.modelValue)
watch(() => props.modelValue, (v) => { visible.value = v })
watch(visible, (v) => emit('update:modelValue', v))

const loading = ref(false)
const formRef = ref(null)
const licenseFile = ref(null)
const licenseUrl = ref('')
const logoFile = ref(null)
const logoUrl = ref('')

const form = reactive({
  name: '',
  category: '',
  address: '',
  phone: '',
  business_hours: '',
  description: '',
})

const rules = {
  name: [{ required: true, message: '请输入商家名称', trigger: 'blur' }],
  category: [{ required: true, message: '请选择经营分类', trigger: 'change' }],
  address: [{ required: true, message: '请输入店铺地址', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入联系电话', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' },
  ],
}

/** 生成并管理本地预览 URL */
function setLogoFile(file) {
  if (logoUrl.value) URL.revokeObjectURL(logoUrl.value)
  logoFile.value = file
  logoUrl.value = file?.raw ? URL.createObjectURL(file.raw) : ''
}

function clearLogoFile() {
  if (logoUrl.value) URL.revokeObjectURL(logoUrl.value)
  logoFile.value = null
  logoUrl.value = ''
}

/** 营业执照选择（单张，提交时放入 FormData） */
function handleLicenseChange(file) {
  if (licenseUrl.value) URL.revokeObjectURL(licenseUrl.value)
  licenseFile.value = file
  licenseUrl.value = file?.raw ? URL.createObjectURL(file.raw) : ''
}

function clearLicenseFile() {
  if (licenseUrl.value) URL.revokeObjectURL(licenseUrl.value)
  licenseFile.value = null
  licenseUrl.value = ''
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const fd = new FormData()
    fd.append('name', form.name)
    fd.append('category', form.category)
    fd.append('address', form.address)
    fd.append('phone', form.phone)
    fd.append('business_hours', form.business_hours)
    fd.append('description', form.description)
    if (logoFile.value?.raw) {
      fd.append('logo', logoFile.value.raw)
    }
    if (licenseFile.value?.raw) {
      fd.append('license_image', licenseFile.value.raw)
    }

    await applyMerchant(fd)
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
  form.category = ''
  form.address = ''
  form.phone = ''
  form.business_hours = ''
  form.description = ''
  clearLicenseFile()
  clearLogoFile()
  formRef.value?.resetFields()
}
</script>

<template>
  <el-dialog v-model="visible" title="商家入驻申请" width="640px" :close-on-click-modal="false" :append-to-body="true">
    <el-alert
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 18px"
      title="提交后由管理员审核，审核通过即可在平台展示店铺信息、发布活动。"
    />

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="商家名称" prop="name">
            <el-input v-model="form.name" placeholder="如：王姐家常菜" maxlength="100" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="经营分类" prop="category">
            <el-select v-model="form.category" placeholder="选择分类" style="width: 100%">
              <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="店铺地址" prop="address">
        <el-input v-model="form.address" placeholder="如：小区东门旁 12 号商铺" maxlength="200" />
      </el-form-item>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="联系电话" prop="phone">
            <el-input v-model="form.phone" placeholder="11 位手机号" maxlength="11" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="营业时间">
            <el-input v-model="form.business_hours" placeholder="如：08:00 - 21:30" maxlength="200" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="商家简介">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="主营内容、特色服务、门店优势..."
          maxlength="1000"
          show-word-limit
        />
      </el-form-item>

      <div class="upload-row">
        <el-form-item label="商家 Logo">
          <el-upload
            v-if="!logoFile"
            class="logo-uploader"
            :auto-upload="false"
            :limit="1"
            accept="image/*"
            list-type="picture-card"
            :show-file-list="false"
            :on-change="setLogoFile"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
          <div v-else class="image-preview">
            <el-image
              :src="logoUrl"
              fit="cover"
              :preview-src-list="[logoUrl]"
              class="preview-img"
            />
            <div class="preview-actions">
              <el-icon class="preview-action" @click="clearLogoFile"><Delete /></el-icon>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="营业执照">
          <el-upload
            v-if="!licenseFile"
            :auto-upload="false"
            :limit="1"
            accept="image/*"
            list-type="picture-card"
            :show-file-list="false"
            :on-change="handleLicenseChange"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
          <div v-else class="image-preview">
            <el-image
              :src="licenseUrl"
              fit="cover"
              :preview-src-list="[licenseUrl]"
              class="preview-img"
            />
            <div class="preview-actions">
              <el-icon class="preview-action" @click="clearLicenseFile"><Delete /></el-icon>
            </div>
          </div>
        </el-form-item>
      </div>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">提交申请</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
/* Logo 上传框大小与营业执照一致（默认 picture-card 尺寸） */
.logo-uploader :deep(.el-upload--picture-card) i.el-icon,
.logo-uploader :deep(.el-upload--picture-card) svg {
  font-size: 28px;
}

.upload-row {
  display: flex;
  gap: 12px;
}

.image-preview {
  width: 148px;
}

.image-preview .preview-img {
  width: 148px;
  height: 148px;
  border-radius: 8px;
  display: block;
}

.image-preview .preview-actions {
  display: flex;
  justify-content: center;
  margin-top: 4px;
}

.image-preview .preview-action {
  color: var(--el-color-danger);
  font-size: 16px;
  cursor: pointer;
  padding: 4px;
}
</style>
