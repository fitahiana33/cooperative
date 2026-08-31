class Env {
  static const apiBaseUrl = String.fromEnvironment(
    'MOBILE_API_BASE_URL',
    defaultValue: '',
  );
}
