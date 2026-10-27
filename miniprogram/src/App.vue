<script>
import { useUserStore } from '@/stores/user'
import { track, reportError } from '@/utils/analytics'

export default {
  onLaunch() {
    // 冷启动静默微信登录：已有 token 则交给请求层 401 刷新兜底；
    // 登录失败（如开发者工具未配置 AppID）静默保持游客态，仅记录日志
    const userStore = useUserStore()
    if (!userStore.accessToken) {
      userStore
        .loginByWechat()
        .then(() => track('wechat_login'))
        .catch((e) => reportError(e, 'wechat-login 失败'))
    }
  },
  // 全局未捕获异常兜底：本地 console + 实时日志双通道，便于线上问题排查
  onError(err) {
    console.error('[app onError]', err)
    reportError(err, '全局异常')
  },
}
</script>

<style>
/* ===== 全局主题与公共样式（对齐 frontend/src/styles/community.css 暖橙主色）===== */
page {
  --oc-primary: #e8622c;
  --oc-primary-light: #fff3ec;
  --oc-bg: #f6f7f9;
  --oc-card: #ffffff;
  --oc-text: #1f2329;
  --oc-text-secondary: #86909c;
  --oc-border: #f0f0f0;
  --oc-danger: #f53f3f;
  --oc-success: #00b42a;
  --oc-warning: #ff7d00;
  background-color: var(--oc-bg);
  color: var(--oc-text);
  font-size: 28rpx;
}

/* 页面容器 */
.oc-page {
  padding: 24rpx;
  padding-bottom: 140rpx;
}

/* 卡片 */
.oc-card {
  background: var(--oc-card);
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
}

/* 主按钮 */
.oc-btn {
  background: var(--oc-primary);
  color: #fff;
  border-radius: 44rpx;
  font-size: 30rpx;
  line-height: 88rpx;
  text-align: center;
}
.oc-btn--ghost {
  background: var(--oc-primary-light);
  color: var(--oc-primary);
}
.oc-btn--plain {
  background: #fff;
  color: var(--oc-text-secondary);
  border: 1rpx solid var(--oc-border);
}
.oc-btn--disabled {
  opacity: 0.5;
}

/* 输入框 */
.oc-input {
  background: #f7f8fa;
  border-radius: 12rpx;
  padding: 20rpx 24rpx;
  font-size: 28rpx;
  width: auto;
}

/* 筛选圆片 */
.oc-chip {
  display: inline-block;
  padding: 10rpx 28rpx;
  border-radius: 30rpx;
  background: #fff;
  color: var(--oc-text-secondary);
  font-size: 26rpx;
  margin-right: 16rpx;
  border: 1rpx solid var(--oc-border);
}
.oc-chip--active {
  background: var(--oc-primary-light);
  color: var(--oc-primary);
  border-color: var(--oc-primary);
  font-weight: 600;
}

/* 标签 */
.oc-tag {
  display: inline-block;
  padding: 4rpx 16rpx;
  border-radius: 8rpx;
  font-size: 22rpx;
}

/* 头像 */
.oc-avatar {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: #ececec;
  flex-shrink: 0;
}

/* 浮动发布按钮 */
.oc-fab {
  position: fixed;
  right: 40rpx;
  bottom: 160rpx;
  width: 108rpx;
  height: 108rpx;
  border-radius: 50%;
  background: var(--oc-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 52rpx;
  box-shadow: 0 8rpx 24rpx rgba(232, 98, 44, 0.4);
  z-index: 99;
}

/* 空态 / 加载提示 */
.oc-empty {
  text-align: center;
  color: var(--oc-text-secondary);
  padding: 120rpx 0;
  font-size: 26rpx;
}
.oc-loadmore {
  text-align: center;
  color: var(--oc-text-secondary);
  padding: 24rpx 0;
  font-size: 24rpx;
}
/* 触底加载失败的重试入口（列表页点击重试） */
.oc-loadmore--error {
  color: var(--oc-primary);
}

/* 区块标题 */
.oc-section-title {
  font-size: 32rpx;
  font-weight: 700;
  margin: 8rpx 0 20rpx;
}

/* 底部安全区留白（评论输入条等 fixed 元素） */
.oc-safe-bottom {
  padding-bottom: constant(safe-area-inset-bottom);
  padding-bottom: env(safe-area-inset-bottom);
}
</style>
