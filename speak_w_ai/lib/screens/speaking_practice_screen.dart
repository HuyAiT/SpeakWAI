import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import '../utils/app_constants.dart';
import '../widgets/custom_button.dart';

class SpeakingPracticeScreen extends StatefulWidget {
  const SpeakingPracticeScreen({super.key});

  @override
  State<SpeakingPracticeScreen> createState() => _SpeakingPracticeScreenState();
}

class _SpeakingPracticeScreenState extends State<SpeakingPracticeScreen> {
  bool _isRecording = false;
  bool _isProcessing = false;
  String _currentSentence = 'Hello, how are you today?';
  String _userSpeech = '';
  int _currentSentenceIndex = 0;

  final List<String> _sentences = [
    'Hello, how are you today?',
    'I would like to order a coffee, please.',
    'What time is the next train?',
    'Can you help me find the nearest restaurant?',
    'Thank you very much for your help.',
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Luyện nói'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () {
            context.pop();
          },
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(AppConstants.spacingLarge),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Progress Indicator
              LinearProgressIndicator(
                value: (_currentSentenceIndex + 1) / _sentences.length,
                backgroundColor: AppConstants.backgroundColor,
                valueColor: const AlwaysStoppedAnimation<Color>(AppConstants.primaryColor),
              ),
              
              const SizedBox(height: AppConstants.spacingMedium),
              
              // Progress Text
              Text(
                'Câu ${_currentSentenceIndex + 1} / ${_sentences.length}',
                style: Theme.of(context).textTheme.bodyMedium,
                textAlign: TextAlign.center,
              ),
              
              const SizedBox(height: AppConstants.spacingXLarge),
              
              // Current Sentence Card
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(AppConstants.spacingLarge),
                  child: Column(
                    children: [
                      Text(
                        'Đọc to câu sau:',
                        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          color: AppConstants.textSecondary,
                        ),
                      ),
                      const SizedBox(height: AppConstants.spacingMedium),
                      Text(
                        _currentSentence,
                        style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ),
              ),
              
              const SizedBox(height: AppConstants.spacingXLarge),
              
