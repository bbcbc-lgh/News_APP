import { defineStore } from 'pinia'
import { ref } from 'vue'
import { newsApi, type Category, type NewsItem } from '@/api/news'

const NEWS_PAGE_SIZE = 30

export const useNewsStore = defineStore('news', () => {
  const categories = ref<Category[]>([])
  const activeSource = ref('all')
  const newsList = ref<NewsItem[]>([])
  const page = ref(1)
  const hasMore = ref(true)
  const loading = ref(false)
  const scrollPositions = ref<Record<string, number>>({})
  let loadId = 0

  async function loadCategories() {
    if (categories.value.length) return
    categories.value = await newsApi.getCategories()
    if (categories.value.length) activeSource.value = categories.value[0].id
  }

  async function loadNews(source: string, reset = false) {
    if (loading.value && !reset) return
    const currentLoadId = ++loadId
    if (reset) {
      newsList.value = []
      page.value = 1
      hasMore.value = true
    }
    if (!hasMore.value) return
    loading.value = true
    try {
      const res = await newsApi.getList(source, page.value, NEWS_PAGE_SIZE)
      if (currentLoadId !== loadId) return
      newsList.value = [...newsList.value, ...res.list]
      hasMore.value = res.hasMore
      page.value++
    } finally {
      if (currentLoadId === loadId) loading.value = false
    }
  }

  function setCategory(id: string) {
    if (activeSource.value === id) return
    activeSource.value = id
  }

  function setScrollTop(source: string, value: number) {
    scrollPositions.value[source] = value
  }

  function getScrollTop(source: string) {
    return scrollPositions.value[source] || 0
  }

  function resetState() {
    loadId++
    activeSource.value = categories.value[0]?.id || 'all'
    newsList.value = []
    page.value = 1
    hasMore.value = true
    loading.value = false
    scrollPositions.value = {}
  }

  return {
    categories,
    activeSource,
    newsList,
    page,
    hasMore,
    loading,
    loadCategories,
    loadNews,
    setCategory,
    setScrollTop,
    getScrollTop,
    resetState,
  }
})
