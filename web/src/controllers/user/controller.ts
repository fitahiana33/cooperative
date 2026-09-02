import { userService } from '../../services/user/service'
import type { User, UserCreate } from '../../models/user/model'

export const userController = {
  list(params?: Parameters<typeof userService.list>[0]) { return userService.list(params) },
  create(payload: UserCreate): Promise<User> { return userService.create(payload) },
}


