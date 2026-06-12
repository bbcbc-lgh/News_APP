<script setup lang="ts">
import { computed } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const showNav = computed(() => auth.isLoggedIn && !route.meta.public)
</script>

<template>
  <div id="app">
    <div class="page-wrap">
      <RouterView />
    </div>
    <nav v-if="showNav" class="bottom-nav">
      <RouterLink to="/news" class="nav-item" active-class="active">
        <span class="nav-icon">📰</span>
        <span class="nav-label">头条</span>
      </RouterLink>
      <RouterLink to="/profile" class="nav-item" active-class="active">
        <span class="nav-icon">👤</span>
        <span class="nav-label">我的</span>
      </RouterLink>
    </nav>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700;900&family=Noto+Sans+SC:wght@400;500;700&display=swap');

:root {
  --brand: #E8420A;
  --brand-dim: rgba(232,66,10,0.10);
  --bg: #F5F3EF;
  --bg-card: #FEFCFA;
  --text-primary: #1A1714;
  --text-secondary: #6B6560;
  --text-muted: #A09B96;
  --border: #E8E4DE;
  --border-strong: #CCC7BE;
  --shadow-sm: 0 1px 3px rgba(26,23,20,0.06);
  --shadow-md: 0 4px 16px rgba(26,23,20,0.10);
  --radius: 12px;
  --radius-sm: 8px;
  --nav-h: 58px;
}

*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

html { -webkit-text-size-adjust: 100%; }

body {
  font-family: 'Noto Sans SC', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  background: var(--bg);
  color: var(--text-primary);
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}

#app { min-height: 100vh; display: flex; flex-direction: column; }

.page-wrap {
  flex: 1;
  max-width: 480px;
  width: 100%;
  margin: 0 auto;
  background: var(--bg);
  min-height: 100vh;
  padding-bottom: calc(var(--nav-h) + 4px);
}

.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 480px;
  height: var(--nav-h);
  background: rgba(254,252,250,0.95);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-top: 1px solid var(--border);
  display: flex;
  z-index: 100;
}

.nav-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  text-decoration: none;
  color: var(--text-muted);
  transition: color 0.18s;
}
.nav-item.active { color: var(--brand); }
.nav-icon { font-size: 20px; line-height: 1; }
.nav-label { font-size: 10px; font-weight: 500; letter-spacing: 0.3px; }

a { text-decoration: none; color: inherit; }
button { cursor: pointer; border: none; outline: none; background: none; font-family: inherit; }
input, textarea, select { outline: none; font-family: inherit; }
</style>
