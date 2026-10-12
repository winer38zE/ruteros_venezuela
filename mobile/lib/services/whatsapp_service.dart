import 'dart:typed_data';

import 'api_client.dart';

class WhatsappService {
  WhatsappService(this._api);
  final ApiClient _api;

  /// Envía la foto del comprobante al backend, que la reenvía por Evolution API.
  /// Si [telefono] va vacío, el servidor usa el WhatsApp del administrador.
  Future<String> enviarComprobanteServidor(
    String telefono,
    String caption,
    Uint8List imagen, {
    String nombreArchivo = 'comprobante.jpg',
  }) async {
    final data = await _api.postMultipart(
      '/whatsapp/enviar-comprobante',
      {
        'telefono': telefono.trim(),
        'caption': caption,
      },
      fileField: 'file',
      bytes: imagen,
      filename: nombreArchivo,
    );
    if (data is Map && data['message'] is String) {
      return data['message'] as String;
    }
    return 'Comprobante enviado por WhatsApp exitosamente';
  }
}
