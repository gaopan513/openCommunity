<script setup>
/**
 * 自由发言 - 帖子详情页
 *
 * 功能：正文展示、图片画廊、点赞、评论（楼中楼）、管理操作
 */
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPost, likePost, addComment, deletePost, featurePost } from '@/api/discussion'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const loading = ref(true)
const post = ref(null)
const liked = ref(false)
const likeCount = ref(0)

const commentForm = reactive({ content: '', parent: null, replyTo: null })
const submitting = ref(false)

const isAuthor = computed(() => post.value && userStore.userInfo?.id === post.value.author)
const canManage = computed(() => userStore.isAdmin)

async function fetchPost() {
  loading.value = true
  try {
    const res = await getPost(route.params.id)
    post.value = res.data
    liked.value = res.data.is_liked
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
    const res = await likePost(route.params.id)
    liked.value = res.data.liked
    likeCount.value = res.data.like_count
  } catch (e) {
    // 错误已处理
  }
}

function setReply(comment) {
  commentForm.parent = comment.id
  commentForm.replyTo = comment.author_info?.username
}

function cancelReply() {
  commentForm.parent = null
  commentForm.replyTo = null
}

async function submitComment() {
  if (!commentForm.content.trim()) {
    ElMessage.warning('评论内容不能为空')
    return
  }
  submitting.value = true
  try {
    await addComment(route.params.id, {
      content: commentForm.content,
      parent: commentForm.parent,
    })
    ElMessage.success('评论成功')
    commentForm.content = ''
    cancelReply()
    fetchPost()
  } catch (e) {
    // 错误已处理
  } finally {
    submitting.value = false
  }
}

async function handleDelete() {
  try {
    await ElMessageBox.confirm('确定删除这篇帖子吗？此操作不可恢复。', '删除确认', {
      type: 'warning',
    })
    await deletePost(route.params.id)
    ElMessage.success('删除成功')
    router.push('/discussion')
  } catch (e) {
    // 用户取消或错误已处理
  }
}

async function toggleFeature(field) {
  try {
    await featurePost(route.params.id, { [field]: !post.value[field] })
    ElMessage.success('操作成功')
    fetchPost()
  } catch (e) {
    // 错误已处理
  }
}

function typeLabel(t) {
  return { chat: '闲聊', help: '求助', share: '分享', notice: '公告' }[t] || t
}

onMounted(fetchPost)
</script>

<template>
  <div class="oc-page post-detail" v-loading="loading">
    <el-button text @click="router.push('/discussion')" style="margin-bottom: 16px">
      <el-icon><ArrowLeft /></el-icon> 返回列表
    </el-button>

    <div v-if="post" class="detail-layout">
      <!-- 主内容 -->
      <div class="oc-card main-card">
        <div class="detail-head">
          <div class="badge-row">
            <span v-if="post.is_top" class="oc-tag oc-tag--top">置顶</span>
            <span v-if="post.is_featured" class="oc-tag oc-tag--featured">精华</span>
            <span class="oc-tag oc-tag--neutral">{{ typeLabel(post.post_type) }}</span>
          </div>
          <h1 class="detail-title">{{ post.title }}</h1>
          <div class="author-row">
            <el-avatar :size="40" :src="post.author_info?.avatar">
              {{ post.author_info?.username?.charAt(0)?.toUpperCase() }}
            </el-avatar>
            <div>
              <div class="author-name">{{ post.author_info?.username }}</div>
              <div class="post-time">{{ post.created_at }} · {{ post.view_count }} 次浏览</div>
            </div>
            <div v-if="isAuthor || canManage" class="manage-actions">
              <el-button v-if="isAuthor || canManage" size="small" type="danger" plain @click="handleDelete">删除</el-button>
              <template v-if="canManage">
                <el-button size="small" :type="post.is_top ? 'warning' : 'default'" @click="toggleFeature('is_top')">
                  {{ post.is_top ? '取消置顶' : '置顶' }}
                </el-button>
                <el-button size="small" :type="post.is_featured ? 'warning' : 'default'" @click="toggleFeature('is_featured')">
                  {{ post.is_featured ? '取消加精' : '加精' }}
                </el-button>
              </template>
            </div>
          </div>
        </div>

        <div class="detail-content">{{ post.content }}</div>

        <!-- 图片画廊 -->
        <div v-if="post.images && post.images.length" class="image-gallery">
          <el-image
            v-for="img in post.images"
            :key="img.id"
            :src="img.image"
            :preview-src-list="post.images.map(i => i.image)"
            fit="cover"
            class="gallery-item"
          />
        </div>

        <div v-if="post.tags" class="detail-tags">
          <span v-for="tag in post.tags.split(',').filter(Boolean)" :key="tag" class="hash-tag">#{{ tag }}</span>
        </div>

        <!-- 点赞 -->
        <div class="like-zone">
          <button class="like-btn" :class="{ active: liked }" @click="handleLike">
            <el-icon :size="18"><Star /></el-icon>
            {{ liked ? '已赞' : '点赞' }} {{ likeCount }}
          </button>
        </div>
      </div>

      <!-- 评论区 -->
      <div class="oc-card comment-card">
        <h3 class="section-title">
          评论 <span class="count">({{ post.comment_count }})</span>
        </h3>

        <div class="comment-input">
          <el-input
            v-model="commentForm.content"
            type="textarea"
            :rows="3"
            :placeholder="commentForm.replyTo ? `回复 @${commentForm.replyTo}` : '写下你的评论...'"
          />
          <div class="comment-input-actions">
            <el-button v-if="commentForm.replyTo" size="small" text @click="cancelReply">
              取消回复 @{{ commentForm.replyTo }}
            </el-button>
            <el-button type="primary" size="small" :loading="submitting" @click="submitComment">发表评论</el-button>
          </div>
        </div>

        <div class="comment-list">
          <div v-for="comment in post.comments" :key="comment.id" class="comment-item">
            <el-avatar :size="36" :src="comment.author_info?.avatar">
              {{ comment.author_info?.username?.charAt(0)?.toUpperCase() }}
            </el-avatar>
            <div class="comment-body">
              <div class="comment-author">{{ comment.author_info?.username }}</div>
              <div class="comment-text">{{ comment.content }}</div>
              <div class="comment-foot">
                <span class="comment-time">{{ comment.created_at }}</span>
                <button class="reply-link" @click="setReply(comment)">回复</button>
              </div>

              <!-- 楼中楼 -->
              <div v-if="comment.replies && comment.replies.length" class="reply-list">
                <div v-for="reply in comment.replies" :key="reply.id" class="reply-item">
                  <el-avatar :size="28" :src="reply.author_info?.avatar">
                    {{ reply.author_info?.username?.charAt(0)?.toUpperCase() }}
                  </el-avatar>
                  <div class="comment-body">
                    <div class="comment-author small">{{ reply.author_info?.username }}</div>
                    <div class="comment-text">{{ reply.content }}</div>
                    <div class="comment-foot">
                      <span class="comment-time">{{ reply.created_at }}</span>
                      <button class="reply-link" @click="setReply(comment)">回复</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="!post.comments || post.comments.length === 0" class="oc-empty">
            还没有评论，来抢沙发吧
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

