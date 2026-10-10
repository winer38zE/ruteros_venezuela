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
import 'nueva_venta_screen.dart';
import 'nuevo_cobro_screen.dart';
import 'registrar_movimiento_screen.dart';
import 'registrar_usuario_screen.dart';
import 'usuarios_screen.dart';
import 'clientes_list_screen.dart';
import 'tasas_screen.dart';
import 'panel_cobranza_screen.dart';
import 'proveedores_screen.dart';
import 'rutas_list_screen.dart';
import 'rutas_resumen_screen.dart';

class _QuickAction {
  const _QuickAction({
    required this.label,
    required this.icon,
    required this.color,
    required this.screen,
    required this.visible,
  });

  final String label;
  final IconData icon;
  final Color color;
  final Widget screen;
  final bool visible;
}

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
    if (user.rolAcceso == 'owner') {
      return _modulosOwner();
    }
    return _modulosEmpleado(state);
  }

  List<_ModuleDef> _modulosOwner() => const [
        _ModuleDef(
          id: 'ventas',
          icon: Icons.point_of_sale_rounded,
          title: 'Ventas',
          subtitle: 'Registra ventas con detalle e inventario',
          color: AppColors.emerald,
          screen: VentasListScreen(),
          badge: 'LIVE',
        ),
        _ModuleDef(
          id: 'cobros',
          icon: Icons.payments_rounded,
          title: 'Cobros',
          subtitle: 'Cobra ventas pendientes en calle',
          color: AppColors.neonCyan,
          screen: CobrosListScreen(),
          badge: 'FIELD',
        ),
        _ModuleDef(
          id: 'panel_cobranza',
          icon: Icons.table_chart_rounded,
          title: 'Panel Cobranza',
          subtitle: 'Tabla estilo Excel con abonos rápidos',
          color: AppColors.neonBlue,
          screen: PanelCobranzaScreen(),
          badge: 'EXCEL',
        ),
        _ModuleDef(
          id: 'rutas',
          icon: Icons.route_rounded,
          title: 'Ruta del Día',
          subtitle: 'Clientes ordenados con navegación GPS',
          color: AppColors.amber,
          screen: RutasListScreen(),
          badge: 'GPS',
        ),
        _ModuleDef(
          id: 'clientes',
          icon: Icons.groups_2_rounded,
          title: 'Gestión de Clientes',
          subtitle: 'Scoring, buró y referencias',
          color: AppColors.neonCyan,
          screen: ClientesListScreen(),
          badge: 'KYC',
        ),
        _ModuleDef(
          id: 'inventario',
          icon: Icons.inventory_2_rounded,
          title: 'Gestión de Inventario',
          subtitle: 'Productos, stock y ajustes',
          color: AppColors.violet,
          screen: InventarioScreen(),
          badge: 'STOCK',
        ),
        _ModuleDef(
          id: 'proveedores',
          icon: Icons.local_shipping_rounded,
          title: 'Proveedores',
          subtitle: 'Deudas y cuentas por pagar',
          color: AppColors.violet,
          screen: ProveedoresScreen(),
          badge: 'CxP',
        ),
        _ModuleDef(
          id: 'tasas',
          icon: Icons.currency_exchange_rounded,
          title: 'Tasas de Cambio',
          subtitle: 'BCV, paralelo y sincronización auto',
          color: AppColors.amber,
          screen: TasasScreen(),
          badge: 'FX',
        ),
        _ModuleDef(
          id: 'rutas_resumen',
          icon: Icons.analytics_rounded,
          title: 'Resumen Rutas',
          subtitle: 'Avance diario de cobradores en calle',
          color: AppColors.violet,
          screen: RutasResumenScreen(),
          badge: 'LIVE',
        ),
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
      ];

  List<_ModuleDef> _modulosEmpleado(AppState state) {
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
      modules.add(const _ModuleDef(
        id: 'panel_cobranza',
        icon: Icons.table_chart_rounded,
        title: 'Panel Cobranza',
        subtitle: 'Tabla estilo Excel con abonos rápidos',
        color: AppColors.neonBlue,
        screen: PanelCobranzaScreen(),
        badge: 'EXCEL',
      ));
    }

    if (state.puedeCobrar || state.puedeVender) {
      modules.add(const _ModuleDef(
        id: 'rutas',
        icon: Icons.route_rounded,
        title: 'Ruta del Día',
        subtitle: 'Clientes ordenados con navegación GPS',
        color: AppColors.amber,
        screen: RutasListScreen(),
        badge: 'GPS',
      ));
    }

    if (state.puedeVender) {
      modules.add(const _ModuleDef(
        id: 'clientes',
        icon: Icons.groups_2_rounded,
        title: 'Gestión de Clientes',
        subtitle: 'Scoring, buró y referencias',
        color: AppColors.neonCyan,
        screen: ClientesListScreen(),
        badge: 'KYC',
      ));
      modules.add(const _ModuleDef(
        id: 'inventario',
        icon: Icons.inventory_2_rounded,
        title: 'Gestión de Inventario',
        subtitle: 'Consulta de stock en calle',
        color: AppColors.violet,
        screen: InventarioScreen(),
        badge: 'STOCK',
      ));
    }

    return modules;
  }

  List<_QuickAction> _quickActions(AppState state) => [
        _QuickAction(
          label: 'Registrar Usuario',
          icon: Icons.person_add_alt_1_rounded,
          color: AppColors.neonBlue,
          screen: const RegistrarUsuarioScreen(),
          visible: state.esOwner,
        ),
        _QuickAction(
          label: 'Registrar Venta',
          icon: Icons.add_shopping_cart_rounded,
          color: AppColors.emerald,
          screen: const NuevaVentaScreen(),
          visible: state.puedeVender,
        ),
        _QuickAction(
          label: 'Registrar Cobro',
          icon: Icons.price_check_rounded,
          color: AppColors.neonCyan,
          screen: const NuevoCobroScreen(),
          visible: state.puedeCobrar,
        ),
        _QuickAction(
          label: 'Registrar Gasto',
          icon: Icons.receipt_long_rounded,
          color: AppColors.amber,
          screen: const RegistrarMovimientoScreen(soloGasto: true),
          visible: state.esOwner,
        ),
      ].where((a) => a.visible).toList();

  void _openModule(BuildContext context, Widget screen) {
    Navigator.push(context, MaterialPageRoute(builder: (_) => screen));
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final user = state.usuario!;
    final modules = _modules(state);
    final quickActions = _quickActions(state);

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
                            Text(state.esOwner ? 'Panel de Control' : 'Panel operativo'),
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
              if (quickActions.isNotEmpty)
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Accesos rápidos',
                          style: TextStyle(
                            fontWeight: FontWeight.w800,
                            fontSize: 15,
                            color: AppColors.textPrimary,
                          ),
                        ),
                        const SizedBox(height: 10),
                        SizedBox(
                          height: 92,
                          child: ListView.separated(
                            scrollDirection: Axis.horizontal,
                            itemCount: quickActions.length,
                            separatorBuilder: (_, __) => const SizedBox(width: 10),
                            itemBuilder: (context, index) {
                              final action = quickActions[index];
                              return _QuickActionChip(
                                label: action.label,
                                icon: action.icon,
                                color: action.color,
                                onTap: () => _openModule(context, action.screen),
                              );
                            },
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                if (state.esOwner)
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(20, 12, 20, 0),
                    child: GlassContainer(
                      accentColor: AppColors.neonBlue,
                      onTap: () => _openModule(context, const UsuariosScreen()),
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                      child: Row(
                        children: [
                          const Icon(Icons.groups_rounded, color: AppColors.neonBlue),
                          const SizedBox(width: 12),
                          const Expanded(
                            child: Text(
                              'Gestionar equipo y roles',
                              style: TextStyle(fontWeight: FontWeight.w700),
                            ),
                          ),
                          Icon(Icons.chevron_right, color: AppColors.neonBlue.withValues(alpha: 0.7)),
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

class _QuickActionChip extends StatelessWidget {
  const _QuickActionChip({
    required this.label,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  final String label;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: GlassContainer(
          accentColor: color,
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          child: SizedBox(
            width: 118,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(icon, color: color, size: 22),
                const SizedBox(height: 8),
                Text(
                  label,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

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
