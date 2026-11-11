import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../domain/entities/user/user_entity.dart';
import '../../controllers/auth/auth_controller.dart';

// Memory-only image cache, discarded when the last avatar leaves the screen.
final profilePhotoProvider =
    FutureProvider.autoDispose.family<Uint8List, (int, String)>((ref, key) {
  return ref.watch(authServiceProvider).profilePhoto();
});

class UserAvatar extends ConsumerWidget {
  const UserAvatar({super.key, required this.user, this.radius = 24});
  final UserEntity user;
  final double radius;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final version = user.photoVersion;
    final bytes = version == null
        ? null
        : ref.watch(profilePhotoProvider((user.id, version))).asData?.value;
    final first = user.firstName.isEmpty ? '' : user.firstName.characters.first;
    final last = user.name.isEmpty ? '' : user.name.characters.first;
    return ExcludeSemantics(
        child: CircleAvatar(
      radius: radius,
      backgroundImage: bytes == null ? null : MemoryImage(bytes),
      child: bytes != null
          ? null
          : Text('$first$last'.toUpperCase(),
              style: TextStyle(
                  fontSize: radius * .65, fontWeight: FontWeight.w700)),
    ));
  }
}
