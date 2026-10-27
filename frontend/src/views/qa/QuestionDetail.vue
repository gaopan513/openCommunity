<script setup>
/**
 * 经验问答 - 问题详情页
 *
 * 功能：问题正文、回答列表、采纳最佳答案、点赞、发表回答
 */
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getQuestion, addAnswer, acceptAnswer, likeQuestion, likeAnswer, deleteQuestion } from '@/api/qa'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const loading = ref(true)
const question = ref(null)
const liked = ref(false)
const likeCount = ref(0)
const answerContent = ref('')
const submitting = ref(false)

const isAuthor = computed(() => question.value && userStore.userInfo?.id === question.value.author)

async function fetchQuestion() {
  loading.value = true
  try {
    const res = await getQuestion(route.params.id)
    question.value = res.data
    liked.value = res.data.is_liked || false
    likeCount.value = res.data.like_count
  } catch (e) {
    // 错误已处理
  } finally {
    loading.value = false
  }
}

async function handleLike() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  try {
    const res = await likeQuestion(route.params.id)
    liked.value = res.data.liked
    likeCount.value = res.data.like_count
  } catch (e) {
    // 错误已处理
  }
}

async function handleAnswerLike(answer) {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  try {
    const res = await likeAnswer(route.params.id, answer.id)
    answer.is_liked = res.data.liked
    answer.like_count = res.data.like_count
  } catch (e) {
    // 错误已处理
  }
}

async function submitAnswer() {
  if (!answerContent.value.trim()) {
    ElMessage.warning('回答内容不能为空')
    return
  }
  submitting.value = true
  try {
    await addAnswer(route.params.id, { content: answerContent.value })
    ElMessage.success('回答成功')
    answerContent.value = ''
    fetchQuestion()
  } catch (e) {
    // 错误已处理
  } finally {
    submitting.value = false
  }
}

async function handleAccept(answerId) {
  try {
    await ElMessageBox.confirm('采纳后该回答将标记为最佳答案，确定吗？', '采纳确认', { type: 'success' })
    await acceptAnswer(route.params.id, answerId)
    ElMessage.success('已采纳为最佳答案')
    fetchQuestion()
  } catch (e) {
    // 用户取消或错误已处理
  }
}

async function handleDelete() {
  try {
    await ElMessageBox.confirm('确定删除这个问题吗？', '删除确认', { type: 'warning' })
    await deleteQuestion(route.params.id)
    ElMessage.success('删除成功')
    router.push('/qa')
  } catch (e) {
    // 用户取消或错误已处理
  }
}

onMounted(fetchQuestion)
</script>

<template>
  <div class="oc-page question-detail" v-loading="loading">
    <el-button text @click="router.push('/qa')" style="margin-bottom: 16px">
      <el-icon><ArrowLeft /></el-icon> 返回问答
    </el-button>

    <div v-if="question" class="detail-layout">
      <!-- 问题主体 -->
      <div class="oc-card main-card">
        <div class="status-strip" :class="{ solved: question.is_solved }">
          <el-icon :size="16"><CircleCheckFilled v-if="question.is_solved" /><QuestionFilled v-else /></el-icon>
          {{ question.is_solved ? '问题已解决' : '等待回答中' }}
        </div>

        <h1 class="detail-title">{{ question.title }}</h1>

        <div class="author-row">
          <el-avatar :size="38" :src="question.author_info?.avatar">
            {{ question.author_info?.username?.charAt(0)?.toUpperCase() }}
          </el-avatar>
          <div>
            <div class="author-name">{{ question.author_info?.username }}</div>
            <div class="post-time">{{ question.created_at }} · {{ question.view_count }} 次浏览</div>
          </div>
          <el-button v-if="isAuthor" size="small" type="danger" plain style="margin-left: auto" @click="handleDelete">
            删除
          </el-button>
        </div>

        <div class="detail-content">{{ question.content }}</div>

        <div v-if="question.tags && question.tags.length" class="detail-tags">
          <span v-for="tag in question.tags" :key="tag.id" class="tag-chip">{{ tag.name }}</span>
        </div>

        <div class="like-zone">
          <button class="like-btn" :class="{ active: liked }" @click="handleLike">
            <el-icon :size="18"><Star /></el-icon>
            {{ liked ? '已赞' : '有用' }} {{ likeCount }}
          </button>
        </div>
      </div>

      <!-- 回答区 -->
      <div class="oc-card answer-card">
        <h3 class="section-title">
          全部回答 <span class="count">({{ question.answer_count }})</span>
        </h3>

        <div class="answer-list">
          <div
            v-for="answer in question.answers"
            :key="answer.id"
            class="answer-item"
            :class="{ accepted: answer.is_accepted }"
          >
            <div v-if="answer.is_accepted" class="accepted-flag">
              <el-icon><CircleCheckFilled /></el-icon> 最佳答案
            </div>
            <div class="answer-main">
              <el-avatar :size="36" :src="answer.author_info?.avatar">
                {{ answer.author_info?.username?.charAt(0)?.toUpperCase() }}
              </el-avatar>
              <div class="answer-body">
                <div class="answer-author">{{ answer.author_info?.username }}</div>
                <div class="answer-text">{{ answer.content }}</div>
                <div class="answer-foot">
                  <span class="answer-time">{{ answer.created_at }}</span>
                  <button
                    class="answer-like-btn"
                    :class="{ active: answer.is_liked }"
                    @click="handleAnswerLike(answer)"
                  >
                    <el-icon><Star /></el-icon> {{ answer.like_count }}
                  </button>
                  <button
                    v-if="isAuthor && !answer.is_accepted && !question.is_solved"
                    class="accept-btn"
                    @click="handleAccept(answer.id)"
                  >
                    采纳为最佳答案
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div v-if="!question.answers || question.answers.length === 0" class="oc-empty">
            还没有回答，来分享你的经验吧
          </div>
        </div>

        <!-- 写回答 -->
        <div class="write-answer">
          <h4 class="write-title">我来回答</h4>
          <el-input
            v-model="answerContent"
            type="textarea"
            :rows="4"
            placeholder="分享你的经验和见解..."
          />
          <div class="write-actions">
            <el-button type="primary" :loading="submitting" @click="submitAnswer">提交回答</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.detail-layout {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.main-card {
  padding: 32px;
}

.status-strip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #fdf3dd;
  color: #b0761a;
  font-size: 13px;
  font-weight: 700;
  padding: 5px 14px;
  border-radius: 999px;
  margin-bottom: 16px;
}

