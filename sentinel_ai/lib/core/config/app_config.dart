/// Sentinel AI — App Configuration
///
/// URLs are read from --dart-define at build time.
/// Android Emulator default: 10.0.2.2 maps to host localhost.
/// Physical device: set to your machine's LAN IP via --dart-define.
library;

const String _kDefaultAgentUrl = String.fromEnvironment(
  'AGENT_URL',
  defaultValue: 'http://10.0.2.2:8001',
);

const String _kDefaultGatewayUrl = String.fromEnvironment(
  'GATEWAY_URL',
  defaultValue: 'http://10.0.2.2:8002',
);

const String _kDefaultExecutorUrl = String.fromEnvironment(
  'EXECUTOR_URL',
  defaultValue: 'http://10.0.2.2:8003',
);

class AppConfig {
  AppConfig._();

  static const String agentBaseUrl = _kDefaultAgentUrl;
  static const String gatewayBaseUrl = _kDefaultGatewayUrl;
  static const String executorBaseUrl = _kDefaultExecutorUrl;

  static const Duration httpTimeout = Duration(seconds: 30);
  static const Duration sseReconnectDelay = Duration(seconds: 3);
  static const int auditTimelineDefaultLimit = 50;
}
