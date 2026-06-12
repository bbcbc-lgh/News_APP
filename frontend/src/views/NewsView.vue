<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useNewsStore } from '@/stores/newsStore'

const news = useNewsStore()
const router = useRouter()

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 60) return m <= 1 ? '刚刚' : `${m}分钟前`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}小时前`
  const d = Math.floor(h / 24)
  if (d < 30) return `${d}天前`
  return new Date(dateStr).toLocaleDateString('zh-CN', { month: 'long', day: 'numeric' })
}

function formatViews(v: number): string {
  return v >= 10000 ? `${(v / 10000).toFixed(1)}万` : String(v)
}

onMounted(async () => {
  await news.loadCategories()
  if (news.newsList.length === 0) news.loadNews(news.activeCategoryId, true)
})

watch(() => news.activeCategoryId, (id) => news.loadNews(id, true))

function onScroll(e: Event) {
  const el = e.target as HTMLElement
  if (el.scrollHeight - el.scrollTop - el.clientHeight < 160 && !news.loading && news.hasMore) {
    news.loadNews(news.activeCategoryId)
  }
}
</script>

<template>
  <div class="news-page">
    <!-- 顶栏 -->
    <header class="top-bar">
      <div class="logo-wrap">
        <span class="logo-zh">AI掘金</span>
        <span class="logo-divider"></span>
        <span class="logo-sub">头条</span>
      </div>
      <div class="header-badge">HOT</div>
    </header>

    <!-- 分类 tabs -->
    <div class="tabs-wrap">
      <div class="tabs">
        <button
          v-for="cat in news.categories"
          :key="cat.id"
          :class="['tab', { active: news.activeCategoryId === cat.id }]"
          @click="news.setCategory(cat.id)"
        >{{ cat.name }}</button>
      </div>
    </div>

    <!-- 新闻列表 -->
    <div class="list-wrap" @scroll="onScroll">
      <!-- 骨架屏 -->
      <div v-if="news.newsList.length === 0 && news.loading" class="skeleton-list">
        <div v-for="i in 5" :key="i" class="skeleton-card">
          <div class="sk-body">
            <div class="sk-line sk-title"></div>
            <div class="sk-line sk-title sk-title-short"></div>
            <div class="sk-line sk-meta"></div>
          </div>
          <div class="sk-img"></div>
        </div>
      </div>

      <!-- 第一条：大图卡片 -->
      <template v-if="news.newsList.length > 0">
        <article
          class="news-card news-card--hero"
          @click="router.push(`/news/detail/${news.newsList[0].id}`)"
        >
          <img v-if="news.newsList[0].image" :src="news.newsList[0].image" class="hero-img" loading="lazy" />
          <div v-else class="hero-img hero-img--empty"></div>
          <div class="hero-overlay">
            <div class="hero-category">
              {{ news.categories.find(c => c.id === news.newsList[0].category_id)?.name || '头条' }}
            </div>
            <h2 class="hero-title">{{ news.newsList[0].title }}</h2>
            <div class="hero-meta">
              <span>{{ news.newsList[0].author || '未知' }}</span>
              <span class="dot">·</span>
              <span>{{ formatViews(news.newsList[0].views) }}阅读</span>
              <span class="dot">·</span>
              <span>{{ timeAgo(news.newsList[0].publish_time) }}</span>
            </div>
          </div>
        </article>

        <!-- 剩余条目 -->
        <article
          v-for="item in news.newsList.slice(1)"
          :key="item.id"
          class="news-card"
          @click="router.push(`/news/detail/${item.id}`)"
        >
          <div class="card-body">
            <h3 class="card-title">{{ item.title }}</h3>
            <div class="card-meta">
              <span class="meta-author">{{ item.author || '未知' }}</span>
              <span class="meta-dot">·</span>
              <span>{{ formatViews(item.views) }}阅读</span>
              <span class="meta-dot">·</span>
              <span>{{ timeAgo(item.publish_time) }}</span>
            </div>
          </div>
          <div class="card-right">
            <img v-if="item.image" :src="item.image" class="card-img" loading="lazy" />
            <div v-else class="card-img card-img--empty"></div>
          </div>
        </article>
      </template>

      <div v-if="news.loading && news.newsList.length" class="load-indicator">
        <span class="load-dot" v-for="i in 3" :key="i"></span>
      </div>
      <div v-if="!news.hasMore && news.newsList.length" class="no-more">
        <span class="no-more-line"></span>
        <span>没有更多了</span>
        <span class="no-more-line"></span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.news-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg);
}

/* ── 顶栏 ── */
.top-bar {
  height: 52px;
  background: var(--bg-card);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  border-bottom: 2px solid var(--text-primary);
  position: sticky;
  top: 0;
  z-index: 10;
  flex-shrink: 0;
}

.logo-wrap { display: flex; align-items: center; gap: 8px; }
.logo-zh {
  font-family: 'Noto Serif SC', serif;
  font-size: 18px;
  font-weight: 900;
  color: var(--text-primary);
  letter-spacing: 1px;
}
.logo-divider {
  width: 1.5px;
  height: 14px;
  background: var(--border-strong);
  display: inline-block;
}
.logo-sub {
  font-family: 'Noto Serif SC', serif;
  font-size: 18px;
  font-weight: 700;
  color: var(--brand);
}

.header-badge {
  font-size: 10px;
  font-weight: 900;
  letter-spacing: 1.5px;
  color: #fff;
  background: var(--brand);
  padding: 2px 7px;
  border-radius: 3px;
}

/* ── 分类 tabs ── */
.tabs-wrap {
  background: var(--bg-card);
  overflow-x: auto;
  scrollbar-width: none;
  position: sticky;
  top: 52px;
  z-index: 9;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.tabs-wrap::-webkit-scrollbar { display: none; }
.tabs { display: flex; padding: 0 10px; }

.tab {
  flex-shrink: 0;
  padding: 10px 13px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
  border-bottom: 2px solid transparent;
  white-space: nowrap;
  transition: color 0.15s, border-color 0.15s;
  letter-spacing: 0.3px;
}
.tab.active {
  color: var(--text-primary);
  border-bottom-color: var(--brand);
  font-weight: 700;
}

/* ── 列表 ── */
.list-wrap {
  flex: 1;
  overflow-y: auto;
  scrollbar-width: none;
  padding: 10px 10px 0;
}
.list-wrap::-webkit-scrollbar { display: none; }

/* Hero 卡片 */
.news-card--hero {
  position: relative;
  border-radius: var(--radius);
  overflow: hidden;
  margin-bottom: 8px;
  cursor: pointer;
  height: 210px;
  background: var(--border);
}
.hero-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.hero-img--empty { background: var(--border-strong); }
.hero-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(20,16,12,0.92) 0%, rgba(20,16,12,0.3) 55%, transparent 100%);
  padding: 14px 14px 16px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}
.hero-category {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1.5px;
  color: var(--brand);
  background: rgba(232,66,10,0.15);
  border: 1px solid var(--brand);
  padding: 2px 8px;
  border-radius: 3px;
  display: inline-block;
  align-self: flex-start;
  margin-bottom: 8px;
}
.hero-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 17px;
  font-weight: 700;
  color: #fff;
  line-height: 1.5;
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.hero-meta { display: flex; align-items: center; gap: 5px; }
.hero-meta span { font-size: 11px; color: rgba(255,255,255,0.6); }

/* 普通卡片 */
.news-card {
  background: var(--bg-card);
  border-radius: var(--radius);
  padding: 14px 12px;
  display: flex;
  gap: 12px;
  align-items: flex-start;
  cursor: pointer;
  margin-bottom: 8px;
  transition: background 0.12s;
  border: 1px solid var(--border);
}
.news-card:active { background: var(--bg); }

.card-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 9px; }
.card-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.55;
  color: var(--text-primary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.card-meta { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.card-meta span, .meta-author { font-size: 11px; color: var(--text-muted); }
.meta-dot { color: var(--border-strong); }

.card-right { flex-shrink: 0; }
.card-img {
  width: 96px;
  height: 70px;
  border-radius: var(--radius-sm);
  object-fit: cover;
  display: block;
}
.card-img--empty { background: var(--border); }

/* 骨架屏 */
.skeleton-list { }
.skeleton-card {
  display: flex;
  gap: 12px;
  background: var(--bg-card);
  border-radius: var(--radius);
  padding: 14px 12px;
  margin-bottom: 8px;
  border: 1px solid var(--border);
}
.sk-body { flex: 1; display: flex; flex-direction: column; gap: 8px; padding-top: 2px; }
.sk-line {
  background: linear-gradient(90deg, var(--border) 25%, #E4E0D8 50%, var(--border) 75%);
  background-size: 400% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}
.sk-title { height: 16px; }
.sk-title-short { width: 70%; }
.sk-meta { height: 11px; width: 55%; margin-top: 4px; }
.sk-img {
  width: 96px; height: 70px;
  border-radius: var(--radius-sm);
  background: linear-gradient(90deg, var(--border) 25%, #E4E0D8 50%, var(--border) 75%);
  background-size: 400% 100%;
  animation: shimmer 1.5s infinite;
  flex-shrink: 0;
}
@keyframes shimmer { 0% { background-position: 100% 0 } 100% { background-position: -100% 0 } }

/* 加载指示 */
.load-indicator {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 5px;
  padding: 20px 0;
}
.load-dot {
  width: 6px; height: 6px;
  background: var(--brand);
  border-radius: 50%;
  animation: bounce 1s infinite;
}
.load-dot:nth-child(2) { animation-delay: 0.15s; }
.load-dot:nth-child(3) { animation-delay: 0.3s; }
@keyframes bounce {
  0%, 100% { transform: scaleY(0.5); opacity: 0.4; }
  50% { transform: scaleY(1.2); opacity: 1; }
}

.no-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 20px 0 8px;
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 1px;
}
.no-more-line {
  flex: 1;
  height: 1px;
  background: var(--border);
  max-width: 60px;
}

.dot { color: var(--border-strong); }
</style>
