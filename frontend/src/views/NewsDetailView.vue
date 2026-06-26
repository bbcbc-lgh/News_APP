<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { newsApi, type NewsDetail } from '@/api/news'
import { favoriteApi } from '@/api/favorite'
import { queueApi } from '@/api/queue'
import { readingApi } from '@/api/readingBehavior'
import { historyApi } from '@/api/history'
import { readingProgressApi } from '@/api/readingProgress'
import { voteApi, type VoteResult } from '@/api/vote'
import { commentApi, type CommentItem } from '@/api/comment'
import { useAuthStore } from '@/stores/authStore'
import { useNewsStore } from '@/stores/newsStore'
import { sourceMeta } from '@/utils/sourceMeta'

const route = useRoute()
const router = useRouter()

const detail = ref<NewsDetail | null>(null)
const isFav = ref(false)
const isInQueue = ref(false)
const loading = ref(true)
const favLoading = ref(false)
const queueLoading = ref(false)
const error = ref('')
const shareStatus = ref<'idle' | 'copied'>('idle')
const readProgress = ref(0)
const showShortcuts = ref(false)
const upvotes = ref(0)
const downvotes = ref(0)
const userVote = ref<number | null>(null)
const voteLoading = ref(false)
const authStore = useAuthStore()
const newsStore = useNewsStore()

// 触控手势：左滑 = 下一篇，右滑 = 返回/上一篇
let touchStartX = 0
let touchStartY = 0

function onTouchStart(e: TouchEvent) {
  touchStartX = e.changedTouches[0].screenX
  touchStartY = e.changedTouches[0].screenY
}

function onTouchEnd(e: TouchEvent) {
  const dx = e.changedTouches[0].screenX - touchStartX
  const dy = e.changedTouches[0].screenY - touchStartY
  // 水平滑动幅度要大于垂直，且超过阈值 60px
  if (Math.abs(dx) < 60 || Math.abs(dx) < Math.abs(dy) * 1.5) return
  if (!detail.value) return
  const list = newsStore.newsList
  const idx = list.findIndex(n => n.id === detail.value!.id)
  if (dx < 0) {
    // 左滑 = 下一篇
    const next = idx >= 0 && idx < list.length - 1 ? list[idx + 1] : null
    if (next) router.push(`/news/detail/${next.id}`)
  } else {
    // 右滑 = 上一篇 / 返回
    if (idx > 0) router.push(`/news/detail/${list[idx - 1].id}`)
    else router.back()
  }
}

// 评论
const comments = ref<CommentItem[]>([])
const commentTotal = ref(0)
const commentHasMore = ref(false)
const commentPage = ref(1)
const commentLoading = ref(false)
const commentInput = ref('')
const commentSubmitting = ref(false)
const replyTo = ref<CommentItem | null>(null)

async function loadComments(reset = false) {
  if (!detail.value) return
  if (reset) { commentPage.value = 1; comments.value = [] }
  commentLoading.value = true
  try {
    const res = await commentApi.list(detail.value.id, commentPage.value)
    if (reset) { comments.value = res.list }
    else { comments.value.push(...res.list) }
    commentTotal.value = res.total
    commentHasMore.value = res.hasMore
  } finally { commentLoading.value = false }
}

async function submitComment() {
  if (!detail.value || !commentInput.value.trim() || commentSubmitting.value) return
  commentSubmitting.value = true
  try {
    const item = await commentApi.create(detail.value.id, commentInput.value.trim(), replyTo.value?.id)
    comments.value.unshift(item)
    commentTotal.value++
    commentInput.value = ''
    replyTo.value = null
  } catch { /* 静默 */ } finally { commentSubmitting.value = false }
}

async function removeComment(commentId: number, newsId: number) {
  await commentApi.remove(commentId)
  comments.value = comments.value.filter(c => c.id !== commentId)
  commentTotal.value = Math.max(0, commentTotal.value - 1)
}

function loadMoreComments() {
  commentPage.value++
  loadComments()
}

