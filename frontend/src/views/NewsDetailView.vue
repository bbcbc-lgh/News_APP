<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
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
const shareStatus = ref<'idle' | 'copied'>('idle')
const readProgress = ref(0)
const showShortcuts = ref(false)

const FONT_OPTS = [
  { key: 'sm', value: 13, btn: 11 },
  { key: 'md', value: 15, btn: 13 },
  { key: 'lg', value: 17, btn: 15 },
] as const
type FontKey = typeof FONT_OPTS[number]['key']

const fontSize = ref<FontKey>(
  (localStorage.getItem('reader-font-size') as FontKey) || 'md'
)
function setFontSize(k: FontKey) {
  fontSize.value = k
  localStorage.setItem('reader-font-size', k)
}
const fontSizePx = computed(() => {
  const opt = FONT_OPTS.find((o) => o.key === fontSize.value)
  return (opt?.value ?? 15) + 'px'
})

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

async function shareArticle() {
  if (!detail.value) return
  const url = `${window.location.origin}/news/detail/${detail.value.id}`
  const title = detail.value.titleZh || detail.value.title
  const text = detail.value.descriptionZh || detail.value.description || ''
  if (navigator.share) {
    try { await navigator.share({ title, text, url }) } catch { /* 用户取消 */ }
    return
  }
  try {
    await navigator.clipboard.writeText(url)
    shareStatus.value = 'copied'
    setTimeout(() => shareStatus.value = 'idle', 1500)
  } catch { /* ignore */ }
}

function updateProgress() {
  const scrollEl = document.querySelector('.page-wrap') as HTMLElement | null
  const target = scrollEl && scrollEl.scrollHeight > scrollEl.clientHeight
    ? scrollEl
    : document.scrollingElement as HTMLElement || document.documentElement
  const scrollTop = target.scrollTop
  const docHeight = target.scrollHeight - target.clientHeight
  readProgress.value = docHeight > 0 ? Math.min(100, Math.max(0, (scrollTop / docHeight) * 100)) : 0
}

function getScrollTarget(): HTMLElement {
  const scrollEl = document.querySelector('.page-wrap') as HTMLElement | null
  if (scrollEl && scrollEl.scrollHeight > scrollEl.clientHeight) return scrollEl
  return (document.scrollingElement as HTMLElement) || document.documentElement
}

