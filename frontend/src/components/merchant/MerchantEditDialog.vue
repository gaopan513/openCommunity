<script setup>
/**
 * 商家编辑店铺信息对话框
 *
 * 已审核通过的商家所有者更新自己的店铺资料（名称、分类、地址、电话、营业时间、简介、Logo、营业执照）。
 * 不允许修改 status / user 等敏感字段（由后端控制）。
 */
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getMyShop, updateMyShop } from '@/api/merchants'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  categories: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue', 'updated'])

const visible = ref(props.modelValue)
watch(() => props.modelValue, (v) => { visible.value = v })
watch(visible, (v) => emit('update:modelValue', v))

const loading = ref(false)
const submitting = ref(false)
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

/** 打开对话框时拉取当前店铺信息预填 */
watch(visible, async (v) => {
  if (!v) return
  loading.value = true
  try {
    const res = await getMyShop()
    const shop = res.data
    form.name = shop.name || ''
    form.category = shop.category?.id || ''
    form.address = shop.address || ''
    form.phone = shop.phone || ''
    form.business_hours = shop.business_hours || ''
    form.description = shop.description || ''
    licenseFile.value = shop.license_image ? { url: shop.license_image } : null
    licenseUrl.value = shop.license_image || ''
    logoFile.value = shop.logo ? { url: shop.logo } : null
    logoUrl.value = shop.logo || ''
  } catch (e) {
    // 错误已由请求层统一提示
  } finally {
    loading.value = false
  }
})

/** 生成并管理本地预览 URL */
function setLogoFile(file) {
  if (logoUrl.value && logoFile.value?.raw) URL.revokeObjectURL(logoUrl.value)
  logoFile.value = file
  logoUrl.value = file?.raw ? URL.createObjectURL(file.raw) : (file?.url || '')
}

function clearLogoFile() {
  if (logoUrl.value && logoFile.value?.raw) URL.revokeObjectURL(logoUrl.value)
  logoFile.value = null
  logoUrl.value = ''
}

function handleLicenseChange(file) {
  if (licenseUrl.value && licenseFile.value?.raw) URL.revokeObjectURL(licenseUrl.value)
  licenseFile.value = file
  licenseUrl.value = file?.raw ? URL.createObjectURL(file.raw) : (file?.url || '')
}

function clearLicenseFile() {
  if (licenseUrl.value && licenseFile.value?.raw) URL.revokeObjectURL(licenseUrl.value)
  licenseFile.value = null
  licenseUrl.value = ''
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
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

    await updateMyShop(fd)
    ElMessage.success('店铺信息已更新')
    emit('updated')
    visible.value = false
  } catch (e) {
    // 错误已由请求层统一提示
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <el-dialog
    v-model="visible"
    title="编辑店铺信息"
    width="640px"
    :close-on-click-modal="false"
    :append-to-body="true"
  >
    <el-alert
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 18px"
      title="修改后立即生效。如需变更营业执照，请重新上传。"
    />

    <el-form
      v-loading="loading"
      ref="formRef"
      :model="form"
      :rules="rules"
      label-position="top"
    >
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
      <el-button type="primary" :loading="submitting" @click="handleSubmit">保存修改</el-button>
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
