<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { favoriteApi, type FavoriteItem } from '@/api/favorite'
import { historyApi, type HistoryItem } from '@/api/history'
import { userApi } from '@/api/user'

const auth = useAuthStore()
const router = useRouter()

const tab = ref<'fav' | 'history'>('fav')
const editMode = ref(false)
const pwdMode = ref(false)

const editForm = ref({ nickname: '', bio: '', gender: 'unknown' as 'male' | 'female' | 'unknown' })
const overlayMousedownTarget = ref<EventTarget | null>(null)
const pwdForm = ref({ oldPassword: '', newPassword: '', confirm: '' })
const formErr = ref('')
const saving = ref(false)

const favList = ref<FavoriteItem[]>([])
const histList = ref<HistoryItem[]>([])
const favPage = ref(1)
const histPage = ref(1)
const favMore = ref(true)
const histMore = ref(true)
const listLoading = ref(false)

function timeAgo(s: string): string {
  if (!s) return ''
  const d = Math.floor((Date.now() - new Date(s).getTime()) / 86400000)
  if (d === 0) return '今天'
  if (d === 1) return '昨天'
  return new Date(s).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

function avatarText() {
  const u = auth.userInfo
  if (!u) return '?'
  return (u.nickname || u.username || '?').charAt(0).toUpperCase()
}

function onOverlayMousedown(e: MouseEvent) {
  overlayMousedownTarget.value = e.target
}
function onOverlayClick(e: MouseEvent, close: () => void) {
  if (overlayMousedownTarget.value === e.currentTarget && e.target === e.currentTarget) {
    close()
  }
  overlayMousedownTarget.value = null
}

function openEdit() {
  if (!auth.userInfo) return
  editForm.value = {
    nickname: auth.userInfo.nickname || '',
    bio: auth.userInfo.bio || '',
    gender: (auth.userInfo.gender as any) || 'unknown'
  }
  editMode.value = true
  formErr.value = ''
}

async function saveEdit() {
  saving.value = true; formErr.value = ''
  try {
    await auth.updateInfo({
      nickname: editForm.value.nickname || undefined,
      bio: editForm.value.bio || undefined,
      gender: editForm.value.gender
    })
    editMode.value = false
  } catch (e) {
    formErr.value = e instanceof Error ? e.message : '保存失败'
  } finally { saving.value = false }
}

async function savePwd() {
  if (pwdForm.value.newPassword !== pwdForm.value.confirm) { formErr.value = '两次密码不一致'; return }
  if (pwdForm.value.newPassword.length < 6) { formErr.value = '新密码至少6位'; return }
  saving.value = true; formErr.value = ''
  try {
    await userApi.changePassword(pwdForm.value.oldPassword, pwdForm.value.newPassword)
    pwdMode.value = false
    pwdForm.value = { oldPassword: '', newPassword: '', confirm: '' }
  } catch (e) {
    formErr.value = e instanceof Error ? e.message : '修改失败'
  } finally { saving.value = false }
}

async function loadFav(reset = false) {
  if (listLoading.value || (!favMore.value && !reset)) return
  if (reset) { favList.value = []; favPage.value = 1; favMore.value = true }
  listLoading.value = true
  try {
    const res = await favoriteApi.getList(favPage.value)
    favList.value = reset ? res.list : [...favList.value, ...res.list]
    favMore.value = res.hasMore; favPage.value++
  } finally { listLoading.value = false }
}

async function loadHist(reset = false) {
  if (listLoading.value || (!histMore.value && !reset)) return
  if (reset) { histList.value = []; histPage.value = 1; histMore.value = true }
  listLoading.value = true
  try {
    const res = await historyApi.getList(histPage.value)
    histList.value = reset ? res.list : [...histList.value, ...res.list]
    histMore.value = res.hasMore; histPage.value++
  } finally { listLoading.value = false }
}

async function removeFav(newsId: number) {
  await favoriteApi.remove(newsId)
  favList.value = favList.value.filter(f => f.id !== newsId)
}

async function clearFav() {
  if (!confirm('确定清空所有收藏？')) return
  await favoriteApi.clear()
  favList.value = []
}

async function removeHist(historyId: number) {
  await historyApi.deleteOne(historyId)
  histList.value = histList.value.filter(h => h.historyId !== historyId)
}

async function clearHist() {
  if (!confirm('确定清空所有历史？')) return
  await historyApi.clear()
  histList.value = []
}

function switchTab(t: 'fav' | 'history') {
  tab.value = t
  if (t === 'fav' && favList.value.length === 0) loadFav(true)
  if (t === 'history' && histList.value.length === 0) loadHist(true)
}

function logout() {
  auth.logout()
  router.push('/login')
}

const genderLabel = (g: string) => ({ male: '男', female: '女', unknown: '保密' }[g] || '保密')

onMounted(async () => {
  if (!auth.userInfo) await auth.fetchInfo().catch(() => {})
  loadFav(true)
})
</script>

<template>
  <div class="profile-page">
    <!-- 顶栏 -->
    <header class="top-bar">
      <span class="top-title">我的</span>
      <button class="logout-btn" @click="logout">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" style="vertical-align:-2px; margin-right:4px">
          <path d="M6 2H3a1 1 0 00-1 1v10a1 1 0 001 1h3M10 11l3-3-3-3M13 8H6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>退出
      </button>
    </header>

    <!-- 用户信息卡 -->
    <div class="user-card">
      <div class="avatar-wrap">
        <div class="avatar">{{ avatarText() }}</div>
      </div>
      <div class="user-info">
        <p class="username">{{ auth.userInfo?.nickname || auth.userInfo?.username || '—' }}</p>
        <div class="user-tags">
          <span class="tag">@{{ auth.userInfo?.username }}</span>
          <span class="tag" v-if="auth.userInfo?.gender !== 'unknown'">{{ genderLabel(auth.userInfo?.gender || '') }}</span>
        </div>
        <p class="bio">{{ auth.userInfo?.bio || '这个人很懒，什么都没留下~' }}</p>
      </div>
      <button class="edit-btn" @click="openEdit">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M9.5 2.5L11.5 4.5L4.5 11.5H2.5V9.5L9.5 2.5Z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>
        </svg>
        编辑
      </button>
    </div>

    <!-- Tabs -->
    <div class="tabs-bar">
      <button :class="['tab-btn', { active: tab === 'fav' }]" @click="switchTab('fav')">
        ★ 收藏
      </button>
      <button :class="['tab-btn', { active: tab === 'history' }]" @click="switchTab('history')">
        ⏱ 历史
      </button>
    </div>

    <!-- 收藏列表 -->
    <div v-if="tab === 'fav'" class="list-section">
      <div v-if="favList.length" class="list-toolbar">
        <span class="list-count">{{ favList.length }} 条收藏</span>
        <button class="danger-text" @click="clearFav">清空全部</button>
      </div>
      <div v-if="listLoading && !favList.length" class="empty-state">
        <div class="mini-spinner"></div>
      </div>
      <div v-else-if="!favList.length" class="empty-state">
        <span class="empty-icon">☆</span>
        <p>暂无收藏</p>
      </div>
      <div
        v-for="item in favList" :key="item.id"
        class="list-item"
        @click="router.push(`/news/detail/${item.id}`)"
      >
        <img v-if="item.image" :src="item.image" class="item-thumb" loading="lazy" />
        <div v-else class="item-thumb item-thumb--empty"></div>
        <div class="item-body">
          <p class="item-title">{{ item.title }}</p>
          <div class="item-meta">
            <span>{{ item.author || '未知' }}</span>
            <span class="sep">·</span>
            <span>{{ timeAgo(item.favoriteTime) }}</span>
          </div>
        </div>
        <button class="del-btn" @click.stop="removeFav(item.id)">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M3 3L11 11M11 3L3 11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
      <button v-if="favMore && favList.length" class="load-more" :disabled="listLoading" @click="loadFav()">
        {{ listLoading ? '加载中…' : '加载更多' }}
      </button>
    </div>

    <!-- 历史列表 -->
    <div v-if="tab === 'history'" class="list-section">
      <div v-if="histList.length" class="list-toolbar">
        <span class="list-count">{{ histList.length }} 条记录</span>
        <button class="danger-text" @click="clearHist">清空全部</button>
      </div>
      <div v-if="listLoading && !histList.length" class="empty-state">
        <div class="mini-spinner"></div>
      </div>
      <div v-else-if="!histList.length" class="empty-state">
        <span class="empty-icon">⏱</span>
        <p>暂无浏览历史</p>
      </div>
      <div
        v-for="item in histList" :key="item.historyId"
        class="list-item"
        @click="router.push(`/news/detail/${item.id}`)"
      >
        <img v-if="item.image" :src="item.image" class="item-thumb" loading="lazy" />
        <div v-else class="item-thumb item-thumb--empty"></div>
        <div class="item-body">
          <p class="item-title">{{ item.title }}</p>
          <div class="item-meta">
            <span>{{ item.author || '未知' }}</span>
            <span class="sep">·</span>
            <span>{{ timeAgo(item.viewTime) }}</span>
          </div>
        </div>
        <button class="del-btn" @click.stop="removeHist(item.historyId)">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M3 3L11 11M11 3L3 11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
      <button v-if="histMore && histList.length" class="load-more" :disabled="listLoading" @click="loadHist()">
        {{ listLoading ? '加载中…' : '加载更多' }}
      </button>
    </div>

    <!-- 编辑资料弹层 -->
    <Transition name="modal">
      <div v-if="editMode" class="modal-overlay" @mousedown="onOverlayMousedown" @click="onOverlayClick($event, () => editMode = false)">
        <div class="modal-sheet">
          <div class="sheet-handle"></div>
          <h3 class="sheet-title">编辑资料</h3>
          <div class="sheet-field">
            <label>昵称</label>
            <input v-model="editForm.nickname" placeholder="设置昵称" />
          </div>
          <div class="sheet-field">
            <label>个人简介</label>
            <textarea v-model="editForm.bio" placeholder="介绍一下自己" rows="3"></textarea>
          </div>
          <div class="sheet-field">
            <label>性别</label>
            <div class="radio-group">
              <button
                v-for="opt in [['unknown','保密'],['male','男'],['female','女']]"
                :key="opt[0]"
                :class="['radio-btn', { active: editForm.gender === opt[0] }]"
                @click="editForm.gender = opt[0] as any"
              >{{ opt[1] }}</button>
            </div>
          </div>
          <p v-if="formErr" class="sheet-err">{{ formErr }}</p>
          <div class="sheet-actions">
            <button class="sheet-cancel" @click="editMode = false">取消</button>
            <button class="sheet-save" :disabled="saving" @click="saveEdit">
              {{ saving ? '保存中…' : '保存' }}
            </button>
          </div>
          <button class="sheet-link" @click="editMode = false; pwdMode = true; formErr = ''">
            修改密码 →
          </button>
        </div>
      </div>
    </Transition>

    <!-- 改密码弹层 -->
    <Transition name="modal">
      <div v-if="pwdMode" class="modal-overlay" @mousedown="onOverlayMousedown" @click="onOverlayClick($event, () => pwdMode = false)">
        <div class="modal-sheet">
          <div class="sheet-handle"></div>
          <h3 class="sheet-title">修改密码</h3>
          <div class="sheet-field">
            <label>当前密码</label>
            <input v-model="pwdForm.oldPassword" type="password" placeholder="输入当前密码" />
          </div>
          <div class="sheet-field">
            <label>新密码</label>
            <input v-model="pwdForm.newPassword" type="password" placeholder="至少6位" />
          </div>
          <div class="sheet-field">
            <label>确认新密码</label>
            <input v-model="pwdForm.confirm" type="password" placeholder="再次输入" />
          </div>
          <p v-if="formErr" class="sheet-err">{{ formErr }}</p>
          <div class="sheet-actions">
            <button class="sheet-cancel" @click="pwdMode = false">取消</button>
            <button class="sheet-save" :disabled="saving" @click="savePwd">
              {{ saving ? '保存中…' : '确认修改' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: var(--bg);
}

/* 顶栏 */
.top-bar {
  height: 52px;
  background: var(--bg-card);
  display: flex;
  align-items: center;
  padding: 0 16px;
  border-bottom: 2px solid var(--text-primary);
}
.top-title {
  flex: 1;
  font-family: 'Noto Serif SC', serif;
  font-size: 18px;
  font-weight: 900;
  color: var(--text-primary);
}
.logout-btn {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 600;
  display: flex;
  align-items: center;
}

/* 用户卡 */
.user-card {
  background: var(--bg-card);
  margin-bottom: 8px;
  padding: 20px 16px;
  display: flex;
  align-items: flex-start;
  gap: 14px;
  border-bottom: 1px solid var(--border);
}

.avatar-wrap { flex-shrink: 0; }
.avatar {
  width: 58px; height: 58px;
  border-radius: 14px;
  background: var(--text-primary);
  color: var(--bg-card);
  font-family: 'Noto Serif SC', serif;
  font-size: 24px;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
  letter-spacing: -1px;
}

.user-info { flex: 1; min-width: 0; }
.username {
  font-family: 'Noto Serif SC', serif;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 5px;
}
.user-tags { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 6px; }
.tag {
  font-size: 11px;
  color: var(--text-muted);
  background: var(--bg);
  border: 1px solid var(--border);
  padding: 1px 8px;
  border-radius: 20px;
}
.bio {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.edit-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 700;
  color: var(--text-secondary);
  border: 1.5px solid var(--border-strong);
  border-radius: 20px;
  padding: 5px 12px;
  flex-shrink: 0;
  transition: border-color 0.15s, color 0.15s;
}
.edit-btn:active { color: var(--brand); border-color: var(--brand); }

/* Tabs */
.tabs-bar {
  background: var(--bg-card);
  display: flex;
  border-bottom: 1px solid var(--border);
  margin-bottom: 8px;
}
.tab-btn {
  flex: 1;
  padding: 13px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.5px;
  border-bottom: 2.5px solid transparent;
  transition: color 0.15s, border-color 0.15s;
}
.tab-btn.active {
  color: var(--text-primary);
  border-bottom-color: var(--brand);
}

/* 列表 */
.list-section { padding: 0 10px; }

.list-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 4px 6px;
}
.list-count { font-size: 12px; color: var(--text-muted); }
.danger-text { font-size: 12px; color: #C0392B; font-weight: 600; }

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 48px 0;
}
.empty-icon { font-size: 32px; opacity: 0.3; }
.empty-state p { font-size: 14px; color: var(--text-muted); }

.mini-spinner {
  width: 24px; height: 24px;
  border: 2px solid var(--border-strong);
  border-top-color: var(--brand);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg) } }

