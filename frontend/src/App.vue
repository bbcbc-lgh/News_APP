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
  <div class="app-shell">
    <nav v-if="showNav" class="sidebar">
      <div class="sidebar-logo">AI</div>
      <RouterLink to="/news" class="nav-item" active-class="active">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
          <rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>
        </svg>
        <span class="nav-label">头条</span>
      </RouterLink>
      <RouterLink to="/profile" class="nav-item" active-class="active">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
        </svg>
        <span class="nav-label">我的</span>
      </RouterLink>
    </nav>
    <div class="page-wrap">
      <RouterView />
    </div>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=JetBrains+Mono:wght@400;500&family=Noto+Serif+SC:wght@400;600;700;900&family=Noto+Sans+SC:wght@400;500;700&display=swap');

:root {
  --brand: #C8860A;
  --brand-dim: rgba(200,134,10,0.10);
  --brand-glow: rgba(200,134,10,0.18);
  --bg: #F7F4EF;
  --bg-card: #FFFFFF;
  --bg-elevated: #F0EDE8;
  --bg-hover: #EDE9E3;
  --text-primary: #1A1612;
  --text-secondary: #4A4540;
  --text-muted: #8C8580;
  --border: #E4DED5;
  --border-strong: #CFC9BF;
  --shadow-sm: 0 1px 3px rgba(26,22,18,0.06);
  --shadow-md: 0 4px 20px rgba(26,22,18,0.08);
  --shadow-glow: 0 0 20px rgba(200,134,10,0.12);
  --radius: 10px;
  --radius-sm: 6px;
  --nav-h: 60px;
  --sidebar-w: 72px;

  /* source colors */
  --hn: #E05D00;
  --openai: #0D8A6A;
  --google: #1A73E8;
  --mit: #9B1C2E;
  --mit-fg: #C0364D;
}

*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }

body {
  font-family: 'Noto Sans SC', 'PingFang SC', 'Hiragino Sans GB', sans-serif;
  background: var(--bg);
  color: var(--text-primary);
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}

body::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 128px;
  pointer-events: none;
  z-index: 9999;
  opacity: 0.4;
}

.app-shell {
  min-height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
}

.page-wrap {
  flex: 1;
  width: 100%;
  background: var(--bg);
  min-height: 100vh;
  padding-bottom: calc(var(--nav-h) + 4px);
}

/* Mobile bottom nav */
.sidebar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: var(--nav-h);
  background: rgba(247,244,239,0.96);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid var(--border);
  display: flex;
  z-index: 100;
}

.sidebar-logo { display: none; }

.nav-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  text-decoration: none;
  color: var(--text-muted);
  transition: color 0.2s;
  position: relative;
}
.nav-item::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%) scaleX(0);
  width: 24px;
  height: 2px;
  background: var(--brand);
  border-radius: 2px 2px 0 0;
  transition: transform 0.2s;
}
.nav-item.active { color: var(--brand); }
.nav-item.active::after { transform: translateX(-50%) scaleX(1); }
.nav-label { font-size: 10px; font-weight: 500; letter-spacing: 0.5px; font-family: 'JetBrains Mono', monospace; }

a { text-decoration: none; color: inherit; }
button { cursor: pointer; border: none; outline: none; background: none; font-family: inherit; }
input, textarea, select { outline: none; font-family: inherit; }

/* Desktop: sidebar layout */
@media (min-width: 768px) {
  .app-shell {
    flex-direction: row;
    height: 100vh;
    overflow: hidden;
  }

  .sidebar {
    position: static;
    width: var(--sidebar-w);
    height: 100vh;
    flex-direction: column;
    border-top: none;
    border-right: 1px solid var(--border);
    padding: 16px 0 20px;
    justify-content: flex-start;
    align-items: center;
    gap: 2px;
    flex-shrink: 0;
    background: rgba(247,244,239,0.98);
    backdrop-filter: blur(20px);
  }

  .sidebar-logo {
    display: flex;
    width: 36px; height: 36px;
    background: var(--brand); color: #fff;
    font-family: 'Libre Baskerville', serif; font-size: 12px; font-weight: 700;
    align-items: center; justify-content: center;
    border-radius: 7px; margin-bottom: 16px; flex-shrink: 0;
  }

  .nav-item {
    flex: none;
    width: 100%;
    height: 52px;
    padding: 0;
    border-radius: 0;
    gap: 5px;
  }

  .nav-item::after { display: none; }
  .nav-item.active {
    background: var(--brand-dim);
    color: var(--brand);
  }
  .nav-label {
    display: block;
    font-size: 9px;
    letter-spacing: 1px;
  }

  .page-wrap {
    flex: 1;
    min-width: 0;
    height: 100vh;
    overflow-y: auto;
    padding-bottom: 0;
  }
}
</style>