.status-strip.solved {
  background: var(--oc-accent-soft);
  color: var(--oc-accent);
}

.detail-title {
  font-family: var(--oc-font-display);
  font-size: 28px;
  font-weight: 700;
  color: var(--oc-ink);
  margin: 0 0 18px;
  line-height: 1.35;
}

.author-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--oc-line);
}

.author-name { font-weight: 700; color: var(--oc-accent); font-size: 15px; }
.post-time { font-size: 12px; color: var(--oc-ink-soft); margin-top: 2px; }

.detail-content {
  font-size: 16px;
  line-height: 1.9;
  color: var(--oc-ink);
  white-space: pre-wrap;
  padding: 22px 0;
}

.detail-tags { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 18px; }

.tag-chip {
  background: var(--oc-accent-soft);
  color: var(--oc-accent);
  font-size: 13px;
  padding: 3px 14px;
  border-radius: 999px;
  font-weight: 600;
}

.like-zone {
  display: flex;
  justify-content: center;
  padding-top: 10px;
  border-top: 1px solid var(--oc-line);
}

.like-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 2px solid var(--oc-line);
  background: #fff;
  color: var(--oc-ink-soft);
  padding: 10px 32px;
  border-radius: 999px;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.25s ease;
}

.like-btn:hover { border-color: var(--oc-accent); color: var(--oc-accent); transform: scale(1.04); }
.like-btn.active { border-color: var(--oc-accent); background: var(--oc-accent-soft); color: var(--oc-accent); }

.answer-card { padding: 28px 32px; }

.section-title {
  font-size: 19px;
  font-weight: 700;
  color: var(--oc-ink);
  margin: 0 0 20px;
}

.section-title .count { color: var(--oc-ink-soft); font-weight: 400; font-size: 15px; }

.answer-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 28px;
}

.answer-item {
  border: 1px solid var(--oc-line);
  border-radius: 12px;
  padding: 18px;
  position: relative;
  transition: border-color 0.2s;
}

.answer-item.accepted {
  border-color: #a8cfba;
  background: linear-gradient(180deg, #f4faf6 0%, #ffffff 60%);
}

.accepted-flag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--oc-accent);
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 12px;
}

.answer-main { display: flex; gap: 12px; }
.answer-body { flex: 1; min-width: 0; }

.answer-author { font-weight: 700; color: var(--oc-ink); font-size: 14px; }

.answer-text {
  color: var(--oc-ink);
  font-size: 14px;
  line-height: 1.8;
  margin: 6px 0 10px;
  white-space: pre-wrap;
}

.answer-foot {
  display: flex;
  align-items: center;
  gap: 16px;
}

.answer-time { font-size: 12px; color: var(--oc-ink-soft); }

.answer-like-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--oc-ink-soft);
  background: #fff;
  border: 1px solid var(--oc-line);
  border-radius: 999px;
  padding: 3px 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.answer-like-btn:hover { border-color: var(--oc-accent); color: var(--oc-accent); }
.answer-like-btn.active { border-color: var(--oc-accent); background: var(--oc-accent-soft); color: var(--oc-accent); }

.accept-btn {
  margin-left: auto;
  border: 1px solid var(--oc-accent);
  background: #fff;
  color: var(--oc-accent);
  font-size: 12px;
  font-weight: 700;
  padding: 5px 14px;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.2s;
}

.accept-btn:hover { background: var(--oc-accent); color: #fff; }

.write-answer {
  border-top: 1px solid var(--oc-line);
  padding-top: 22px;
}

.write-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--oc-ink);
  margin: 0 0 12px;
}

.write-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
</style>
