import { userService } from '../services/userService'
import type { User, UserCreate } from '../models/user'

export const userController = {
  list(): Promise<User[]> { return userService.list() },
  create(payload: UserCreate): Promise<User> { return userService.create(payload) },
}

