import 'package:shared_preferences/shared_preferences.dart';

/// Preferencias de onboarding y tutorial de primer uso (solo local).
class OnboardingPrefs {
  OnboardingPrefs._();

  static const _kWelcomeCompleted = 'onboarding_welcome_completed';
  static const _kTutorialCompleted = 'onboarding_tutorial_completed';

  static Future<bool> welcomeCompletado() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_kWelcomeCompleted) ?? false;
  }

  static Future<void> marcarWelcomeCompletado() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kWelcomeCompleted, true);
  }

  static Future<bool> tutorialCompletado() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_kTutorialCompleted) ?? false;
  }

  static Future<void> marcarTutorialCompletado() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kTutorialCompleted, true);
  }

  static Future<void> reiniciarTutorial() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kTutorialCompleted, false);
  }
}