function formatCommentTime(dateStr: string): string {
  const d = new Date(dateStr)
  const now = Date.now()
  const diff = now - d.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

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

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}
function formatViews(v: number): string {
  const count = v >= 10000 ? `${(v / 10000).toFixed(1)}万` : String(v)
  return `${count} reads`
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

function cleanArticleText(raw: string): string {
  return raw
    .replace(/^这是一篇[^。\n]{0,60}。我为您翻译如下[:：]\s*/i, '')
    .replace(/^这是一篇[^。\n]{0,60}的翻译[:：]\s*/i, '')
    .replace(/^这是一篇[^：:\n]{0,80}翻译[:：]\s*/i, '')
    .replace(/^我为您翻译如下[:：]\s*/i, '')
    .replace(/^以下是(?:这篇|该)?[^。\n]{0,40}的?中文翻译[:：]\s*/i, '')
    .replace(/^翻译如下[:：]\s*/i, '')
    .trim()
}

function isBadArticleText(raw: string): boolean {
  const text = raw.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()
  if (!text) return true
  const normalized = text.toLowerCase().replace(/[\s>：:。.!！-]+/g, '')
  if (['点击查看原文', '查看原文', '阅读全文', 'readmore', 'continuereading'].includes(normalized)) return true
  return [
    'i appreciate you sharing',
    'i need to be straightforward',
    'copyrighted',
    'full article from a blog',
    'not a news article',
    'could you paste',
    'could you share',
    'i\'m ready to help',
    '我注意到你提供的内容',
    '请确认你是否想让我翻译',
    '不是新闻文章',
    '我准备好了',
    '没有看到需要翻译',
    '请提供你想翻译',
    '我无法完整翻译',
    '不能直接翻译',
    '受版权保护',
  ].some((pattern) => text.toLowerCase().includes(pattern.toLowerCase()))
}

const articleContent = computed(() => {
  const d = detail.value
  if (!d) return ''
  for (const raw of [d.contentZh, d.descriptionZh, d.content, d.description]) {
    const cleaned = cleanArticleText(raw || '')
    if (cleaned && !isBadArticleText(cleaned)) return cleaned
  }
  return ''
})

async function castVote(value: number) {
  if (!detail.value || voteLoading.value) return
  voteLoading.value = true
  try {
    // 再次点同一方向 = 撤销
    const newValue = userVote.value === value ? 0 : value
    const res = await voteApi.cast(detail.value.id, newValue)
    upvotes.value = res.upvotes
    downvotes.value = res.downvotes
    userVote.value = res.userVote
  } catch { /* 未登录静默失败 */ } finally { voteLoading.value = false }
}

async function toggleFav() {
  if (!detail.value) return
  favLoading.value = true
  try {
    if (isFav.value) { await favoriteApi.remove(detail.value.id) }
    else {
      await favoriteApi.add(detail.value.id)
      readingApi.report(detail.value.id, 'favorite').catch(() => {})
    }
    isFav.value = !isFav.value
  } finally { favLoading.value = false }
}

async function toggleQueue() {
  if (!detail.value || queueLoading.value) return
  queueLoading.value = true
  try {
    if (isInQueue.value) {
      await queueApi.remove(detail.value.id)
      isInQueue.value = false
    } else {
      await queueApi.add(detail.value.id)
      isInQueue.value = true
    }
  } finally { queueLoading.value = false }
}

async function shareArticle() {
  if (!detail.value) return
  const url = `${window.location.origin}/news/detail/${detail.value.id}`
  const title = detail.value.titleZh || detail.value.title
  const text = detail.value.descriptionZh || detail.value.description || ''
  if (navigator.share) {
    try {
      await navigator.share({ title, text, url })
      readingApi.report(detail.value.id, 'share').catch(() => {})
    } catch { /* 用户取消 */ }
    return
  }
  try {
    await navigator.clipboard.writeText(url)
    shareStatus.value = 'copied'
    pendingTimers.push(setTimeout(() => shareStatus.value = 'idle', 1500))
    readingApi.report(detail.value.id, 'share').catch(() => {})
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
  checkComplete()
}

// 阅读行为采集
let behaviorTimer: ReturnType<typeof setInterval> | null = null
let lastReportTime = 0
let completedReported = false

// 阅读进度持久化
let progressTimer: ReturnType<typeof setInterval> | null = null
let lastSavedPosition = -1
let pendingTimers: ReturnType<typeof setTimeout>[] = []

function startBehaviorTracking(newsId: number) {
  stopBehaviorTracking()
  lastReportTime = Date.now()
  completedReported = false
  readingApi.report(newsId, 'view', 0).catch(() => {})
  behaviorTimer = setInterval(() => {
    if (!detail.value) return
    const inc = Math.floor((Date.now() - lastReportTime) / 1000)
    lastReportTime = Date.now()
    if (inc > 0) readingApi.report(detail.value.id, 'view', inc).catch(() => {})
  }, 30000)
}

function stopBehaviorTracking() {
  if (behaviorTimer) { clearInterval(behaviorTimer); behaviorTimer = null }
}

function reportFinalDuration() {
  if (!detail.value) return
  const inc = Math.floor((Date.now() - lastReportTime) / 1000)
  if (inc > 0) readingApi.report(detail.value.id, 'view', inc).catch(() => {})
  lastReportTime = Date.now()
}

function checkComplete() {
  if (!detail.value || completedReported) return
  if (readProgress.value >= 80) {
    completedReported = true
    readingApi.report(detail.value.id, 'complete').catch(() => {})
  }
}

function getScrollTarget(): HTMLElement {
  const scrollEl = document.querySelector('.page-wrap') as HTMLElement | null
  if (scrollEl && scrollEl.scrollHeight > scrollEl.clientHeight) return scrollEl
  return (document.scrollingElement as HTMLElement) || document.documentElement
}

function saveProgress() {
  if (!detail.value) return
  const target = getScrollTarget()
  const pos = target.scrollTop
  if (Math.abs(pos - lastSavedPosition) < 50) return
  lastSavedPosition = pos
  const docHeight = target.scrollHeight - target.clientHeight
  const prog = docHeight > 0 ? Math.min(100, Math.round((pos / docHeight) * 100)) : 0
  readingProgressApi.save(detail.value.id, prog, pos).catch(() => {})
}

function startProgressTracking() {
  stopProgressTracking()
  lastSavedPosition = -1
  progressTimer = setInterval(saveProgress, 15000)
}

function stopProgressTracking() {
  if (progressTimer) { clearInterval(progressTimer); progressTimer = null }
}

async function restoreProgress(newsId: number) {
  try {
    const res = await readingProgressApi.get(newsId)
    if (res.lastPosition > 100) {
      await nextTick()
      pendingTimers.push(setTimeout(() => {
        getScrollTarget().scrollTo({ top: res.lastPosition, behavior: 'instant' })
      }, 300))
    }
  } catch { /* 未登录时忽略 */ }
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
  isInQueue.value = false
  try {
    const [d, fav, queue, voteState] = await Promise.allSettled([
      newsApi.getDetail(id),
      favoriteApi.check(id),
      queueApi.check(id),
      voteApi.get(id),
    ])
    if (d.status === 'fulfilled') {
      detail.value = d.value
      upvotes.value = d.value.upvotes
      downvotes.value = d.value.downvotes
      historyApi.add(id).catch(() => {})
      startBehaviorTracking(id)
      restoreProgress(id)
      startProgressTracking()
      loadComments(true)
    } else { error.value = '加载失败' }
    if (fav.status === 'fulfilled') isFav.value = fav.value.isFavorite
    if (queue.status === 'fulfilled') isInQueue.value = queue.value.inQueue
    if (voteState.status === 'fulfilled') userVote.value = voteState.value.userVote
  } finally { loading.value = false }
}

onMounted(() => {
  loadDetail()
  window.addEventListener('scroll', updateProgress, true)
  window.addEventListener('resize', updateProgress)
  window.addEventListener('keydown', onKeydown)
  window.addEventListener('touchstart', onTouchStart, { passive: true })
  window.addEventListener('touchend', onTouchEnd, { passive: true })
  updateProgress()
})
watch(() => route.params.id, () => {
  reportFinalDuration()
  stopBehaviorTracking()
  saveProgress()
  stopProgressTracking()
  loadDetail()
  pendingTimers.push(setTimeout(updateProgress, 100))
})
onUnmounted(() => {
  window.removeEventListener('scroll', updateProgress, true)
  window.removeEventListener('resize', updateProgress)
  window.removeEventListener('keydown', onKeydown)
  window.removeEventListener('touchstart', onTouchStart)
  window.removeEventListener('touchend', onTouchEnd)
  reportFinalDuration()
  stopBehaviorTracking()
  saveProgress()
  stopProgressTracking()
  pendingTimers.forEach(t => clearTimeout(t))
  pendingTimers = []
})
</script>

<template>
  <div class="detail-page">
    <header class="top-bar">
      <button class="back-btn" aria-label="返回" @click="router.back()">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M13 4L7 10L13 16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <span class="top-label">ARTICLE</span>
      <button class="queue-btn" :class="{ active: isInQueue }" :disabled="queueLoading"
        aria-label="加入稍后阅读" :title="isInQueue ? '已加入稍后阅读' : '稍后阅读'" @click="toggleQueue">
        <svg width="20" height="20" viewBox="0 0 22 22" fill="none">
          <path d="M5 4h9l4 4v10a1 1 0 01-1 1H5a1 1 0 01-1-1V5a1 1 0 011-1z"
            :stroke="isInQueue ? 'var(--brand)' : 'currentColor'" stroke-width="1.6" stroke-linejoin="round"/>
          <path d="M14 4v4h4" :stroke="isInQueue ? 'var(--brand)' : 'currentColor'" stroke-width="1.6" stroke-linejoin="round"/>
          <path d="M8 13h6M8 16h4" :stroke="isInQueue ? 'var(--brand)' : 'currentColor'" stroke-width="1.6" stroke-linecap="round"/>
        </svg>
      </button>
      <button :class="['share-btn', { copied: shareStatus === 'copied' }]"
        aria-label="分享" :title="shareStatus === 'copied' ? '已复制链接' : '分享'" @click="shareArticle">
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
      <button :class="['vote-btn', { active: userVote === 1 }]" :disabled="voteLoading"
        aria-label="点赞" title="点赞" @click="castVote(1)">
        <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
          <path d="M10 4L4 12h4v4h4v-4h4L10 4Z" :fill="userVote === 1 ? 'var(--brand)' : 'none'"
            :stroke="userVote === 1 ? 'var(--brand)' : 'currentColor'" stroke-width="1.6" stroke-linejoin="round"/>
        </svg>
        <span v-if="upvotes > 0" class="vote-count">{{ upvotes }}</span>
      </button>
      <button :class="['vote-btn', 'vote-down', { active: userVote === -1 }]" :disabled="voteLoading"
        aria-label="踩" title="踩" @click="castVote(-1)">
        <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
          <path d="M10 16L4 8h4V4h4v4h4L10 16Z" :fill="userVote === -1 ? 'var(--text-secondary)' : 'none'"
            :stroke="userVote === -1 ? 'var(--text-secondary)' : 'currentColor'" stroke-width="1.6" stroke-linejoin="round"/>
        </svg>
        <span v-if="downvotes > 0" class="vote-count">{{ downvotes }}</span>
      </button>
      <button :class="['fav-btn', { active: isFav }]" :disabled="favLoading" aria-label="收藏" @click="toggleFav">
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
            <RouterLink v-if="detail.author" class="meta-author" :to="`/author/${encodeURIComponent(detail.author)}`">{{ detail.author }}</RouterLink>
            <span v-else class="meta-author">未知来源</span>
            <span class="meta-sep">·</span>
            <span>{{ formatDate(detail.publishTime) }}</span>
            <span class="meta-sep">·</span>
            <span>{{ formatViews(detail.views) }}</span>
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

        <div v-if="articleContent" class="article-text" v-html="renderContent(articleContent)"></div>
        <div v-else class="article-empty">
          <p>本站暂未收录可展示的正文内容。</p>
          <p>可通过下方链接阅读原文。</p>
        </div>

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

      <!-- 评论区 -->
      <div class="comment-section">
        <div class="comment-header">
          <span class="comment-eyebrow">COMMENTS</span>
          <span class="comment-count-badge">{{ commentTotal }}</span>
        </div>

        <!-- 输入框 -->
        <div v-if="authStore.isLoggedIn" class="comment-input-wrap">
          <div v-if="replyTo" class="reply-hint">
            回复 <strong>{{ replyTo.user.nickname }}</strong>
            <button class="reply-cancel" @click="replyTo = null">×</button>
          </div>
          <textarea
            v-model="commentInput"
            class="comment-textarea"
            :placeholder="replyTo ? '写下你的回复…' : '写下你的评论…'"
            rows="3"
            maxlength="1000"
            @keydown.ctrl.enter="submitComment"
          ></textarea>
          <div class="comment-input-footer">
            <span class="comment-char-count">{{ commentInput.length }}/1000</span>
            <button class="comment-submit-btn" :disabled="!commentInput.trim() || commentSubmitting" @click="submitComment">
              {{ commentSubmitting ? '发布中…' : '发布' }}
            </button>
          </div>
        </div>
        <div v-else class="comment-login-hint">
          <router-link to="/login" class="comment-login-link">登录后参与评论</router-link>
        </div>

        <!-- 评论列表 -->
        <div v-if="commentLoading && comments.length === 0" class="comment-loading">
          <div class="spinner"></div>
        </div>
        <div v-else-if="comments.length === 0" class="comment-empty">暂无评论，来说第一句话吧</div>
        <div v-else class="comment-list">
          <div v-for="c in comments" :key="c.id" class="comment-item" :class="{ 'comment-reply': c.parentId }">
            <img :src="c.user.avatar" class="comment-avatar" :alt="c.user.nickname" />
            <div class="comment-body">
              <div class="comment-meta">
                <span class="comment-author">{{ c.user.nickname }}</span>
                <span class="comment-time">{{ formatCommentTime(c.createdAt) }}</span>
              </div>
              <p class="comment-text">{{ c.content }}</p>
              <div class="comment-actions">
                <button v-if="authStore.isLoggedIn" class="comment-reply-btn" @click="replyTo = c">回复</button>
                <button v-if="authStore.userInfo?.id === c.user.id" class="comment-delete-btn"
                  @click="removeComment(c.id, detail!.id)">删除</button>
              </div>
            </div>
          </div>
          <button v-if="commentHasMore" class="comment-load-more" :disabled="commentLoading" @click="loadMoreComments">
            {{ commentLoading ? '加载中…' : '加载更多评论' }}
          </button>
        </div>
      </div>
    </article>
    <div style="height: 32px"></div>

    <button class="kbd-toggle" :class="{ hidden: showShortcuts }"
      aria-label="快捷键帮助" title="快捷键 (?) " @click="showShortcuts = true">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <rect x="2" y="6" width="20" height="12" rx="2"/>
        <path d="M6 10h.01M10 10h.01M14 10h.01M18 10h.01M6 14h12"/>
      </svg>
    </button>
    <div v-if="showShortcuts" class="kbd-panel" @click.self="showShortcuts = false">
      <div class="kbd-card">
        <div class="kbd-head">
          <span class="kbd-title">键盘快捷键</span>
          <button class="kbd-close" aria-label="关闭" @click="showShortcuts = false">×</button>
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

.queue-btn {
  padding: 6px; display: flex; align-items: center; color: var(--text-secondary);
  margin-right: 2px; transition: transform 0.2s, color 0.2s;
}
.queue-btn:active { transform: scale(0.85); }
.queue-btn.active { color: var(--brand); }

.share-btn {
  padding: 6px; display: flex; align-items: center; color: var(--text-secondary);
  margin-right: 2px; transition: transform 0.2s, color 0.2s;
}
.share-btn:active { transform: scale(0.85); }
.share-btn.copied { color: var(--brand); }

.vote-btn {
  padding: 4px 6px; display: flex; align-items: center; gap: 3px;
  color: var(--text-secondary); transition: transform 0.2s, color 0.2s;
}
.vote-btn:active { transform: scale(0.85); }
.vote-btn.active { color: var(--brand); }
.vote-btn.vote-down.active { color: var(--text-secondary); }
.vote-count { font-family: 'JetBrains Mono', monospace; font-size: 10px; }

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
.meta-author { color: var(--text-secondary) !important; font-weight: 500; text-decoration: none; }
.meta-author:hover { color: var(--accent) !important; text-decoration: underline; }
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
.article-empty {
  padding: 18px;
  border: 1px dashed var(--border-strong);
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  background: var(--bg-elevated);
  font-size: 14px;
  line-height: 1.7;
}
.article-empty p + p { margin-top: 4px; }

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
.related-text { flex: 1; font-size: 13px; color: var(--text-primary); line-height: 1.55; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

/* 评论区 */
.comment-section { padding: 0 18px 24px; border-top: 1px solid var(--border); }
.comment-header { display: flex; align-items: center; gap: 10px; padding: 16px 0 12px; }
.comment-eyebrow { font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 500; letter-spacing: 3px; color: var(--brand); }
.comment-count-badge {
  font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 600;
  background: var(--brand-dim); color: var(--brand); padding: 1px 7px; border-radius: 10px;
}

.comment-input-wrap { margin-bottom: 18px; }
.reply-hint {
  font-size: 12px; color: var(--text-muted); margin-bottom: 6px;
  display: flex; align-items: center; gap: 6px;
}
.reply-hint strong { color: var(--text-secondary); }
.reply-cancel { font-size: 14px; color: var(--text-muted); padding: 0 4px; line-height: 1; }
.comment-textarea {
  width: 100%; padding: 10px 12px; border: 1px solid var(--border);
  border-radius: var(--radius-sm); background: var(--bg-elevated);
  color: var(--text-primary); font-size: 14px; font-family: inherit;
  line-height: 1.6; resize: vertical; transition: border-color 0.15s;
  box-sizing: border-box;
}
.comment-textarea:focus { outline: none; border-color: var(--brand); }
.comment-input-footer { display: flex; align-items: center; justify-content: space-between; margin-top: 8px; }
.comment-char-count { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--text-muted); }
.comment-submit-btn {
  padding: 7px 20px; background: var(--brand); color: #fff;
  border-radius: 20px; font-size: 13px; font-weight: 600;
  transition: opacity 0.15s;
}
.comment-submit-btn:disabled { opacity: 0.45; cursor: not-allowed; }

.comment-login-hint { padding: 12px 0; font-size: 13px; color: var(--text-muted); }
.comment-login-link { color: var(--brand); border-bottom: 1px solid var(--brand); padding-bottom: 1px; }

.comment-loading { display: flex; justify-content: center; padding: 24px; }
.comment-empty { font-size: 13px; color: var(--text-muted); padding: 16px 0; text-align: center; }

.comment-list { display: flex; flex-direction: column; gap: 0; }
.comment-item {
  display: flex; gap: 10px; padding: 14px 0; border-bottom: 1px solid var(--border);
}
.comment-item:last-child { border-bottom: none; }
.comment-reply { padding-left: 20px; background: rgba(200,134,10,0.03); border-radius: var(--radius-sm); }
.comment-avatar { width: 32px; height: 32px; border-radius: 50%; object-fit: cover; flex-shrink: 0; }
.comment-body { flex: 1; min-width: 0; }
.comment-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.comment-author { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.comment-time { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--text-muted); }
.comment-text { font-size: 14px; color: var(--text-secondary); line-height: 1.6; white-space: pre-wrap; word-break: break-word; }
.comment-actions { display: flex; gap: 12px; margin-top: 6px; }
.comment-reply-btn { font-size: 12px; color: var(--text-muted); transition: color 0.15s; }
.comment-reply-btn:hover { color: var(--brand); }
.comment-delete-btn { font-size: 12px; color: var(--text-muted); transition: color 0.15s; }
.comment-delete-btn:hover { color: #C0364D; }
.comment-load-more {
  width: 100%; margin-top: 12px; padding: 10px; text-align: center;
  font-size: 13px; color: var(--brand); border: 1px solid var(--border);
  border-radius: var(--radius-sm); transition: background 0.15s;
}
.comment-load-more:hover { background: var(--brand-dim); }

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
    max-width: 1120px;
    grid-template-columns: minmax(0, 740px) 300px;
    column-gap: 36px;
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
  .article-title { font-size: 28px; }
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
