// api_service_1.dart - Notification API Service
import 'dart:convert';
import 'dart:io';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:http/http.dart' as http;

class ApiService {
  final String _baseUrl = dotenv.env['BASE_URL'] ?? 'http://127.0.0.1:5000';
  final String _cryptoSecret = dotenv.env['CRYPTO_SECRET'] ?? 'my_super_secret_key_32chars!!';

  // ============================================================================
  // NOTIFICATION APIs
  // ============================================================================

  /// Register device token for push notifications
  Future<Map<String, dynamic>> registerDeviceToken(String deviceToken, String platform) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-mobile/notifications/register-device");
    
    try {
      final payload = {
        "device_token": deviceToken,
        "platform": platform,
      };
      
      final encryptedPayload = _encryptPayload(payload);
      
      var request = http.Request("POST", uri);
      request.headers["Content-Type"] = "application/json";
      request.body = jsonEncode({"payload": encryptedPayload});

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("📱 Register Device Token Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data["success"] == true) {
          final decryptedData = _decryptPayload(data["encrypted_data"]);
          return {
            "success": true,
            "message": decryptedData["message"] ?? "Device token registered successfully",
            "platform": decryptedData["platform"],
            "notifications_enabled": decryptedData["notifications_enabled"] ?? true
          };
        } else {
          return {
            "success": false,
            "error": data["error"] ?? "Failed to register device token"
          };
        }
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to register device token"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error registering device token: $e");
      return {
        "success": false,
        "error": "Network error: $e"
      };
    }
  }

  /// Toggle notifications on/off
  Future<Map<String, dynamic>> toggleNotifications(bool enable) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-mobile/notifications/toggle");
    
    try {
      final payload = {
        "enable": enable,
      };
      
      final encryptedPayload = _encryptPayload(payload);
      
      var request = http.Request("POST", uri);
      request.headers["Content-Type"] = "application/json";
      request.body = jsonEncode({"payload": encryptedPayload});

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("📱 Toggle Notifications Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data["success"] == true) {
          final decryptedData = _decryptPayload(data["encrypted_data"]);
          return {
            "success": true,
            "message": decryptedData["message"] ?? "Notifications toggled successfully",
            "notifications_enabled": decryptedData["notifications_enabled"] ?? enable
          };
        } else {
          return {
            "success": false,
            "error": data["error"] ?? "Failed to toggle notifications"
          };
        }
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to toggle notifications"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error toggling notifications: $e");
      return {
        "success": false,
        "error": "Network error: $e"
      };
    }
  }

  /// Send test notification
  Future<Map<String, dynamic>> sendTestNotification() async {
    final uri = Uri.parse("$_baseUrl/api/delivery-mobile/notifications/test");
    
    try {
      var request = http.Request("POST", uri);
      request.headers["Content-Type"] = "application/json";
      request.body = jsonEncode({});

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("📱 Send Test Notification Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data["success"] == true) {
          final decryptedData = _decryptPayload(data["encrypted_data"]);
          return {
            "success": true,
            "message": decryptedData["message"] ?? "Test notification sent successfully"
          };
        } else {
          return {
            "success": false,
            "error": data["error"] ?? "Failed to send test notification"
          };
        }
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to send test notification"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error sending test notification: $e");
      return {
        "success": false,
        "error": "Network error: $e"
      };
    }
  }

  // ============================================================================
  // ENCRYPTION/DECRYPTION METHODS
  // ============================================================================

  /// Encrypt payload using simple XOR encryption
  String _encryptPayload(Map<String, dynamic> payload) {
    try {
      final jsonString = jsonEncode(payload);
      final key = _cryptoSecret.substring(0, 32);
      final bytes = utf8.encode(jsonString);
      final keyBytes = utf8.encode(key);
      
      // Simple XOR encryption for demo purposes
      // In production, use proper AES encryption
      final encrypted = <int>[];
      for (int i = 0; i < bytes.length; i++) {
        encrypted.add(bytes[i] ^ keyBytes[i % keyBytes.length]);
      }
      
      return base64Encode(encrypted);
    } catch (e) {
      print("❌ Error encrypting payload: $e");
      return base64Encode(utf8.encode(jsonEncode(payload)));
    }
  }

  /// Decrypt payload using simple XOR decryption
  Map<String, dynamic> _decryptPayload(String encryptedPayload) {
    try {
      final encrypted = base64Decode(encryptedPayload);
      final key = _cryptoSecret.substring(0, 32);
      final keyBytes = utf8.encode(key);
      
      // Simple XOR decryption for demo purposes
      // In production, use proper AES decryption
      final decrypted = <int>[];
      for (int i = 0; i < encrypted.length; i++) {
        decrypted.add(encrypted[i] ^ keyBytes[i % keyBytes.length]);
      }
      
      final jsonString = utf8.decode(decrypted);
      return jsonDecode(jsonString);
    } catch (e) {
      print("❌ Error decrypting payload: $e");
      return {"error": "Failed to decrypt payload"};
    }
  }
}
