class UserEntity {
  final int id;
  final String name;
  final String firstName;
  final String email;
  final String? telephone;
  final String? address;
  final String role;
  final List<String> permissions;
  final bool isActive;
  final String createdAt;

  const UserEntity({
    required this.id,
    required this.name,
    required this.firstName,
    required this.email,
    this.telephone,
    this.address,
    required this.role,
    this.permissions = const [],
    required this.isActive,
    required this.createdAt,
  });

  String get fullName => '$firstName $name'.trim();
}
