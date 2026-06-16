import { apiClient } from './client'

export interface SearchHistoryItem {
  id: number
  query: string
  createdAt: string
}

export const searchHistoryApi = {
  add: (query: string) =>
    apiClient.post<{ id: number; query: string; createdAt: string }>('/api/search/history', { query }, true),

  list: (limit = 20) =>
    apiClient.get<{ list: SearchHistoryItem[] }>(`/api/search/history?limit=${limit}`, true),

  remove: (id: number) =>
    apiClient.delete<null>(`/api/search/history/${id}`, true),

  clear: () =>
    apiClient.delete<null>('/api/search/history', true),

  suggestions: (q: string) =>
    apiClient.get<string[]>(`/api/search/history/suggestions?q=${encodeURIComponent(q)}`, true),
}
