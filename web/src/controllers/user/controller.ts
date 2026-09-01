import { userService } from '../../services/user/service'
import type { User, UserCreate } from '../../models/user/model'

export const userController = {
  list(): Promise<User[]> { return userService.list() },
  create(payload: UserCreate): Promise<User> { return userService.create(payload) },
}