.list-item {
  background: var(--bg-card);
  border-radius: var(--radius);
  margin-bottom: 8px;
  padding: 12px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
  border: 1px solid var(--border);
  transition: background 0.12s;
}
.list-item:active { background: var(--bg); }

.item-thumb {
  width: 76px; height: 56px;
  border-radius: var(--radius-sm);
  object-fit: cover;
  flex-shrink: 0;
}
.item-thumb--empty { background: var(--border); }

.item-body { flex: 1; min-width: 0; }
.item-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.5;
  margin-bottom: 6px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.item-meta { display: flex; align-items: center; gap: 4px; }
.item-meta span { font-size: 11px; color: var(--text-muted); }
.sep { color: var(--border-strong); }

.del-btn {
  color: var(--text-muted);
  padding: 4px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  transition: color 0.15s;
}
.del-btn:active { color: #C0392B; }

.load-more {
  width: 100%; padding: 13px;
  text-align: center;
  font-size: 13px; font-weight: 600;
  color: var(--brand);
  background: var(--bg-card);
  border-radius: var(--radius);
  margin-bottom: 8px;
  border: 1px solid var(--border);
}
.load-more:disabled { color: var(--text-muted); }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.5);
  z-index: 200;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}
.modal-sheet {
  background: var(--bg-card);
  width: 100%;
  max-width: 480px;
  border-radius: 20px 20px 0 0;
  padding: 8px 20px 40px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-height: 90vh;
  overflow-y: auto;
}
.sheet-handle {
  width: 36px; height: 4px;
  background: var(--border-strong);
  border-radius: 2px;
  margin: 4px auto 4px;
  flex-shrink: 0;
}
.sheet-title {
  font-family: 'Noto Serif SC', serif;
  font-size: 18px;
  font-weight: 900;
  color: var(--text-primary);
}
.sheet-field { display: flex; flex-direction: column; gap: 6px; }
.sheet-field label {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-secondary);
  letter-spacing: 0.5px;
}
.sheet-field input,
.sheet-field textarea,
.sheet-field select {
  width: 100%;
  padding: 11px 13px;
  background: var(--bg);
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 15px;
  color: var(--text-primary);
  transition: border-color 0.18s;
  resize: none;
}
.sheet-field input:focus,
.sheet-field textarea:focus {
  border-color: var(--brand);
}

