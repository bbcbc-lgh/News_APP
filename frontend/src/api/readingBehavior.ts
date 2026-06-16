import { apiClient } from './client'

export type ActionType = 'view' | 'favorite' | 'share' | 'complete'
export type StatsPeriod = 'today' | 'week' | 'month' | 'all'

export interface ReadingStats {
  viewCount: number
  completeCount: number
  favoriteCount: number
  shareCount: number
  distinctNews: number
  totalDurationSec: number
  bySource: Record<string, number>
}

export const readingApi = {
  report: (newsId: number, actionType: ActionType, duration = 0) =>
    apiClient.post<null>(
      '/api/reading/behavior',
      { newsId, actionType, duration },
      true,
    ),

  getStats: (period: StatsPeriod = 'week') =>
    apiClient.get<ReadingStats>(`/api/reading/stats?period=${period}`, true),
}
