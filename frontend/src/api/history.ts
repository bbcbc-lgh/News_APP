import { apiClient } from './client'
import type { NewsItem } from './news'

export interface HistoryItem extends NewsItem {
  historyId: number
  viewTime: string
}

export interface HistoryList {
  list: HistoryItem[]
  total: number
  hasMore: boolean
}

export const historyApi = {
  add: (newsId: number) =>
    apiClient.post<null>('/api/history/add', { newsId }, true),

  getList: (page = 1, pageSize = 10) =>
    apiClient.get<HistoryList>(`/api/history/list?page=${page}&pageSize=${pageSize}`, true),

  deleteOne: (id: number) =>
    apiClient.delete<null>(`/api/history/delete/${id}`, true),

  clear: () =>
    apiClient.delete<null>('/api/history/clear', true)
}
