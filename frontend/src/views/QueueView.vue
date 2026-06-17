<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { queueApi, type QueueItem } from '@/api/queue'

const router = useRouter()
const queueList = ref<QueueItem[]>([])
const page = ref(1)
const hasMore = ref(true)
const loading = ref(false)

const SOURCE_META: Record<string, { label: string; color: string }> = {
  hackernews: { label: 'HN', color: 'var(--hn)' },
  openai: { label: 'OpenAI', color: 'var(--openai)' },
  google_ai: { label: 'Google AI', color: 'var(--google)' },
  mit: { label: 'MIT', color: 'var(--mit-fg)' },
}

function sourceMeta(source?: string | null) {
  return SOURCE_META[source || ''] || { label: 'AI', color: 'var(--brand)' }
}

function timeAgo(s: string): string {
  if (!s) return ''
  const d = Math.floor((Date.now() - new Date(s).getTime()) / 86400000)
  if (d === 0) return '今天'
  if (d === 1) return '昨天'
  return new Date(s).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function itemTopic(item: QueueItem): string {
  const text = `${item.title} ${item.title_zh || ''}`.toLowerCase()
  if (/open source|oss|开源/.test(text)) return 'OPEN'
  if (/model|gpt|gemini|claude|llm|模型/.test(text)) return 'MODEL'
  if (/funding|raises|融资|募资/.test(text)) return 'FUND'
  if (/policy|legal|law|监管|政策/.test(text)) return 'POLICY'
  return sourceMeta(item.source_platform).label
}

async function loadQueue(reset = false) {
  if (loading.value || (!hasMore.value && !reset)) return
  if (reset) { queueList.value = []; page.value = 1; hasMore.value = true }
  loading.value = true
  try {
    const res = await queueApi.getList(page.value)
    queueList.value = reset ? res.list : [...queueList.value, ...res.list]
    hasMore.value = res.hasMore
    page.value++
  } finally { loading.value = false }
}

async function removeItem(newsId: number) {
  await queueApi.remove(newsId)
  queueList.value = queueList.value.filter(q => q.id !== newsId)
}

async function clearAll() {
  if (!confirm('确定清空整个稍后阅读队列？')) return
  await queueApi.clear()
  queueList.value = []
}

onMounted(() => loadQueue(true))
</script>

<template>
  <div class="queue-page">
    <header class="top-bar">
      <button class="back-btn" @click="router.back()" aria-label="返回">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M13 4L7 10L13 16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <span class="top-title">稍后阅读</span>
      <button v-if="queueList.length" class="clear-btn" @click="clearAll">清空</button>
    </header>

    <div class="list-section">
      <div v-if="queueList.length" class="list-toolbar">
        <span class="list-count">{{ queueList.length }} items</span>
      </div>

      <div v-if="loading && !queueList.length" class="empty-state"><div class="mini-spinner"></div></div>
      <div v-else-if="!queueList.length" class="empty-state">
        <svg width="32" height="32" viewBox="0 0 22 22" fill="none" style="opacity:0.2">
          <path d="M5 4h9l4 4v10a1 1 0 01-1 1H5a1 1 0 01-1-1V5a1 1 0 011-1z" stroke="var(--text-muted)" stroke-width="1.5" stroke-linejoin="round"/>
          <path d="M14 4v4h4" stroke="var(--text-muted)" stroke-width="1.5" stroke-linejoin="round"/>
          <path d="M8 13h6M8 16h4" stroke="var(--text-muted)" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <p>队列是空的</p>
      </div>

      <div v-for="item in queueList" :key="item.id" class="list-item"
        @click="router.push(`/news/detail/${item.id}`)">
        <img v-if="item.image" :src="item.image" class="item-thumb" loading="lazy" />
        <div v-else class="item-thumb item-thumb--poster"
          :style="{ '--poster-color': sourceMeta(item.source_platform).color }">
          <span>{{ itemTopic(item) }}</span>
          <small>{{ sourceMeta(item.source_platform).label }}</small>
        </div>
        <div class="item-body">
          <p class="item-title">{{ item.title_zh || item.title }}</p>
          <div class="item-meta">
            <span>{{ item.author || '未知' }}</span><span class="sep">·</span><span>{{ timeAgo(item.queueTime) }}</span>
          </div>
        </div>
        <button class="del-btn" @click.stop="removeItem(item.id)" title="移出队列" aria-label="删除">
          <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
            <path d="M3 3L11 11M11 3L3 11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </button>
      </div>

      <button v-if="hasMore && queueList.length" class="load-more" :disabled="loading"
        @click="loadQueue()">{{ loading ? '加载中…' : '加载更多' }}</button>
    </div>
  </div>
</template>

<style scoped>
.queue-page { min-height: 100%; background: var(--bg); width: 100%; }

.top-bar {
  height: 52px; background: color-mix(in srgb, var(--bg) 95%, transparent);
  backdrop-filter: blur(16px);
  display: flex; align-items: center; padding: 0 12px;
  border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 10;
  box-shadow: var(--shadow-sm);
}
.back-btn { color: var(--text-primary); padding: 6px; display: flex; align-items: center; margin-right: 4px; }
.top-title {
  flex: 1; font-family: 'Libre Baskerville', 'Noto Serif SC', serif;
  font-size: 17px; font-weight: 700; color: var(--text-primary);
}
.clear-btn { font-size: 13px; color: var(--mit-fg); font-weight: 600; }

.list-section { padding: 0 10px; }
.list-toolbar { padding: 10px 4px 6px; }
.list-count {
  font-family: 'JetBrains Mono', monospace; font-size: 11px;
  color: var(--text-muted); letter-spacing: 0.5px;
}

.empty-state { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 56px 0; }
.empty-state p { font-size: 13px; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; letter-spacing: 1px; }
.mini-spinner { width: 22px; height: 22px; border: 2px solid var(--border); border-top-color: var(--brand); border-radius: 50%; animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg) } }

