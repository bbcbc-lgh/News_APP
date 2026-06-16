<script setup lang="ts">
import { onMounted, onUnmounted, watch, ref, computed } from 'vue'
import { useNewsStore } from '@/stores/newsStore'
import { newsApi, type NewsItem, type TimeRange } from '@/api/news'
import { searchHistoryApi, type SearchHistoryItem } from '@/api/searchHistory'
import { tagApi, type TopicTag } from '@/api/topicTag'
import { favoriteApi } from '@/api/favorite'
import { queueApi } from '@/api/queue'

const news = useNewsStore()
const refreshing = ref(false)
const refreshDone = ref(false)
const sentinel = ref<HTMLElement | null>(null)
let observer: IntersectionObserver | null = null

// 搜索状态
const searchQuery = ref('')
const searchActive = ref(false)
const searchResults = ref<NewsItem[]>([])
const searchLoading = ref(false)
const searchPage = ref(1)
const searchHasMore = ref(false)
const searchTotal = ref(0)
let searchTimer: ReturnType<typeof setTimeout> | null = null

// 高级搜索筛选
const SOURCE_FILTERS = [
  { key: 'hackernews', label: 'HN' },
  { key: 'openai',     label: 'OpenAI' },
  { key: 'google_ai',  label: 'Google' },
  { key: 'mit',        label: 'MIT' },
] as const
const TIME_FILTERS: { key: TimeRange; label: string }[] = [
  { key: 'all',   label: '全部' },
  { key: 'day',   label: '今天' },
  { key: 'week',  label: '本周' },
  { key: 'month', label: '本月' },
  { key: 'year',  label: '今年' },
]
const selectedSources = ref<string[]>([])
const timeRange = ref<TimeRange>('all')
const selectedTags = ref<string[]>([])
const allTags = ref<TopicTag[]>([])

function toggleSource(key: string) {
  const i = selectedSources.value.indexOf(key)
  if (i >= 0) selectedSources.value.splice(i, 1)
  else selectedSources.value.push(key)
  doSearch(true)
}
function setTimeRange(t: TimeRange) {
  if (timeRange.value === t) return
  timeRange.value = t
  doSearch(true)
}
function toggleTag(slug: string) {
  const i = selectedTags.value.indexOf(slug)
  if (i >= 0) selectedTags.value.splice(i, 1)
  else selectedTags.value.push(slug)
  doSearch(true)
}

// 搜索历史
const historyList = ref<SearchHistoryItem[]>([])

async function doSearch(reset = false) {
  const q = searchQuery.value.trim()
  if (!q) {
    exitSearch()
    return
  }
  if (reset) {
    searchResults.value = []
    searchPage.value = 1
    searchHasMore.value = false
  }
  searchLoading.value = true
  try {
    const res = await newsApi.search(
      q, searchPage.value, 10,
      selectedSources.value, timeRange.value, selectedTags.value,
    )
    searchResults.value = reset ? res.list : [...searchResults.value, ...res.list]
    searchTotal.value = res.total
    searchHasMore.value = res.hasMore
    searchPage.value++
  } finally {
    searchLoading.value = false
  }
}

// 搜索建议
const suggestions = ref<string[]>([])
let suggestTimer: ReturnType<typeof setTimeout> | null = null

async function fetchSuggestions(q: string) {
  if (!q.trim()) { suggestions.value = []; return }
  try {
    suggestions.value = await searchHistoryApi.suggestions(q.trim())
  } catch { suggestions.value = [] }
}

function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  if (suggestTimer) clearTimeout(suggestTimer)
  const q = searchQuery.value.trim()
  if (!q) { exitSearch(); return }
  searchActive.value = true
  suggestTimer = setTimeout(() => fetchSuggestions(q), 200)
  searchTimer = setTimeout(() => doSearch(true), 400)
}

function commitSearch() {
  const q = searchQuery.value.trim()
  if (!q) return
  suggestions.value = []
  searchHistoryApi.add(q).then(loadHistory).catch(() => {})
}

function searchFromHistory(q: string) {
  searchQuery.value = q
  searchActive.value = true
  doSearch(true)
  searchHistoryApi.add(q).then(loadHistory).catch(() => {})
}

async function loadHistory() {
  try {
    const res = await searchHistoryApi.list(15)
    historyList.value = res.list
  } catch { /* 静默 */ }
}

async function removeHistory(e: MouseEvent, id: number) {
  e.stopPropagation()
  try {
    await searchHistoryApi.remove(id)
    historyList.value = historyList.value.filter(h => h.id !== id)
  } catch { /* ignore */ }
}

