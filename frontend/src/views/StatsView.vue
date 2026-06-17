<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { readingApi, type ReadingStats, type StatsPeriod } from '@/api/readingBehavior'

const router = useRouter()
const period = ref<StatsPeriod>('week')
const stats = ref<ReadingStats | null>(null)
const loading = ref(true)

const PERIODS: { key: StatsPeriod; label: string }[] = [
  { key: 'today', label: '今日' },
  { key: 'week',  label: '本周' },
  { key: 'month', label: '本月' },
  { key: 'all',   label: '全部' },
]

const SOURCE_META: Record<string, { label: string; color: string }> = {
  hackernews: { label: 'Hacker News', color: 'var(--hn)' },
  openai:     { label: 'OpenAI',      color: 'var(--openai)' },
  google_ai:  { label: 'Google AI',   color: 'var(--google)' },
  mit:        { label: 'MIT',         color: 'var(--mit-fg)' },
}

const sourceBreakdown = computed(() => {
  if (!stats.value) return []
  const entries = Object.entries(stats.value.bySource)
  const total = entries.reduce((s, [, c]) => s + c, 0) || 1
  return entries
    .filter(([, c]) => c > 0)
    .map(([k, c]) => ({
      key: k,
      meta: SOURCE_META[k] || { label: k, color: 'var(--brand)' },
      count: c,
      pct: Math.round((c / total) * 100),
    }))
    .sort((a, b) => b.count - a.count)
})

function formatDuration(sec: number): string {
  if (sec < 60) return `${sec}s`
  const m = Math.floor(sec / 60)
  if (m < 60) return `${m}m`
  const h = Math.floor(m / 60)
  return `${h}h ${m % 60}m`
}

async function loadStats() {
  loading.value = true
  try { stats.value = await readingApi.getStats(period.value) }
  finally { loading.value = false }
}

function setPeriod(p: StatsPeriod) {
  if (period.value === p) return
  period.value = p
  loadStats()
}

onMounted(loadStats)
</script>

<template>
  <div class="stats-page">
    <header class="top-bar">
      <button class="back-btn" @click="router.back()" aria-label="返回">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M13 4L7 10L13 16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <span class="top-title">阅读统计</span>
      <span class="top-spacer"></span>
    </header>

    <div class="period-bar">
      <button v-for="p in PERIODS" :key="p.key"
        :class="['period-btn', { active: period === p.key }]"
        @click="setPeriod(p.key)">{{ p.label }}</button>
    </div>

    <div v-if="loading" class="state-wrap"><div class="spinner"></div></div>

    <div v-else-if="stats" class="stats-content">
      <div class="cards-grid">
        <div class="stat-card">
          <span class="stat-label">阅读篇数</span>
          <span class="stat-value">{{ stats.distinctNews }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">阅读次数</span>
          <span class="stat-value">{{ stats.viewCount }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">完成阅读</span>
          <span class="stat-value">{{ stats.completeCount }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">阅读时长</span>
          <span class="stat-value mono">{{ formatDuration(stats.totalDurationSec) }}</span>
        </div>
      </div>

      <div class="breakdown-section">
        <h3 class="section-title">
          <span class="title-eyebrow">DISTRIBUTION</span>
          <span class="title-text">来源分布</span>
        </h3>
        <div v-if="sourceBreakdown.length" class="breakdown-list">
          <div v-for="s in sourceBreakdown" :key="s.key" class="bd-item">
            <div class="bd-head">
              <span class="bd-dot" :style="{ background: s.meta.color }"></span>
              <span class="bd-label">{{ s.meta.label }}</span>
              <span class="bd-count">{{ s.count }} 次 · {{ s.pct }}%</span>
            </div>
            <div class="bd-bar">
              <div class="bd-fill" :style="{ width: s.pct + '%', background: s.meta.color }"></div>
            </div>
          </div>
        </div>
        <div v-else class="empty">暂无阅读记录</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stats-page { min-height: 100%; background: var(--bg); width: 100%; }

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
.top-spacer { width: 32px; }

.period-bar {
  display: flex; gap: 4px; padding: 12px 12px 8px;
  background: var(--bg-card); border-bottom: 1px solid var(--border);
}
.period-btn {
  flex: 1; padding: 8px 0; font-size: 13px; font-weight: 600;
  color: var(--text-muted); background: transparent;
  border-radius: var(--radius-sm); transition: all 0.15s;
}
.period-btn:hover { color: var(--text-primary); background: var(--bg-hover); }
.period-btn.active { color: var(--brand); background: var(--brand-dim); }

.state-wrap { display: flex; justify-content: center; padding: 80px 20px; }
.spinner { width: 28px; height: 28px; border: 2px solid var(--border); border-top-color: var(--brand); border-radius: 50%; animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg) } }

.stats-content { padding: 16px 12px; }

.cards-grid {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;
  margin-bottom: 20px;
}
.stat-card {
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 18px 16px;
  display: flex; flex-direction: column; gap: 8px;
}
.stat-label {
  font-family: 'JetBrains Mono', monospace; font-size: 10px;
  font-weight: 500; color: var(--text-muted); letter-spacing: 1.5px;
}
.stat-value {
  font-family: 'Libre Baskerville', 'Noto Serif SC', serif;
  font-size: 28px; font-weight: 700; color: var(--text-primary);
  line-height: 1;
}
.stat-value.mono { font-family: 'JetBrains Mono', monospace; font-size: 22px; color: var(--brand); }

.breakdown-section {
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 16px;
}
.section-title { display: flex; flex-direction: column; gap: 2px; margin-bottom: 14px; }
.title-eyebrow {
  font-family: 'JetBrains Mono', monospace; font-size: 9px;
  font-weight: 500; letter-spacing: 2.5px; color: var(--brand);
}
.title-text {
  font-family: 'Libre Baskerville', 'Noto Serif SC', serif;
  font-size: 16px; font-weight: 700; color: var(--text-primary);
}
.breakdown-list { display: flex; flex-direction: column; gap: 12px; }
.bd-item { display: flex; flex-direction: column; gap: 6px; }
.bd-head { display: flex; align-items: center; gap: 8px; font-size: 12px; }
.bd-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.bd-label { color: var(--text-primary); font-weight: 600; flex: 1; }
.bd-count {
  font-family: 'JetBrains Mono', monospace; font-size: 10px;
  color: var(--text-muted); letter-spacing: 0.5px;
}
.bd-bar {
  height: 4px; background: var(--bg-elevated);
  border-radius: 2px; overflow: hidden;
}
.bd-fill { height: 100%; border-radius: 2px; transition: width 0.3s; }
.empty { padding: 32px 0; text-align: center; color: var(--text-muted); font-size: 13px; }

@media (min-width: 768px) {
  .top-bar { padding: 0 24px; }
  .stats-content {
    width: min(720px, calc(100% - 48px));
    margin: 20px auto 0;
  }
  .cards-grid { grid-template-columns: repeat(4, 1fr); }
}
</style>
