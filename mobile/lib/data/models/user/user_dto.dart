import '../../../domain/entities/user/user_entity.dart';

class UserDto extends UserEntity {
  const UserDto({
    required super.id,
    required super.name,
    required super.firstName,
    required super.email,
    super.telephone,
    super.address,
    required super.role,
    super.permissions,
    required super.isActive,
    required super.createdAt,
  });

  factory UserDto.fromJson(Map<String, dynamic> json) {
    return UserDto(
      id: json['id'] as int,
      name: json['name'] as String? ?? '',
      firstName: json['first_name'] as String? ?? '',
      email: json['email'] as String? ?? '',
      telephone: json['telephone'] as String?,
      address: json['address'] as String?,
      role: json['role'] as String? ?? 'passenger',
      permissions: (json['permissions'] as List? ?? const []).whereType<String>().toList(),
      isActive: json['is_active'] as bool? ?? true,
      createdAt: json['created_at'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'first_name': firstName,
      'email': email,
      'telephone': telephone,
      'address': address,
      'role': role,
      'permissions': permissions,
      'is_active': isActive,
      'created_at': createdAt,
    };
  }
}
