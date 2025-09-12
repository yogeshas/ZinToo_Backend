import 'dart:convert';
import 'dart:io';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:http/http.dart' as http;

class ApiServiceEarnings {
  final String _baseUrl = dotenv.env['BASE_URL'] ?? 'http://127.0.0.1:5000';

  // ============================================================================
  // DELIVERY GUY EARNINGS APIs
  // ============================================================================

  /// Get all earnings for delivery guy
  Future<Map<String, dynamic>> getDeliveryEarnings(String authToken, {String? type, String? period}) async {
    final uri = Uri.parse("$_baseUrl/api/earnings-management/delivery/earnings").replace(
      queryParameters: {
        if (type != null && type != 'all') 'type': type,
        if (period != null && period != 'all') 'period': period,
      },
    );

    try {
      var request = http.Request("GET", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("💰 Get Earnings Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final earnings = List<Map<String, dynamic>>.from(data["earnings"] ?? []);
        
        // Debug: Print earnings data structure
        print("📊 Earnings data structure:");
        for (int i = 0; i < earnings.length && i < 3; i++) {
          print("Earning $i: ${earnings[i]}");
        }
        
        // Debug: Count by payment type
        Map<String, int> typeCount = {};
        for (var earning in earnings) {
          String type = earning['payment_type']?.toString() ?? 'unknown';
          typeCount[type] = (typeCount[type] ?? 0) + 1;
        }
        print("📈 Payment type counts: $typeCount");
        
        return {
          "success": true,
          "earnings": earnings,
          "total": data["total"] ?? 0
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to get earnings"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error getting earnings: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Get earnings summary for delivery guy dashboard
  Future<Map<String, dynamic>> getDeliveryEarningsSummary(String authToken, {String period = 'monthly'}) async {
    final uri = Uri.parse("$_baseUrl/api/earnings-management/delivery/earnings/summary").replace(
      queryParameters: {'period': period},
    );

    try {
      var request = http.Request("GET", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("📊 Get Earnings Summary Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final summary = data["summary"] ?? {};
        
        // Debug: Print summary data structure
        print("📊 Summary data structure: $summary");
        print("📊 Summary keys: ${summary.keys.toList()}");
        
        return {
          "success": true,
          "summary": summary,
          "weekly_breakdown": List<Map<String, dynamic>>.from(data["weekly_breakdown"] ?? []),
          "daily_breakdown": List<Map<String, dynamic>>.from(data["daily_breakdown"] ?? []),
          "period": data["period"] ?? period
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to get earnings summary"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error getting earnings summary: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  // ============================================================================
  // ADMIN EARNINGS APIs
  // ============================================================================

  /// Get all earnings for admin review
  Future<Map<String, dynamic>> getAllEarnings(String authToken, {String? type, String? status, int? deliveryGuyId}) async {
    final uri = Uri.parse("$_baseUrl/api/earnings-management/admin/earnings").replace(
      queryParameters: {
        if (type != null && type != 'all') 'type': type,
        if (status != null && status != 'all') 'status': status,
        if (deliveryGuyId != null) 'delivery_guy_id': deliveryGuyId.toString(),
      },
    );

    try {
      var request = http.Request("GET", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("👨‍💼 Get All Earnings Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "earnings": List<Map<String, dynamic>>.from(data["earnings"] ?? []),
          "total": data["total"] ?? 0
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to get earnings"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error getting all earnings: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Create new earning entry
  Future<Map<String, dynamic>> createEarning(
    String authToken,
    int deliveryGuyId,
    String paymentType,
    double amount,
    String paymentPeriod,
    String startDate,
    String? endDate,
    String? description,
    String? adminNotes,
  ) async {
    final uri = Uri.parse("$_baseUrl/api/earnings-management/admin/earnings");

    try {
      final requestBody = {
        "delivery_guy_id": deliveryGuyId,
        "payment_type": paymentType,
        "amount": amount,
        "payment_period": paymentPeriod,
        "start_date": startDate,
        if (endDate != null) "end_date": endDate,
        if (description != null) "description": description,
        if (adminNotes != null) "admin_notes": adminNotes,
      };

      var request = http.Request("POST", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";
      request.headers["Content-Type"] = "application/json";
      request.body = jsonEncode(requestBody);

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("➕ Create Earning Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 201) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "message": data["message"] ?? "Earning created successfully",
          "earning": data["earning"]
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to create earning"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error creating earning: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Approve an earning entry
  Future<Map<String, dynamic>> approveEarning(String authToken, int earningId, {String? adminNotes}) async {
    final uri = Uri.parse("$_baseUrl/api/earnings-management/admin/earnings/$earningId/approve");

    try {
      final requestBody = {
        if (adminNotes != null) "admin_notes": adminNotes,
      };

      var request = http.Request("POST", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";
      request.headers["Content-Type"] = "application/json";
      request.body = jsonEncode(requestBody);

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("✅ Approve Earning Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "message": data["message"] ?? "Earning approved successfully",
          "earning": data["earning"]
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to approve earning"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error approving earning: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Reject an earning entry
  Future<Map<String, dynamic>> rejectEarning(String authToken, int earningId, String adminNotes) async {
    final uri = Uri.parse("$_baseUrl/api/earnings-management/admin/earnings/$earningId/reject");

    try {
      final requestBody = {
        "admin_notes": adminNotes,
      };

      var request = http.Request("POST", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";
      request.headers["Content-Type"] = "application/json";
      request.body = jsonEncode(requestBody);

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("❌ Reject Earning Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "message": data["message"] ?? "Earning rejected successfully",
          "earning": data["earning"]
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to reject earning"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error rejecting earning: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Mark an earning entry as paid
  Future<Map<String, dynamic>> markEarningPaid(String authToken, int earningId) async {
    final uri = Uri.parse("$_baseUrl/api/earnings-management/admin/earnings/$earningId/mark-paid");

    try {
      var request = http.Request("POST", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("💳 Mark Earning Paid Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "message": data["message"] ?? "Earning marked as paid successfully",
          "earning": data["earning"]
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to mark earning as paid"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error marking earning as paid: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Get earnings summary for admin dashboard
  Future<Map<String, dynamic>> getAdminEarningsSummary(String authToken, {String period = 'monthly', int? deliveryGuyId}) async {
    final uri = Uri.parse("$_baseUrl/api/earnings-management/admin/earnings/summary").replace(
      queryParameters: {
        'period': period,
        if (deliveryGuyId != null) 'delivery_guy_id': deliveryGuyId.toString(),
      },
    );

    try {
      var request = http.Request("GET", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("📊 Get Admin Earnings Summary Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "summary": data["summary"] ?? {},
          "weekly_breakdown": List<Map<String, dynamic>>.from(data["weekly_breakdown"] ?? []),
          "daily_breakdown": List<Map<String, dynamic>>.from(data["daily_breakdown"] ?? []),
          "period": data["period"] ?? period
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to get earnings summary"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error getting admin earnings summary: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Get list of delivery guys for admin
  Future<Map<String, dynamic>> getDeliveryGuys(String authToken) async {
    final uri = Uri.parse("$_baseUrl/api/earnings-management/admin/delivery-guys");

    try {
      var request = http.Request("GET", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("👥 Get Delivery Guys Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "delivery_guys": data["delivery_guys"] ?? []
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to get delivery guys"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error getting delivery guys: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }
}