async function clearHistory() {
  if (!confirm('确定清空所有搜索历史？')) return
  try {
    await searchHistoryApi.clear()
    historyList.value = []
  } catch { /* ignore */ }
}

function selectSuggestion(word: string) {
  searchQuery.value = word
  suggestions.value = []
  doSearch(true)
  searchHistoryApi.add(word).then(loadHistory).catch(() => {})
}

function exitSearch() {
  searchQuery.value = ''
  searchResults.value = []
  searchPage.value = 1
  searchHasMore.value = false
  suggestions.value = []
}

// 推荐
const recommendList = ref<import('@/api/news').NewsItem[]>([])
const recommendLoading = ref(false)

async function loadRecommend() {
  recommendLoading.value = true
  try { recommendList.value = await newsApi.recommend(20) }
  catch { recommendList.value = [] }
  finally { recommendLoading.value = false }
}

function selectSource(id: string) {
  if (id === 'recommend') {
    news.setCategory('recommend')
    if (!recommendList.value.length) loadRecommend()
  } else {
    news.setCategory(id)
  }
}

const displayList = computed(() =>
  searchActive.value ? searchResults.value
  : news.activeSource === 'recommend' ? recommendList.value
  : news.newsList
)

async function handleRefresh() {
  if (refreshing.value) return
  refreshing.value = true
  refreshDone.value = false
  try {
    await newsApi.refresh()
    refreshDone.value = true
    setTimeout(() => { refreshDone.value = false }, 3000)
    setTimeout(() => news.loadNews(news.activeSource, true), 8000)
  } catch {
    // 静默失败
  } finally {
    refreshing.value = false
  }
}

const SOURCE_META: Record<string, { label: string; color: string; key: string; bg: string }> = {
  'hackernews': { label: 'HN',        color: 'var(--hn)',     key: 'hn',     bg: 'rgba(224,93,0,0.08)' },
  'openai':     { label: 'OpenAI',    color: 'var(--openai)', key: 'openai', bg: 'rgba(13,138,106,0.08)' },
  'google_ai':  { label: 'Google AI', color: 'var(--google)', key: 'google', bg: 'rgba(26,115,232,0.08)' },
  'mit':        { label: 'MIT',       color: 'var(--mit-fg)', key: 'mit',    bg: 'rgba(155,28,46,0.08)' },
}

