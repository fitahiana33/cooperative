import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/network/api_client.dart';
import '../../../data/datasources/user/user_remote_datasource.dart';
import '../../../data/repositories/user/user_repository_impl.dart';
import '../../../domain/entities/user/user_entity.dart';
import '../../../domain/repositories/user/user_repository.dart';
import '../../../domain/services/user/user_service.dart';

final Provider<UserRemoteDataSource> userRemoteDataSourceProvider =
    Provider<UserRemoteDataSource>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return UserRemoteDataSource(apiClient);
});

final Provider<UserRepository> userRepositoryProvider =
    Provider<UserRepository>((ref) {
  final remote = ref.watch(userRemoteDataSourceProvider);
  return UserRepositoryImpl(remote);
});

final Provider<UserService> userServiceProvider = Provider<UserService>((ref) {
  final repo = ref.watch(userRepositoryProvider);
  return UserService(repo);
});

final userControllerProvider =
    AsyncNotifierProvider<UserController, List<UserEntity>>(UserController.new);

class UserController extends AsyncNotifier<List<UserEntity>> {
  @override
  Future<List<UserEntity>> build() {
    final service = ref.watch(userServiceProvider);
    return service.listUsers();
  }
}
