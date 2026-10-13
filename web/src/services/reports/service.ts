import { api } from '../api'

export const reportsService = {
  async get(type: string, params: Record<string, string>) {
    return (await api.get('/rapports', { params: { type, ...params } })).data
  },
  async csv(type: string, params: Record<string, string>) {
    return (await api.get('/rapports/export.csv', { params: { type, ...params }, responseType: 'blob' })).data as Blob
  },
  async pdf(type: string, params: Record<string, string>) {
    return (await api.get('/rapports/export.pdf', { params: { type, ...params }, responseType: 'blob' })).data as Blob
  },
}
