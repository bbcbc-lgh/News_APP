import { apiClient } from './client'

export interface VoteResult {
  upvotes: number
  downvotes: number
  userVote: number | null
}

export const voteApi = {
  cast: (newsId: number, value: number) =>
    apiClient.post<VoteResult>(`/api/news/${newsId}/vote`, { value }, true),

  get: (newsId: number) =>
    apiClient.get<VoteResult>(`/api/news/${newsId}/vote`, true),
}
