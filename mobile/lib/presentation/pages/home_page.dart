import 'package:flutter/material.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Coopérative')),
        body: const Center(
          child: Padding(
            padding: EdgeInsets.all(24),
            child: Text('Bienvenue. La recherche de voyages et la réservation seront disponibles ici.'),
          ),
        ),
      );
}

