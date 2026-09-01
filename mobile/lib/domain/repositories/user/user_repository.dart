import '../../entities/user/user_entity.dart';

abstract class UserRepository {
  Future<List<UserEntity>> list();
}