.list-item {
  background: var(--bg-card); border-radius: var(--radius); margin-bottom: 6px;
  padding: 12px; display: flex; align-items: flex-start; gap: 10px; cursor: pointer;
  border: 1px solid var(--border); transition: background 0.12s;
}
.list-item:active { background: var(--bg-hover); }
.item-thumb { width: 72px; height: 54px; border-radius: var(--radius-sm); object-fit: cover; flex-shrink: 0; border: 1px solid var(--border); }
.item-thumb--poster {
  display: flex; flex-direction: column; align-items: flex-start; justify-content: space-between;
  padding: 7px;
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--poster-color) 16%, transparent), transparent 58%),
    repeating-linear-gradient(45deg, rgba(26,22,18,0.035) 0 1px, transparent 1px 8px),
    var(--bg-elevated);
}
.item-thumb--poster span { font-family: 'JetBrains Mono', monospace; font-size: 9px; color: var(--poster-color); letter-spacing: 0.6px; }
.item-thumb--poster small { font-family: 'JetBrains Mono', monospace; font-size: 8px; color: var(--text-muted); letter-spacing: 0.8px; }
.item-body { flex: 1; min-width: 0; }
.item-title { font-size: 13px; font-weight: 600; color: var(--text-primary); line-height: 1.5; margin-bottom: 5px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.item-meta { display: flex; align-items: center; gap: 4px; }
.item-meta span { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--text-muted); }
.sep { color: var(--border-strong); }
.del-btn { color: var(--text-muted); padding: 4px; flex-shrink: 0; display: flex; align-items: center; transition: color 0.15s; }
.del-btn:active { color: var(--mit-fg); }

.load-more {
  width: 100%; padding: 12px; text-align: center;
  font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 500;
  letter-spacing: 1px; color: var(--brand); background: var(--bg-card);
  border-radius: var(--radius); margin: 6px 0 8px; border: 1px solid var(--border);
}
.load-more:disabled { color: var(--text-muted); }

@media (min-width: 768px) {
  .top-bar { padding: 0 24px; }
  .list-section {
    width: min(1180px, calc(100% - 48px));
    margin: 20px auto 0;
  }
}

@media (min-width: 1200px) {
  .list-section {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }
  .list-toolbar, .empty-state, .load-more {
    grid-column: 1 / -1;
  }
  .list-item { min-height: 96px; margin-bottom: 0; }
  .item-thumb { width: 96px; height: 72px; }
  .item-title { font-size: 14px; }
}
</style>
