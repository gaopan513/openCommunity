<template>
  <view class="oc-page">
    <!-- 品牌横幅 -->
    <view class="hero">
      <view class="hero-title">邻里社区</view>
      <view class="hero-sub">家门口的互助生活圈</view>
    </view>

    <!-- 板块入口 -->
    <view class="grid">
      <view v-for="entry in entries" :key="entry.label" class="grid-item" @tap="entry.go">
        <view class="grid-icon" :style="{ background: entry.bg, color: entry.color }">{{ entry.icon }}</view>
        <view class="grid-label">{{ entry.label }}</view>
        <view class="grid-desc">{{ entry.desc }}</view>
      </view>
    </view>

    <!-- 公告 -->
    <view class="oc-card notice-card">
      <view class="oc-section-title">社区公告</view>
      <block v-if="announcements.length">
        <view v-for="item in announcements" :key="item.id" class="notice-item" @tap="toggleNotice(item)">
          <view class="notice-dot"></view>
          <view class="notice-body">
            <view class="notice-title">{{ item.title }}</view>
            <view v-if="expandedId === item.id && item.content" class="notice-content">{{ item.content }}</view>
            <view class="notice-time">{{ shortDate(item.created_at) }}</view>
          </view>
        </view>
      </block>
      <view v-else-if="!loading" class="oc-empty">暂无公告</view>
    </view>
  </view>
</template>

<script setup>
/**
 * 首页：板块入口 + 社区公告。
 * 经验问答为二级页入口，其余为 Tab 页跳转。
 */
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { getAnnouncements } from '@/api/admin'
import { shortDate } from '@/utils/format'
import { ROUTE, TAB } from '@/router/paths'

const announcements = ref([])
const loading = ref(true)
const expandedId = ref(null)

const entries = [
  {
    label: '邻里圈',
    icon: '圈',
    desc: '闲聊求助分享',
    bg: '#fff3ec',
    color: '#e8622c',
    go: () => uni.switchTab({ url: TAB.posts }),
  },
  {
    label: '经验问答',
    icon: '问',
    desc: '有问必答互助',
    bg: '#ecf2ff',
    color: '#165dff',
    go: () => uni.navigateTo({ url: ROUTE.qaList() }),
  },
  {
    label: '二手市场',
    icon: '市',
    desc: '闲置好物流转',
    bg: '#e8f7ef',
    color: '#00b42a',
    go: () => uni.switchTab({ url: TAB.products }),
  },
  {
    label: '服务圈',
    icon: '服',
    desc: '家政与周边商家',
    bg: '#f4ebff',
    color: '#722ed1',
    go: () => uni.switchTab({ url: TAB.services }),
  },
]

onLoad(loadAnnouncements)

async function loadAnnouncements() {
  loading.value = true
  try {
    const res = await getAnnouncements({ page_size: 5 })
    announcements.value = res.data?.results || []
  } catch {
    /* 请求层已提示 */
  } finally {
    loading.value = false
  }
}

/** 点击展开/收起公告正文 */
function toggleNotice(item) {
  expandedId.value = expandedId.value === item.id ? null : item.id
}
</script>

<style scoped>
.hero {
  background: linear-gradient(135deg, #e8622c, #f38b52);
  border-radius: 20rpx;
  padding: 48rpx 40rpx;
  color: #fff;
  margin-bottom: 24rpx;
}
.hero-title {
  font-size: 44rpx;
  font-weight: 700;
}
.hero-sub {
  opacity: 0.9;
  margin-top: 10rpx;
  font-size: 26rpx;
}
.grid {
  display: flex;
  flex-wrap: wrap;
  gap: 20rpx;
  justify-content: space-between;
  margin-bottom: 8rpx;
}
.grid-item {
  width: calc(50% - 10rpx);
  box-sizing: border-box;
  background: #fff;
  border-radius: 16rpx;
  padding: 32rpx;
}
.grid-icon {
  width: 76rpx;
  height: 76rpx;
  border-radius: 20rpx;
  font-size: 36rpx;
  font-weight: 700;
  text-align: center;
  line-height: 76rpx;
  margin-bottom: 20rpx;
}
.grid-label {
  font-size: 32rpx;
  font-weight: 700;
}
.grid-desc {
  color: var(--oc-text-secondary);
  font-size: 24rpx;
  margin-top: 6rpx;
}
.notice-item {
  display: flex;
  gap: 20rpx;
  padding: 18rpx 0;
  border-bottom: 1rpx solid var(--oc-border);
}
.notice-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}
.notice-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: var(--oc-primary);
  margin-top: 14rpx;
  flex-shrink: 0;
}
.notice-title {
  font-size: 28rpx;
  font-weight: 600;
}
.notice-content {
  color: var(--oc-text-secondary);
  font-size: 26rpx;
  margin-top: 8rpx;
  white-space: pre-wrap;
}
.notice-time {
  color: var(--oc-text-secondary);
  font-size: 22rpx;
  margin-top: 6rpx;
}
</style>
