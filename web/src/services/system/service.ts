import { api } from '../api'

export interface ResetBusinessDataResult {
  message: string
  tables_cleared: number
  users_deleted: number
}

export const systemService = {
  async resetBusinessData() {
    return (await api.post<ResetBusinessDataResult>('/system/reset-business-data')).data
  },
}
