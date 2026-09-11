import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/theme/app_theme.dart';
import '../../core/config/app_config.dart';
import '../../core/network/sse_client.dart';
import '../../repositories/session_repository.dart';
import '../../services/agent_service.dart';
import '../../widgets/sentinel_drawer.dart';

const _sessionRepo = SessionRepository();

final chatSessionProvider = StateProvider<String?>((ref) => null);

class ChatMessage {
  const ChatMessage({
    required this.sender, // 'user' | 'agent' | 'system'
    required this.text,
    required this.timestamp,
    this.thought,
  });

  final String sender;
  final String text;
  final String? thought;
  final DateTime timestamp;
}

final chatMessagesProvider = StateProvider<List<ChatMessage>>((ref) => []);

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _textController = TextEditingController();
  final _scrollController = ScrollController();
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _initSession();
  }

  Future<void> _initSession() async {
    final currentSession = ref.read(chatSessionProvider);
    if (currentSession == null) {
      try {
        final session = await _sessionRepo.createSession('customer-support-agent');
        ref.read(chatSessionProvider.notifier).state = session.sessionId;
        _listenToSessionEvents(session.sessionId);
      } catch (e) {
        // Log or handle
      }
    } else {
      _listenToSessionEvents(currentSession);
    }
  }

  void _listenToSessionEvents(String sessionId) {
    final stream = SseClient.subscribe('${AppConfig.agentBaseUrl}/v1/agent/sessions/$sessionId/events');
    stream.listen((event) {
      final eventType = event['type'];
      if (eventType == 'token' || eventType == 'message') {
        final content = event['content'] ?? event['data']?['content'] ?? '';
        if (content.isNotEmpty) {
          final msgs = List<ChatMessage>.from(ref.read(chatMessagesProvider));
          if (msgs.isNotEmpty && msgs.last.sender == 'agent') {
            final last = msgs.removeLast();
            msgs.add(ChatMessage(
              sender: 'agent',
              text: last.text + content.toString(),
              timestamp: DateTime.now(),
            ));
          } else {
            msgs.add(ChatMessage(
              sender: 'agent',
              text: content.toString(),
              timestamp: DateTime.now(),
            ));
          }
          ref.read(chatMessagesProvider.notifier).state = msgs;
          _scrollToBottom();
        }
      }
    });
  }

  Future<void> _sendMessage() async {
    final text = _textController.text.trim();
    if (text.isEmpty) return;

    final sessionId = ref.read(chatSessionProvider);
    if (sessionId == null) return;

    _textController.clear();
    final msgs = List<ChatMessage>.from(ref.read(chatMessagesProvider));
    msgs.add(ChatMessage(sender: 'user', text: text, timestamp: DateTime.now()));
    ref.read(chatMessagesProvider.notifier).state = msgs;
    _scrollToBottom();

    setState(() => _isLoading = true);
    try {
      await AgentService.sendMessage(sessionId, text);
    } catch (e) {
      final updated = List<ChatMessage>.from(ref.read(chatMessagesProvider));
      updated.add(ChatMessage(
        sender: 'system',
        text: 'Error sending message: $e',
        timestamp: DateTime.now(),
      ));
      ref.read(chatMessagesProvider.notifier).state = updated;
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final messages = ref.watch(chatMessagesProvider);
    final sessionId = ref.watch(chatSessionProvider);

    return Scaffold(
      backgroundColor: AppTheme.background,
      drawer: const SentinelDrawer(currentRoute: '/chat'),
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Autonomous Agent Chat', style: TextStyle(fontSize: 16)),
            Text(
              sessionId != null ? 'Session: ${sessionId.substring(0, 8)}...' : 'Connecting...',
              style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
            ),
          ],
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: messages.isEmpty
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.all(32),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.smart_toy_outlined, color: AppTheme.amber, size: 48),
                          const SizedBox(height: 16),
                          Text(
                            'Autonomous Agent Ready',
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            'Send a prompt to test LangGraph decisions, taint propagation, and Gateway policy checks.',
                            textAlign: TextAlign.center,
                            style: TextStyle(color: AppTheme.textMuted, fontSize: 13),
                          ),
                        ],
                      ),
                    ),
                  )
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.all(16),
                    itemCount: messages.length,
                    itemBuilder: (context, index) {
                      final msg = messages[index];
                      final isUser = msg.sender == 'user';
                      final isSystem = msg.sender == 'system';

                      if (isSystem) {
                        return Container(
                          margin: const EdgeInsets.symmetric(vertical: 6),
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: AppTheme.redDim,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(msg.text, style: const TextStyle(color: AppTheme.red, fontSize: 12)),
                        );
                      }

                      return Align(
                        alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                        child: Container(
                          margin: const EdgeInsets.symmetric(vertical: 6),
                          padding: const EdgeInsets.all(14),
                          constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.78),
                          decoration: BoxDecoration(
                            color: isUser ? AppTheme.amber : AppTheme.surface,
                            borderRadius: BorderRadius.circular(12),
                            border: isUser ? null : Border.all(color: AppTheme.border),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                msg.text,
                                style: TextStyle(
                                  color: isUser ? Colors.black : AppTheme.textPrimary,
                                  fontSize: 14,
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
          ),
          if (_isLoading)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 4),
              child: LinearProgressIndicator(color: AppTheme.amber, backgroundColor: AppTheme.surface),
            ),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: const BoxDecoration(
              color: AppTheme.surface,
              border: Border(top: BorderSide(color: AppTheme.border)),
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _textController,
                    decoration: InputDecoration(
                      hintText: 'Enter command for agent...',
                      hintStyle: const TextStyle(color: AppTheme.textMuted),
                      fillColor: AppTheme.surfaceVariant,
                      filled: true,
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                        borderSide: BorderSide.none,
                      ),
                    ),
                    onSubmitted: (_) => _sendMessage(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(
                  style: IconButton.styleFrom(backgroundColor: AppTheme.amber, foregroundColor: Colors.black),
                  icon: const Icon(Icons.send),
                  onPressed: _isLoading ? null : _sendMessage,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
