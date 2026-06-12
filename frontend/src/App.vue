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
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Mono:wght@400;500&family=Noto+Serif+SC:wght@400;600;700;900&family=Noto+Sans+SC:wght@400;500;700&display=swap');

:root {
  --brand: #F5A623;
  --brand-dim: rgba(245,166,35,0.12);
  --brand-glow: rgba(245,166,35,0.25);
  --bg: #0D1117;
  --bg-card: #161B22;
  --bg-elevated: #1C2128;
  --bg-hover: #21262D;
  --text-primary: #E6EDF3;
  --text-secondary: #8B949E;
  --text-muted: #484F58;
  --border: #21262D;
  --border-strong: #30363D;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.4);
  --shadow-md: 0 4px 20px rgba(0,0,0,0.5);
  --shadow-glow: 0 0 20px rgba(245,166,35,0.15);
  --radius: 10px;
  --radius-sm: 6px;
  --nav-h: 60px;

  /* source colors */
  --hn: #FF6600;
  --openai: #10A37F;
  --google: #4285F4;
  --mit: #A31F34;
  --mit-fg: #E05A6D;
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

/* scanline texture overlay */
body::before {
  content: '';
  position: fixed;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0,0,0,0.03) 2px,
    rgba(0,0,0,0.03) 4px
  );
  pointer-events: none;
  z-index: 9999;
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
  background: rgba(22,27,34,0.96);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid var(--border-strong);
  display: flex;
  z-index: 100;
}

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
.nav-label { font-size: 10px; font-weight: 500; letter-spacing: 0.5px; font-family: 'DM Mono', monospace; }

a { text-decoration: none; color: inherit; }
button { cursor: pointer; border: none; outline: none; background: none; font-family: inherit; }
input, textarea, select { outline: none; font-family: inherit; }
</style>
