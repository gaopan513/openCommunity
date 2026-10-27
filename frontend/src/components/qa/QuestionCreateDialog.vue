<script setup>
/**
 * 提问对话框组件
 */
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { createQuestion } from '@/api/qa'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'created'])

const visible = ref(props.modelValue)
watch(() => props.modelValue, (v) => { visible.value = v })
watch(visible, (v) => emit('update:modelValue', v))

const loading = ref(false)
const formRef = ref(null)

const form = reactive({
  title: '',
  content: '',
  tags: [],
})

const commonTags = ['装修', '育儿', '养宠', '法律', '医疗', '美食', '出行', '其他']

const rules = {
  title: [{ required: true, message: '请输入问题标题', trigger: 'blur' }],
  content: [{ required: true, message: '请描述你的问题', trigger: 'blur' }],
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await createQuestion({
      title: form.title,
      content: form.content,
      tags: form.tags,
    })
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
  form.content = ''
  form.tags = []
  formRef.value?.resetFields()
}
</script>

<template>
  <el-dialog v-model="visible" title="我要提问" width="600px" :close-on-click-modal="false" :append-to-body="true">
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="问题标题" prop="title">
        <el-input v-model="form.title" placeholder="一句话说清你的问题" maxlength="100" show-word-limit />
      </el-form-item>

      <el-form-item label="详细描述" prop="content">
        <el-input
          v-model="form.content"
          type="textarea"
          :rows="6"
          placeholder="详细描述你的问题，信息越全越容易获得有效回答..."
          maxlength="2000"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="标签（可多选）">
        <el-select v-model="form.tags" multiple filterable allow-create placeholder="选择或输入标签" style="width: 100%">
          <el-option v-for="tag in commonTags" :key="tag" :label="tag" :value="tag" />
        </el-select>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">发布问题</el-button>
    </template>
  </el-dialog>
</template>
