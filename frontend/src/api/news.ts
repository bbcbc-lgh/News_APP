import { apiClient } from './client'

export interface Category {
  id: string
  name: string
}

export interface NewsItem {
  id: number
  title: string
  title_zh: string | null
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
  upvotes: number
  downvotes: number
  commentCount: number
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

export type TimeRange = 'day' | 'week' | 'month' | 'year' | 'all'

export const newsApi = {
  getCategories: () =>
    apiClient.get<Category[]>('/api/news/categories'),

  getList: (source: string, page = 1, pageSize = 10) =>
    apiClient.get<NewsList>(`/api/news/list?source=${source}&page=${page}&pageSize=${pageSize}`),

  getDetail: (id: number) =>
    apiClient.get<NewsDetail>(`/api/news/detail?id=${id}`),

  search: (
    keyword: string,
    page = 1,
    pageSize = 10,
    sources: string[] = [],
    timeRange: TimeRange = 'all',
    tags: string[] = [],
  ) => {
    const params = new URLSearchParams({
      keyword,
      page: String(page),
      pageSize: String(pageSize),
      timeRange,
    })
    sources.forEach((s) => params.append('sources', s))
    tags.forEach((t) => params.append('tags', t))
    return apiClient.get<SearchResult>(`/api/news/search?${params.toString()}`)
  },

  refresh: () =>
    apiClient.post<null>('/api/news/refresh'),

  getByAuthor: (author: string, page = 1, pageSize = 10) =>
    apiClient.get<NewsList & { author: string }>(`/api/news/author/${encodeURIComponent(author)}?page=${page}&pageSize=${pageSize}`),
}
