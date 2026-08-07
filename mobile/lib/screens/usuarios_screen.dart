import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/usuarios_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';
import '../widgets/glass_list_tile.dart';
import 'registrar_usuario_screen.dart';

class UsuariosScreen extends StatefulWidget {
  const UsuariosScreen({super.key});

  @override
  State<UsuariosScreen> createState() => _UsuariosScreenState();
}

class _UsuariosScreenState extends State<UsuariosScreen> {
  List<UsuarioEquipo> _usuarios = [];
  bool _cargando = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      _usuarios = await context.read<AppState>().usuarios.listar();
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  Future<void> _toggleActivo(UsuarioEquipo u) async {
    try {
      final actualizado = await context.read<AppState>().usuarios.actualizarActivo(u.id, !u.activo);
      setState(() {
        _usuarios = _usuarios.map((x) => x.id == actualizado.id ? actualizado : x).toList();
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$e'), backgroundColor: const Color(0xFFEF4444)),
        );
      }
    }
  }

  Color _rolColor(String rol) {
    switch (rol) {
      case 'DUEÑO':
        return AppColors.neonBlue;
      case 'VENDEDOR':
        return AppColors.emerald;
      case 'COBRADOR':
        return AppColors.neonCyan;
      default:
        return AppColors.textMuted;
    }
  }

  @override
  Widget build(BuildContext context) {
    return FuturisticScaffold(
      title: 'Equipo y Roles',
      accentColor: AppColors.neonBlue,
      actions: [
        IconButton(icon: const Icon(Icons.refresh_rounded), onPressed: _cargar),
      ],
      floatingActionButton: NeonFab(
        label: 'Nuevo',
        icon: Icons.person_add_rounded,
        color: AppColors.neonBlue,
        onPressed: () async {
          final ok = await Navigator.push<bool>(
            context,
            MaterialPageRoute(builder: (_) => const RegistrarUsuarioScreen()),
          );
          if (ok == true) _cargar();
        },
      ),
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Color(0xFFEF4444))))
              : RefreshIndicator(
                  onRefresh: _cargar,
                  child: ListView(
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
                    children: [
                      GlassContainer(
                        accentColor: AppColors.neonBlue,
                        child: const Text(
                          'Administra vendedores, cobradores y accesos del equipo en ruta.',
                          style: TextStyle(color: AppColors.textMuted, height: 1.4),
                        ),
                      ),
                      const SizedBox(height: 16),
                      const SectionTitle(title: 'Usuarios registrados'),
                      if (_usuarios.isEmpty)
                        const EmptyState(icon: Icons.group_off_rounded, message: 'No hay usuarios registrados')
                      else
                        ..._usuarios.map((u) {
                          final color = _rolColor(u.rol);
                          return GlassListTile(
                            accentColor: color,
                            leading: CircleAvatar(
                              backgroundColor: color.withValues(alpha: 0.15),
                              child: Text(
                                u.nombre[0].toUpperCase(),
                                style: TextStyle(color: color, fontWeight: FontWeight.w800),
                              ),
                            ),
                            title: Text(u.nombre),
                            subtitle: Text('@${u.username} · ${u.rol}'),
                            trailing: Switch.adaptive(
                              value: u.activo,
                              activeColor: AppColors.emerald,
                              onChanged: (_) => _toggleActivo(u),
                            ),
                          );
                        }),
                    ],
                  ),
                ),
    );
  }
}
