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

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}

function formatViews(v: number): string {
  return v >= 10000 ? `${(v / 10000).toFixed(1)}万` : String(v)
}

async function toggleFav() {
  if (!detail.value) return
  favLoading.value = true
  try {
    if (isFav.value) {
      await favoriteApi.remove(detail.value.id)
    } else {
      await favoriteApi.add(detail.value.id)
    }
    isFav.value = !isFav.value
  } finally {
    favLoading.value = false
  }
}

onMounted(async () => {
  const id = Number(route.params.id)
  try {
    const [d, fav] = await Promise.allSettled([
      newsApi.getDetail(id),
      favoriteApi.check(id)
    ])
    if (d.status === 'fulfilled') {
      detail.value = d.value
      historyApi.add(id).catch(() => {})
    } else {
      error.value = '加载失败'
    }
    if (fav.status === 'fulfilled') isFav.value = fav.value.isFavorite
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="detail-page">
    <!-- 顶栏 -->
    <header class="top-bar">
      <button class="back-btn" @click="router.back()">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M13 4L7 10L13 16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <span class="top-label">正文</span>
      <button :class="['fav-btn', { active: isFav }]" :disabled="favLoading" @click="toggleFav">
        <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
          <path d="M11 19L3.5 11.5C2 10 2 7.5 3.5 6C5 4.5 7.5 4.5 9 6L11 8L13 6C14.5 4.5 17 4.5 18.5 6C20 7.5 20 10 18.5 11.5L11 19Z"
            :fill="isFav ? 'var(--brand)' : 'none'"
            :stroke="isFav ? 'var(--brand)' : 'var(--text-secondary)'"
            stroke-width="1.8"
            stroke-linejoin="round"/>
        </svg>
      </button>
    </header>

    <!-- 加载中 -->
    <div v-if="loading" class="state-wrap">
      <div class="spinner"></div>
    </div>

    <!-- 错误 -->
    <div v-else-if="error" class="state-wrap err-state">
      <p>{{ error }}</p>
      <button class="retry-btn" @click="router.back()">返回</button>
    </div>

    <!-- 正文 -->
    <article v-else-if="detail" class="content">
      <!-- 封面图 -->
      <div v-if="detail.image" class="cover-wrap">
        <img :src="detail.image" class="cover-img" />
      </div>

      <div class="article-body">
        <!-- 标题区 -->
        <div class="title-section">
          <h1 class="article-title">{{ detail.title }}</h1>
          <div class="article-meta">
            <span class="meta-author">{{ detail.author || '未知来源' }}</span>
            <span class="meta-sep">|</span>
            <span>{{ formatDate(detail.publishTime) }}</span>
            <span class="meta-sep">|</span>
            <span>{{ formatViews(detail.views) }} 阅读</span>
          </div>
        </div>

        <!-- 分割线 -->
        <div class="divider">
          <span class="divider-line"></span>
          <span class="divider-dot"></span>
          <span class="divider-line"></span>
        </div>

        <!-- 正文 -->
        <div class="article-text" v-html="detail.content.replace(/\n/g, '<br>')"></div>
      </div>

      <!-- 相关新闻 -->
      <div v-if="detail.relatedNews?.length" class="related-section">
        <div class="related-header">
          <span class="related-tag">相关阅读</span>
        </div>
        <div
          v-for="r in detail.relatedNews"
          :key="r.id"
          class="related-item"
          @click="router.push(`/news/detail/${r.id}`)"
        >
          <span class="related-bar"></span>
          <span class="related-text">{{ r.title }}</span>
          <svg class="related-arrow" width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M5 3L9 7L5 11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
      </div>
    </article>

    <!-- 底部留白 -->
    <div style="height: 32px"></div>
  </div>
</template>

<style scoped>
.detail-page {
  min-height: 100vh;
  background: var(--bg-card);
}

.top-bar {
  position: sticky; top: 0; z-index: 10;
  height: 52px;
  background: rgba(254,252,250,0.95);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  padding: 0 12px;
  border-bottom: 1px solid var(--border);
}
.back-btn {
  color: var(--text-primary);
  padding: 6px;
  display: flex;
  align-items: center;
  margin-right: 4px;
}
.top-label {
  flex: 1;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-secondary);
  letter-spacing: 0.5px;
}
.fav-btn {
  padding: 6px;
  display: flex;
  align-items: center;
  transition: transform 0.2s;
}
.fav-btn:active { transform: scale(0.88); }

/* 状态页 */
.state-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 80px 20px;
}
.err-state p { font-size: 15px; color: var(--text-secondary); }
.retry-btn {
  padding: 9px 24px;
  border: 1.5px solid var(--brand);
  border-radius: 20px;
  font-size: 14px;
  color: var(--brand);
  font-weight: 600;
}

/* 封面图 */
.cover-wrap { width: 100%; }
.cover-img {
  width: 100%;
  max-height: 250px;
  object-fit: cover;
  display: block;
}

/* 正文区 */
.article-body {
  padding: 20px 18px 8px;
}

.title-section { margin-bottom: 16px; }
.article-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 21px;
  font-weight: 900;
  line-height: 1.55;
  color: var(--text-primary);
  margin-bottom: 12px;
  letter-spacing: 0.3px;
}
.article-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.article-meta span { font-size: 12px; color: var(--text-muted); }
.meta-author { color: var(--text-secondary); font-weight: 600; }
.meta-sep { color: var(--border-strong); }

.divider {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 18px;
}
.divider-line { flex: 1; height: 1px; background: var(--border); }
.divider-dot {
  width: 5px; height: 5px;
  background: var(--brand);
  border-radius: 50%;
  flex-shrink: 0;
}

.article-text {
  font-size: 16px;
  line-height: 1.9;
  color: var(--text-primary);
  letter-spacing: 0.3px;
}

/* 相关新闻 */
.related-section {
  margin-top: 8px;
  padding: 0 18px 16px;
  border-top: 6px solid var(--bg);
}
.related-header {
  padding: 16px 0 12px;
}
.related-tag {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1.5px;
  color: var(--text-secondary);
  background: var(--brand-dim);
  border-left: 3px solid var(--brand);
  padding: 3px 10px 3px 8px;
  border-radius: 0 4px 4px 0;
}
.related-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: opacity 0.15s;
}
.related-item:active { opacity: 0.6; }
.related-bar {
  width: 3px;
  height: 16px;
  background: var(--brand);
  border-radius: 2px;
  flex-shrink: 0;
  margin-top: 3px;
}
.related-text {
  flex: 1;
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.related-arrow {
  color: var(--text-muted);
  flex-shrink: 0;
  margin-top: 4px;
}

/* spinner */
.spinner {
  width: 32px; height: 32px;
  border: 2.5px solid var(--border-strong);
  border-top-color: var(--brand);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg) } }
</style>
