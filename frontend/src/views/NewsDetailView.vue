<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { newsApi, type NewsDetail } from '@/api/news'
import { favoriteApi } from '@/api/favorite'
import { historyApi } from '@/api/history'

const route = useRoute()
const router = useRouter()

const detail = ref<NewsDetail | null>(null)
const isFav = ref(false)
const loading = ref(true)
const favLoading = ref(false)
const error = ref('')

const SOURCE_META: Record<string, { label: string; color: string }> = {
  'hackernews': { label: 'HN',        color: 'var(--hn)' },
  'openai':     { label: 'OpenAI',    color: 'var(--openai)' },
  'google_ai':  { label: 'Google AI', color: 'var(--google)' },
  'mit':        { label: 'MIT',       color: 'var(--mit-fg)' },
}
function sourceMeta(s: string) {
  return SOURCE_META[s] || { label: s, color: 'var(--brand)' }
}
function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}
function formatViews(v: number): string {
  return v >= 10000 ? `${(v / 10000).toFixed(1)}万` : String(v)
}

async function toggleFav() {
  if (!detail.value) return
  favLoading.value = true
  try {
    if (isFav.value) { await favoriteApi.remove(detail.value.id) }
    else { await favoriteApi.add(detail.value.id) }
    isFav.value = !isFav.value
  } finally { favLoading.value = false }
}

onMounted(async () => {
  const id = Number(route.params.id)
  try {
    const [d, fav] = await Promise.allSettled([newsApi.getDetail(id), favoriteApi.check(id)])
    if (d.status === 'fulfilled') { detail.value = d.value; historyApi.add(id).catch(() => {}) }
    else { error.value = '加载失败' }
    if (fav.status === 'fulfilled') isFav.value = fav.value.isFavorite
  } finally { loading.value = false }
})
</script>

<template>
  <div class="detail-page">
    <header class="top-bar">
      <button class="back-btn" @click="router.back()">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M13 4L7 10L13 16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <span class="top-label">ARTICLE</span>
      <button :class="['fav-btn', { active: isFav }]" :disabled="favLoading" @click="toggleFav">
        <svg width="20" height="20" viewBox="0 0 22 22" fill="none">
          <path d="M11 19L3.5 11.5C2 10 2 7.5 3.5 6C5 4.5 7.5 4.5 9 6L11 8L13 6C14.5 4.5 17 4.5 18.5 6C20 7.5 20 10 18.5 11.5L11 19Z"
            :fill="isFav ? 'var(--brand)' : 'none'"
            :stroke="isFav ? 'var(--brand)' : 'var(--text-secondary)'"
            stroke-width="1.8" stroke-linejoin="round"/>
        </svg>
      </button>
    </header>

    <div v-if="loading" class="state-wrap"><div class="spinner"></div></div>

    <div v-else-if="error" class="state-wrap err-state">
      <p>{{ error }}</p>
      <button class="retry-btn" @click="router.back()">返回</button>
    </div>

    <article v-else-if="detail" class="content">
      <div v-if="detail.image" class="cover-wrap">
        <img :src="detail.image" class="cover-img" />
        <div class="cover-fade"></div>
      </div>

      <div class="article-body">
        <div class="title-section">
          <div v-if="detail.source" class="source-badge"
            :style="{ color: sourceMeta(detail.source).color, borderColor: sourceMeta(detail.source).color }">
            {{ sourceMeta(detail.source).label }}
          </div>
          <h1 class="article-title">{{ detail.title }}</h1>
          <div class="article-meta">
            <span class="meta-author">{{ detail.author || '未知来源' }}</span>
            <span class="meta-sep">·</span>
            <span>{{ formatDate(detail.publishTime) }}</span>
            <span class="meta-sep">·</span>
            <span>{{ formatViews(detail.views) }} reads</span>
          </div>
        </div>

        <div class="divider">
          <span class="divider-line"></span>
          <span class="divider-diamond"></span>
          <span class="divider-line"></span>
        </div>

        <div class="article-text" v-html="detail.content.replace(/\n/g, '<br>')"></div>
      </div>

      <div v-if="detail.relatedNews?.length" class="related-section">
        <div class="related-header"><span class="related-eyebrow">RELATED</span></div>
        <div v-for="r in detail.relatedNews" :key="r.id" class="related-item"
          @click="router.push(`/news/detail/${r.id}`)">
          <span class="related-num">{{ String(detail.relatedNews.indexOf(r) + 1).padStart(2,'0') }}</span>
          <span class="related-text">{{ r.title }}</span>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M5 3L9 7L5 11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
      </div>
    </article>
    <div style="height: 32px"></div>
  </div>