function onKeydown(e: KeyboardEvent) {
  const t = e.target as HTMLElement
  if (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable) return
  if (e.metaKey || e.ctrlKey || e.altKey) return

  switch (e.key.toLowerCase()) {
    case 'j':
      e.preventDefault()
      getScrollTarget().scrollBy({ top: getScrollTarget().clientHeight * 0.6, behavior: 'smooth' })
      break
    case 'k':
      e.preventDefault()
      getScrollTarget().scrollBy({ top: -getScrollTarget().clientHeight * 0.6, behavior: 'smooth' })
      break
    case 'f':
      if (detail.value && !favLoading.value) { e.preventDefault(); toggleFav() }
      break
    case 'escape':
      if (showShortcuts.value) { showShortcuts.value = false }
      else { router.back() }
      break
    case '?':
      e.preventDefault()
      showShortcuts.value = !showShortcuts.value
      break
  }
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

onMounted(() => {
  loadDetail()
  window.addEventListener('scroll', updateProgress, true)
  window.addEventListener('resize', updateProgress)
  window.addEventListener('keydown', onKeydown)
  updateProgress()
})
watch(() => route.params.id, () => {
  loadDetail()
  setTimeout(updateProgress, 100)
})
onUnmounted(() => {
  window.removeEventListener('scroll', updateProgress, true)
  window.removeEventListener('resize', updateProgress)
  window.removeEventListener('keydown', onKeydown)
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
      <button class="share-btn" :class="{ copied: shareStatus === 'copied' }"
        :title="shareStatus === 'copied' ? '已复制链接' : '分享'" @click="shareArticle">
        <svg v-if="shareStatus === 'copied'" width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M5 10L9 14L15 6" stroke="var(--brand)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <svg v-else width="20" height="20" viewBox="0 0 22 22" fill="none">
          <circle cx="6" cy="11" r="2.4" stroke="currentColor" stroke-width="1.6"/>
          <circle cx="16" cy="5.5" r="2.4" stroke="currentColor" stroke-width="1.6"/>
          <circle cx="16" cy="16.5" r="2.4" stroke="currentColor" stroke-width="1.6"/>
          <path d="M8.1 10L13.9 6.6M8.1 12L13.9 15.4" stroke="currentColor" stroke-width="1.6"/>
        </svg>
      </button>
      <button :class="['fav-btn', { active: isFav }]" :disabled="favLoading" @click="toggleFav">
        <svg width="20" height="20" viewBox="0 0 22 22" fill="none">
          <path d="M11 19L3.5 11.5C2 10 2 7.5 3.5 6C5 4.5 7.5 4.5 9 6L11 8L13 6C14.5 4.5 17 4.5 18.5 6C20 7.5 20 10 18.5 11.5L11 19Z"
            :fill="isFav ? 'var(--brand)' : 'none'"
            :stroke="isFav ? 'var(--brand)' : 'var(--text-secondary)'"
            stroke-width="1.8" stroke-linejoin="round"/>
        </svg>
      </button>
      <div class="read-progress-track">
        <div class="read-progress-bar" :style="{ width: readProgress + '%' }"></div>
      </div>
    </header>

    <div v-if="loading" class="state-wrap"><div class="spinner"></div></div>

    <div v-else-if="error" class="state-wrap err-state">
      <p>{{ error }}</p>
      <button class="retry-btn" @click="router.back()">返回</button>
    </div>

    <article v-else-if="detail" class="content">      <div v-if="detail.image" class="cover-wrap">
        <img :src="detail.image" class="cover-img" />
        <div class="cover-fade"></div>
      </div>

      <div class="article-body" :style="{ '--reader-fs': fontSizePx }">
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

        <div class="reader-tools" role="group" aria-label="字号">
          <span class="tools-label">字号</span>
          <div class="size-btns">
            <button v-for="opt in FONT_OPTS" :key="opt.key"
              :class="['size-btn', { active: fontSize === opt.key }]"
              :style="{ fontSize: opt.btn + 'px', lineHeight: 1 }"
              :aria-pressed="fontSize === opt.key"
              @click="setFontSize(opt.key)">A</button>
          </div>
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

    <button class="kbd-toggle" :class="{ hidden: showShortcuts }"
      title="快捷键 (?) " @click="showShortcuts = true">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <rect x="2" y="6" width="20" height="12" rx="2"/>
        <path d="M6 10h.01M10 10h.01M14 10h.01M18 10h.01M6 14h12"/>
      </svg>
    </button>
    <div v-if="showShortcuts" class="kbd-panel" @click.self="showShortcuts = false">
      <div class="kbd-card">
        <div class="kbd-head">
          <span class="kbd-title">键盘快捷键</span>
          <button class="kbd-close" @click="showShortcuts = false">×</button>
        </div>
        <ul class="kbd-list">
          <li><kbd>J</kbd><span>向下滚动</span></li>
          <li><kbd>K</kbd><span>向上滚动</span></li>
          <li><kbd>F</kbd><span>收藏 / 取消</span></li>
          <li><kbd>Esc</kbd><span>返回</span></li>
          <li><kbd>?</kbd><span>显示 / 隐藏帮助</span></li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.detail-page { min-height: 100%; background: var(--bg); width: 100%; }

.top-bar {
  position: sticky; top: 0; z-index: 10; height: 52px;
  background: color-mix(in srgb, var(--bg) 95%, transparent);
  backdrop-filter: blur(16px);
  display: flex; align-items: center; padding: 0 12px;
  border-bottom: 1px solid var(--border); box-shadow: var(--shadow-sm);
}
.read-progress-track {
  position: absolute; left: 0; right: 0; bottom: -1px;
  height: 2px; background: rgba(200,134,10,0.08); overflow: hidden;
}
.read-progress-bar {
  height: 100%; background: var(--brand);
  transition: width 0.1s linear;
}
.back-btn { color: var(--text-primary); padding: 6px; display: flex; align-items: center; margin-right: 4px; }
.top-label {
  flex: 1; font-family: 'JetBrains Mono', monospace;
  font-size: 11px; font-weight: 500; color: var(--text-muted); letter-spacing: 3px;
}
.fav-btn { padding: 6px; display: flex; align-items: center; transition: transform 0.2s; }
.fav-btn:active { transform: scale(0.85); }

.share-btn {
  padding: 6px; display: flex; align-items: center; color: var(--text-secondary);
  margin-right: 2px; transition: transform 0.2s, color 0.2s;
}
.share-btn:active { transform: scale(0.85); }
.share-btn.copied { color: var(--brand); }

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

.reader-tools {
  display: flex; align-items: center; gap: 12px;
  margin-bottom: 18px; padding: 8px 12px;
  background: var(--bg-elevated); border-radius: var(--radius-sm);
}
.tools-label {
  font-family: 'JetBrains Mono', monospace; font-size: 10px;
  font-weight: 500; letter-spacing: 2px; color: var(--text-muted);
}
.size-btns { display: flex; align-items: baseline; gap: 6px; }
.size-btn {
  width: 28px; height: 28px; display: inline-flex;
  align-items: center; justify-content: center;
  color: var(--text-secondary); border-radius: var(--radius-sm);
  transition: background 0.15s, color 0.15s;
}
.size-btn:hover { background: var(--bg-hover); }
.size-btn.active { background: var(--brand-dim); color: var(--brand); }

.article-text {
  font-size: var(--reader-fs, 15px); line-height: 1.8; color: var(--text-primary); letter-spacing: 0.3px;
}
.article-text :deep(p) { margin: 0 0 1em; }
.article-text :deep(p:last-child) { margin-bottom: 0; }
.article-text :deep(h2), .article-text :deep(h3) { font-family: 'Noto Serif SC', serif; font-size: 1.08em; font-weight: 700; margin: 1.4em 0 0.6em; color: var(--text-primary); }
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

.kbd-toggle {
  position: fixed; right: 16px; bottom: calc(var(--nav-h) + 16px);
  width: 38px; height: 38px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: var(--bg-card); color: var(--text-muted);
  box-shadow: var(--shadow-md); border: 1px solid var(--border);
  transition: color 0.15s, transform 0.15s, opacity 0.2s;
  z-index: 50;
}
.kbd-toggle:hover { color: var(--brand); transform: scale(1.05); }
.kbd-toggle.hidden { opacity: 0; pointer-events: none; transform: scale(0.8); }

.kbd-panel {
  position: fixed; inset: 0; z-index: 200;
  background: rgba(26,22,18,0.25); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; padding: 20px;
}
.kbd-card {
  width: 100%; max-width: 320px; background: var(--bg-card);
  border-radius: var(--radius); box-shadow: var(--shadow-md);
  padding: 18px 20px;
}
.kbd-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.kbd-title {
  font-family: 'Libre Baskerville', serif; font-size: 15px;
  font-weight: 700; color: var(--text-primary);
}
.kbd-close { font-size: 22px; color: var(--text-muted); width: 28px; height: 28px; line-height: 1; }
.kbd-list { list-style: none; display: flex; flex-direction: column; gap: 10px; }
.kbd-list li { display: flex; align-items: center; justify-content: space-between; gap: 16px; font-size: 13px; color: var(--text-secondary); }
.kbd-list kbd {
  font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 600;
  background: var(--bg-elevated); border: 1px solid var(--border);
  border-bottom-width: 2px; border-radius: 4px; padding: 3px 8px; color: var(--text-primary);
  min-width: 32px; text-align: center;
}

@media (min-width: 768px) {
  .detail-page { min-height: 100%; }
  .content { max-width: 960px; margin: 0 auto; }
  .cover-img { max-height: 420px; }
  .article-body { padding: 32px 40px 8px; }
  .article-title { font-size: 26px; }
  .related-section { padding: 0 40px 24px; }
  .kbd-toggle { bottom: 24px; right: 24px; }
}

@media (min-width: 1200px) {
  .top-bar { padding: 0 28px; }
  .content {
    max-width: 1180px;
    display: grid;
    grid-template-columns: minmax(0, 760px) 340px;
    column-gap: 40px;
    align-items: start;
    padding: 28px;
  }
  .cover-wrap {
    grid-column: 1;
    border: 1px solid var(--border);
    border-radius: var(--radius);
  }
  .article-body {
    grid-column: 1;
    padding: 28px 0 8px;
  }
  .article-title { font-size: 30px; }
  .related-section {
    grid-column: 2;
    grid-row: 1 / span 2;
    margin-top: 0;
    padding: 0;
    border-top: none;
    position: sticky;
    top: 76px;
  }
}
</style>
