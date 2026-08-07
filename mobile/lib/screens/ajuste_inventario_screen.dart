import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/inventario_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';

class AjusteInventarioScreen extends StatefulWidget {
  const AjusteInventarioScreen({super.key, required this.producto});

  final ProductoInventario producto;

  @override
  State<AjusteInventarioScreen> createState() => _AjusteInventarioScreenState();
}

class _AjusteInventarioScreenState extends State<AjusteInventarioScreen> {
  String _tipo = 'entrada';
  String _motivo = InventarioService.motivosEntrada.first.$1;
  final _cantidadCtrl = TextEditingController();
  bool _guardando = false;

  @override
  void dispose() {
    _cantidadCtrl.dispose();
    super.dispose();
  }

  List<(String, String)> get _motivos =>
      _tipo == 'entrada' ? InventarioService.motivosEntrada : InventarioService.motivosSalida;

  Future<void> _guardar() async {
    final cantidad = int.tryParse(_cantidadCtrl.text);
    if (cantidad == null || cantidad <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ingresa una cantidad válida')),
      );
      return;
    }

    setState(() => _guardando = true);
    try {
      await context.read<AppState>().inventario.ajustarStock(
            productoId: widget.producto.producto.id,
            tipo: _tipo,
            cantidad: cantidad,
            motivo: _motivo,
          );
      if (!mounted) return;
      Navigator.pop(context, true);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$e'), backgroundColor: const Color(0xFFEF4444)),
        );
      }
    } finally {
      if (mounted) setState(() => _guardando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final p = widget.producto;

    return FuturisticScaffold(
      title: 'Ajuste de Inventario',
      accentColor: AppColors.violet,
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: FilledButton.icon(
            onPressed: _guardando ? null : _guardar,
            icon: _guardando
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                : Icon(_tipo == 'entrada' ? Icons.add_rounded : Icons.remove_rounded),
            label: Text(_guardando ? 'Aplicando…' : 'Registrar ajuste'),
            style: FilledButton.styleFrom(
              minimumSize: const Size(double.infinity, 52),
              backgroundColor: _tipo == 'entrada' ? AppColors.emerald : AppColors.amber,
              foregroundColor: AppColors.bgDeep,
            ),
          ),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          GlassContainer(
            accentColor: AppColors.violet,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(p.producto.nombre, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 17)),
                const SizedBox(height: 6),
                Text(
                  'Stock disponible: ${p.stockTotal} uds',
                  style: const TextStyle(color: AppColors.textMuted),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _TipoChip(
                  label: 'Entrada',
                  subtitle: 'Compra / recepción',
                  icon: Icons.arrow_downward_rounded,
                  color: AppColors.emerald,
                  selected: _tipo == 'entrada',
                  onTap: () => setState(() {
                    _tipo = 'entrada';
                    _motivo = InventarioService.motivosEntrada.first.$1;
                  }),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _TipoChip(
                  label: 'Salida',
                  subtitle: 'Merma / daño',
                  icon: Icons.arrow_upward_rounded,
                  color: AppColors.amber,
                  selected: _tipo == 'salida',
                  onTap: () => setState(() {
                    _tipo = 'salida';
                    _motivo = InventarioService.motivosSalida.first.$1;
                  }),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          GlassContainer(
            accentColor: _tipo == 'entrada' ? AppColors.emerald : AppColors.amber,
            child: Column(
              children: [
                DropdownButtonFormField<String>(
                  value: _motivo,
                  decoration: const InputDecoration(
                    labelText: 'Motivo del ajuste',
                    prefixIcon: Icon(Icons.notes_rounded),
                  ),
                  dropdownColor: AppColors.bgElevated,
                  items: _motivos.map((m) => DropdownMenuItem(value: m.$1, child: Text(m.$2))).toList(),
                  onChanged: (v) => setState(() => _motivo = v!),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _cantidadCtrl,
                  keyboardType: TextInputType.number,
                  style: const TextStyle(color: AppColors.textPrimary),
                  decoration: InputDecoration(
                    labelText: 'Cantidad',
                    prefixIcon: const Icon(Icons.numbers_rounded),
                    hintText: _tipo == 'salida' ? 'Máx. ${p.stockTotal}' : null,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _TipoChip extends StatelessWidget {
  const _TipoChip({
    required this.label,
    required this.subtitle,
    required this.icon,
    required this.color,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final String subtitle;
  final IconData icon;
  final Color color;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 10),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            color: selected ? color.withValues(alpha: 0.15) : AppColors.bgElevated,
            border: Border.all(color: selected ? color : AppColors.glassBorder, width: selected ? 1.5 : 1),
          ),
          child: Column(
            children: [
              Icon(icon, color: selected ? color : AppColors.textMuted),
              const SizedBox(height: 6),
              Text(label, style: TextStyle(fontWeight: FontWeight.w700, color: selected ? color : AppColors.textMuted)),
              Text(subtitle, style: Theme.of(context).textTheme.bodySmall, textAlign: TextAlign.center),
            ],
          ),
        ),
      ),
    );
  }
}
