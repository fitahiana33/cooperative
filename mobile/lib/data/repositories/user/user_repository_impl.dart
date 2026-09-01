import '../../../domain/entities/user/user_entity.dart';
import '../../../domain/repositories/user/user_repository.dart';
import '../../datasources/user/user_remote_datasource.dart';

class UserRepositoryImpl implements UserRepository {
  final UserRemoteDataSource _remoteDataSource;

  UserRepositoryImpl(this._remoteDataSource);

  @override
  Future<List<UserEntity>> list() async {
    return await _remoteDataSource.getUsers();
  }
}
