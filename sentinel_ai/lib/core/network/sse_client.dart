import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/app_config.dart';

/// Server-Sent Events client.
///
/// Connects to an SSE endpoint and yields parsed event maps as a stream.
/// Automatically reconnects after [AppConfig.sseReconnectDelay] on error.
class SseClient {
  SseClient._();

  /// Returns a broadcast stream of parsed SSE event data maps.
  /// Each yielded map contains at minimum a `type` key.
  static Stream<Map<String, dynamic>> subscribe(String url) async* {
    while (true) {
      try {
        final request = http.Request('GET', Uri.parse(url));
        request.headers['Accept'] = 'text/event-stream';
        request.headers['Cache-Control'] = 'no-cache';

        final client = http.Client();
        final response = await client.send(request).timeout(
          const Duration(minutes: 10),
        );

        if (response.statusCode != 200) {
          client.close();
          await Future.delayed(AppConfig.sseReconnectDelay);
          continue;
        }

        String eventType = 'message';
        final buffer = StringBuffer();

        await for (final chunk in response.stream
            .transform(utf8.decoder)
            .transform(const LineSplitter())) {
          if (chunk.startsWith('event:')) {
            eventType = chunk.substring(6).trim();
          } else if (chunk.startsWith('data:')) {
            buffer.write(chunk.substring(5).trim());
          } else if (chunk.isEmpty && buffer.isNotEmpty) {
            // Blank line = dispatch event
            try {
              final data = json.decode(buffer.toString());
              if (data is Map<String, dynamic>) {
                data['type'] ??= eventType;
                yield data;
              }
            } catch (_) {
              // Ignore malformed JSON frames
            }
            buffer.clear();
            eventType = 'message';
          }
        }

        client.close();
      } catch (_) {
        // Connection dropped — reconnect after delay
      }
      await Future.delayed(AppConfig.sseReconnectDelay);
    }
  }
}
