// Flutter Device Token Generator for AWS SNS
// Add this to your Flutter app

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'dart:io';

class DeviceTokenService {
  static String? _deviceToken;
  
  // Get device token for AWS SNS
  static Future<String?> getDeviceToken() async {
    try {
      if (Platform.isIOS) {
        // For iOS - generate a unique device token
        _deviceToken = await _generateIOSDeviceToken();
      } else if (Platform.isAndroid) {
        // For Android - generate a unique device token
        _deviceToken = await _generateAndroidDeviceToken();
      }
      
      print('📱 Device Token: $_deviceToken');
      return _deviceToken;
    } catch (e) {
      print('❌ Error getting device token: $e');
      return null;
    }
  }
  
  // Generate iOS device token
  static Future<String> _generateIOSDeviceToken() async {
    // Generate a unique device token for iOS
    // In real implementation, this would come from APNS
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    final random = (timestamp % 1000000).toString().padLeft(6, '0');
    return 'ios_${timestamp}_${random}';
  }
  
  // Generate Android device token
  static Future<String> _generateAndroidDeviceToken() async {
    // Generate a unique device token for Android
    // In real implementation, this would come from FCM
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    final random = (timestamp % 1000000).toString().padLeft(6, '0');
    return 'android_${timestamp}_${random}';
  }
  
  // Register device token with backend
  static Future<bool> registerDeviceToken(String token, String platform) async {
    try {
      // Replace with your actual API call
      print('📱 Registering device token with backend...');
      print('📱 Token: $token');
      print('📱 Platform: $platform');
      
      // TODO: Make API call to register device token
      // await ApiService.registerDeviceToken(token, platform);
      
      return true;
    } catch (e) {
      print('❌ Error registering device token: $e');
      return false;
    }
  }
}

// Updated main.dart with device token generation
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await dotenv.load(fileName: ".env");
  
  // Get device token
  String? deviceToken = await DeviceTokenService.getDeviceToken();
  if (deviceToken != null) {
    print('📱 Device Token Generated: $deviceToken');
    
    // Register with backend
    String platform = Platform.isIOS ? 'ios' : 'android';
    await DeviceTokenService.registerDeviceToken(deviceToken, platform);
  }
  
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Zintoo',
      debugShowCheckedModeBanner: false,
      initialRoute: '/splash',
      onGenerateRoute: (settings) {
        if (settings.name == '/splash') {
          return MaterialPageRoute(builder: (_) => const SplashScreen());
        }
        if (settings.name == '/login') {
          return MaterialPageRoute(builder: (_) => const LoginScreen());
        }
        if (settings.name == '/dashboard') {
          final args = settings.arguments as Map<String, dynamic>;
          return MaterialPageRoute(
            builder: (_) => DashboardScreen(email: args['email']),
          );
        }
        if (settings.name == '/onboarding') {
          final args = settings.arguments as Map<String, dynamic>;
          return MaterialPageRoute(
            builder: (_) => OnboardingScreen(
              email: args['email'],
              authToken: args['authToken'],
            ),
          );
        }
        return null;
      },
    );
  }
}
