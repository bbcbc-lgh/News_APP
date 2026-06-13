import { apiClient } from './client'

export interface Category {
  id: string
  name: string
}

export interface NewsItem {
  id: number
  title: string
  description: string | null
  image: string | null
  author: string | null
  source_platform: string | null
  views: number
  publish_time: string
}

export interface NewsDetail {
  id: number
  title: string
  titleZh: string | null
  description: string | null
  descriptionZh: string | null
  content: string
  contentZh: string | null
  image: string | null
  author: string | null
  source: string | null
  sourceUrl: string | null
  publishTime: string
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

  getList: (source: string, page = 1, pageSize = 10) =>
    apiClient.get<NewsList>(`/api/news/list?source=${source}&page=${page}&pageSize=${pageSize}`),

  getDetail: (id: number) =>
    apiClient.get<NewsDetail>(`/api/news/detail?id=${id}`),

  // 按关键词搜索新闻（匹配标题和摘要）
  search: (keyword: string, page = 1, pageSize = 10) =>
    apiClient.get<SearchResult>(`/api/news/search?keyword=${encodeURIComponent(keyword)}&page=${page}&pageSize=${pageSize}`)
}
