import { gareService } from '../gare/service'
import { cooperativeService } from '../cooperative/service'
import { roleService } from '../role/service'
import { permissionService } from '../permission/service'

export const managementService = {
  ...gareService,
  ...cooperativeService,
  ...roleService,
  ...permissionService,
}
