import 'package:flutter/material.dart';
import 'presentation/pages/home_page.dart';

class CooperativeApp extends StatelessWidget {
  const CooperativeApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'Coopérative',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(colorSchemeSeed: const Color(0xff356ae6), useMaterial3: true),
        home: const HomePage(),
      );
}

