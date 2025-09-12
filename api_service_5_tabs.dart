import 'dart:convert';
import 'dart:io';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:http/http.dart' as http;

class ApiService5Tabs {
  static final String _baseUrl = dotenv.env['BASE_URL'] ?? 'http://127.0.0.1:5000';

  // ============================================================================
  // 5-TAB DELIVERY ORDER MANAGEMENT APIs
  // ============================================================================

  /// Get all orders assigned to delivery guy (Tab 1: Orders)
  Future<Map<String, dynamic>> getDeliveryOrders(String authToken, {String status = "all"}) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-orders/orders?status=$status");

    try {
      var request = http.Request("GET", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("📦 Get Delivery Orders Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "orders": data["orders"] ?? [],
          "total": data["total"] ?? 0,
          "delivery_guy_id": data["delivery_guy_id"]
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
      print("❌ Error getting delivery orders: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Get all exchanges assigned to delivery guy (Tab 2: Exchanges)
  Future<Map<String, dynamic>> getDeliveryExchanges(String authToken) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-orders/exchanges");

    try {
      var request = http.Request("GET", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("🔄 Get Delivery Exchanges Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "exchanges": data["exchanges"] ?? [],
          "total": data["total"] ?? 0,
          "delivery_guy_id": data["delivery_guy_id"]
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
      print("❌ Error getting delivery exchanges: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Get all cancelled order items assigned to delivery guy (Tab 3: Cancelled)
  Future<Map<String, dynamic>> getCancelledOrderItems(String authToken) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-orders/cancelled-items");

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
          "cancelled_items": data["cancelled_items"] ?? [],
          "total": data["total"] ?? 0,
          "delivery_guy_id": data["delivery_guy_id"]
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

  /// Get all approved items (Tab 4: Approved)
  Future<Map<String, dynamic>> getApprovedItems(String authToken) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-orders/approved");

    try {
      var request = http.Request("GET", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("✅ Get Approved Items Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "approved_items": data["approved_items"] ?? [],
          "total": data["total"] ?? 0,
          "delivery_guy_id": data["delivery_guy_id"]
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to get approved items"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error getting approved items: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Get all rejected items (Tab 5: Rejected)
  Future<Map<String, dynamic>> getRejectedItems(String authToken) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-orders/rejected");

    try {
      var request = http.Request("GET", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("❌ Get Rejected Items Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "rejected_items": data["rejected_items"] ?? [],
          "total": data["total"] ?? 0,
          "delivery_guy_id": data["delivery_guy_id"]
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to get rejected items"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error getting rejected items: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  // ============================================================================
  // ORDER APPROVAL/REJECTION APIs
  // ============================================================================

  /// Approve order
  Future<Map<String, dynamic>> approveOrder(String authToken, String orderId, {String reason = "Order approved by delivery personnel"}) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-orders/orders/$orderId/approve");

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

  /// Reject order
  Future<Map<String, dynamic>> rejectOrder(String authToken, String orderId, String reason) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-orders/orders/$orderId/reject");

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

  /// Approve exchange
  Future<Map<String, dynamic>> approveExchange(String authToken, String exchangeId, {String reason = "Exchange approved by delivery personnel"}) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-orders/exchanges/$exchangeId/approve");

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

  /// Reject exchange
  Future<Map<String, dynamic>> rejectExchange(String authToken, String exchangeId, String reason) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-orders/exchanges/$exchangeId/reject");

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
  // DELIVERY STATUS UPDATE APIs
  // ============================================================================

  /// Mark order as out for delivery
  Future<Map<String, dynamic>> markOrderOutForDelivery(String authToken, String orderId) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-orders/orders/$orderId/out-for-delivery");

    try {
      var request = http.Request("POST", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";
      request.headers["Content-Type"] = "application/json";

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("🚚 Mark Order Out for Delivery Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "message": data["message"] ?? "Order marked as out for delivery",
          "order": data["order"]
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to mark order as out for delivery"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error marking order as out for delivery: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Mark order as delivered
  Future<Map<String, dynamic>> markOrderDelivered(String authToken, String orderId) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-orders/orders/$orderId/delivered");

    try {
      var request = http.Request("POST", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";
      request.headers["Content-Type"] = "application/json";

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("✅ Mark Order Delivered Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "message": data["message"] ?? "Order marked as delivered",
          "order": data["order"]
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to mark order as delivered"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error marking order as delivered: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Mark exchange as out for delivery
  Future<Map<String, dynamic>> markExchangeOutForDelivery(String authToken, String exchangeId) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-orders/exchanges/$exchangeId/out-for-delivery");

    try {
      var request = http.Request("POST", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";
      request.headers["Content-Type"] = "application/json";

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("🚚 Mark Exchange Out for Delivery Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "message": data["message"] ?? "Exchange marked as out for delivery",
          "exchange": data["exchange"]
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to mark exchange as out for delivery"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error marking exchange as out for delivery: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Mark exchange as delivered
  Future<Map<String, dynamic>> markExchangeDelivered(String authToken, String exchangeId) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-orders/exchanges/$exchangeId/delivered");

    try {
      var request = http.Request("POST", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";
      request.headers["Content-Type"] = "application/json";

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("✅ Mark Exchange Delivered Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "message": data["message"] ?? "Exchange marked as delivered",
          "exchange": data["exchange"]
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to mark exchange as delivered"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error marking exchange as delivered: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  // ============================================================================
  // CANCELLED ITEMS MANAGEMENT APIs
  // ============================================================================

  /// Mark cancelled item as out for delivery
  Future<Map<String, dynamic>> markCancelledItemOutForDelivery(String authToken, String itemId) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-orders/cancelled-items/$itemId/out-for-delivery");

    try {
      var request = http.Request("PUT", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";
      request.headers["Content-Type"] = "application/json";

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("📦 Mark Cancelled Item Out for Delivery Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "message": data["message"] ?? "Cancelled item marked as out for delivery"
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to mark cancelled item as out for delivery"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error marking cancelled item as out for delivery: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Mark cancelled item as returned
  Future<Map<String, dynamic>> markCancelledItemAsReturned(String authToken, String itemId) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-orders/cancelled-items/$itemId/returned");

    try {
      var request = http.Request("PUT", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";
      request.headers["Content-Type"] = "application/json";

      var response = await request.send();
      var responseBody = await response.stream.bytesToString();

      if (response.statusCode == 200) {
        return jsonDecode(responseBody);
      } else {
        return {"success": false, "error": "Failed to mark as returned: ${response.statusCode}"};
      }
    } catch (e) {
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Mark cancelled item as delivered
  Future<Map<String, dynamic>> markCancelledItemDelivered(String authToken, String itemId) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-orders/cancelled-items/$itemId/delivered");

    try {
      var request = http.Request("PUT", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";
      request.headers["Content-Type"] = "application/json";

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("📦 Mark Cancelled Item Delivered Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "message": data["message"] ?? "Cancelled item marked as delivered"
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to mark cancelled item as delivered"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error marking cancelled item as delivered: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  // ============================================================================
  // OTP MANAGEMENT APIs
  // ============================================================================

  /// Send delivery OTP to customer
  Future<Map<String, dynamic>> sendDeliveryOTP(String authToken, String itemId, String itemType) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-orders/send-otp");

    try {
      var request = http.Request("POST", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";
      request.headers["Content-Type"] = "application/json";

      final body = {
        "item_id": itemId,
        "item_type": itemType, // 'orders', 'exchanges', 'cancelled_items'
      };

      request.body = jsonEncode(body);

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("📱 Send Delivery OTP Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "message": data["message"] ?? "OTP sent successfully",
          "otp": data["otp"] // For testing purposes
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
      print("❌ Error sending delivery OTP: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Verify delivery OTP
  Future<Map<String, dynamic>> verifyDeliveryOTP(String authToken, String itemId, String itemType, String otp) async {
    final uri = Uri.parse("$_baseUrl/api/delivery-orders/verify-otp");

    try {
      var request = http.Request("POST", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";
      request.headers["Content-Type"] = "application/json";

      final body = {
        "item_id": itemId,
        "item_type": itemType, // 'orders', 'exchanges', 'cancelled_items'
        "otp": otp,
      };

      request.body = jsonEncode(body);

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("🔐 Verify Delivery OTP Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "message": data["message"] ?? "OTP verified successfully"
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Invalid OTP"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error verifying delivery OTP: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  // ============================================================================
  // DELIVERY PHOTO UPLOAD API
  // ============================================================================

  /// Upload delivery photo
  static Future<Map<String, dynamic>> uploadDeliveryPhoto({
    required String authToken,
    required String itemId,
    required String itemType,
    required String imageBase64,
  }) async {
    try {
      final uri = Uri.parse("$_baseUrl/api/delivery-orders/upload-delivery-photo");

      final response = await http.post(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $authToken',
        },
        body: jsonEncode({
          'item_id': itemId,
          'item_type': itemType,
          'image_base64': imageBase64,
        }),
      );

      print("📸 Upload delivery photo response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data;
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData['error'] ?? "Upload failed"
          };
        } catch (e) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error uploading delivery photo: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }
}