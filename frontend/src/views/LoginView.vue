<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const auth = useAuthStore()
const router = useRouter()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const sourceBadges = [
  { label: 'HN', color: 'var(--hn)', bg: 'rgba(224,93,0,0.08)', border: 'rgba(224,93,0,0.2)' },
  { label: 'OpenAI', color: 'var(--openai)', bg: 'rgba(13,138,106,0.08)', border: 'rgba(13,138,106,0.2)' },
  { label: 'Google AI', color: 'var(--google)', bg: 'rgba(26,115,232,0.08)', border: 'rgba(26,115,232,0.2)' },
  { label: 'Hugging Face', color: '#FF9D00', bg: 'rgba(255,157,0,0.10)', border: 'rgba(255,157,0,0.22)' },
  { label: 'arXiv AI', color: '#B31B1B', bg: 'rgba(179,27,27,0.10)', border: 'rgba(179,27,27,0.22)' },
  { label: 'TechCrunch AI', color: '#00A562', bg: 'rgba(0,165,98,0.10)', border: 'rgba(0,165,98,0.22)' },
  { label: 'MIT Tech', color: 'var(--mit-fg)', bg: 'rgba(155,28,46,0.08)', border: 'rgba(155,28,46,0.2)' },
  { label: 'InfoQ 中文', color: '#2563EB', bg: 'rgba(37,99,235,0.10)', border: 'rgba(37,99,235,0.22)' },
  { label: 'GitHub AI', color: '#57606A', bg: 'rgba(87,96,106,0.10)', border: 'rgba(87,96,106,0.22)' },
]

async function submit() {
  if (!username.value || !password.value) { error.value = '请填写用户名和密码'; return }
  loading.value = true
  error.value = ''
  try {
    await auth.login(username.value, password.value)
    router.push('/news')
  } catch (e) {
    error.value = e instanceof Error ? e.message : '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-bg"></div>
    <div class="auth-top">
      <h1 class="brand-name">Nexus</h1>
      <p class="brand-sub">NEXUS · DAILY DIGEST</p>
    </div>
    <div class="auth-card">
      <div class="card-eyebrow">SIGN IN</div>
      <h2 class="card-title">欢迎回来</h2>
      <div class="field">
        <label>USERNAME</label>
        <input v-model="username" type="text" placeholder="输入用户名" autocomplete="username" />
      </div>
      <div class="field">
        <label>PASSWORD</label>
        <input v-model="password" type="password" placeholder="输入密码" @keyup.enter="submit" autocomplete="current-password" />
      </div>
      <p v-if="error" class="err-msg">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" style="flex-shrink:0;margin-top:1px">
          <circle cx="7" cy="7" r="6" stroke="#C0364D" stroke-width="1.4"/>
          <path d="M7 4v4M7 9.5v.5" stroke="#C0364D" stroke-width="1.4" stroke-linecap="round"/>
        </svg>
        {{ error }}
      </p>
      <button class="btn-submit" :class="{ loading }" :disabled="loading" @click="submit">
        <span v-if="!loading">登 录</span>
        <span v-else class="btn-spinner"></span>
      </button>
      <p class="switch-link">还没有账号？<RouterLink to="/register">立即注册 →</RouterLink></p>
    </div>
    <div class="source-badges">
      <span
        v-for="badge in sourceBadges"
        :key="badge.label"
        class="badge"
        :style="{ color: badge.color, background: badge.bg, borderColor: badge.border }"
      >{{ badge.label }}</span>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100%;
  width: 100%;
  background: var(--bg);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 24px;
  position: relative;
  overflow: hidden;
  gap: 24px;
}
.auth-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 80% 50% at 50% 0%, rgba(200,134,10,0.06) 0%, transparent 70%),
    repeating-linear-gradient(0deg, transparent, transparent 39px, rgba(200,134,10,0.04) 39px, rgba(200,134,10,0.04) 40px),
    repeating-linear-gradient(90deg, transparent, transparent 39px, rgba(200,134,10,0.04) 39px, rgba(200,134,10,0.04) 40px);
  pointer-events: none;
}
.auth-top {
  text-align: center;
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.brand-name {
  font-family: 'Libre Baskerville', 'Noto Serif SC', serif;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 2px;
}
.brand-sub {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: var(--text-muted);
  letter-spacing: 3px;
}
.auth-card {
  width: 100%;
  max-width: 360px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 26px 24px 22px;
  position: relative;
  z-index: 1;
  box-shadow: var(--shadow-md);
}
.auth-card::before {
  content: '';
  position: absolute;
  top: 0; left: 24px; right: 24px; height: 2px;
  background: linear-gradient(90deg, transparent, var(--brand), transparent);
  border-radius: 2px;
}
.card-eyebrow {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px; font-weight: 500;
  letter-spacing: 1.8px; color: var(--brand); margin-bottom: 6px;
}
.card-title {
  font-family: 'Libre Baskerville', 'Noto Serif SC', serif;
  font-size: 22px; font-weight: 700;
  color: var(--text-primary); margin-bottom: 24px;
}
.field { margin-bottom: 16px; }
label {
  display: block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px; font-weight: 500;
  color: var(--text-muted); letter-spacing: 1.2px; margin-bottom: 7px;
}
input {
  width: 100%; padding: 11px 14px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 15px; color: var(--text-primary);
  transition: border-color 0.18s, box-shadow 0.18s;
}
input::placeholder { color: var(--text-muted); }
input:focus { border-color: var(--brand); box-shadow: 0 0 0 3px var(--brand-dim); }
.err-msg {
  display: flex; align-items: flex-start; gap: 7px;
  font-size: 13px; color: var(--mit-fg);
  background: rgba(192,54,77,0.06);
  border: 1px solid rgba(192,54,77,0.18);
  border-radius: var(--radius-sm);
  padding: 9px 12px; margin-bottom: 14px;
}
.btn-submit {
  width: 100%; padding: 13px;
  background: var(--brand); color: #fff;
  border-radius: var(--radius-sm);
  font-size: 14px; font-weight: 700; letter-spacing: 1.5px;
  margin-top: 4px; margin-bottom: 18px;
  transition: opacity 0.18s, transform 0.12s, box-shadow 0.18s;
  display: flex; align-items: center; justify-content: center; min-height: 46px;
}
.btn-submit:not(:disabled):hover { box-shadow: 0 4px 16px rgba(200,134,10,0.3); }
.btn-submit:not(:disabled):active { transform: scale(0.98); opacity: 0.9; }
.btn-submit:disabled { opacity: 0.45; }
.btn-spinner {
  width: 18px; height: 18px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%; animation: spin 0.6s linear infinite; display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg) } }
.switch-link { text-align: center; font-size: 13px; color: var(--text-muted); }
.switch-link a { color: var(--brand); font-weight: 700; }
.source-badges {
  display: flex; gap: 8px; position: relative; z-index: 1;
  flex-wrap: wrap; justify-content: center;
}
.badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px; font-weight: 500;
  padding: 3px 9px; border-radius: 4px; letter-spacing: 0.5px;
  border: 1px solid;
}
</style>