              // Recording Area
              Expanded(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    // Microphone Button
                    GestureDetector(
                      onTap: _isProcessing ? null : _toggleRecording,
                      child: Container(
                        width: 140,
                        height: 140,
                        decoration: BoxDecoration(
                          gradient: _isRecording
                              ? AppConstants.warmGradient
                              : AppConstants.funGradient,
                          shape: BoxShape.circle,
                          boxShadow: [
                            BoxShadow(
                              color: (_isRecording ? AppConstants.pinkColor : AppConstants.blueColor).withOpacity(0.4),
                              blurRadius: 25,
                              spreadRadius: 8,
                            ),
                          ],
                        ),
                        child: _isProcessing
                            ? const CircularProgressIndicator(
                                color: AppConstants.textOnPrimary,
                                strokeWidth: 4,
                              )
                            : Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(
                                    _isRecording ? Icons.stop : Icons.mic,
                                    size: 60,
                                    color: AppConstants.textOnPrimary,
                                  ),
                                  if (_isRecording) ...[
                                    const SizedBox(height: 8),
                                    Text(
                                      'ĐANG GHI ÂM',
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
                    ),
                    
                    const SizedBox(height: AppConstants.spacingLarge),
                    
                    // Recording Status
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: AppConstants.spacingLarge,
                        vertical: AppConstants.spacingMedium,
                      ),
                      decoration: BoxDecoration(
                        color: _isRecording
                            ? AppConstants.pinkColor.withOpacity(0.1)
                            : _isProcessing
                                ? AppConstants.blueColor.withOpacity(0.1)
                                : AppConstants.backgroundColor,
                        borderRadius: BorderRadius.circular(AppConstants.borderRadiusLarge),
                        border: Border.all(
                          color: _isRecording
                              ? AppConstants.pinkColor
                              : _isProcessing
                                  ? AppConstants.blueColor
                                  : Colors.transparent,
                          width: 2,
                        ),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          if (_isRecording) ...[
                            Container(
                              width: 12,
                              height: 12,
                              decoration: const BoxDecoration(
                                color: AppConstants.pinkColor,
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: AppConstants.spacingSmall),
                            Text(
                              '🎙️ Đang ghi âm...',
                              style: GoogleFonts.nunito(
                                fontSize: AppConstants.fontSizeLarge,
                                fontWeight: FontWeight.w800,
                                color: AppConstants.pinkColor,
                              ),
                            ),
                          ] else if (_isProcessing) ...[
                            const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                strokeWidth: 3,
                                valueColor: AlwaysStoppedAnimation<Color>(AppConstants.blueColor),
                              ),
                            ),
                            const SizedBox(width: AppConstants.spacingSmall),
                            Text(
                              '⚡ Đang xử lý...',
                              style: GoogleFonts.nunito(
                                fontSize: AppConstants.fontSizeLarge,
                                fontWeight: FontWeight.w800,
                                color: AppConstants.blueColor,
                              ),
                            ),
                          ] else ...[
                            Text(
                              '🎯 Nhấn để bắt đầu ghi âm',
                              style: GoogleFonts.nunito(
                                fontSize: AppConstants.fontSizeLarge,
                                fontWeight: FontWeight.w600,
                                color: AppConstants.textSecondary,
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                    
                    const SizedBox(height: AppConstants.spacingMedium),
                    
                    // User Speech Result
                    if (_userSpeech.isNotEmpty) ...[
                      Card(
                        color: AppConstants.backgroundColor,
                        child: Padding(
                          padding: const EdgeInsets.all(AppConstants.spacingMedium),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Bạn đã nói:',
                                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                  color: AppConstants.textSecondary,
                                ),
                              ),
                              const SizedBox(height: AppConstants.spacingSmall),
                              Text(
                                _userSpeech,
                                style: Theme.of(context).textTheme.bodyLarge,
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              
              // Action Buttons
              Column(
                children: [
                  // Next Button
                  CustomButton(
                    text: 'Câu tiếp theo',
                    onPressed: _nextSentence,
                    icon: const Icon(Icons.arrow_forward, size: 20),
                  ),
                  
                  const SizedBox(height: AppConstants.spacingMedium),
                  
                  // Skip Button
                  CustomButton(
                    text: 'Bỏ qua',
                    isOutlined: true,
                    onPressed: _nextSentence,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _toggleRecording() {
    setState(() {
      if (_isRecording) {
        _isRecording = false;
        _isProcessing = true;
        _processRecording();
      } else {
        _isRecording = true;
        _userSpeech = '';
        // TODO: Start actual recording
      }
    });
  }

  void _processRecording() async {
    // Simulate processing
    await Future.delayed(const Duration(seconds: 2));
    
    // TODO: Implement actual speech recognition
    setState(() {
      _isProcessing = false;
      _userSpeech = _currentSentence; // Simulate perfect recognition
    });
  }

  void _nextSentence() {
    setState(() {
      if (_currentSentenceIndex < _sentences.length - 1) {
        _currentSentenceIndex++;
        _currentSentence = _sentences[_currentSentenceIndex];
        _userSpeech = '';
        _isRecording = false;
        _isProcessing = false;
      } else {
        // Show completion dialog
        _showCompletionDialog();
      }
    });
  }

  void _showCompletionDialog() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('Hoàn thành!'),
          content: const Text('Bạn đã hoàn thành tất cả các câu luyện nói hôm nay.'),
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
                setState(() {
                  _currentSentenceIndex = 0;
                  _currentSentence = _sentences[0];
                  _userSpeech = '';
                  _isRecording = false;
                  _isProcessing = false;
                });
              },
              child: const Text('Làm lại'),
            ),
          ],
        );
      },
    );
  }
}