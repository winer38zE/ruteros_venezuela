import 'package:shared_preferences/shared_preferences.dart';

/// Últimas tasas conocidas para mostrar en login (sin auth).
class TasasLoginCache {
  TasasLoginCache._();

  static const _kBcv = 'tasas_login_usd_bcv_bs';
  static const _kParalelo = 'tasas_login_usd_paralelo_bs';

  static Future<void> guardar({
    required double usdBcvBs,
    required double usdParaleloBs,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setDouble(_kBcv, usdBcvBs);
    await prefs.setDouble(_kParalelo, usdParaleloBs);
  }

  static Future<({double? bcv, double? paralelo})> leer() async {
    final prefs = await SharedPreferences.getInstance();
    return (
      bcv: prefs.getDouble(_kBcv),
      paralelo: prefs.getDouble(_kParalelo),
    );
  }
}
