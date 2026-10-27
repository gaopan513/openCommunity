<script setup>
/**
 * 发布闲置对话框组件
 */
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { createProduct } from '@/api/secondhand'

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
const fileList = ref([])

const form = reactive({
  title: '',
  description: '',
  price: '',
  condition: 'good',
  category: '',
})

const conditionOptions = [
  { label: '全新', value: 'brand_new' },
  { label: '九成新', value: 'like_new' },
  { label: '八成新', value: 'good' },
  { label: '七成新及以下', value: 'fair' },
]

const rules = {
  title: [{ required: true, message: '请输入商品标题', trigger: 'blur' }],
  description: [{ required: true, message: '请描述商品情况', trigger: 'blur' }],
  price: [{ required: true, message: '请输入价格', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
}

function handleFileChange(file, list) {
  if (list.length > 9) {
    ElMessage.warning('最多上传9张图片')
    fileList.value = list.slice(0, 9)
    return
  }
  fileList.value = list
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const fd = new FormData()
    fd.append('title', form.title)
    fd.append('description', form.description)
    fd.append('price', form.price)
    fd.append('condition', form.condition)
    fd.append('category', form.category)
    fileList.value.forEach((f) => fd.append('images', f.raw))

    await createProduct(fd)
    emit('created')
    resetForm()
  } catch (e) {
    // 错误已处理
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.title = ''
  form.description = ''
  form.price = ''
  form.condition = 'good'
  form.category = ''
  fileList.value = []
  formRef.value?.resetFields()
}
</script>

<template>
  <el-dialog v-model="visible" title="发布闲置" width="640px" :close-on-click-modal="false" :append-to-body="true">
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="商品标题" prop="title">
        <el-input v-model="form.title" placeholder="品牌型号 + 简要描述" maxlength="100" show-word-limit />
      </el-form-item>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="价格（元）" prop="price">
            <el-input-number v-model="form.price" :min="0" :precision="2" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="成色" prop="condition">
            <el-select v-model="form.condition" style="width: 100%">
              <el-option v-for="c in conditionOptions" :key="c.value" :label="c.label" :value="c.value" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="分类" prop="category">
        <el-select v-model="form.category" placeholder="选择商品分类" style="width: 100%">
          <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
        </el-select>
      </el-form-item>

      <el-form-item label="商品描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="4"
          placeholder="入手渠道、使用情况、转手原因..."
          maxlength="1000"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="商品图片（最多9张）">
        <el-upload
          v-model:file-list="fileList"
          list-type="picture-card"
          :auto-upload="false"
          accept="image/*"
          :on-change="handleFileChange"
        >
          <el-icon><Plus /></el-icon>
        </el-upload>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">发布</el-button>
    </template>
  </el-dialog>
</template>
