<script setup>
/**
 * 家政服务 - 预约下单对话框
 *
 * 居民选择日期、时段并提交预约，仅居民角色可操作。
 */
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { createBooking } from '@/api/housekeeping'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  /** 预约的服务项目（含 id、title、provider_name、价格区间） */
  serviceItem: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue', 'created'])

const visible = ref(props.modelValue)
watch(() => props.modelValue, (v) => { visible.value = v })
watch(visible, (v) => emit('update:modelValue', v))

const loading = ref(false)
const formRef = ref(null)

const form = reactive({
  preferred_date: '',
  preferred_time: '',
  remark: '',
})

/** 常用家政时段 */
const timeSlots = [
  '08:00 - 10:00',
  '10:00 - 12:00',
  '14:00 - 16:00',
  '16:00 - 18:00',
  '18:00 - 20:00',
]

const rules = {
  preferred_date: [{ required: true, message: '请选择预约日期', trigger: 'change' }],
  preferred_time: [{ required: true, message: '请选择预约时段', trigger: 'change' }],
}

/** 日期禁用：只能选今天及以后 */
function disabledDate(date) {
  return date.getTime() < Date.now() - 24 * 3600 * 1000
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await createBooking({
      service_item: props.serviceItem.id,
      preferred_date: form.preferred_date,
      preferred_time: form.preferred_time,
      remark: form.remark,
    })
    emit('created')
    resetForm()
  } catch (e) {
    // 错误已由请求层统一提示
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.preferred_date = ''
  form.preferred_time = ''
  form.remark = ''
  formRef.value?.resetFields()
}
</script>

<template>
  <el-dialog v-model="visible" title="预约服务" width="520px" :close-on-click-modal="false" :append-to-body="true">
    <!-- 预约的服务信息 -->
    <div v-if="serviceItem" class="booking-target">
      <div class="target-info">
        <h4>{{ serviceItem.title }}</h4>
        <p>{{ serviceItem.provider_name }} 提供</p>
      </div>
      <span class="target-price">
        ¥{{ serviceItem.price_min }}<template v-if="Number(serviceItem.price_max) > Number(serviceItem.price_min)"> - {{ serviceItem.price_max }}</template>
      </span>
    </div>

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="预约日期" prop="preferred_date">
        <el-date-picker
          v-model="form.preferred_date"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="选择上门日期"
          :disabled-date="disabledDate"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="预约时段" prop="preferred_time">
        <div class="slot-grid">
          <button
            v-for="slot in timeSlots"
            :key="slot"
            type="button"
            class="slot-chip"
            :class="{ active: form.preferred_time === slot }"
            @click="form.preferred_time = slot"
          >
            {{ slot }}
          </button>
        </div>
      </el-form-item>

      <el-form-item label="备注说明">
        <el-input
          v-model="form.remark"
          type="textarea"
          :rows="3"
          placeholder="门牌号、注意事项、特殊需求..."
          maxlength="500"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">提交预约</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.booking-target {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
  background: var(--oc-accent-soft);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 18px;
}

.target-info h4 {
  margin: 0 0 4px;
  font-size: 15px;
  font-weight: 800;
  color: var(--oc-ink);
}

.target-info p {
  margin: 0;
  font-size: 12px;
  color: var(--oc-ink-soft);
}

.target-price {
  font-size: 18px;
  font-weight: 800;
  color: var(--oc-primary);
  white-space: nowrap;
}

.slot-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  width: 100%;
}

.slot-chip {
  border: 1px solid var(--oc-line);
  background: #fff;
  padding: 8px 14px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--oc-ink-soft);
  cursor: pointer;
  transition: all 0.2s ease;
}

.slot-chip:hover { border-color: var(--oc-accent); color: var(--oc-accent); }

.slot-chip.active {
  background: var(--oc-accent);
  border-color: var(--oc-accent);
  color: #fff;
  box-shadow: 0 3px 10px rgba(31, 111, 84, 0.3);
}
</style>
