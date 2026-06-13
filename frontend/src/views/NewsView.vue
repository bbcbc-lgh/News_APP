<script setup lang="ts">
import { onMounted, onUnmounted, watch, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useNewsStore } from '@/stores/newsStore'
import { newsApi, type NewsItem } from '@/api/news'

const news = useNewsStore()
const router = useRouter()
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
    const res = await newsApi.search(q, searchPage.value)
    searchResults.value = reset ? res.list : [...searchResults.value, ...res.list]
    searchTotal.value = res.total
    searchHasMore.value = res.hasMore
    searchPage.value++
  } finally {
    searchLoading.value = false
  }
}

function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  const q = searchQuery.value.trim()
  if (!q) { exitSearch(); return }
  searchActive.value = true
  searchTimer = setTimeout(() => doSearch(true), 400)
}

function exitSearch() {
  searchActive.value = false
  searchQuery.value = ''
  searchResults.value = []
  searchPage.value = 1
  searchHasMore.value = false
}

const displayList = computed(() => searchActive.value ? searchResults.value : news.newsList)

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

function setupObserver() {
  if (observer) observer.disconnect()
  observer = new IntersectionObserver((entries) => {
    if (!entries[0].isIntersecting) return
    if (searchActive.value) {
      if (!searchLoading.value && searchHasMore.value) doSearch()
    } else {
      if (!news.loading && news.hasMore) news.loadNews(news.activeSource)
    }
  }, { rootMargin: '200px' })
  if (sentinel.value) observer.observe(sentinel.value)
}

onMounted(async () => {
  await news.loadCategories()
  if (news.newsList.length === 0) news.loadNews(news.activeSource, true)
  setupObserver()
})

onUnmounted(() => { observer?.disconnect() })

watch(() => news.activeSource, (src) => news.loadNews(src, true))
watch(sentinel, () => setupObserver())
</script>

<template>
  <div class="news-page">
    <header class="top-bar">
      <div class="logo-wrap">
        <span class="logo-mark">AI</span>
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
          @click="news.setCategory(cat.id)"
        >{{ cat.name }}</button>
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
          @keydown.escape="exitSearch"
        />
        <button v-if="searchActive" class="search-clear" @click="exitSearch">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M2 2L10 10M10 2L2 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
      <div v-if="searchActive && searchTotal > 0" class="search-meta">
        <span class="search-count">{{ searchTotal }} 条结果</span>
      </div>
    </div>

    <div class="list-wrap">
      <div v-if="searchActive && searchLoading && searchResults.length === 0" class="skeleton-list">
        <div v-for="i in 3" :key="i" class="skeleton-card">
          <div class="sk-body">
            <div class="sk-eyebrow"></div>
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

      <div v-if="!searchActive && news.newsList.length === 0 && news.loading" class="skeleton-list">
        <div v-for="i in 5" :key="i" class="skeleton-card">
          <div class="sk-body">
            <div class="sk-eyebrow"></div>
            <div class="sk-line sk-title"></div>
            <div class="sk-line sk-title sk-short"></div>
            <div class="sk-line sk-meta"></div>
          </div>
          <div class="sk-img"></div>
        </div>
      </div>

      <template v-if="displayList.length > 0">
        <article class="news-card news-card--hero" @click="router.push(`/news/detail/${displayList[0].id}`)">
          <img v-if="displayList[0].image" :src="displayList[0].image" class="hero-img" loading="lazy" />
          <div v-else class="hero-img hero-img--empty" :style="{ background: sourceMeta(displayList[0].source_platform || '').bg }">
            <span class="placeholder-label">{{ sourceMeta(displayList[0].source_platform || '').label }}</span>
          </div>
          <div class="hero-overlay">
            <div class="hero-source-badge" :style="{ '--src-color': sourceMeta(displayList[0].source_platform || '').color }">
              {{ sourceMeta(displayList[0].source_platform || '').label }}
            </div>
            <h2 class="hero-title">{{ displayList[0].title_zh || displayList[0].title }}</h2>
            <div class="hero-meta">
              <span>{{ displayList[0].author || '未知' }}</span>
              <span class="dot">·</span>
              <span>{{ formatViews(displayList[0].views) }} reads</span>
              <span class="dot">·</span>
              <span>{{ timeAgo(displayList[0].publish_time) }}</span>
            </div>
          </div>
        </article>

        <article
          v-for="(item, idx) in displayList.slice(1)"
          :key="item.id"
          class="news-card"
          @click="router.push(`/news/detail/${item.id}`)"
        >
          <div class="card-index">{{ String(idx + 2).padStart(2, '0') }}</div>
          <div class="card-body">
            <div class="card-source" :style="{ color: sourceMeta(item.source_platform || '').color }">
              {{ sourceMeta(item.source_platform || '').label }}
            </div>
            <h3 class="card-title">{{ item.title_zh || item.title }}</h3>
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
            <div v-else class="card-img card-img--empty" :style="{ background: sourceMeta(item.source_platform || '').bg }">
              <span class="placeholder-label small">{{ sourceMeta(item.source_platform || '').label }}</span>
            </div>
          </div>
        </article>
      </template>

      <div v-if="(searchActive ? searchLoading : news.loading) && displayList.length" class="load-indicator">
        <span class="load-dot" v-for="i in 3" :key="i"></span>
      </div>
      <div v-if="!searchActive && !news.hasMore && news.newsList.length" class="no-more">
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
  </div>
</template>

<style scoped>
.news-page { display: flex; flex-direction: column; min-height: 100%; background: var(--bg); width: 100%; }

.top-bar {
  height: 54px; background: var(--bg-card);
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 16px; border-bottom: 1px solid var(--border);
  position: sticky; top: 0; z-index: 10; flex-shrink: 0;
  box-shadow: var(--shadow-sm);
}
.logo-wrap { display: flex; align-items: center; gap: 10px; }
.logo-mark {
  width: 32px; height: 32px; background: var(--brand); color: #fff;
  font-family: 'Libre Baskerville', serif; font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  border-radius: 7px; flex-shrink: 0;
}
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
.search-meta { padding: 4px 2px 0; }
.search-count {
  font-family: 'JetBrains Mono', monospace; font-size: 10px;
  color: var(--brand); letter-spacing: 0.5px;
}

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

.list-wrap { flex: 1; padding: 10px 10px 16px; }
.sentinel { height: 1px; }

.news-card--hero {
  position: relative; border-radius: var(--radius); overflow: hidden;
  margin-bottom: 8px; cursor: pointer; height: 220px;
  background: var(--bg-elevated); border: 1px solid var(--border);
}
.hero-img { width: 100%; height: 100%; object-fit: cover; display: block; }
.hero