</template>

<style scoped>
.detail-page { min-height: 100vh; background: var(--bg); }

.top-bar {
  position: sticky; top: 0; z-index: 10; height: 52px;
  background: rgba(247,244,239,0.95); backdrop-filter: blur(16px);
  display: flex; align-items: center; padding: 0 12px;
  border-bottom: 1px solid var(--border); box-shadow: var(--shadow-sm);
}
.back-btn { color: var(--text-primary); padding: 6px; display: flex; align-items: center; margin-right: 4px; }
.top-label {
  flex: 1; font-family: 'JetBrains Mono', monospace;
  font-size: 11px; font-weight: 500; color: var(--text-muted); letter-spacing: 3px;
}
.fav-btn { padding: 6px; display: flex; align-items: center; transition: transform 0.2s; }
.fav-btn:active { transform: scale(0.85); }

.state-wrap { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; padding: 80px 20px; }
.err-state p { font-size: 15px; color: var(--text-secondary); }
.retry-btn { padding: 9px 24px; border: 1px solid var(--brand); border-radius: 20px; font-size: 14px; color: var(--brand); font-weight: 600; }

.cover-wrap { width: 100%; position: relative; }
.cover-img { width: 100%; max-height: 260px; object-fit: cover; display: block; }
.cover-fade { position: absolute; bottom: 0; left: 0; right: 0; height: 80px; background: linear-gradient(to bottom, transparent, var(--bg)); }

.article-body { padding: 20px 18px 8px; }
.title-section { margin-bottom: 16px; }
.source-badge {
  font-family: 'JetBrains Mono', monospace; font-size: 9px; font-weight: 500;
  letter-spacing: 2px; border: 1px solid; padding: 2px 8px; border-radius: 3px;
  display: inline-block; margin-bottom: 12px; background: rgba(200,134,10,0.04);
}
.article-title {
  font-family: 'Noto Serif SC', serif; font-size: 21px; font-weight: 900;
  line-height: 1.55; color: var(--text-primary); margin-bottom: 12px; letter-spacing: 0.3px;
}
.article-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.article-meta span { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--text-muted); }
.meta-author { color: var(--text-secondary) !important; font-weight: 500; }
.meta-sep { color: var(--border-strong) !important; }

.divider { display: flex; align-items: center; gap: 8px; margin-bottom: 18px; }
.divider-line { flex: 1; height: 1px; background: var(--border); }
.divider-diamond { width: 6px; height: 6px; background: var(--brand); transform: rotate(45deg); flex-shrink: 0; }

.article-text { font-size: 15px; line-height: 1.95; color: var(--text-primary); letter-spacing: 0.3px; }

.related-section { margin-top: 8px; padding: 0 18px 16px; border-top: 1px solid var(--border); }
.related-header { padding: 16px 0 10px; }
.related-eyebrow { font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 500; letter-spacing: 3px; color: var(--brand); }
.related-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 12px 0; border-bottom: 1px solid var(--border);
  cursor: pointer; transition: opacity 0.15s; color: var(--text-muted);
}
.related-item:active { opacity: 0.6; }
.related-num { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--text-muted); flex-shrink: 0; padding-top: 3px; min-width: 20px; }
.related-text { flex: 1; font-size: 14px; color: var(--text-primary); line-height: 1.6; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

.spinner { width: 28px; height: 28px; border: 2px solid var(--border); border-top-color: var(--brand); border-radius: 50%; animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg) } }
</style>
