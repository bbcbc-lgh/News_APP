import { apiClient } from './client'

export interface ReadingProgressData {
  progress: number
  lastPosition: number
}

export const readingProgressApi = {
  save: (newsId: number, progress: number, lastPosition: number) =>
    apiClient.post<null>('/api/reading-progress', { news_id: newsId, progress, last_position: lastPosition }, true),

  get: (newsId: number) =>
    apiClient.get<ReadingProgressData>(`/api/reading-progress/${newsId}`, true),
}
