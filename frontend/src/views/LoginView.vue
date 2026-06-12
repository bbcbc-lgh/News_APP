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
    <div class="auth-bg">
      <div class="bg-line" v-for="i in 6" :key="i"></div>
    </div>

    <div class="auth-top">
      <div class="masthead">
        <span class="masthead-zh">AI掘金头条</span>
        <span class="masthead-rule"></span>
        <span class="masthead-en">DAILY DIGEST</span>
      </div>
      <p class="tagline">洞见时代·掘金资讯</p>
    </div>

    <div class="auth-card">
      <div class="card-header">
        <h2>登录</h2>
        <span class="card-sub">欢迎回来</span>
      </div>

      <div class="field">
        <label>用户名</label>
        <input v-model="username" type="text" placeholder="请输入用户名" autocomplete="username" />
      </div>
      <div class="field">
        <label>密码</label>
        <input v-model="password" type="password" placeholder="请输入密码" @keyup.enter="submit" autocomplete="current-password" />
      </div>

      <p v-if="error" class="err-msg">{{ error }}</p>

      <button class="btn-submit" :class="{ loading }" :disabled="loading" @click="submit">
        <span v-if="!loading">登 录</span>
        <span v-else class="btn-spinner"></span>
      </button>

      <p class="switch-link">还没有账号？<RouterLink to="/register">立即注册 →</RouterLink></p>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  background: #1A1714;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 24px;
  position: relative;
  overflow: hidden;
}

.auth-bg {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-evenly;
  pointer-events: none;
}
.bg-line {
  width: 100%;
  height: 1px;
  background: rgba(255,255,255,0.04);
}

.auth-top {
  text-align: center;
  margin-bottom: 36px;
  position: relative;
  z-index: 1;
}

.masthead {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 10px;
}
.masthead-zh {
  font-family: 'Noto Serif SC', serif;
  font-size: 24px;
  font-weight: 900;
  color: #FEFCFA;
  letter-spacing: 2px;
}
.masthead-rule {
  width: 1px;
  height: 20px;
  background: rgba(255,255,255,0.25);
  display: inline-block;
}
.masthead-en {
  font-size: 11px;
  font-weight: 700;
  color: var(--brand);
  letter-spacing: 3px;
}
.tagline {
  font-size: 12px;
  color: rgba(255,255,255,0.35);
  letter-spacing: 2px;
}

.auth-card {
  width: 100%;
  max-width: 360px;
  background: #FEFCFA;
  border-radius: 16px;
  padding: 28px 24px 24px;
  position: relative;
  z-index: 1;
  box-shadow: 0 20px 60px rgba(0,0,0,0.4);
}

.card-header {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 22px;
}
h2 {
  font-family: 'Noto Serif SC', serif;
  font-size: 22px;
  font-weight: 900;
  color: var(--text-primary);
}
.card-sub {
  font-size: 13px;
  color: var(--text-muted);
}

.field {
  margin-bottom: 14px;
}
label {
  display: block;
  font-size: 12px;
  font-weight: 700;
  color: var(--text-secondary);
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}
input {
  width: 100%;
  padding: 12px 14px;
  background: var(--bg);
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 15px;
  color: var(--text-primary);
  transition: border-color 0.18s, background 0.18s;
}
input:focus {
  border-color: var(--brand);
  background: #fff;
}

.err-msg {
  font-size: 13px;
  color: #C0392B;
  background: rgba(192,57,43,0.08);
  border-radius: 6px;
  padding: 8px 12px;
  margin-bottom: 14px;
}

.btn-submit {
  width: 100%;
  padding: 13px;
  background: var(--brand);
  color: #fff;
  border-radius: var(--radius-sm);
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 2px;
  margin-top: 4px;
  margin-bottom: 18px;
  transition: opacity 0.18s, transform 0.12s;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 46px;
}
.btn-submit:not(:disabled):active { transform: scale(0.98); opacity: 0.9; }
.btn-submit:disabled { opacity: 0.55; }

.btn-spinner {
  width: 18px; height: 18px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg) } }

.switch-link {
  text-align: center;
  font-size: 13px;
  color: var(--text-muted);
}
.switch-link a {
  color: var(--brand);
  font-weight: 700;
}
</style>