.badge-row {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
}

.detail-title {
  font-family: var(--oc-font-display);
  font-size: 30px;
  font-weight: 700;
  color: var(--oc-ink);
  margin: 0 0 20px;
  line-height: 1.35;
}

.author-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--oc-line);
}

.author-name {
  font-weight: 700;
  color: var(--oc-accent);
  font-size: 15px;
}

.post-time {
  font-size: 12px;
  color: var(--oc-ink-soft);
  margin-top: 2px;
}

.manage-actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

.detail-content {
  font-size: 16px;
  line-height: 1.9;
  color: var(--oc-ink);
  white-space: pre-wrap;
  padding: 24px 0;
}

.image-gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 10px;
  margin-bottom: 20px;
}

.gallery-item {
  border-radius: 10px;
  height: 160px;
  cursor: zoom-in;
}

.detail-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.hash-tag {
  color: var(--oc-primary);
  font-size: 14px;
  background: var(--oc-primary-soft);
  padding: 3px 12px;
  border-radius: 999px;
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

.like-btn:hover {
  border-color: var(--oc-gold);
  color: var(--oc-gold);
  transform: scale(1.04);
}

.like-btn.active {
  border-color: var(--oc-gold);
  background: #fdf3dd;
  color: var(--oc-gold);
}

.comment-card {
  padding: 28px 32px;
}

.section-title {
  font-size: 19px;
  font-weight: 700;
  color: var(--oc-ink);
  margin: 0 0 20px;
}

.section-title .count {
  color: var(--oc-ink-soft);
  font-weight: 400;
  font-size: 15px;
}

.comment-input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.comment-list {
  margin-top: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.comment-item {
  display: flex;
  gap: 12px;
}

.comment-body {
  flex: 1;
  min-width: 0;
}

.comment-author {
  font-weight: 700;
  color: var(--oc-ink);
  font-size: 14px;
}

.comment-author.small {
  font-size: 13px;
}

.comment-text {
  color: var(--oc-ink);
  font-size: 14px;
  line-height: 1.7;
  margin: 4px 0 6px;
  white-space: pre-wrap;
}

.comment-foot {
  display: flex;
  align-items: center;
  gap: 14px;
}

.comment-time {
  font-size: 12px;
  color: var(--oc-ink-soft);
}

.reply-link {
  border: none;
  background: none;
  color: var(--oc-primary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
}

.reply-link:hover {
  text-decoration: underline;
}

.reply-list {
  margin-top: 12px;
  padding: 12px 14px;
  background: var(--oc-paper);
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.reply-item {
  display: flex;
  gap: 10px;
}
</style>
