import { apiClient } from './client'
import type { Token, User } from './types'

export const authApi = {
  login: async (email: string, password: string): Promise<Token> => {
    const { data } = await apiClient.post<Token>('/auth/login/json', { email, password })
    return data
  },

  register: async (email: string, password: string, full_name?: string, team_id?: number): Promise<User> => {
    const { data } = await apiClient.post<User>('/auth/register', {
      email,
      password,
      full_name,
      team_id,
    })
    return data
  },

  me: async (): Promise<User> => {
    const { data } = await apiClient.get<User>('/auth/me')
    return data
  },
}
