import 'dart:convert';
import 'dart:io';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:http/http.dart' as http;

class ApiServiceEnhanced {
  final String _baseUrl = dotenv.env['BASE_URL'] ?? 'http://127.0.0.1:5000';

  // ============================================================================
  // ENHANCED DELIVERY ORDER MANAGEMENT APIs
  // ============================================================================

  /// Scan barcode and get order details
  Future<Map<String, dynamic>> scanBarcode(String authToken, String barcode) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-enhanced/orders/scan-barcode");

    try {
      var request = http.Request("POST", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";
      request.headers["Content-Type"] = "application/json";
      request.body = jsonEncode({"barcode": barcode});

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("📱 Scan Barcode Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "order": data["order"],
          "message": data["message"] ?? "Order found successfully"
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to scan barcode"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error scanning barcode: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Send OTP to customer for order verification
  Future<Map<String, dynamic>> sendDeliveryOTP(String authToken, String orderId) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-enhanced/orders/$orderId/send-otp");

    try {
      var request = http.Request("POST", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";
      request.headers["Content-Type"] = "application/json";

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("📧 Send OTP Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "message": data["message"] ?? "OTP sent successfully",
          "expires_in": data["expires_in"] ?? 600
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to send OTP"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error sending OTP: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Verify OTP and mark order as delivered
  Future<Map<String, dynamic>> verifyDeliveryOTP(String authToken, String orderId, String otp) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-enhanced/orders/$orderId/verify-otp");

    try {
      var request = http.Request("POST", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";
      request.headers["Content-Type"] = "application/json";
      request.body = jsonEncode({"otp": otp});

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("✅ Verify OTP Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "message": data["message"] ?? "Order delivered successfully",
          "order": data["order"]
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to verify OTP"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error verifying OTP: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Get combined orders, exchanges, and cancelled items
  Future<Map<String, dynamic>> getCombinedOrders(String authToken, {String status = "all"}) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-enhanced/orders/combined?status=$status");

    try {
      var request = http.Request("GET", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("📦 Get Combined Orders Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "data": data["data"],
          "status": data["status"]
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to get combined orders"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error getting combined orders: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Get all orders assigned to delivery guy
  Future<Map<String, dynamic>> getDeliveryOrders(String authToken, {String status = "all"}) async {
    final uri = Uri.parse("$_baseUrl/api/delivery/orders?status=$status");

    try {
      var request = http.Request("GET", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("📦 Get Orders Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "orders": data["orders"] ?? []
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to get orders"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error getting orders: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }


  /// Get cancelled order items assigned to delivery guy
  Future<Map<String, dynamic>> getCancelledOrderItems(String authToken) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-enhanced/order-items/cancelled");

    try {
      var request = http.Request("GET", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("❌ Get Cancelled Items Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "cancelled_items": data["cancelled_items"] ?? []
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to get cancelled items"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error getting cancelled items: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  // ============================================================================
  // ORDER APPROVAL/REJECTION APIs
  // ============================================================================

  /// Approve order with enhanced tracking
  Future<Map<String, dynamic>> approveOrderEnhanced(String authToken, String orderId, {String reason = "Order approved by delivery personnel"}) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-enhanced/orders/$orderId/approve");

    try {
      var request = http.Request("POST", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";
      request.headers["Content-Type"] = "application/json";
      request.body = jsonEncode({"reason": reason});

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("✅ Approve Order Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "message": data["message"] ?? "Order approved successfully",
          "order": data["order"],
          "delivery_track_id": data["delivery_track_id"]
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to approve order"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error approving order: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Reject order with enhanced tracking
  Future<Map<String, dynamic>> rejectOrderEnhanced(String authToken, String orderId, String reason) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-enhanced/orders/$orderId/reject");

    try {
      var request = http.Request("POST", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";
      request.headers["Content-Type"] = "application/json";
      request.body = jsonEncode({"reason": reason});

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("❌ Reject Order Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "message": data["message"] ?? "Order rejected successfully",
          "order": data["order"],
          "delivery_track_id": data["delivery_track_id"]
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to reject order"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error rejecting order: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Approve exchange with enhanced tracking
  Future<Map<String, dynamic>> approveExchangeEnhanced(String authToken, String exchangeId, {String reason = "Exchange approved by delivery personnel"}) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-enhanced/exchanges/$exchangeId/approve");

    try {
      var request = http.Request("POST", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";
      request.headers["Content-Type"] = "application/json";
      request.body = jsonEncode({"reason": reason});

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("✅ Approve Exchange Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "message": data["message"] ?? "Exchange approved successfully",
          "exchange": data["exchange"],
          "delivery_track_id": data["delivery_track_id"]
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to approve exchange"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error approving exchange: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Reject exchange with enhanced tracking
  Future<Map<String, dynamic>> rejectExchangeEnhanced(String authToken, String exchangeId, String reason) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-enhanced/exchanges/$exchangeId/reject");

    try {
      var request = http.Request("POST", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";
      request.headers["Content-Type"] = "application/json";
      request.body = jsonEncode({"reason": reason});

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("❌ Reject Exchange Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "message": data["message"] ?? "Exchange rejected successfully",
          "exchange": data["exchange"],
          "delivery_track_id": data["delivery_track_id"]
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to reject exchange"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error rejecting exchange: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  // ============================================================================
  // EXISTING AUTHENTICATION APIs (from original service)
  // ============================================================================

  /// Sends an OTP to the specified email.
  Future<bool> sendOtpToEmail(String email) async {
    final Uri uri = Uri.parse('$_baseUrl/api/delivery-mobile/auth/send-otp');
    try {
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email}),
      );
      print('Send OTP response: ${response.statusCode} - ${response.body}');
      return response.statusCode == 200;
    } catch (e) {
      print('Error sending OTP to $email: $e');
      return false;
    }
  }

  /// Verifies the OTP entered by the user.
  Future<Map<String, dynamic>> verifyOtp(String email, String otp) async {
    final Uri uri = Uri.parse('$_baseUrl/api/delivery-mobile/auth/verify-otp');
    try {
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'otp': otp}),
      );

      print('OTP verification response: ${response.statusCode} - ${response.body}');

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        return {
          'success': true,
          'is_new_user': responseData['is_new_user'] ?? false,
          'is_onboarded': responseData['is_onboarded'] ?? false,
          'auth_token': responseData['auth_token'],
          'user': responseData['user'] ?? {},
          'message': responseData['message'] ?? 'OTP verified successfully'
        };
      } else {
        final errorData = jsonDecode(response.body);
        return {
          'success': false,
          'message': errorData['error'] ?? 'OTP verification failed',
          'redirect_to': 'login'
        };
      }
    } catch (e) {
      print('Error verifying OTP for $email: $e');
      return {
        'success': false,
        'message': 'Network error occurred',
        'redirect_to': 'login'
      };
    }
  }

  /// Get exchanges assigned to delivery guy (alternative endpoint)
  Future<Map<String, dynamic>> getDeliveryExchanges(String authToken) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-enhanced/exchanges");

    try {
      var request = http.Request("GET", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("🔄 Get Exchanges Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "exchanges": data["exchanges"] ?? []
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to get exchanges"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error getting exchanges: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Get dashboard data
  Future<Map<String, dynamic>> getDashboardData(String authToken) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-mobile/dashboard");

    try {
      var request = http.Request("GET", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("📊 Dashboard Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "dashboard": data["dashboard"] ?? {}
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to get dashboard data"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error getting dashboard data: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }
}
