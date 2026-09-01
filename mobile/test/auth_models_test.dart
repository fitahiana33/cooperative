import 'package:flutter_test/flutter_test.dart';
import 'package:cooperative_mobile/data/models/auth/login_request_dto.dart';
import 'package:cooperative_mobile/data/models/auth/register_request_dto.dart';
import 'package:cooperative_mobile/data/models/auth/token_response_dto.dart';

void main() {
  group('Auth Models Tests', () {
    test('LoginRequestDto toJson formats correctly', () {
      const request = LoginRequestDto(email: ' user@example.com ', password: 'password123');
      final json = request.toJson();

      expect(json['email'], 'user@example.com');
      expect(json['password'], 'password123');
    });

    test('RegisterRequestDto toJson formats correctly', () {
      const request = RegisterRequestDto(
        name: ' Rasoa ',
        firstName: ' Jeanne ',
        email: ' rasoa@example.com ',
        telephone: ' 0340000000 ',
        address: ' Antananarivo ',
        password: 'securepassword',
      );
      final json = request.toJson();

      expect(json['name'], 'Rasoa');
      expect(json['first_name'], 'Jeanne');
      expect(json['email'], 'rasoa@example.com');
      expect(json['telephone'], '0340000000');
      expect(json['address'], 'Antananarivo');
      expect(json['password'], 'securepassword');
    });

    test('TokenResponseDto deserialization from json', () {
      final json = {
        'access_token': 'access_token_xyz',
        'refresh_token': 'refresh_token_xyz',
        'token_type': 'bearer',
        'user': {
          'id': 1,
          'name': 'Rabe',
          'first_name': 'Paul',
          'email': 'paul@example.com',
          'role': 'passenger',
          'is_active': true,
          'created_at': '2026-09-01T10:00:00Z',
        },
      };

      final response = TokenResponseDto.fromJson(json);

      expect(response.accessToken, 'access_token_xyz');
      expect(response.refreshToken, 'refresh_token_xyz');
      expect(response.tokenType, 'bearer');
      expect(response.user, isNotNull);
      expect(response.user!.fullName, 'Paul Rabe');
    });
  });
}
