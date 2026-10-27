/**
 * 分页列表 composable（uni-app 页面级）
 *
 * 收敛社区/问答/二手等列表页的通用逻辑：
 * - 首次进入加载 + 触底加载更多 + 下拉刷新（依赖 pages.json 启用 enablePullDownRefresh）
 * - 请求序号守卫：筛选/搜索切换时作废在途响应，避免旧请求结果串台
 * - 脏标记：子页面发布/删除成功后 uni.$emit(EVENTS.LIST_CHANGED)，返回本页时自动重载
 *
 * @param {(pageNo: number) => Promise<{results: Array, total: number}>} fetchPage
 *        取指定页数据（请求层已统一提示错误），返回分页信封
 * @param {Object} [options]
 * @param {Ref<boolean>} [options.active] 当前 tab 是否激活。
 *        uni-app 的组合式生命周期（onShow/onReachBottom/onPullDownRefresh）只在页面根组件
 *        setup 生效，无法下沉到子组件。因此单页承载多列表（如「服务圈」的家政/商家双 tab）
 *        时，把各列表状态收敛到页面 setup 内，用 active 控制：仅激活 tab 响应触底加载；
 *        active 由 false->true 时自动 refresh，非激活列表不自动刷新。
 * @param {boolean} [options.listenChanged=true] 是否监听全局 LIST_CHANGED 事件标记脏。
 *        单页面同时挂多个列表实例时，只有激活实例应消费全局广播，避免重复刷新。
 * @returns {{items, loading, finished, loadError, loadFirst, loadMore, refresh}}
 *          loadError：触底加载失败标记，页面可展示"点击重试"，再次调用 loadMore 即重试
 *          refresh：手动刷新（等价 loadFirst），多 tab 切回激活时自动调用
 */
import { ref, watch } from 'vue'
import { onShow, onPullDownRefresh, onReachBottom, onUnload } from '@dcloudio/uni-app'
import { EVENTS } from '@/constants'

export function usePagedList(fetchPage, { active = null, listenChanged = true } = {}) {
  const items = ref([])
  const loading = ref(false)
  const finished = ref(false)
  // 触底加载失败标记：供页面展示"加载失败，点击重试"
  const loadError = ref(false)
  const page = ref(1)
  const total = ref(0)

  // 上次是否已加载过（active 模式下，true->false 再 false->true 需要恢复）
  let loadedOnce = false
  // 首次进入视为脏数据；单列表模式 onShow 时统一加载
  let dirty = true
  // 请求序号：新请求发起后，在途旧响应落地前比对 seq，不一致则丢弃
  let seq = 0

  // 是否激活（未传 active 时永远激活，保持与旧行为完全一致）
  const isActive = () => (active ? active.value : true)

  async function loadFirst() {
    const cur = ++seq
    loading.value = true
    try {
      const data = await fetchPage(1)
      if (cur !== seq) return
      items.value = data.results || []
      total.value = data.total || items.value.length
      page.value = 1
      finished.value = items.value.length >= total.value
      loadError.value = false
      loadedOnce = true
    } catch {
      /* 错误提示由请求层统一弹出 */
    } finally {
      if (cur === seq) loading.value = false
    }
  }

  async function loadMore() {
    if (loading.value || finished.value) return
    const cur = ++seq
    loading.value = true
    try {
      const data = await fetchPage(page.value + 1)
      if (cur !== seq) return
      const results = data.results || []
      items.value.push(...results)
      page.value += 1
      total.value = data.total || total.value
      finished.value = items.value.length >= total.value
      loadError.value = false
    } catch {
      // 请求层已 toast；此处置标记供页面展示重试入口
      if (cur === seq) loadError.value = true
    } finally {
      if (cur === seq) loading.value = false
    }
  }

  // 子页面发布/删除后 uni.$emit(EVENTS.LIST_CHANGED) 标记脏，返回本页时刷新
  const onChanged = () => {
    dirty = true
  }
  if (listenChanged) uni.$on(EVENTS.LIST_CHANGED, onChanged)

  onShow(() => {
    // 单列表模式（无 active）：统一用脏标记触发
    if (!isActive() || !dirty) return
    dirty = false
    loadFirst()
  })
  onPullDownRefresh(async () => {
    if (!isActive()) return
    dirty = false
    await loadFirst()
    uni.stopPullDownRefresh()
  })
  onReachBottom(() => {
    if (isActive() && !loading.value && !finished.value) loadMore()
  })
  onUnload(() => {
    if (listenChanged) uni.$off(EVENTS.LIST_CHANGED, onChanged)
  })

  // 双 tab 模式：切回激活时若已完成过一次加载，则依赖脏标记决定是否刷新；
  // 首次激活（从未加载过）直接加载，避免依赖 onShow 的 active 竞态。
  if (active) {
    watch(active, (v) => {
      if (!v) return
      if (!loadedOnce || dirty) {
        dirty = false
        loadFirst()
      }
    })
  }

  // 手动刷新：双 tab 页在 tab 首次激活时调用；单列表页无需显式调用
  function refresh() {
    dirty = false
    loadFirst()
  }

  return { items, loading, finished, loadError, loadFirst, loadMore, refresh }
}
