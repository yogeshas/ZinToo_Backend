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

  /// Get user profile data from onboarding
  Future<Map<String, dynamic>> getUserProfile(String authToken) async {
    final Uri uri = Uri.parse('$_baseUrl/api/delivery/onboard');

    final headers = {
      'Authorization': authToken.startsWith('Bearer ') ? authToken : 'Bearer $authToken',
      'Content-Type': 'application/json',
    };

    print('Making GET request to fetch user profile: $uri');
    print('Headers: $headers');

    try {
      final response = await http.get(uri, headers: headers);

      print('Get user profile response: ${response.statusCode} - ${response.body}');

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        return {
          'success': true,
          'profile': responseData['onboarding'],
          'user_status': responseData['onboarding']?['status'] ?? 'not_started',
        };
      } else if (response.statusCode == 404) {
        print('No profile found - user needs to complete onboarding');
        return {
          'success': false,
          'message': 'Profile not found. Please complete onboarding first.',
        };
      } else {
        final errorData = jsonDecode(response.body);
        return {
          'success': false,
          'message': errorData['message'] ?? 'Failed to fetch profile data',
        };
      }
    } catch (e) {
      print('Error getting user profile: $e');
      return {
        'success': false,
        'message': 'Network error occurred: $e'
      };
    }
  }

  /// Update user profile data
  Future<Map<String, dynamic>> updateUserProfile(
      String authToken,
      Map<String, dynamic> profileData,
      {File? profileImage}
      ) async {
    final Uri uri = Uri.parse('$_baseUrl/api/delivery/onboard');

    try {
      var request = http.MultipartRequest('PUT', uri);

      request.headers['Authorization'] =
      authToken.startsWith('Bearer ') ? authToken : 'Bearer $authToken';

      // Add form fields
      profileData.forEach((key, value) {
        if (value != null && value.toString().isNotEmpty) {
          request.fields[key] = value.toString();
        }
      });

      // Add profile image if provided
      if (profileImage != null && profileImage.existsSync()) {
        request.files.add(
          await http.MultipartFile.fromPath('profile_image', profileImage.path),
        );
      }

      print('Making PUT request to update profile: $uri');
      print('Headers: ${request.headers}');
      print('Form fields: ${request.fields}');
      print('Files: ${request.files.length}');

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print('Update profile API Response: ${response.statusCode} - ${response.body}');

      if (response.statusCode == 200 || response.statusCode == 201) {
        final responseData = jsonDecode(response.body);
        return {
          'success': true,
          'message': responseData['message'] ?? 'Profile updated successfully!',
          'profile': responseData['onboarding'],
        };
      } else {
        final errorData = jsonDecode(response.body);
        return {
          'success': false,
          'message': errorData['message'] ??
              'Failed to update profile (Status: ${response.statusCode})'
        };
      }
    } catch (e) {
      print('Error updating profile: $e');
      return {
        'success': false,
        'message': 'Network error occurred: $e'
      };
    }
  }

  /// Update delivery onboarding with document support
  Future<Map<String, dynamic>> updateDeliveryOnboarding(
      String authToken,
      Map<String, dynamic> profileData,
      {File? profileImage, File? aadharCardImage, File? panCardImage, File? dlImage, File? rcCardImage, File? bankPassbookImage}
      ) async {
    final Uri uri = Uri.parse('$_baseUrl/api/delivery/onboard');

    try {
      var request = http.MultipartRequest('PUT', uri);

      request.headers['Authorization'] =
      authToken.startsWith('Bearer ') ? authToken : 'Bearer $authToken';

      // Add form fields
      profileData.forEach((key, value) {
        if (value != null && value.toString().isNotEmpty) {
          request.fields[key] = value.toString();
        }
      });

      // Add profile image if provided
      if (profileImage != null && profileImage.existsSync()) {
        request.files.add(
          await http.MultipartFile.fromPath('profile_picture', profileImage.path),
        );
      }

      // Add Aadhar card image if provided
      if (aadharCardImage != null && aadharCardImage.existsSync()) {
        request.files.add(
          await http.MultipartFile.fromPath('aadhar_card', aadharCardImage.path),
        );
      }

      // Add PAN card image if provided
      if (panCardImage != null && panCardImage.existsSync()) {
        request.files.add(
          await http.MultipartFile.fromPath('pan_card', panCardImage.path),
        );
      }

      // Add DL image if provided
      if (dlImage != null && dlImage.existsSync()) {
        request.files.add(
          await http.MultipartFile.fromPath('dl', dlImage.path),
        );
      }

      // Add RC card image if provided
      if (rcCardImage != null && rcCardImage.existsSync()) {
        request.files.add(
          await http.MultipartFile.fromPath('rc_card', rcCardImage.path),
        );
      }

      // Add bank passbook image if provided
      if (bankPassbookImage != null && bankPassbookImage.existsSync()) {
        request.files.add(
          await http.MultipartFile.fromPath('bank_passbook', bankPassbookImage.path),
        );
      }

      print('🔍 [DEBUG MOBILE APP] Making PUT request to update delivery onboarding: $uri');
      print('🔍 [DEBUG] Headers: ${request.headers}');
      print('🔍 [DEBUG] Form fields: ${request.fields}');
      print('🔍 [DEBUG] Files count: ${request.files.length}');
      
      // Debug each file being sent
      for (int i = 0; i < request.files.length; i++) {
        var file = request.files[i];
        print('🔍 [DEBUG] File $i: field=${file.field}, filename=${file.filename}, length=${file.length}');
      }

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print('Update delivery onboarding API Response: ${response.statusCode} - ${response.body}');

      if (response.statusCode == 200 || response.statusCode == 201) {
        final responseData = jsonDecode(response.body);
        return {
          'success': true,
          'message': responseData['message'] ?? 'Profile updated successfully!',
          'profile': responseData['onboarding'],
        };
      } else {
        final errorData = jsonDecode(response.body);
        return {
          'success': false,
          'message': errorData['message'] ??
              'Failed to update profile (Status: ${response.statusCode})'
        };
      }
    } catch (e) {
      print('Error updating delivery onboarding: $e');
      return {
        'success': false,
        'message': 'Network error occurred: $e'
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
  // ORDER MANAGEMENT APIs - CORRECTED FOR DELIVERY GUY APP
  // ============================================================================

  /// Get all orders assigned to delivery personnel (DELIVERY GUY ENDPOINT)
  Future<Map<String, dynamic>> getOrders(String authToken, {String? status}) async {
    // CORRECTED: Using delivery guy endpoint (not admin)
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

        // Check if data is encrypted
        if (responseData['encrypted_data'] != null) {
          print('📦 Received encrypted data, attempting to decrypt...');

          // Try to decrypt the data
          final decryptedData = _decryptData(responseData['encrypted_data']);

          if (decryptedData.isNotEmpty) {
            return {
              'success': true,
              'orders': decryptedData['orders'] ?? [],
            };
          } else {
            // If decryption fails, return empty orders list for now
            print('⚠️ Decryption failed, returning empty orders list');
            return {
              'success': true,
              'orders': [],
            };
          }
        } else {
          // Data is not encrypted
          return {
            'success': true,
            'orders': responseData['orders'] ?? [],
          };
        }
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

  /// Get approved/active orders (DELIVERY GUY ENDPOINT)
  Future<Map<String, dynamic>> getApprovedOrders(String authToken) async {
    return await getOrders(authToken, status: 'approved');
  }

  /// Get rejected orders (DELIVERY GUY ENDPOINT)
  Future<Map<String, dynamic>> getRejectedOrders(String authToken) async {
    return await getOrders(authToken, status: 'rejected');
  }

  /// Get cancelled orders (DELIVERY GUY ENDPOINT)
  Future<Map<String, dynamic>> getCancelledOrders(String authToken) async {
    return await getOrders(authToken, status: 'cancelled');
  }

  /// Get delivered orders (DELIVERY GUY ENDPOINT)
  Future<Map<String, dynamic>> getDeliveredOrders(String authToken) async {
    return await getOrders(authToken, status: 'delivered');
  }

  /// Get assigned orders (DELIVERY GUY ENDPOINT)
  Future<Map<String, dynamic>> getAssignedOrders(String authToken) async {
    return await getOrders(authToken, status: 'assigned');
  }

  /// Get order details by ID (DELIVERY GUY ENDPOINT)
  Future<Map<String, dynamic>> getOrderDetails(String authToken, int orderId) async {
    // CORRECTED: Using delivery guy endpoint (not admin)
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

        if (responseData['encrypted_data'] != null) {
          final decryptedData = _decryptData(responseData['encrypted_data']);
          return {
            'success': true,
            'order': decryptedData['order'],
          };
        } else {
          return {
            'success': true,
            'order': responseData['order'],
          };
        }
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

  /// Approve an order (DELIVERY GUY ENDPOINT)
  Future<Map<String, dynamic>> approveOrder(String authToken, int orderId) async {
    // CORRECTED: Using delivery guy endpoint (not admin)
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

        if (responseData['encrypted_data'] != null) {
          final decryptedData = _decryptData(responseData['encrypted_data']);
          return {
            'success': true,
            'message': decryptedData['message'] ?? 'Order approved successfully',
            'order': decryptedData['order'],
          };
        } else {
          return {
            'success': true,
            'message': responseData['message'] ?? 'Order approved successfully',
            'order': responseData['order'],
          };
        }
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

  /// Reject an order (DELIVERY GUY ENDPOINT)

  /// Mark order as out for delivery (DELIVERY GUY ENDPOINT)

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
        return 'wait_approval';
      default:
        return 'onboarding';
    }
  }

  /// Upload documents to backend
  Future<Map<String, dynamic>> uploadDocuments({
    required String authToken,
    File? aadharCard, 
    File? panCard,
    File? dl,
    File? rcCard,
    File? bankPassbook,
  }) async {
    final Uri uri = Uri.parse('$_baseUrl/api/delivery/documents');
    
    try {
      var request = http.MultipartRequest('POST', uri);
      
      // Add authorization header
      request.headers['Authorization'] = 'Bearer $authToken';
      
      // Add files to request
      if (aadharCard != null) {
        request.files.add(await http.MultipartFile.fromPath(
          'aadhar_card',
          aadharCard.path,
        ));
      }
      
      if (panCard != null) {
        request.files.add(await http.MultipartFile.fromPath(
          'pan_card',
          panCard.path,
        ));
      }
      
      if (dl != null) {
        request.files.add(await http.MultipartFile.fromPath(
          'dl',
          dl.path,
        ));
      }
      
      if (rcCard != null) {
        request.files.add(await http.MultipartFile.fromPath(
          'rc_card',
          rcCard.path,
        ));
      }
      
      if (bankPassbook != null) {
        request.files.add(await http.MultipartFile.fromPath(
          'bank_passbook',
          bankPassbook.path,
        ));
      }
      
      print('Uploading documents...');
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);
      
      print('Document upload response: ${response.statusCode} - ${response.body}');
      
      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        return {
          'success': true,
          'message': responseData['message'] ?? 'Documents uploaded successfully',
          'onboarding_id': responseData['onboarding_id'],
          'user_status': responseData['user_status'],
          'next_step': responseData['next_step'],
        };
      } else {
        final errorData = jsonDecode(response.body);
        return {
          'success': false,
          'message': errorData['message'] ?? 'Failed to upload documents',
        };
      }
    } catch (e) {
      print('Error uploading documents: $e');
      return {
        'success': false,
        'message': 'Error uploading documents: $e',
      };
    }
  }

  /// Update profile with document numbers
  Future<Map<String, dynamic>> updateProfileWithDocuments({
    required String authToken,
    required Map<String, dynamic> profileData,
  }) async {
    final Uri uri = Uri.parse('$_baseUrl/api/delivery/onboard');
    
    try {
      final response = await http.put(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $authToken',
        },
        body: jsonEncode(profileData),
      );
      
      print('Profile update response: ${response.statusCode} - ${response.body}');
      
      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        return {
          'success': true,
          'message': responseData['message'] ?? 'Profile updated successfully',
          'onboarding_id': responseData['onboarding_id'],
          'user_status': responseData['user_status'],
          'next_step': responseData['next_step'],
        };
      } else {
        final errorData = jsonDecode(response.body);
        return {
          'success': false,
          'message': errorData['message'] ?? 'Failed to update profile',
        };
      }
    } catch (e) {
      print('Error updating profile: $e');
      return {
        'success': false,
        'message': 'Error updating profile: $e',
      };
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
// TODO Implement this library.