// Flutter Notification Permissions
// Add this to your Flutter app to request notification permissions

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'dart:io';

class NotificationPermissionService {
  // Request notification permissions
  static Future<bool> requestPermissions() async {
    try {
      if (Platform.isIOS) {
        // For iOS - request notification permissions
        return await _requestIOSPermissions();
      } else if (Platform.isAndroid) {
        // For Android - request notification permissions
        return await _requestAndroidPermissions();
      }
      return false;
    } catch (e) {
      print('❌ Error requesting permissions: $e');
      return false;
    }
  }
  
  // Request iOS permissions
  static Future<bool> _requestIOSPermissions() async {
    try {
      // In a real app, you would use a notification plugin
      // For now, we'll just show instructions
      print('📱 iOS: Please enable notifications in Settings > Notifications > ZinToo');
      return true;
    } catch (e) {
      print('❌ Error requesting iOS permissions: $e');
      return false;
    }
  }
  
  // Request Android permissions
  static Future<bool> _requestAndroidPermissions() async {
    try {
      // In a real app, you would use a notification plugin
      // For now, we'll just show instructions
      print('📱 Android: Please enable notifications in Settings > Apps > ZinToo > Notifications');
      return true;
    } catch (e) {
      print('❌ Error requesting Android permissions: $e');
      return false;
    }
  }
  
  // Show permission dialog
  static Future<void> showPermissionDialog(BuildContext context) async {
    return showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('🔔 Enable Notifications'),
          content: const Text(
            'To receive delivery notifications, please enable notifications for ZinToo in your device settings.\n\n'
            'iOS: Settings > Notifications > ZinToo\n'
            'Android: Settings > Apps > ZinToo > Notifications'
          ),
          actions: <Widget>[
            TextButton(
              child: const Text('Cancel'),
              onPressed: () {
                Navigator.of(context).pop();
              },
            ),
            TextButton(
              child: const Text('Open Settings'),
              onPressed: () {
                Navigator.of(context).pop();
                // Open device settings
                _openDeviceSettings();
              },
            ),
          ],
        );
      },
    );
  }
  
  // Open device settings
  static void _openDeviceSettings() {
    try {
      if (Platform.isIOS) {
        // Open iOS settings
        // In a real app, you would use a plugin like app_settings
        print('📱 Opening iOS Settings...');
      } else if (Platform.isAndroid) {
        // Open Android settings
        // In a real app, you would use a plugin like app_settings
        print('📱 Opening Android Settings...');
      }
    } catch (e) {
      print('❌ Error opening settings: $e');
    }
  }
}

// Updated main.dart with permission request
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await dotenv.load(fileName: ".env");
  
  // Request notification permissions
  bool hasPermission = await NotificationPermissionService.requestPermissions();
  
  if (hasPermission) {
    print('✅ Notification permissions granted');
  } else {
    print('❌ Notification permissions denied');
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
