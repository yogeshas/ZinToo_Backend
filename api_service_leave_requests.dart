import 'dart:convert';
import 'dart:io';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:http/http.dart' as http;

class ApiServiceLeaveRequests {
  final String _baseUrl = dotenv.env['BASE_URL'] ?? 'http://127.0.0.1:5000';

  // ============================================================================
  // DELIVERY GUY LEAVE REQUEST APIs
  // ============================================================================

  /// Get all leave requests for delivery guy
  Future<Map<String, dynamic>> getDeliveryLeaveRequests(String authToken) async {
    final uri = Uri.parse("$_baseUrl/api/leave-requests/delivery/leave-requests");

    try {
      var request = http.Request("GET", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("📋 Get Leave Requests Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "leave_requests": data["leave_requests"] ?? [],
          "total": data["total"] ?? 0
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to get leave requests"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error getting leave requests: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Create a new leave request
  Future<Map<String, dynamic>> createLeaveRequest(
    String authToken,
    String startDate,
    String endDate,
    String reason,
  ) async {
    final uri = Uri.parse("$_baseUrl/api/leave-requests/delivery/leave-requests");

    try {
      var request = http.Request("POST", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";
      request.headers["Content-Type"] = "application/json";

      final body = {
        "start_date": startDate,
        "end_date": endDate,
        "reason": reason,
      };

      request.body = jsonEncode(body);

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("📝 Create Leave Request Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 201) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "message": data["message"] ?? "Leave request created successfully",
          "leave_request": data["leave_request"]
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to create leave request"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error creating leave request: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  // ============================================================================
  // ADMIN LEAVE REQUEST APIs
  // ============================================================================

  /// Get all leave requests for admin review
  Future<Map<String, dynamic>> getAllLeaveRequests(String authToken, {String status = "all"}) async {
    final uri = Uri.parse("$_baseUrl/api/leave-requests/admin/leave-requests?status=$status");

    try {
      var request = http.Request("GET", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("📋 Get All Leave Requests Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "leave_requests": data["leave_requests"] ?? [],
          "total": data["total"] ?? 0
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to get leave requests"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error getting all leave requests: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Approve a leave request
  Future<Map<String, dynamic>> approveLeaveRequest(
    String authToken,
    int requestId,
    {String adminNotes = ""}
  ) async {
    final uri = Uri.parse("$_baseUrl/api/leave-requests/admin/leave-requests/$requestId/approve");

    try {
      var request = http.Request("POST", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";
      request.headers["Content-Type"] = "application/json";

      final body = {
        "admin_notes": adminNotes,
      };

      request.body = jsonEncode(body);

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("✅ Approve Leave Request Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "message": data["message"] ?? "Leave request approved successfully",
          "leave_request": data["leave_request"]
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to approve leave request"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error approving leave request: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  /// Reject a leave request
  Future<Map<String, dynamic>> rejectLeaveRequest(
    String authToken,
    int requestId,
    String adminNotes,
  ) async {
    final uri = Uri.parse("$_baseUrl/api/leave-requests/admin/leave-requests/$requestId/reject");

    try {
      var request = http.Request("POST", uri);
      request.headers["Authorization"] = authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";
      request.headers["Content-Type"] = "application/json";

      final body = {
        "admin_notes": adminNotes,
      };

      request.body = jsonEncode(body);

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("❌ Reject Leave Request Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "message": data["message"] ?? "Leave request rejected successfully",
          "leave_request": data["leave_request"]
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Failed to reject leave request"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error rejecting leave request: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }
}
