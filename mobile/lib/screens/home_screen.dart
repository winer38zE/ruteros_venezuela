import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../theme/app_theme.dart';
import '../widgets/floating_nav_bar.dart';
import '../widgets/futuristic_background.dart';
import '../widgets/glass_container.dart';
import '../widgets/module_grid_card.dart';
import 'contabilidad_screen.dart';
import 'inventario_screen.dart';
import 'ventas_list_screen.dart';
import 'cobros_list_screen.dart';
import 'finanzas_screen.dart';

class _ModuleDef {
  const _ModuleDef({
    required this.id,
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.color,
    required this.screen,
    required this.badge,
  });

  final String id;
  final IconData icon;
  final String title;
  final String subtitle;
  final Color color;
  final Widget screen;
  final String badge;
}

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  List<_ModuleDef> _modules(AppState state) {
    final user = state.usuario!;
    final modules = <_ModuleDef>[];

    if (state.puedeVender) {
      modules.add(const _ModuleDef(
        id: 'ventas',
        icon: Icons.point_of_sale_rounded,
        title: 'Ventas',
        subtitle: 'Registra ventas con detalle e inventario',
        color: AppColors.emerald,
        screen: VentasListScreen(),
        badge: 'LIVE',
      ));
    }

    if (state.puedeCobrar) {
      modules.add(const _ModuleDef(
        id: 'cobros',
        icon: Icons.payments_rounded,
        title: 'Cobros',
        subtitle: 'Cobra ventas pendientes en calle',
        color: AppColors.neonCyan,
        screen: CobrosListScreen(),
        badge: 'FIELD',
      ));
    }

    if (user.esDueno) {
      modules.addAll(const [
        _ModuleDef(
          id: 'finanzas',
          icon: Icons.account_balance_rounded,
          title: 'Finanzas',
          subtitle: 'Gastos, entradas y nómina',
          color: AppColors.amber,
          screen: FinanzasScreen(),
          badge: 'CTRL',
        ),
        _ModuleDef(
          id: 'contabilidad',
          icon: Icons.account_balance_wallet_rounded,
          title: 'Contabilidad',
          subtitle: 'Resumen, asientos y Excel',
          color: AppColors.neonBlue,
          screen: ContabilidadScreen(),
          badge: 'PRO',
        ),
        _ModuleDef(
          id: 'inventario',
          icon: Icons.inventory_2_rounded,
          title: 'Inventario',
          subtitle: 'Stock en tiempo real valorado',
          color: AppColors.violet,
          screen: InventarioScreen(),
          badge: 'STOCK',
        ),
      ]);
    }

    return modules;
  }

  void _openModule(BuildContext context, Widget screen) {
    Navigator.push(context, MaterialPageRoute(builder: (_) => screen));
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final user = state.usuario!;
    final modules = _modules(state);

    return Scaffold(
      extendBody: true,
      body: FuturisticBackground(
        child: SafeArea(
          bottom: false,
          child: CustomScrollView(
            slivers: [
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(20, 12, 20, 8),
                  child: Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            ShaderMask(
                              shaderCallback: (bounds) => const LinearGradient(
                                colors: [AppColors.neonCyan, AppColors.neonBlue],
                              ).createShader(bounds),
                              child: const Text(
                                'ED NET PRO',
                                style: TextStyle(
                                  fontSize: 22,
                                  fontWeight: FontWeight.w900,
                                  color: Colors.white,
                                  letterSpacing: 1.2,
                                ),
                              ),
                            ),
                            const Text('Panel de Control'),
                          ],
                        ),
                      ),
                      _StatusChip(label: user.rol),
                      IconButton(
                        onPressed: () => state.logout(),
                        icon: const Icon(Icons.logout_rounded, color: AppColors.textMuted),
                        tooltip: 'Cerrar sesión',
                      ),
                    ],
                  ),
                ),
              ),
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: GlassContainer(
                    accentColor: AppColors.neonBlue,
                    padding: const EdgeInsets.all(18),
                    child: Row(
                      children: [
                        Container(
                          width: 52,
                          height: 52,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            gradient: LinearGradient(
                              colors: [
                                AppColors.neonCyan.withValues(alpha: 0.3),
                                AppColors.neonBlue.withValues(alpha: 0.2),
                              ],
                            ),
                            border: Border.all(color: AppColors.neonCyan.withValues(alpha: 0.5)),
                          ),
                          alignment: Alignment.center,
                          child: Text(
                            user.nombre[0].toUpperCase(),
                            style: const TextStyle(
                              fontWeight: FontWeight.w800,
                              fontSize: 20,
                              color: AppColors.neonCyan,
                            ),
                          ),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                user.nombre,
                                style: const TextStyle(
                                  fontWeight: FontWeight.w700,
                                  fontSize: 17,
                                  color: AppColors.textPrimary,
                                ),
                              ),
                              Text('Operador · ${user.rol}'),
                            ],
                          ),
                        ),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Container(
                                  width: 8,
                                  height: 8,
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    color: AppColors.emerald,
                                    boxShadow: [
                                      BoxShadow(
                                        color: AppColors.emerald.withValues(alpha: 0.6),
                                        blurRadius: 8,
                                      ),
                                    ],
                                  ),
                                ),
                                const SizedBox(width: 6),
                                const Text(
                                  'Online',
                                  style: TextStyle(
                                    color: AppColors.emerald,
                                    fontWeight: FontWeight.w600,
                                    fontSize: 12,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 4),
                            Text('${modules.length} módulos', style: Theme.of(context).textTheme.bodySmall),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              SliverPadding(
                padding: const EdgeInsets.fromLTRB(20, 20, 20, 120),
                sliver: modules.isEmpty
                    ? SliverToBoxAdapter(
                        child: GlassContainer(
                          child: const Text('No hay módulos disponibles para tu rol.'),
                        ),
                      )
                    : SliverGrid(
                        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: 2,
                          mainAxisSpacing: 14,
                          crossAxisSpacing: 14,
                          childAspectRatio: 0.88,
                        ),
                        delegate: SliverChildBuilderDelegate(
                          (context, index) {
                            final mod = modules[index];
                            return ModuleGridCard(
                              icon: mod.icon,
                              title: mod.title,
                              subtitle: mod.subtitle,
                              accentColor: mod.color,
                              badge: mod.badge,
                              onTap: () => _openModule(context, mod.screen),
                            );
                          },
                          childCount: modules.length,
                        ),
                      ),
              ),
            ],
          ),
        ),
      ),
      bottomNavigationBar: modules.isEmpty
          ? null
          : Padding(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
              child: FloatingNavBar(
                items: [
                  const NavItem(icon: Icons.dashboard_rounded, label: 'Inicio', onTap: _noop, active: true),
                  ...modules.take(3).map((mod) => NavItem(
                        icon: mod.icon,
                        label: mod.title,
                        onTap: () => _openModule(context, mod.screen),
                      )),
                ],
              ),
            ),
    );
  }
}

void _noop() {}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: AppColors.neonBlue.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.neonBlue.withValues(alpha: 0.35)),
      ),
      child: Text(
        label,
        style: const TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w700,
          color: AppColors.neonBlue,
        ),
      ),
    );
  }
}
