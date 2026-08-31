import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/datasources/api_client.dart';
import '../../data/models/user_model.dart';
import '../../data/repositories/user_repository_impl.dart';
import '../../domain/services/user_service.dart';

final homeControllerProvider = AsyncNotifierProvider<HomeController, List<UserModel>>(HomeController.new);

class HomeController extends AsyncNotifier<List<UserModel>> {
  @override
  Future<List<UserModel>> build() => UserService(UserRepositoryImpl(ApiClient())).listUsers();
}

