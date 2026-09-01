class RegisterRequestDto {
  final String name;
  final String firstName;
  final String email;
  final String? telephone;
  final String? address;
  final String password;

  const RegisterRequestDto({
    required this.name,
    required this.firstName,
    required this.email,
    this.telephone,
    this.address,
    required this.password,
  });

  Map<String, dynamic> toJson() {
    return {
      'name': name.trim(),
      'first_name': firstName.trim(),
      'email': email.trim(),
      'telephone': telephone?.trim().isEmpty == true ? null : telephone?.trim(),
      'address': address?.trim().isEmpty == true ? null : address?.trim(),
      'password': password,
    };
  }
}
