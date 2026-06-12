import { apiClient } from './client'

export interface Category {
  id: number
  name: string
  sort_order: number
}

export interface NewsItem {
  id: number
  title: string
  description: string | null
  image: string | null
  author: string | null
  category_id: number
  views: number
  publish_time: string
}

export interface NewsDetail {
  id: number
  title: string
  content: string
  image: string | null
  author: string | null
  publishTime: string
  categoryId: number
  views: number
  relatedNews: NewsItem[]
}

export interface NewsList {
  list: NewsItem[]
  total: number
  hasMore: boolean
}

export interface SearchResult {
  list: NewsItem[]
  total: number
  hasMore: boolean
  keyword: string
}

export const newsApi = {
  getCategories: () =>
    apiClient.get<Category[]>('/api/news/categories'),

  getList: (categoryId: number, page = 1, pageSize = 10) =>
    apiClient.get<NewsList>(`/api/news/list?categoryId=${categoryId}&page=${page}&pageSize=${pageSize}`),

  getDetail: (id: number) =>
    apiClient.get<NewsDetail>(`/api/news/detail?id=${id}`),

  // 按关键词搜索新闻（匹配标题和摘要）
  search: (keyword: string, page = 1, pageSize = 10) =>
    apiClient.get<SearchResult>(`/api/news/search?keyword=${encodeURIComponent(keyword)}&page=${page}&pageSize=${pageSize}`)
}
