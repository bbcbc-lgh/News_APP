import { defineStore } from 'pinia'
import { ref } from 'vue'
import { newsApi, type Category, type NewsItem } from '@/api/news'

const NEWS_PAGE_SIZE = 100

export const useNewsStore = defineStore('news', () => {
  const categories = ref<Category[]>([])
  const activeSource = ref('all')
  const newsList = ref<NewsItem[]>([])
  const page = ref(1)
  const hasMore = ref(true)
  const loading = ref(false)
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
      const appendPage = (res: Awaited<ReturnType<typeof newsApi.getList>>) => {
        if (currentLoadId !== loadId) return false
        newsList.value = [...newsList.value, ...res.list]
        hasMore.value = res.hasMore
        page.value++
        return true
      }

      const firstPage = await newsApi.getList(source, page.value, NEWS_PAGE_SIZE)
      if (!appendPage(firstPage)) return

      while (reset && hasMore.value && newsList.value.length < firstPage.total) {
        const res = await newsApi.getList(source, page.value, NEWS_PAGE_SIZE)
        if (!appendPage(res) || res.list.length === 0) break
      }
    } finally {
      if (currentLoadId === loadId) loading.value = false
    }
  }

  function setCategory(id: string) {
    activeSource.value = id
    loadNews(id, true)
  }

  return { categories, activeSource, newsList, page, hasMore, loading, loadCategories, loadNews, setCategory }
})
