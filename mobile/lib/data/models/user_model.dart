class UserModel {
  const UserModel({required this.id, required this.email, required this.fullName});
  final int id;
  final String email;
  final String fullName;

  factory UserModel.fromJson(Map<String, dynamic> json) => UserModel(
        id: json['id'] as int,
        email: json['email'] as String,
        fullName: json['full_name'] as String,
      );
}

