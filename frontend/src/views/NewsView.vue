<script setup lang="ts">
import { onMounted, watch, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useNewsStore } from '@/stores/newsStore'
import { newsApi } from '@/api/news'

const news = useNewsStore()
const router = useRouter()
const refreshing = ref(false)
const refreshDone = ref(false)

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

onMounted(async () => {
  await news.loadCategories()
  if (news.newsList.length === 0) news.loadNews(news.activeSource, true)
})

watch(() => news.activeSource, (src) => news.loadNews(src, true))

function onScroll(e: Event) {
  const el = e.target as HTMLElement
  if (el.scrollHeight - el.scrollTop - el.clientHeight < 160 && !news.loading && news.hasMore) {
    news.loadNews(news.activeSource)
  }
}
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

    <div class="source-strip">
      <div class="source-chips">
        <button
          v-for="cat in news.categories"
          :key="cat.id"
          :class="['chip', { active: news.activeSource === cat.id }]"
          @click="news.setCategory(cat.id)"
        >{{ cat.name }}</button>
      </div>
    </div>

    <div class="list-wrap" @scroll="onScroll">
      <div v-if="news.newsList.length === 0 && news.loading" class="skeleton-list">
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

      <template v-if="news.newsList.length > 0">
        <article class="news-card news-card--hero" @click="router.push(`/news/detail/${news.newsList[0].id}`)">
          <img v-if="news.newsList[0].image" :src="news.newsList[0].image" class="hero-img" loading="lazy" />
          <div v-else class="hero-img hero-img--empty" :style="{ background: sourceMeta(news.newsList[0].source_platform || '').bg }">
            <span class="placeholder-label">{{ sourceMeta(news.newsList[0].source_platform || '').label }}</span>
          </div>
          <div class="hero-overlay">
            <div class="hero-source-badge" :style="{ '--src-color': sourceMeta(news.newsList[0].source_platform || '').color }">
              {{ sourceMeta(news.newsList[0].source_platform || '').label }}
            </div>
            <h2 class="hero-title">{{ news.newsList[0].title }}</h2>
            <div class="hero-meta">
              <span>{{ news.newsList[0].author || '未知' }}</span>
              <span class="dot">·</span>
              <span>{{ formatViews(news.newsList[0].views) }} reads</span>
              <span class="dot">·</span>
              <span>{{ timeAgo(news.newsList[0].publish_time) }}</span>
            </div>
          </div>
        </article>

        <article
          v-for="(item, idx) in news.newsList.slice(1)"
          :key="item.id"
          class="news-card"
          @click="router.push(`/news/detail/${item.id}`)"
        >
          <div class="card-index">{{ String(idx + 2).padStart(2, '0') }}</div>
          <div class="card-body">
            <div class="card-source" :style="{ color: sourceMeta(item.source_platform || '').color }">
              {{ sourceMeta(item.source_platform || '').label }}
            </div>
            <h3 class="card-title">{{ item.title }}</h3>
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

      <div v-if="news.loading && news.newsList.length" class="load-indicator">
        <span class="load-dot" v-for="i in 3" :key="i"></span>
      </div>
      <div v-if="!news.hasMore && news.newsList.length" class="no-more">
        <span class="no-more-line"></span>
        <span class="no-more-text">END OF FEED</span>
        <span class="no-more-line"></span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.news-page { display: flex; flex-direction: column; height: 100vh; background: var(--bg); }

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
}
.source-strip::-webkit-scrollbar { display: none; }
.source-chips { display: flex; padding: 8px 12px; gap: 6px; width: max-content; min-width: 100%; }