function sourceMeta(source: string) {
  return SOURCE_META[source] || { label: '?', color: 'var(--brand)', key: 'default', bg: 'var(--bg-elevated)' }
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 60) return m <= 1 ? '刚刚' : `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  const d = Math.floor(h / 24)
  if (d < 30) return `${d}d ago`
  return new Date(dateStr).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function formatViews(v: number): string {
  return v >= 10000 ? `${(v / 10000).toFixed(1)}万` : String(v)
}

function displayTitle(item: NewsItem): string {
  return item.title_zh || item.title
}

function posterTopic(item: NewsItem): string {
  const text = `${item.title} ${item.title_zh || ''}`.toLowerCase()
  if (/open source|oss|开源/.test(text)) return 'OPEN'
  if (/model|gpt|gemini|claude|llm|模型|大模型/.test(text)) return 'MODEL'
  if (/funding|raises|seed|series|融资|募资|投资/.test(text)) return 'FUND'
  if (/law|legal|policy|regulation|investigation|lawsuit|监管|政策|调查|诉讼|出口管制/.test(text)) return 'POLICY'
  if (/research|paper|study|benchmark|研究|论文|基准/.test(text)) return 'RESEARCH'
  if (/show hn|launch|release|发布|推出/.test(text)) return 'LAUNCH'
  return 'AI NOTE'
}

function setupObserver() {
  if (observer) observer.disconnect()
  observer = new IntersectionObserver((entries) => {
    if (!entries[0].isIntersecting) return
    if (searchActive.value) {
      if (!searchLoading.value && searchHasMore.value) doSearch()
    }
  }, { rootMargin: '200px' })
  if (sentinel.value) observer.observe(sentinel.value)
}

onMounted(async () => {
  await news.loadCategories()
  if (news.newsList.length === 0) news.loadNews(news.activeSource, true)
  setupObserver()
  loadHistory()
  tagApi.listAll().then(list => { allTags.value = list }).catch(() => {})
})

onUnmounted(() => { observer?.disconnect() })

watch(() => news.activeSource, (src) => {
  if (src !== 'recommend') news.loadNews(src, true)
})
watch(sentinel, () => setupObserver())

// 长按菜单
interface ContextMenu {
  item: NewsItem
  x: number
  y: number
  isFav: boolean
  isInQueue: boolean
}
const contextMenu = ref<ContextMenu | null>(null)
let longPressTimer: ReturnType<typeof setTimeout> | null = null
let longPressItem: NewsItem | null = null

function onCardTouchStart(e: TouchEvent, item: NewsItem) {
  longPressItem = item
  const touch = e.changedTouches[0]
  longPressTimer = setTimeout(async () => {
    const [favRes, queueRes] = await Promise.allSettled([
      favoriteApi.check(item.id),
      queueApi.check(item.id),
    ])
    contextMenu.value = {
      item,
      x: Math.min(touch.clientX, window.innerWidth - 180),
      y: Math.min(touch.clientY, window.innerHeight - 120),
      isFav: favRes.status === 'fulfilled' ? favRes.value.isFavorite : false,
      isInQueue: queueRes.status === 'fulfilled' ? queueRes.value.inQueue : false,
    }
    // 取消默认点击跳转（通过事件标记）
    e.preventDefault()
  }, 500)
}

function onCardTouchEnd() {
  if (longPressTimer) { clearTimeout(longPressTimer); longPressTimer = null }
}

function closeMenu() {
  contextMenu.value = null
}

async function menuFav() {
  if (!contextMenu.value) return
  const { item, isFav } = contextMenu.value
  if (isFav) await favoriteApi.remove(item.id)
  else await favoriteApi.add(item.id)
  contextMenu.value = null
}

async function menuQueue() {
  if (!contextMenu.value) return
  const { item, isInQueue } = contextMenu.value
  if (isInQueue) await queueApi.remove(item.id)
  else await queueApi.add(item.id)
  contextMenu.value = null
}
</script>

<template>
  <div class="news-page">
    <header class="top-bar">
      <div class="logo-wrap">
        <div class="logo-text">
          <span class="logo-zh">Nexus</span>
          <span class="logo-en">DAILY DIGEST</span>
        </div>
      </div>
      <div class="header-right">
        <button class="refresh-btn" :class="{ spinning: refreshing, done: refreshDone }" @click="handleRefresh" :title="refreshDone ? '采集中，稍后自动更新' : '获取最新资讯'">
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
            <path d="M13 7.5A5.5 5.5 0 1 1 7.5 2a5.5 5.5 0 0 1 3.89 1.61L13 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M13 2v3h-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
        <span class="live-dot"></span>
        <span class="live-label">LIVE</span>
      </div>
    </header>

    <div class="source-strip" :class="{ hidden: searchActive }">
      <div class="source-chips">
        <button
          v-for="cat in news.categories"
          :key="cat.id"
          :class="['chip', { active: news.activeSource === cat.id }]"
          @click="selectSource(cat.id)"
        >{{ cat.name }}</button>
        <button :class="['chip', 'chip--recommend', { active: news.activeSource === 'recommend' }]"
          @click="selectSource('recommend')">
          <svg width="11" height="11" viewBox="0 0 12 12" fill="none" style="margin-right:3px;vertical-align:-1px">
            <path d="M6 1l1.3 2.6L10 4.1l-2 2 .5 2.9L6 7.6l-2.5 1.4.5-2.9-2-2 2.7-.5z" fill="currentColor"/>
          </svg>
          推荐
        </button>
      </div>
    </div>

    <div class="search-bar" :style="{ top: searchActive ? '54px' : 'calc(54px + 44px)' }">
      <div class="search-inner">
        <svg class="search-icon" width="14" height="14" viewBox="0 0 16 16" fill="none">
          <circle cx="6.5" cy="6.5" r="5" stroke="currentColor" stroke-width="1.5"/>
          <path d="M10.5 10.5L14 14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <input
          v-model="searchQuery"
          class="search-input"
          placeholder="搜索文章…"
          @input="onSearchInput"
          @keydown.enter="commitSearch"
          @keydown.escape="exitSearch"
        />
        <button v-if="searchActive" class="search-clear" @click="exitSearch">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M2 2L10 10M10 2L2 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
      <div v-if="suggestions.length" class="suggestions-drop">
        <button
          v-for="s in suggestions" :key="s"
          class="suggestion-item"
          @mousedown.prevent="selectSuggestion(s)"
        >{{ s }}</button>
      </div>
      <div v-if="searchActive && searchTotal > 0" class="search-meta">
        <span class="search-count">{{ searchTotal }} 条结果</span>
      </div>
      <div v-if="searchActive" class="filter-bar">
        <div class="filter-row">
          <span class="filter-label">来源</span>
          <div class="filter-chips">
            <button v-for="s in SOURCE_FILTERS" :key="s.key"
              :class="['fchip', { active: selectedSources.includes(s.key) }]"
              @click="toggleSource(s.key)">{{ s.label }}</button>
          </div>
        </div>
        <div class="filter-row">
          <span class="filter-label">时间</span>
          <div class="filter-chips">
            <button v-for="t in TIME_FILTERS" :key="t.key"
              :class="['fchip', { active: timeRange === t.key }]"
              @click="setTimeRange(t.key)">{{ t.label }}</button>
          </div>
        </div>
        <div v-if="allTags.length" class="filter-row">
          <span class="filter-label">标签</span>
          <div class="filter-chips filter-chips--wrap">
            <button v-for="tag in allTags" :key="tag.slug"
              :class="['fchip', 'fchip--tag', { active: selectedTags.includes(tag.slug) }]"
              :style="selectedTags.includes(tag.slug) ? { background: tag.color, borderColor: tag.color, color: '#fff' } : { borderColor: tag.color, color: tag.color }"
              @click="toggleTag(tag.slug)">{{ tag.name }}</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="!searchActive && historyList.length" class="history-bar"
      :style="{ top: 'calc(54px + 44px + 56px)' }">
      <div class="history-head">
        <span class="history-label">RECENT</span>
        <button class="history-clear" @click="clearHistory">清空</button>
      </div>
      <div class="history-chips">
        <button v-for="h in historyList" :key="h.id" class="history-chip"
          @click="searchFromHistory(h.query)">
          <svg class="hc-icon" width="11" height="11" viewBox="0 0 16 16" fill="none">
            <circle cx="6.5" cy="6.5" r="5" stroke="currentColor" stroke-width="1.5"/>
            <path d="M10.5 10.5L14 14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span class="hc-text">{{ h.query }}</span>
          <span class="hc-remove" @click="removeHistory($event, h.id)">
            <svg width="9" height="9" viewBox="0 0 12 12" fill="none">
              <path d="M2 2L10 10M10 2L2 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </span>
        </button>
      </div>
    </div>

    <div class="list-wrap">
      <div v-if="searchActive && searchLoading && searchResults.length === 0" class="skeleton-list">
        <div v-for="i in 3" :key="i" class="skeleton-card">
          <div class="sk-index"></div>
          <div class="sk-body">
            <div class="sk-source"></div>
            <div class="sk-line sk-title"></div>
            <div class="sk-line sk-title sk-short"></div>
            <div class="sk-line sk-meta"></div>
          </div>
          <div class="sk-img"></div>
        </div>
      </div>

      <div v-else-if="searchActive && !searchLoading && searchResults.length === 0" class="no-result">
        <span class="no-result-text">未找到 "{{ searchQuery }}" 相关内容</span>
      </div>

      <div v-if="!searchActive && news.activeSource !== 'recommend' && news.newsList.length === 0 && news.loading" class="skeleton-list">
        <div v-for="i in 5" :key="i" class="skeleton-card">
          <div class="sk-index"></div>
          <div class="sk-body">
            <div class="sk-source"></div>
            <div class="sk-line sk-title"></div>
            <div class="sk-line sk-title sk-short"></div>
            <div class="sk-line sk-meta"></div>
          </div>
          <div class="sk-img"></div>
        </div>
      </div>

      <div v-if="!searchActive && news.activeSource === 'recommend' && recommendLoading" class="state-wrap">
        <div class="spinner"></div>
      </div>
      <div v-else-if="!searchActive && news.activeSource === 'recommend' && !recommendLoading && recommendList.length === 0" class="no-result">
        <span class="no-result-text">暂无推荐，多阅读几篇后再试</span>
      </div>

      <template v-if="displayList.length > 0">
        <RouterLink
          v-for="(item, idx) in displayList"
          :key="item.id"
          class="news-card"
          :to="`/news/detail/${item.id}`"
          @touchstart.passive="onCardTouchStart($event, item)"
          @touchend="onCardTouchEnd"
          @touchmove="onCardTouchEnd"
        >
          <div class="card-index">{{ String(idx + 1).padStart(2, '0') }}</div>
          <div class="card-body">
            <div class="card-source" :style="{ color: sourceMeta(item.source_platform || '').color }">
              {{ sourceMeta(item.source_platform || '').label }}
            </div>
            <h3 class="card-title">{{ displayTitle(item) }}</h3>
            <div class="card-meta">
              <span>{{ item.author || '未知' }}</span>
              <span class="meta-dot">·</span>
              <span>{{ formatViews(item.views) }}</span>
              <span class="meta-dot">·</span>
              <span>{{ timeAgo(item.publish_time) }}</span>
            </div>
          </div>
          <div class="card-right">
            <img v-if="item.image" :src="item.image" class="card-img" loading="lazy" />
            <div v-else class="card-img card-img--poster" :style="{ '--poster-color': sourceMeta(item.source_platform || '').color }">
              <span class="thumb-topic">{{ posterTopic(item) }}</span>
              <span class="thumb-source">{{ sourceMeta(item.source_platform || '').label }}</span>
            </div>
          </div>
        </RouterLink>
      </template>

      <div v-if="(searchActive ? searchLoading : news.loading) && displayList.length" class="load-indicator">
        <span class="load-dot" v-for="i in 3" :key="i"></span>
      </div>
      <div v-if="!searchActive && news.activeSource !== 'recommend' && news.hasMore && news.newsList.length && !news.loading" class="load-more-wrap">
        <button class="load-more-btn" @click="news.loadNews(news.activeSource)">加载更多</button>
      </div>
      <div v-if="!searchActive && news.activeSource !== 'recommend' && !news.hasMore && news.newsList.length" class="no-more">
        <span class="no-more-line"></span>
        <span class="no-more-text">END OF FEED</span>
        <span class="no-more-line"></span>
      </div>
      <div v-if="searchActive && !searchHasMore && searchResults.length" class="no-more">
        <span class="no-more-line"></span>
        <span class="no-more-text">END OF RESULTS</span>
        <span class="no-more-line"></span>
      </div>
      <div ref="sentinel" class="sentinel"></div>
    </div>

    <!-- 长按上下文菜单 -->
    <Teleport to="body">
      <div v-if="contextMenu" class="ctx-overlay" @click="closeMenu">
        <div class="ctx-menu" :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }" @click.stop>
          <button class="ctx-item" @click="menuFav">
            <svg width="15" height="15" viewBox="0 0 22 22" fill="none">
              <path d="M11 19L3.5 11.5C2 10 2 7.5 3.5 6C5 4.5 7.5 4.5 9 6L11 8L13 6C14.5 4.5 17 4.5 18.5 6C20 7.5 20 10 18.5 11.5L11 19Z"
                :fill="contextMenu.isFav ? 'var(--brand)' : 'none'"
                :stroke="contextMenu.isFav ? 'var(--brand)' : 'currentColor'"
                stroke-width="1.8" stroke-linejoin="round"/>
            </svg>
            <span>{{ contextMenu.isFav ? '取消收藏' : '收藏' }}</span>
          </button>
          <button class="ctx-item" @click="menuQueue">
            <svg width="15" height="15" viewBox="0 0 22 22" fill="none">
              <path d="M5 4h9l4 4v10a1 1 0 01-1 1H5a1 1 0 01-1-1V5a1 1 0 011-1z"
                :stroke="contextMenu.isInQueue ? 'var(--brand)' : 'currentColor'" stroke-width="1.6" stroke-linejoin="round"/>
              <path d="M14 4v4h4" :stroke="contextMenu.isInQueue ? 'var(--brand)' : 'currentColor'" stroke-width="1.6" stroke-linejoin="round"/>
              <path d="M8 13h6M8 16h4" :stroke="contextMenu.isInQueue ? 'var(--brand)' : 'currentColor'" stroke-width="1.6" stroke-linecap="round"/>
            </svg>
            <span>{{ contextMenu.isInQueue ? '移出队列' : '稍后阅读' }}</span>
          </button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.news-page { display: flex; flex-direction: column; min-height: 100vh; background: var(--bg); width: 100%; }

.top-bar {
  height: 54px; background: var(--bg-card);
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 16px; border-bottom: 1px solid var(--border);
  position: sticky; top: 0; z-index: 10; flex-shrink: 0;
  box-shadow: var(--shadow-sm);
}
.logo-wrap { display: flex; align-items: center; gap: 10px; }
.logo-text { display: flex; flex-direction: column; gap: 1px; }
.logo-zh {
  font-family: 'Libre Baskerville', 'Noto Serif SC', serif;
  font-size: 16px; font-weight: 700; color: var(--text-primary);
  letter-spacing: 1px; line-height: 1;
}
.logo-en {
  font-family: 'JetBrains Mono', monospace; font-size: 8px;
  color: var(--text-muted); letter-spacing: 2px; line-height: 1;
}
.header-right { display: flex; align-items: center; gap: 6px; }
.refresh-btn {
  display: flex; align-items: center; justify-content: center;
  width: 28px; height: 28px; border-radius: 50%;
  color: var(--text-muted); transition: color 0.2s, background 0.2s;
}
.refresh-btn:hover { color: var(--brand); background: var(--brand-dim); }
.refresh-btn.spinning svg { animation: spin-once 0.8s linear infinite; }
.refresh-btn.done { color: var(--openai); }
@keyframes spin-once { to { transform: rotate(360deg); } }
.live-dot {
  width: 7px; height: 7px; background: #1A8C4E;
  border-radius: 50%; animation: pulse 2s infinite;
}
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(0.8)} }
.live-label {
  font-family: 'JetBrains Mono', monospace; font-size: 10px;
  font-weight: 500; color: #1A8C4E; letter-spacing: 2px;
}

.source-strip {
  background: var(--bg-card); border-bottom: 1px solid var(--border);
  position: sticky; top: 54px; z-index: 9; flex-shrink: 0;
  overflow-x: auto; scrollbar-width: none;
  transition: max-height 0.2s, opacity 0.2s;
}
.source-strip.hidden { max-height: 0; opacity: 0; overflow: hidden; border-bottom: none; }
.source-strip::after {
  content: '';
  position: sticky;
  right: 0;
  top: 0;
  bottom: 0;
  float: right;
  width: 28px;
  height: 40px;
  margin-top: -40px;
  background: linear-gradient(90deg, color-mix(in srgb, var(--bg-card) 0%, transparent), var(--bg-card));
  pointer-events: none;
}
.source-strip::-webkit-scrollbar { display: none; }
.source-chips { display: flex; padding: 8px 12px; gap: 6px; width: max-content; min-width: 100%; }

.search-bar {
  background: var(--bg-card); border-bottom: 1px solid var(--border);
  position: sticky; z-index: 8; flex-shrink: 0;
  padding: 8px 12px; transition: top 0.2s;
}
.search-inner {
  display: flex; align-items: center; gap: 8px;
  background: var(--bg-elevated); border: 1px solid var(--border);
  border-radius: 20px; padding: 7px 12px;
  transition: border-color 0.18s, box-shadow 0.18s;
}
.search-inner:focus-within {
  border-color: var(--brand); box-shadow: 0 0 0 3px var(--brand-dim);
}
.search-icon { color: var(--text-muted); flex-shrink: 0; }
.search-input {
  flex: 1; background: transparent; border: none;
  font-family: 'Noto Sans SC', sans-serif; font-size: 13px;
  color: var(--text-primary); min-width: 0;
}
.search-input::placeholder { color: var(--text-muted); }
.search-clear {
  color: var(--text-muted); display: flex; align-items: center;
  padding: 2px; border-radius: 50%; transition: color 0.15s;
}
.search-clear:hover { color: var(--text-primary); }
.suggestions-drop {
  margin-top: 4px; border: 1px solid var(--border);
  border-radius: var(--radius); background: var(--bg-card);
  overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,.08);
}
.suggestion-item {
  display: block; width: 100%; text-align: left;
  padding: 9px 12px; font-size: 13px; color: var(--text-primary);
  background: none; border: none; border-bottom: 1px solid var(--border);
  cursor: pointer;
}
.suggestion-item:last-child { border-bottom: none; }
.suggestion-item:hover { background: var(--bg-hover); color: var(--accent); }
.search-meta { padding: 4px 2px 0; }
.search-count {
  font-family: 'JetBrains Mono', monospace; font-size: 10px;
  color: var(--brand); letter-spacing: 0.5px;
}

.filter-bar {
  padding: 6px 12px 10px; display: flex; flex-direction: column; gap: 6px;
  border-top: 1px dashed var(--border);
}
.filter-row { display: flex; align-items: center; gap: 8px; }
.filter-label {
  font-family: 'JetBrains Mono', monospace; font-size: 9px;
  color: var(--text-muted); letter-spacing: 1.5px; flex-shrink: 0; width: 30px;
}
.filter-chips { display: flex; gap: 6px; flex-wrap: wrap; }
.fchip {
  padding: 3px 10px; font-family: 'JetBrains Mono', monospace;
  font-size: 10px; font-weight: 500; color: var(--text-secondary);
  background: transparent; border: 1px solid var(--border);
  border-radius: 12px; letter-spacing: 0.5px; transition: all 0.15s;
}
.fchip:hover { border-color: var(--border-strong); color: var(--text-primary); }
.fchip.active {
  color: var(--brand); border-color: var(--brand);
  background: var(--brand-dim);
}

.history-bar {
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  position: sticky; z-index: 7; flex-shrink: 0;
  padding: 8px 12px;
}
.history-head {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 6px;
}
.history-label {
  font-family: 'JetBrains Mono', monospace; font-size: 9px;
  font-weight: 600; color: var(--text-muted); letter-spacing: 2px;
}
.history-clear {
  font-family: 'JetBrains Mono', monospace; font-size: 10px;
  color: var(--text-muted); transition: color 0.15s;
}
.history-clear:hover { color: var(--mit-fg); }
.history-chips {
  display: flex; gap: 6px; overflow-x: auto; padding-bottom: 2px;
}
.history-chips::-webkit-scrollbar { display: none; }
.history-chip {
  flex-shrink: 0; display: inline-flex; align-items: center; gap: 5px;
  padding: 5px 10px; background: var(--bg-elevated);
  border: 1px solid var(--border); border-radius: 16px;
  color: var(--text-secondary); transition: all 0.15s; max-width: 200px;
}
.history-chip:hover { border-color: var(--brand); color: var(--brand); }
.hc-icon { color: var(--text-muted); flex-shrink: 0; }
.history-chip:hover .hc-icon { color: var(--brand); }
.hc-text {
  font-size: 12px; white-space: nowrap; overflow: hidden;
  text-overflow: ellipsis; max-width: 140px;
}
.hc-remove {
  display: inline-flex; align-items: center; justify-content: center;
  width: 14px; height: 14px; border-radius: 50%;
  color: var(--text-muted); flex-shrink: 0;
  transition: background 0.15s, color 0.15s;
}
.hc-remove:hover { background: var(--bg-hover); color: var(--mit-fg); }

.no-result {
  display: flex; align-items: center; justify-content: center;
  padding: 48px 20px;
}
.no-result-text {
  font-family: 'JetBrains Mono', monospace; font-size: 11px;
  color: var(--text-muted); letter-spacing: 1px;
}

.chip {
  flex-shrink: 0; padding: 5px 13px;
  font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 500;
  color: var(--text-muted); background: transparent;
  border: 1px solid var(--border); border-radius: 20px;
  white-space: nowrap; transition: all 0.18s; letter-spacing: 0.5px;
}
.chip.active { color: #fff; background: var(--brand); border-color: var(--brand); }
.chip--recommend { display: flex; align-items: center; }
.state-wrap { display: flex; justify-content: center; padding: 60px 20px; }
.spinner { width: 26px; height: 26px; border: 2px solid var(--border); border-top-color: var(--brand); border-radius: 50%; animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg) } }

.list-wrap { flex: 1; padding: 10px 10px 16px; }
.sentinel { height: 1px; }

.news-card {
  background: var(--bg-card); border-radius: var(--radius); padding: 13px 12px;
  display: flex; gap: 10px; align-items: stretch; cursor: pointer;
  margin-bottom: 6px; transition: background 0.15s; border: 1px solid var(--border);
  height: 96px; overflow: hidden;
  color: inherit; text-decoration: none;
}
.news-card:active { background: var(--bg-hover); }
.news-card:focus-visible {
  outline: 2px solid var(--brand);
  outline-offset: 2px;
}
.card-index {
  font-family: 'JetBrains Mono', monospace; font-size: 11px;
  color: var(--text-muted); flex-shrink: 0; padding-top: 3px; min-width: 22px;
}
.card-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 6px; }
.card-source {
  font-family: 'JetBrains Mono', monospace; font-size: 9px;
  font-weight: 500; letter-spacing: 1.5px; text-transform: uppercase;
}
.card-title {
  font-family: 'Noto Serif SC', serif; font-size: 14px; font-weight: 600;
  line-height: 1.55; color: var(--text-primary);
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  flex: 1;
}
.card-meta { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; margin-top: auto; }
.card-meta span { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--text-muted); }
.meta-dot { color: var(--border-strong); }
.card-right { flex-shrink: 0; display: flex; align-items: center; }
.card-img {
  width: 88px; height: 64px; border-radius: var(--radius-sm);
  object-fit: cover; display: block; border: 1px solid var(--border);
}
.card-img--poster {
  display: flex; flex-direction: column; align-items: flex-start; justify-content: space-between;
  padding: 8px;
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--poster-color) 14%, transparent), transparent 58%),
    repeating-linear-gradient(45deg, rgba(26,22,18,0.035) 0 1px, transparent 1px 8px),
    var(--bg-elevated);
}
.thumb-topic {
  font-family: 'JetBrains Mono', monospace; font-size: 9px; line-height: 1.1;
  color: var(--poster-color); letter-spacing: 0.7px;
}
.thumb-source {
  font-family: 'JetBrains Mono', monospace; font-size: 8px;
  color: var(--text-muted); letter-spacing: 1px;
}

.skeleton-card {
  display: flex; gap: 10px; align-items: stretch;
  background: var(--bg-card); border-radius: var(--radius);
  padding: 13px 12px; margin-bottom: 6px; border: 1px solid var(--border);
  height: 96px; overflow: hidden;
}
.sk-index {
  width: 22px; flex-shrink: 0;
  background: var(--border); border-radius: 3px;
  height: 10px; margin-top: 3px;
  animation: shimmer 1.5s infinite;
  background: linear-gradient(90deg, var(--border) 25%, var(--bg-elevated) 50%, var(--border) 75%);
  background-size: 400% 100%;
}
.sk-body { flex: 1; display: flex; flex-direction: column; gap: 7px; }
.sk-source { height: 8px; width: 28px; border-radius: 3px; background: var(--border); }
.sk-line {
  background: linear-gradient(90deg, var(--border) 25%, var(--bg-elevated) 50%, var(--border) 75%);
  background-size: 400% 100%; animation: shimmer 1.5s infinite; border-radius: 3px;
}
.sk-title { height: 13px; }
.sk-short { width: 60%; }
.sk-meta { height: 9px; width: 48%; margin-top: auto; }
.sk-img {
  width: 88px; height: 64px; border-radius: var(--radius-sm); flex-shrink: 0; align-self: center;
  background: linear-gradient(90deg, var(--border) 25%, var(--bg-elevated) 50%, var(--border) 75%);
  background-size: 400% 100%; animation: shimmer 1.5s infinite;
}
@keyframes shimmer { 0%{background-position:100% 0} 100%{background-position:-100% 0} }

.load-indicator { display: flex; justify-content: center; gap: 5px; padding: 20px 0; }
.load-dot {
  width: 5px; height: 5px; background: var(--brand); border-radius: 50%;
  animation: bounce 0.9s infinite;
}
.load-dot:nth-child(2) { animation-delay: 0.15s; }
.load-dot:nth-child(3) { animation-delay: 0.3s; }
@keyframes bounce { 0%,100%{transform:scaleY(0.4);opacity:0.3} 50%{transform:scaleY(1.2);opacity:1} }

.load-more-wrap { display: flex; justify-content: center; padding: 18px 0 10px; }
.load-more-btn {
  min-width: 132px; height: 36px; padding: 0 18px;
  border-radius: 18px; border: 1px solid var(--brand);
  background: var(--brand); color: #fff;
  font-family: 'JetBrains Mono', 'Noto Sans SC', sans-serif;
  font-size: 11px; font-weight: 500; letter-spacing: 1px;
  transition: background 0.18s, color 0.18s, transform 0.18s;
}
.load-more-btn:hover { background: #A66F08; }
.load-more-btn:active { transform: translateY(1px); }

.no-more { display: flex; align-items: center; justify-content: center; gap: 10px; padding: 20px 0 8px; }
.no-more-text { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--text-muted); letter-spacing: 3px; }
.no-more-line { flex: 1; height: 1px; background: var(--border); max-width: 50px; }
@media (min-width: 768px) {
  .news-page { height: 100vh; }
  .list-wrap {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
    padding: 12px 24px 24px;
  }
  .skeleton-list, .load-indicator, .load-more-wrap, .no-more { grid-column: 1 / -1; }
  .top-bar { padding: 0 24px; }
  .source-chips { padding: 8px 24px; }
}

@media (min-width: 1200px) {
  .list-wrap {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    padding: 16px 28px 28px;
  }
  .news-card { height: 110px; padding: 16px 14px; }
  .card-img { width: 108px; height: 76px; }
  .card-title { font-size: 15px; }
}

@media (min-width: 1680px) {
  .list-wrap {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

/* 长按上下文菜单 */
.ctx-overlay {
  position: fixed; inset: 0; z-index: 9000;
}
.ctx-menu {
  position: fixed; min-width: 160px;
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: var(--radius); box-shadow: var(--shadow-md);
  overflow: hidden; animation: ctx-in 0.12s ease;
}
@keyframes ctx-in {
  from { opacity: 0; transform: scale(0.92); }
  to   { opacity: 1; transform: scale(1); }
}
.ctx-item {
  width: 100%; display: flex; align-items: center; gap: 10px;
  padding: 12px 16px; font-size: 14px; color: var(--text-primary);
  transition: background 0.12s;
}
.ctx-item:hover { background: var(--bg-elevated); }
.ctx-item + .ctx-item { border-top: 1px solid var(--border); }
</style>
