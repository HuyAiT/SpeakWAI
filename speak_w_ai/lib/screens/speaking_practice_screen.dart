import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:math' as math;

import '../utils/app_constants.dart';
import '../services/api_service.dart';

class SpeakingPracticeScreen extends StatefulWidget {
  const SpeakingPracticeScreen({super.key});

  @override
  State<SpeakingPracticeScreen> createState() => _SpeakingPracticeScreenState();
}

class _SpeakingPracticeScreenState extends State<SpeakingPracticeScreen>
    with TickerProviderStateMixin {
  // Recording
  final AudioRecorder _recorder = AudioRecorder();
  bool _isRecording = false;
  bool _isProcessing = false;
  String? _recordingPath;

  // Sentences
  int _currentSentenceIndex = 0;
  final List<Map<String, String>> _sentences = [
    {'en': 'Hello, how are you today?', 'vi': 'Xin chào, hôm nay bạn thế nào?'},
    {
      'en': 'I would like to order a coffee, please.',
      'vi': 'Tôi muốn gọi một ly cà phê.',
    },
    {
      'en': 'What time is the next train?',
      'vi': 'Chuyến tàu tiếp theo lúc mấy giờ?',
    },
    {
      'en': 'Can you help me find the nearest restaurant?',
      'vi': 'Bạn có thể giúp tôi tìm nhà hàng gần nhất không?',
    },
    {
      'en': 'Thank you very much for your help.',
      'vi': 'Cảm ơn bạn rất nhiều vì đã giúp đỡ.',
    },
  ];

  // Scores
  Map<String, dynamic>? _scores;
  Map<String, dynamic>? _feedback;
  bool _showResults = false;

  // Animations
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;
  late AnimationController _scoreController;

  @override
  void initState() {
    super.initState();
    _initRecorder();

    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1000),
    )..repeat(reverse: true);

    _pulseAnimation = Tween<double>(begin: 1.0, end: 1.15).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );

    _scoreController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    );
  }

  Future<void> _initRecorder() async {
    if (await _recorder.hasPermission()) {
      // Permission granted
    }
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _scoreController.dispose();
    _recorder.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Luyện nói'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
        actions: [
          if (_showResults)
            IconButton(
              icon: const Icon(Icons.refresh),
              onPressed: _resetPractice,
              tooltip: 'Thử lại',
            ),
        ],
      ),
      body: SafeArea(
        child: _showResults ? _buildResultsView() : _buildRecordingView(),
      ),
    );
  }

  Widget _buildRecordingView() {
    return Padding(
      padding: const EdgeInsets.all(AppConstants.spacingLarge),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Progress
          LinearProgressIndicator(
            value: (_currentSentenceIndex + 1) / _sentences.length,
            backgroundColor: AppConstants.backgroundColor,
            valueColor: const AlwaysStoppedAnimation<Color>(
              AppConstants.primaryColor,
            ),
          ),
          const SizedBox(height: AppConstants.spacingSmall),
          Text(
            'Câu ${_currentSentenceIndex + 1} / ${_sentences.length}',
            style: Theme.of(context).textTheme.bodyMedium,
            textAlign: TextAlign.center,
          ),

          const SizedBox(height: AppConstants.spacingXLarge),

          // Sentence Card
          Card(
            elevation: 4,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(
                AppConstants.borderRadiusLarge,
              ),
            ),
            child: Container(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(
                  AppConstants.borderRadiusLarge,
                ),
                gradient: LinearGradient(
                  colors: [Colors.white, Colors.blue.shade50],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
              ),
              padding: const EdgeInsets.all(AppConstants.spacingLarge),
              child: Column(
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: AppConstants.blueColor.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          '🎯 Đọc to câu sau',
                          style: GoogleFonts.nunito(
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                            color: AppConstants.blueColor,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: AppConstants.spacingMedium),
                  Text(
                    _sentences[_currentSentenceIndex]['en']!,
                    style: GoogleFonts.nunito(
                      fontSize: 24,
                      fontWeight: FontWeight.w700,
                      color: AppConstants.textPrimary,
                      height: 1.4,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: AppConstants.spacingSmall),
                  Text(
                    _sentences[_currentSentenceIndex]['vi']!,
                    style: GoogleFonts.nunito(
                      fontSize: 16,
                      color: AppConstants.textSecondary,
                      fontStyle: FontStyle.italic,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          ),

          const Spacer(),

          // Recording Button
          Center(
            child: GestureDetector(
              onTap: _isProcessing ? null : _toggleRecording,
              child: AnimatedBuilder(
                animation: _pulseAnimation,
                builder: (context, child) {
                  return Transform.scale(
                    scale: _isRecording ? _pulseAnimation.value : 1.0,
                    child: Container(
                      width: 140,
                      height: 140,
                      decoration: BoxDecoration(
                        gradient: _isRecording
                            ? const LinearGradient(
                                colors: [Color(0xFFFF6B6B), Color(0xFFFF8E53)],
                                begin: Alignment.topLeft,
                                end: Alignment.bottomRight,
                              )
                            : const LinearGradient(
                                colors: [Color(0xFF1CB0F6), Color(0xFF6C5CE7)],
                                begin: Alignment.topLeft,
                                end: Alignment.bottomRight,
                              ),
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(
                            color:
                                (_isRecording
                                        ? Colors.red
                                        : AppConstants.blueColor)
                                    .withOpacity(0.4),
                            blurRadius: 25,
                            spreadRadius: 8,
                          ),
                        ],
                      ),
                      child: _isProcessing
                          ? const Center(
                              child: CircularProgressIndicator(
                                color: Colors.white,
                                strokeWidth: 4,
                              ),
                            )
                          : Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(
                                  _isRecording
                                      ? Icons.stop_rounded
                                      : Icons.mic_rounded,
                                  size: 60,
                                  color: Colors.white,
                                ),
                                if (_isRecording) ...[
                                  const SizedBox(height: 4),
                                  Text(
                                    'DỪNG',
                                    style: GoogleFonts.nunito(
                                      fontSize: 12,
                                      fontWeight: FontWeight.w800,
                                      color: Colors.white,
                                    ),
                                  ),
                                ],
                              ],
                            ),
                    ),
                  );
                },
              ),
            ),
          ),

          const SizedBox(height: AppConstants.spacingLarge),

          // Status Text
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
            decoration: BoxDecoration(
              color: _isRecording
                  ? Colors.red.withOpacity(0.1)
                  : _isProcessing
                  ? AppConstants.blueColor.withOpacity(0.1)
                  : AppConstants.backgroundColor,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: _isRecording
                    ? Colors.red.withOpacity(0.3)
                    : _isProcessing
                    ? AppConstants.blueColor.withOpacity(0.3)
                    : Colors.transparent,
                width: 2,
              ),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (_isRecording) ...[
                  Container(
                    width: 10,
                    height: 10,
                    decoration: const BoxDecoration(
                      color: Colors.red,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    '🎙️ Đang ghi âm...',
                    style: GoogleFonts.nunito(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: Colors.red,
                    ),
                  ),
                ] else if (_isProcessing) ...[
                  const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    '⚡ Đang chấm điểm...',
                    style: GoogleFonts.nunito(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: AppConstants.blueColor,
                    ),
                  ),
                ] else ...[
                  Text(
                    '👆 Nhấn để bắt đầu ghi âm',
                    style: GoogleFonts.nunito(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: AppConstants.textSecondary,
                    ),
                  ),
                ],
              ],
            ),
          ),

          const Spacer(),

          // Skip button
          TextButton(
            onPressed: _nextSentence,
            child: Text(
              'Bỏ qua câu này →',
              style: GoogleFonts.nunito(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: AppConstants.textSecondary,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildResultsView() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppConstants.spacingLarge),
      child: Column(
        children: [
          // Total Score
          _buildMainScoreCircle(),

          const SizedBox(height: AppConstants.spacingXLarge),

          // Feedback
          if (_feedback != null) ...[
            Container(
              padding: const EdgeInsets.all(AppConstants.spacingMedium),
              decoration: BoxDecoration(
                color: _getGradeColor(
                  (_scores?['total'] ?? 0).toDouble(),
                ).withOpacity(0.1),
                borderRadius: BorderRadius.circular(
                  AppConstants.borderRadiusLarge,
                ),
                border: Border.all(
                  color: _getGradeColor(
                    (_scores?['total'] ?? 0).toDouble(),
                  ).withOpacity(0.3),
                ),
              ),
              child: Row(
                children: [
                  Text(
                    _getGradeEmoji((_scores?['total'] ?? 0).toDouble()),
                    style: const TextStyle(fontSize: 32),
                  ),
                  const SizedBox(width: AppConstants.spacingMedium),
                  Expanded(
                    child: Text(
                      _feedback?['overall'] ?? '',
                      style: GoogleFonts.nunito(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: AppConstants.textPrimary,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: AppConstants.spacingLarge),
          ],

          // Detail Scores
          Text(
            'Chi tiết điểm số',
            style: GoogleFonts.nunito(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: AppConstants.textPrimary,
            ),
          ),

          const SizedBox(height: AppConstants.spacingMedium),

          // Score Cards Grid
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            childAspectRatio: 1.1,
            children: [
              _buildScoreCard(
                'Độ chính xác',
                _scores?['accuracy'] ?? 0,
                Icons.check_circle_outline,
                const Color(0xFF58CC02),
                _feedback?['accuracy'],
              ),
              _buildScoreCard(
                'Độ lưu loát',
                _scores?['fluency'] ?? 0,
                Icons.waves,
                const Color(0xFF1CB0F6),
                _feedback?['fluency'],
              ),
              _buildScoreCard(
                'Ngữ điệu',
                _scores?['prosodic'] ?? 0,
                Icons.music_note,
                const Color(0xFFCE82FF),
                _feedback?['prosodic'],
              ),
              _buildScoreCard(
                'Hoàn thiện',
                _scores?['completeness'] ?? 0,
                Icons.done_all,
                const Color(0xFFFFAF00),
                null,
              ),
            ],
          ),

          const SizedBox(height: AppConstants.spacingXLarge),

          // Sentence practiced
          Container(
            padding: const EdgeInsets.all(AppConstants.spacingMedium),
            decoration: BoxDecoration(
              color: AppConstants.backgroundColor,
              borderRadius: BorderRadius.circular(
                AppConstants.borderRadiusMedium,
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Câu đã luyện:',
                  style: GoogleFonts.nunito(
                    fontSize: 14,
                    color: AppConstants.textSecondary,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  _sentences[_currentSentenceIndex]['en']!,
                  style: GoogleFonts.nunito(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: AppConstants.spacingXLarge),

          // Action Buttons
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: _retryCurrentSentence,
                  icon: const Icon(Icons.refresh),
                  label: const Text('Thử lại'),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: _nextSentence,
                  icon: const Icon(Icons.arrow_forward),
                  label: const Text('Câu tiếp theo'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppConstants.primaryColor,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildMainScoreCircle() {
    final score = (_scores?['total'] ?? 0).toDouble();

    return AnimatedBuilder(
      animation: _scoreController,
      builder: (context, child) {
        return Container(
          width: 200,
          height: 200,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: LinearGradient(
              colors: [
                _getGradeColor(score).withOpacity(0.1),
                _getGradeColor(score).withOpacity(0.05),
              ],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          child: Stack(
            alignment: Alignment.center,
            children: [
              // Background circle
              SizedBox(
                width: 180,
                height: 180,
                child: CircularProgressIndicator(
                  value: 1,
                  strokeWidth: 12,
                  backgroundColor: Colors.grey.shade200,
                  valueColor: const AlwaysStoppedAnimation<Color>(
                    Colors.transparent,
                  ),
                ),
              ),
              // Progress circle
              SizedBox(
                width: 180,
                height: 180,
                child: TweenAnimationBuilder<double>(
                  tween: Tween(begin: 0, end: score / 100),
                  duration: const Duration(milliseconds: 1500),
                  curve: Curves.easeOutCubic,
                  builder: (context, value, child) {
                    return CircularProgressIndicator(
                      value: value,
                      strokeWidth: 12,
                      strokeCap: StrokeCap.round,
                      backgroundColor: Colors.transparent,
                      valueColor: AlwaysStoppedAnimation<Color>(
                        _getGradeColor(score),
                      ),
                    );
                  },
                ),
              ),
              // Score text
              Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TweenAnimationBuilder<double>(
                    tween: Tween(begin: 0, end: score),
                    duration: const Duration(milliseconds: 1500),
                    curve: Curves.easeOutCubic,
                    builder: (context, value, child) {
                      return Text(
                        value.toInt().toString(),
                        style: GoogleFonts.nunito(
                          fontSize: 56,
                          fontWeight: FontWeight.w900,
                          color: _getGradeColor(score),
                        ),
                      );
                    },
                  ),
                  Text(
                    'Điểm tổng',
                    style: GoogleFonts.nunito(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: AppConstants.textSecondary,
                    ),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildScoreCard(
    String label,
    dynamic score,
    IconData icon,
    Color color,
    String? feedback,
  ) {
    final scoreValue =
        (score is int ? score.toDouble() : (score ?? 0.0)) as double;

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: color.withOpacity(0.15),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Stack(
        children: [
          Positioned(
            right: -10,
            top: -10,
            child: Icon(icon, size: 60, color: color.withOpacity(0.1)),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(icon, color: color, size: 20),
                ),
                const Spacer(),
                TweenAnimationBuilder<double>(
                  tween: Tween(begin: 0, end: scoreValue),
                  duration: const Duration(milliseconds: 1200),
                  curve: Curves.easeOutCubic,
                  builder: (context, value, child) {
                    return Text(
                      '${value.toInt()}',
                      style: GoogleFonts.nunito(
                        fontSize: 32,
                        fontWeight: FontWeight.w900,
                        color: color,
                      ),
                    );
                  },
                ),
                Text(
                  label,
                  style: GoogleFonts.nunito(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: AppConstants.textSecondary,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Color _getGradeColor(double score) {
    if (score >= 85) return const Color(0xFF58CC02);
    if (score >= 70) return const Color(0xFF1CB0F6);
    if (score >= 50) return const Color(0xFFFFAF00);
    return const Color(0xFFEA4335);
  }

  String _getGradeEmoji(double score) {
    if (score >= 85) return '🌟';
    if (score >= 70) return '👍';
    if (score >= 50) return '💪';
    return '📚';
  }

  Future<void> _toggleRecording() async {
    if (_isRecording) {
      await _stopRecording();
    } else {
      await _startRecording();
    }
  }

  Future<void> _startRecording() async {
    try {
      if (await _recorder.hasPermission()) {
        final dir = await getTemporaryDirectory();
        final path =
            '${dir.path}/recording_${DateTime.now().millisecondsSinceEpoch}.wav';

        await _recorder.start(
          RecordConfig(
            encoder: AudioEncoder.wav,
            sampleRate: 16000,
            numChannels: 1,
          ),
          path: path,
        );

        setState(() {
          _isRecording = true;
          _recordingPath = path;
        });
      }
    } catch (e) {
      _showError('Không thể bắt đầu ghi âm: $e');
    }
  }

  Future<void> _stopRecording() async {
    try {
      final path = await _recorder.stop();

      setState(() {
        _isRecording = false;
        _isProcessing = true;
      });

      if (path != null) {
        await _processRecording(path);
      }
    } catch (e) {
      setState(() {
        _isRecording = false;
        _isProcessing = false;
      });
      _showError('Lỗi khi dừng ghi âm: $e');
    }
  }

  Future<void> _processRecording(String filePath) async {
    try {
      // Read audio file and convert to base64
      final file = File(filePath);
      final bytes = await file.readAsBytes();
      final base64Audio = base64Encode(bytes);

      // Get token
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString(AppConstants.tokenKey);

      if (token == null) {
        throw Exception('Chưa đăng nhập');
      }

      // Call API
      final result = await ApiService.scorePronunciation(
        token,
        base64Audio,
        expectedText: _sentences[_currentSentenceIndex]['en'],
      );

      setState(() {
        _isProcessing = false;
        _scores = result['scores'];
        _feedback = result['feedback'];
        _showResults = true;
      });

      _scoreController.forward();

      // Clean up temp file
      await file.delete();
    } catch (e) {
      setState(() {
        _isProcessing = false;
      });
      _showError(e.toString().replaceAll('Exception:', ''));
    }
  }

  void _nextSentence() {
    if (_currentSentenceIndex < _sentences.length - 1) {
      setState(() {
        _currentSentenceIndex++;
        _showResults = false;
        _scores = null;
        _feedback = null;
      });
      _scoreController.reset();
    } else {
      _showCompletionDialog();
    }
  }

  void _retryCurrentSentence() {
    setState(() {
      _showResults = false;
      _scores = null;
      _feedback = null;
    });
    _scoreController.reset();
  }

  void _resetPractice() {
    setState(() {
      _currentSentenceIndex = 0;
      _showResults = false;
      _scores = null;
      _feedback = null;
    });
    _scoreController.reset();
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: AppConstants.errorColor,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
    );
  }

  void _showCompletionDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Row(
          children: [
            const Text('🎉 ', style: TextStyle(fontSize: 28)),
            Text(
              'Hoàn thành!',
              style: GoogleFonts.nunito(fontWeight: FontWeight.w700),
            ),
          ],
        ),
        content: Text(
          'Bạn đã hoàn thành tất cả các câu luyện nói hôm nay. Tiếp tục luyện tập mỗi ngày để cải thiện kỹ năng nhé!',
          style: GoogleFonts.nunito(fontSize: 16),
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              context.pop();
            },
            child: const Text('Quay lại'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.of(context).pop();
              _resetPractice();
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppConstants.primaryColor,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
              ),
            ),
            child: const Text('Làm lại', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }
}
