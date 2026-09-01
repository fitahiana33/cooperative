import '../../entities/user/user_entity.dart';
import '../../repositories/user/user_repository.dart';

class UserService {
  final UserRepository _repository;

  UserService(this._repository);

  Future<List<UserEntity>> listUsers() async {
    return await _repository.list();
  }
}
