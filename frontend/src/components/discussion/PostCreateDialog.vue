<script setup>
/**
 * 发帖对话框组件
 *
 * 支持标题、内容、类型、标签、多图上传。
 */
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { createPost } from '@/api/discussion'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
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
  content: '',
  post_type: 'chat',
  tags: '',
})

const rules = {
  title: [
    { required: true, message: '请输入标题', trigger: 'blur' },
    { max: 100, message: '标题不超过100字', trigger: 'blur' },
  ],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }],
}

function handleFileChange(file, list) {
  if (list.length > 9) {
    ElMessage.warning('最多上传9张图片')
    fileList.value = list.slice(0, 9)
    return
  }
  fileList.value = list
}

function handleRemove(file, list) {
  fileList.value = list
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const fd = new FormData()
    fd.append('title', form.title)
    fd.append('content', form.content)
    fd.append('post_type', form.post_type)
    fd.append('tags', form.tags)
    fileList.value.forEach((f) => fd.append('images', f.raw))

    await createPost(fd)
    emit('created')
    resetForm()
  } catch (e) {
    // 错误已在拦截器处理
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.title = ''
  form.content = ''
  form.post_type = 'chat'
  form.tags = ''
  fileList.value = []
  formRef.value?.resetFields()
}

function handleClose() {
  visible.value = false
}
</script>

<template>
  <el-dialog
    v-model="visible"
    title="发布新帖"
    width="640px"
    :close-on-click-modal="false"
    :append-to-body="true"
    @close="handleClose"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="标题" prop="title">
        <el-input v-model="form.title" placeholder="一句话概括你的帖子" maxlength="100" show-word-limit />
      </el-form-item>

      <el-form-item label="类型">
        <el-radio-group v-model="form.post_type">
          <el-radio-button value="chat">闲聊</el-radio-button>
          <el-radio-button value="help">求助</el-radio-button>
          <el-radio-button value="share">分享</el-radio-button>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="内容" prop="content">
        <el-input
          v-model="form.content"
          type="textarea"
          :rows="6"
          placeholder="想说点什么呢..."
          maxlength="2000"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="话题标签">
        <el-input v-model="form.tags" placeholder="多个标签用逗号分隔，如：美食,遛娃" />
      </el-form-item>

      <el-form-item label="图片（最多9张）">
        <el-upload
          v-model:file-list="fileList"
          list-type="picture-card"
          :auto-upload="false"
          accept="image/*"
          :on-change="handleFileChange"
          :on-remove="handleRemove"
        >
          <el-icon><Plus /></el-icon>
        </el-upload>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">发布</el-button>
    </template>
  </el-dialog>
</template>
