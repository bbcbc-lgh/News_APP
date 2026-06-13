<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
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

function escapeHtml(raw: string): string {
  return raw
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function sanitizeHtml(raw: string): string {
  const doc = new DOMParser().parseFromString(raw, 'text/html')
  const allowedTags = new Set(['A', 'P', 'BR', 'STRONG', 'EM', 'B', 'I', 'UL', 'OL', 'LI', 'H2', 'H3', 'H4', 'BLOCKQUOTE', 'CODE', 'PRE', 'IMG'])
  const allowedAttrs: Record<string, Set<string>> = {
    A: new Set(['href', 'title', 'target', 'rel']),
    IMG: new Set(['src', 'alt', 'title']),
  }
  const safeUrl = (value: string) => {
    try {
      const url = new URL(value, window.location.origin)
      return ['http:', 'https:', 'mailto:'].includes(url.protocol)
    } catch {
      return false
    }
  }
  const clean = (node: Node) => {
    if (node.nodeType === Node.ELEMENT_NODE) {
      const el = node as HTMLElement
      if (!allowedTags.has(el.tagName)) {
        el.replaceWith(document.createTextNode(el.textContent || ''))
        return
      }
      Array.from(el.attributes).forEach((attr) => {
        const name = attr.name.toLowerCase()
        const tagAttrs = allowedAttrs[el.tagName] || new Set<string>()
        if (!tagAttrs.has(name) || name.startsWith('on')) el.removeAttribute(attr.name)
        if ((name === 'href' || name === 'src') && !safeUrl(attr.value)) el.removeAttribute(attr.name)
      })
      if (el.tagName === 'A' && el.hasAttribute('href')) {
        el.setAttribute('target', '_blank')
        el.setAttribute('rel', 'noopener')
      }
    }
    Array.from(node.childNodes).forEach(clean)
  }
  Array.from(doc.body.childNodes).forEach(clean)
  return doc.body.innerHTML
}

function renderContent(raw: string): string {
  if (!raw) return ''
  if (/<[a-z][\s\S]*>/i.test(raw)) return sanitizeHtml(raw)
  // 纯文本：按空行分段落，单换行转 <br>
  return raw.split(/\n{2,}/)
    .map(p => `<p>${escapeHtml(p.trim()).replace(/\n/g, '<br>')}</p>`)
    .filter(p => p !== '<p></p>')
    .join('')
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

async function loadDetail() {
  const id = Number(route.params.id)
  loading.value = true
  error.value = ''
  detail.value = null
  isFav.value = false
  try {
    const [d, fav] = await Promise.allSettled([newsApi.getDetail(id), favoriteApi.check(id)])
    if (d.status === 'fulfilled') { detail.value = d.value; historyApi.add(id).catch(() => {}) }
    else { error.value = '加载失败' }
    if (fav.status === 'fulfilled') isFav.value = fav.value.isFavorite
  } finally { loading.value = false }
}

onMounted(loadDetail)
watch(() => route.params.id, loadDetail)
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
          <h1 class="article-title">{{ detail.titleZh || detail.title }}</h1>
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

        <div class="article-text" v-html="renderContent(detail.contentZh || detail.descriptionZh || detail.content || detail.description || '')"></div>

        <a v-if="detail.sourceUrl" :href="detail.sourceUrl" target="_blank" rel="noopener" class="source-link">
          <span>阅读原文</span>
          <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
            <path d="M2 11L11 2M11 2H5M11 2V8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </a>
      </div>

      <div v-if="detail.relatedNews?.length" class="related-section">
        <div class="related-header"><span class="related-eyebrow">RELATED</span></div>
        <div v-for="r in detail.relatedNews" :key="r.id" class="related-item"
          @click="router.replace(`/news/detail/${r.id}`)">
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
.detail-page { min-height: 100%; background: var(--bg); width: 100%; }

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

.cover-wrap { width: 100%; position: relative; overflow: hidden; }
.cover-img { width: 100%; max-height: 260px; object-fit: cover; object-position: center; display: block; }
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

.article-text {
  font-size: 15px; line-height: 1.8; color: var(--text-primary); letter-spacing: 0.3px;
}
.article-text :deep(p) { margin: 0 0 1em; }
.article-text :deep(p:last-child) { margin-bottom: 0; }
.article-text :deep(h2), .article-text :deep(h3) { font-family: 'Noto Serif SC', serif; font-size: 16px; font-weight: 700; margin: 1.4em 0 0.6em; color: var(--text-primary); }
.article-text :deep(ul), .article-text :deep(ol) { padding-left: 1.4em; margin: 0.6em 0 1em; }
.article-text :deep(li) { margin-bottom: 0.4em; }
.article-text :deep(a) { color: var(--brand); border-bottom: 1px solid rgba(200,134,10,0.3); }
.article-text :deep(img) { max-width: 100%; border-radius: var(--radius-sm); margin: 0.8em 0; display: block; }

.source-link {
  display: inline-flex; align-items: center; gap: 5px; margin-top: 20px;
  font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 500;
  color: var(--brand); letter-spacing: 1px; border-bottom: 1px solid var(--brand);
  padding-bottom: 1px; transition: opacity 0.15s;
}
.source-link:hover { opacity: 0.7; }

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

@media (min-width: 768px) {
  .detail-page { min-height: 100%; }
  .content { max-width: 800px; margin: 0 auto; }
  .cover-img { max-height: 420px; }
  .article-body { padding: 32px 40px 8px; }
  .article-title { font-size: 26px; }
  .related-section { padding: 0 40px 24px; }
}
</style>
