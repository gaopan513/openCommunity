<script setup>
/**
 * 首页 — 邻里通讯封面
 *
 * 顶部为编辑式英雄区（报头封面感），下方为五大板块入口卡片。
 */
import { useRouter } from 'vue-router'

const router = useRouter()

const boards = [
  { name: '自由发言', icon: '💬', desc: '邻里闲聊、生活分享、互助求助', path: '/discussion' },
  { name: '经验问答', icon: '❓', desc: '装修、育儿、养宠等生活经验交流', path: '/qa' },
  { name: '二手市场', icon: '🛒', desc: '闲置物品交易，邻里互惠互利', path: '/secondhand' },
  { name: '周边商家', icon: '🏪', desc: '小区周边商家信息、优惠活动', path: '/merchants' },
  { name: '家政服务', icon: '🧹', desc: '保洁、维修、搬家等生活服务预约', path: '/housekeeping' },
]

const stats = [
  { num: '5', label: '生活板块' },
  { num: '24h', label: '邻里在线' },
  { num: '∞', label: '善意流转' },
]

function go(path) {
  router.push(path)
}
</script>

<template>
  <div class="oc-page home-page">
    <!-- 英雄封面 -->
    <section class="oc-hero">
      <div class="oc-hero-content">
        <span class="oc-hero-kicker">Neighborhood Gazette · 邻里通讯</span>
        <h1 class="oc-hero-title">
          把小区变成<br />
          一份<em>会说话</em>的通讯
        </h1>
        <p class="oc-hero-sub">
          这里没有喧嚣的流量，只有楼栋间的烟火气。发帖、提问、淘闲置、找服务——
          以小区为中心，让每一次邻里互动都像翻开一份本地的、温暖的、属于你自己的小报。
        </p>
        <div class="oc-hero-stats">
          <div v-for="s in stats" :key="s.label" class="oc-hero-stat">
            <div class="oc-hero-stat-num">{{ s.num }}</div>
            <div class="oc-hero-stat-label">{{ s.label }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 板块入口 -->
    <div class="home-section-head">
      <span class="oc-kicker">Boards · 板块入口</span>
      <h2>今日，从哪个板块开始？</h2>
    </div>

    <div class="oc-board-grid">
      <div
        v-for="board in boards"
        :key="board.path"
        class="oc-board"
        @click="go(board.path)"
      >
        <div class="oc-board-icon">{{ board.icon }}</div>
        <h3 class="oc-board-name">{{ board.name }}</h3>
        <p class="oc-board-desc">{{ board.desc }}</p>
        <span class="oc-board-arrow">→</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-page {
  padding-top: 8px;
}

.home-section-head {
  margin: 8px 0 20px;
}

.home-section-head .oc-kicker {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--oc-primary);
  margin-bottom: 6px;
}

.home-section-head h2 {
  font-family: var(--oc-font-display);
  font-size: 24px;
  font-weight: 700;
  color: var(--oc-ink);
  margin: 0;
  letter-spacing: -0.01em;
}

@media (max-width: 768px) {
  .oc-hero {
    padding: 32px 24px;
  }
  .oc-hero-title {
    font-size: 32px;
  }
}
</style>
