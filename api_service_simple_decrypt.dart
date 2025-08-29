import 'dart:convert';
import 'dart:io';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:http/http.dart' as http;

class ApiService {
  final String _baseUrl = dotenv.env['BASE_URL'] ?? 'http://127.0.0.1:5000';

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

  /// Get onboarding status
  Future<Map<String, dynamic>> getOnboardingStatus(String authToken) async {
    final Uri uri = Uri.parse('$_baseUrl/api/delivery/onboard');

    final headers = {
      'Authorization': authToken.startsWith('Bearer ') ? authToken : 'Bearer $authToken',
      'Content-Type': 'application/json',
    };

    print('Making GET request to: $uri');
    print('Headers: $headers');

    try {
      final response = await http.get(uri, headers: headers);

      print('Get onboarding status response: ${response.statusCode} - ${response.body}');

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        return {
          'success': true,
          'onboarding': responseData['onboarding'],
          'user_status': responseData['onboarding']?['status'] ?? 'not_started',
          'next_step': _getNextStep(responseData['onboarding']?['status']),
        };
      } else if (response.statusCode == 404) {
        print('No onboarding record found - user needs to complete onboarding');
        return {
          'success': true,
          'onboarding': null,
          'user_status': 'not_started',
          'next_step': 'onboarding',
        };
      } else {
        final errorData = jsonDecode(response.body);
        return {
          'success': false,
          'message': errorData['message'] ?? 'Failed to get onboarding status',
        };
      }
    } catch (e) {
      print('Error getting onboarding status: $e');
      return {
        'success': false,
        'message': 'Network error occurred: $e'
      };
    }
  }

  /// Submits initial onboarding form data (basic profile).
  Future<Map<String, dynamic>> submitOnboarding(
      String authToken,
      Map<String, dynamic> formData,
      List<http.MultipartFile> files,
      ) async {
    final Uri uri = Uri.parse('$_baseUrl/api/delivery/onboard');

    try {
      var request = http.MultipartRequest('POST', uri);

      request.headers['Authorization'] =
      authToken.startsWith('Bearer ') ? authToken : 'Bearer $authToken';

      formData.forEach((key, value) {
        if (value != null && value.toString().isNotEmpty) {
          request.fields[key] = value.toString();
        }
      });

      for (var file in files) {
        request.files.add(file);
      }

      print('Making POST request to: $uri');
      print('Headers: ${request.headers}');
      print('Form fields: ${request.fields}');
      print('Files: ${request.files.length}');

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print('Onboarding API Response: ${response.statusCode} - ${response.body}');

      if (response.statusCode == 201 || response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        return {
          'success': true,
          'message': responseData['message'] ?? 'Profile created successfully!',
          'onboarding_id': responseData['onboarding_id'],
          'user_status': responseData['user_status'] ?? 'profile_incomplete',
          'next_step': 'documents'
        };
      } else {
        final errorData = jsonDecode(response.body);
        return {
          'success': false,
          'message': errorData['message'] ??
              'Failed to submit onboarding (Status: ${response.statusCode})'
        };
      }
    } catch (e) {
      print('Error submitting onboarding: $e');
      return {
        'success': false,
        'message': 'Network error occurred: $e'
      };
    }
  }

  /// Submits documents for verification.
  Future<Map<String, dynamic>> submitDocuments(
      String authToken,
      Map<String, File> documents,
      ) async {
    final uri = Uri.parse("$_baseUrl/api/delivery/documents");

    try {
      var request = http.MultipartRequest("POST", uri);

      request.headers["Authorization"] =
      authToken.startsWith("Bearer ") ? authToken : "Bearer $authToken";

      for (var entry in documents.entries) {
        if (entry.value.existsSync()) {
          request.files.add(
            await http.MultipartFile.fromPath(entry.key, entry.value.path),
          );
        }
      }

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("📡 Submit Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200 || response.statusCode == 201) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "message": data["message"] ?? "Documents submitted successfully",
          "documents": data["documents"],
          "user_status": data["user_status"] ?? "documents_pending_verification",
          "next_step": "wait_verification"
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "message": errorData["message"] ??
                "Failed with status ${response.statusCode}"
          };
        } catch (_) {
          return {
            "success": false,
            "message": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error uploading: $e");
      return {"success": false, "message": "Network error: $e"};
    }
  }

  // ============================================================================
  // ORDER MANAGEMENT APIs
  // ============================================================================

  /// Get all orders assigned to delivery personnel
  Future<Map<String, dynamic>> getOrders(String authToken, {String? status}) async {
    final Uri uri = Uri.parse('$_baseUrl/api/delivery/orders${status != null ? '?status=$status' : ''}');
    
    final headers = {
      'Authorization': authToken.startsWith('Bearer ') ? authToken : 'Bearer $authToken',
      'Content-Type': 'application/json',
    };

    try {
      final response = await http.get(uri, headers: headers);
      print('Get orders response: ${response.statusCode} - ${response.body}');

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        
        // Backend now returns normal JSON (no encryption)
        return {
          'success': true,
          'orders': responseData['orders'] ?? [],
        };
      } else {
        final errorData = jsonDecode(response.body);
        return {
          'success': false,
          'message': errorData['error'] ?? 'Failed to fetch orders',
        };
      }
    } catch (e) {
      print('Error fetching orders: $e');
      return {
        'success': false,
        'message': 'Network error occurred: $e'
      };
    }
  }

  /// Get approved/active orders
  Future<Map<String, dynamic>> getApprovedOrders(String authToken) async {
    return await getOrders(authToken, status: 'approved');
  }

  /// Get rejected orders
  Future<Map<String, dynamic>> getRejectedOrders(String authToken) async {
    return await getOrders(authToken, status: 'rejected');
  }

  /// Get cancelled orders
  Future<Map<String, dynamic>> getCancelledOrders(String authToken) async {
    return await getOrders(authToken, status: 'cancelled');
  }

  /// Get delivered orders
  Future<Map<String, dynamic>> getDeliveredOrders(String authToken) async {
    return await getOrders(authToken, status: 'delivered');
  }

  /// Get order details by ID
  Future<Map<String, dynamic>> getOrderDetails(String authToken, int orderId) async {
    final Uri uri = Uri.parse('$_baseUrl/api/delivery/orders/$orderId');
    
    final headers = {
      'Authorization': authToken.startsWith('Bearer ') ? authToken : 'Bearer $authToken',
      'Content-Type': 'application/json',
    };

    try {
      final response = await http.get(uri, headers: headers);
      print('Get order details response: ${response.statusCode} - ${response.body}');

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        
        // Backend now returns normal JSON (no encryption)
        return {
          'success': true,
          'order': responseData['order'],
        };
      } else {
        final errorData = jsonDecode(response.body);
        return {
          'success': false,
          'message': errorData['error'] ?? 'Failed to fetch order details',
        };
      }
    } catch (e) {
      print('Error fetching order details: $e');
      return {
        'success': false,
        'message': 'Network error occurred: $e'
      };
    }
  }

  /// Approve an order
  Future<Map<String, dynamic>> approveOrder(String authToken, int orderId) async {
    final Uri uri = Uri.parse('$_baseUrl/api/delivery/orders/$orderId/approve');
    
    final headers = {
      'Authorization': authToken.startsWith('Bearer ') ? authToken : 'Bearer $authToken',
      'Content-Type': 'application/json',
    };

    try {
      final response = await http.post(uri, headers: headers);
      print('Approve order response: ${response.statusCode} - ${response.body}');

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        
        // Backend now returns normal JSON (no encryption)
        return {
          'success': true,
          'message': responseData['message'] ?? 'Order approved successfully',
          'order': responseData['order'],
        };
      } else {
        final errorData = jsonDecode(response.body);
        return {
          'success': false,
          'message': errorData['error'] ?? 'Failed to approve order',
        };
      }
    } catch (e) {
      print('Error approving order: $e');
      return {
        'success': false,
        'message': 'Network error occurred: $e'
      };
    }
  }

  /// Reject an order
  Future<Map<String, dynamic>> rejectOrder(String authToken, int orderId, String rejectionReason) async {
    final Uri uri = Uri.parse('$_baseUrl/api/delivery/orders/$orderId/reject');
    
    final headers = {
      'Authorization': authToken.startsWith('Bearer ') ? authToken : 'Bearer $authToken',
      'Content-Type': 'application/json',
    };

    final body = jsonEncode({
      'rejection_reason': rejectionReason,
    });

    try {
      final response = await http.post(uri, headers: headers, body: body);
      print('Reject order response: ${response.statusCode} - ${response.body}');

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        
        // Backend now returns normal JSON (no encryption)
        return {
          'success': true,
          'message': responseData['message'] ?? 'Order rejected successfully',
          'order': responseData['order'],
        };
      } else {
        final errorData = jsonDecode(response.body);
        return {
          'success': false,
          'message': errorData['error'] ?? 'Failed to reject order',
        };
      }
    } catch (e) {
      print('Error rejecting order: $e');
      return {
        'success': false,
        'message': 'Network error occurred: $e'
      };
    }
  }

  /// Helper method to determine next step based on status
  String _getNextStep(String? status) {
    switch (status) {
      case 'approved':
        return 'dashboard';
      case 'pending':
        return 'wait_approval';
      case 'profile_incomplete':
        return 'documents';
      case 'documents_pending_verification':
        return 'wait_verification';
      default:
        return 'onboarding';
    }
  }

  /// Simple decryption method - returns empty map if decryption fails
  Map<String, dynamic> _decryptData(String encryptedData) {
    try {
      // For now, return empty data if decryption fails
      // This allows the app to work even if decryption is not implemented
      print('⚠️ Decryption not implemented, returning empty data');
      return {};
    } catch (e) {
      print('Error in decryption: $e');
      return {};
    }
  }
}
