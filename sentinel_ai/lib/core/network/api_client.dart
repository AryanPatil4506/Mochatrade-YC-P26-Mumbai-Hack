import 'package:dio/dio.dart';
import '../../core/config/app_config.dart';

/// Factory for creating pre-configured Dio instances for each service.
class ApiClient {
  ApiClient._();

  static Dio _build(String baseUrl) {
    final dio = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: AppConfig.httpTimeout,
        receiveTimeout: AppConfig.httpTimeout,
        headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
        validateStatus: (status) => status != null && status < 600,
      ),
    );
    dio.interceptors.add(_LogInterceptor());
    return dio;
  }

  static final Dio agent = _build(AppConfig.agentBaseUrl);
  static final Dio gateway = _build(AppConfig.gatewayBaseUrl);
  static final Dio executor = _build(AppConfig.executorBaseUrl);
}

class _LogInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    // ignore: avoid_print
    print('[API] ${options.method} ${options.uri}');
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    // ignore: avoid_print
    print('[API ERROR] ${err.message} — ${err.response?.statusCode}');
    handler.next(err);
  }
}
