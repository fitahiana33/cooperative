/// The reset email contains a link (…/forgot-password?token=…). Accept the
/// whole link pasted from the email, or just the code.
String extractResetToken(String input) {
  final text = input.trim();
  final fromLink = Uri.tryParse(text)?.queryParameters['token'];
  return (fromLink != null && fromLink.isNotEmpty) ? fromLink : text;
}
