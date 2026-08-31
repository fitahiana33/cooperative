import '../../data/models/user_model.dart';

abstract interface class UserRepository {
  Future<List<UserModel>> list();
}