.radio-group { display: flex; gap: 8px; }
.radio-btn {
  flex: 1;
  padding: 9px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  background: var(--bg);
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  transition: all 0.15s;
}
.radio-btn.active {
  background: var(--brand-dim);
  border-color: var(--brand);
  color: var(--brand);
}

.sheet-err {
  font-size: 13px;
  color: #C0392B;
  background: rgba(192,57,43,0.08);
  border-radius: 6px;
  padding: 8px 12px;
}
.sheet-actions { display: flex; gap: 10px; }
.sheet-cancel {
  flex: 1; padding: 12px;
  background: var(--bg);
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 15px; font-weight: 600;
  color: var(--text-secondary);
}
.sheet-save {
  flex: 2; padding: 12px;
  background: var(--brand); color: #fff;
  border-radius: var(--radius-sm);
  font-size: 15px; font-weight: 700;
  transition: opacity 0.15s;
}
.sheet-save:disabled { opacity: 0.6; }
.sheet-link {
  text-align: center;
  font-size: 14px;
  color: var(--brand);
  font-weight: 600;
  padding: 4px 0;
}

/* modal transition */
.modal-enter-active, .modal-leave-active {
  transition: opacity 0.25s;
}
.modal-enter-active .modal-sheet,
.modal-leave-active .modal-sheet {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .modal-sheet,
.modal-leave-to .modal-sheet { transform: translateY(100%); }
</style>
