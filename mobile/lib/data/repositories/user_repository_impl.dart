import '../datasources/api_client.dart';
import '../models/user_model.dart';
import '../../domain/repositories/user_repository.dart';

class UserRepositoryImpl implements UserRepository {
  UserRepositoryImpl(this.client);
  final ApiClient client;

  @override
  Future<List<UserModel>> list() async {
    final response = await client.dio.get('/users');
    return (response.data as List).map((item) => UserModel.fromJson(item)).toList();
  }
}