.chip {
  flex-shrink: 0; padding: 5px 13px;
  font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 500;
  color: var(--text-muted); background: transparent;
  border: 1px solid var(--border); border-radius: 20px;
  white-space: nowrap; transition: all 0.18s; letter-spacing: 0.5px;
}
.chip.active { color: #fff; background: var(--brand); border-color: var(--brand); }

.list-wrap { flex: 1; overflow-y: auto; scrollbar-width: none; padding: 10px 10px 0; }
.list-wrap::-webkit-scrollbar { display: none; }

.news-card--hero {
  position: relative; border-radius: var(--radius); overflow: hidden;
  margin-bottom: 8px; cursor: pointer; height: 220px;
  background: var(--bg-elevated); border: 1px solid var(--border);
}
.hero-img { width: 100%; height: 100%; object-fit: cover; display: block; }
.hero-img--empty { background: var(--bg-elevated); }
.hero-overlay {
  position: absolute; inset: 0;
  background: linear-gradient(to top, rgba(26,22,18,0.85) 0%, rgba(26,22,18,0.2) 55%, transparent 100%);
  padding: 14px; display: flex; flex-direction: column; justify-content: flex-end;
}
.hero-source-badge {
  font-family: 'JetBrains Mono', monospace; font-size: 9px; font-weight: 500;
  letter-spacing: 2px; color: var(--src-color, var(--brand));
  background: rgba(247,244,239,0.15); border: 1px solid var(--src-color, var(--brand));
  padding: 2px 8px; border-radius: 3px;
  display: inline-block; align-self: flex-start; margin-bottom: 8px;
}
.hero-title {
  font-family: 'Noto Serif SC', serif; font-size: 17px; font-weight: 700;
  color: #fff; line-height: 1.5; margin-bottom: 8px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.hero-meta { display: flex; align-items: center; gap: 5px; }
.hero-meta span { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: rgba(247,244,239,0.7); }

.news-card {
  background: var(--bg-card); border-radius: var(--radius); padding: 13px 12px;
  display: flex; gap: 10px; align-items: stretch; cursor: pointer;
  margin-bottom: 6px; transition: background 0.15s; border: 1px solid var(--border);
  height: 96px; overflow: hidden;
}
.news-card:active { background: var(--bg-hover); }
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
.card-img--empty { background: var(--bg-elevated); display: flex; align-items: center; justify-content: center; }
.hero-img--empty { display: flex; align-items: center; justify-content: center; }
.placeholder-label {
  font-family: 'JetBrains Mono', monospace; font-weight: 500;
  font-size: 13px; letter-spacing: 1px; opacity: 0.5; color: var(--text-primary);
}
.placeholder-label.small { font-size: 9px; letter-spacing: 0.5px; }

.skeleton-card {
  display: flex; gap: 12px; background: var(--bg-card); border-radius: var(--radius);
  padding: 13px 12px; margin-bottom: 6px; border: 1px solid var(--border);
}
.sk-body { flex: 1; display: flex; flex-direction: column; gap: 7px; padding-top: 2px; }
.sk-line {
  background: linear-gradient(90deg, var(--border) 25%, var(--bg-elevated) 50%, var(--border) 75%);
  background-size: 400% 100%; animation: shimmer 1.5s infinite; border-radius: 3px;
}
.sk-eyebrow { height: 8px; width: 40px; border-radius: 3px; background: var(--border); }
.sk-title { height: 14px; }
.sk-short { width: 65%; }
.sk-meta { height: 10px; width: 50%; margin-top: 2px; }
.sk-img {
  width: 88px; height: 64px; border-radius: var(--radius-sm); flex-shrink: 0;
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

.no-more { display: flex; align-items: center; justify-content: center; gap: 10px; padding: 20px 0 8px; }
.no-more-text { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--text-muted); letter-spacing: 3px; }
.no-more-line { flex: 1; height: 1px; background: var(--border); max-width: 50px; }
.dot { color: var(--border-strong); }

@media (min-width: 768px) {
  .list-wrap {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    padding: 12px 20px 0;
    align-items: start;
  }
  .news-card--hero { grid-column: 1 / -1; height: 300px; }
  .skeleton-list, .load-indicator, .no-more { grid-column: 1 / -1; }
  .top-bar { padding: 0 24px; }
  .source-chips { padding: 8px 20px; }
}
</style>
