export interface NotificationItem {
  id: number
  id_user: number
  type_notification: string
  titre: string
  message: string
  id_reservation?: number | null
  id_depart?: number | null
  canal: string
  est_lue: boolean
  date_envoi: string
  date_lecture?: string | null
}
