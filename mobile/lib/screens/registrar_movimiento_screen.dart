import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/finanzas_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';

class RegistrarMovimientoScreen extends StatefulWidget {
  const RegistrarMovimientoScreen({super.key});

  @override
  State<RegistrarMovimientoScreen> createState() => _RegistrarMovimientoScreenState();
}

class _RegistrarMovimientoScreenState extends State<RegistrarMovimientoScreen> {
  String _tipo = 'salida';
  String _categoria = 'gasto_moto';
  final _montoCtrl = TextEditingController();
  final _descCtrl = TextEditingController();
  bool _guardando = false;

  @override
  void dispose() {
    _montoCtrl.dispose();
    _descCtrl.dispose();
    super.dispose();
  }

  List<(String, String)> get _categorias =>
      _tipo == 'entrada' ? FinanzasService.categoriasEntrada : FinanzasService.categoriasSalida;

  Future<void> _guardar() async {
    final monto = double.tryParse(_montoCtrl.text);
    if (monto == null || monto <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ingresa un monto válido')),
      );
      return;
    }
    if (_descCtrl.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ingresa una descripción')),
      );
      return;
    }

    setState(() => _guardando = true);
    try {
      await context.read<AppState>().finanzas.registrarMovimiento(
            tipo: _tipo,
            categoria: _categoria,
            montoUsd: monto,
            descripcion: _descCtrl.text.trim(),
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
    return FuturisticScaffold(
      title: 'Registrar Movimiento',
      accentColor: AppColors.amber,
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: FilledButton.icon(
            onPressed: _guardando ? null : _guardar,
            icon: _guardando
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.save_rounded),
            label: Text(_guardando ? 'Guardando...' : 'Registrar'),
            style: FilledButton.styleFrom(
              minimumSize: const Size(double.infinity, 52),
              backgroundColor: AppColors.amber,
              foregroundColor: AppColors.bgDeep,
            ),
          ),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(
            children: [
              Expanded(
                child: _TipoChip(
                  label: 'Entrada',
                  icon: Icons.arrow_downward_rounded,
                  color: AppColors.emerald,
                  selected: _tipo == 'entrada',
                  onTap: () => setState(() {
                    _tipo = 'entrada';
                    _categoria = FinanzasService.categoriasEntrada.first.$1;
                  }),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _TipoChip(
                  label: 'Salida',
                  icon: Icons.arrow_upward_rounded,
                  color: AppColors.amber,
                  selected: _tipo == 'salida',
                  onTap: () => setState(() {
                    _tipo = 'salida';
                    _categoria = FinanzasService.categoriasSalida.first.$1;
                  }),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          GlassContainer(
            accentColor: _tipo == 'entrada' ? AppColors.emerald : AppColors.amber,
            child: Column(
              children: [
                DropdownButtonFormField<String>(
                  value: _categoria,
                  decoration: const InputDecoration(labelText: 'Categoría', prefixIcon: Icon(Icons.category_rounded)),
                  dropdownColor: AppColors.bgElevated,
                  items: _categorias
                      .map((c) => DropdownMenuItem(value: c.$1, child: Text(c.$2)))
                      .toList(),
                  onChanged: (v) => setState(() => _categoria = v!),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _montoCtrl,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  style: const TextStyle(color: AppColors.textPrimary),
                  decoration: const InputDecoration(
                    labelText: 'Monto USD',
                    prefixIcon: Icon(Icons.attach_money_rounded),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _descCtrl,
                  maxLines: 2,
                  style: const TextStyle(color: AppColors.textPrimary),
                  decoration: const InputDecoration(
                    labelText: 'Descripción',
                    prefixIcon: Icon(Icons.notes_rounded),
                    hintText: 'Ej: Gasolina moto ruta norte',
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
    required this.icon,
    required this.color,
    required this.selected,
    required this.onTap,
  });

  final String label;
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
          padding: const EdgeInsets.symmetric(vertical: 16),
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
            ],
          ),
        ),
      ),
    );
  }
}
