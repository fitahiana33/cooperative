import '../../data/models/user_model.dart';
import '../repositories/user_repository.dart';

class UserService {
  UserService(this.repository);
  final UserRepository repository;
  Future<List<UserModel>> listUsers() => repository.list();
}

