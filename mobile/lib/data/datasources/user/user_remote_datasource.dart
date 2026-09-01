import 'package:dio/dio.dart';
import '../../../core/network/api_client.dart';
import '../../models/user/user_dto.dart';

class UserRemoteDataSource {
  final ApiClient _apiClient;

  UserRemoteDataSource(this._apiClient);

  Future<List<UserDto>> getUsers() async {
    try {
      final response = await _apiClient.dio.get('/users');
      return (response.data as List)
          .map((item) => UserDto.fromJson(item as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw Exception(e.message ?? 'Erreur lors de la récupération des utilisateurs');
    }
  }
}
