import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../auth/screens/login_screen.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';
import 'view_orders.dart';
import 'approved_orders.dart';
import 'cancelled_orders.dart';
import '../../../core/services/api_service.dart';
import 'edit_profile_screen.dart';
import 'leave_request_screen.dart';
import 'earnings_management_screen.dart';

class DeliveryDashboard extends StatefulWidget {
  final String email;
  final String authToken;
  const DeliveryDashboard({Key? key, required this.email, required this.authToken}) : super(key: key);

  @override
  State<DeliveryDashboard> createState() => _DeliveryDashboardState();
}

class _DeliveryDashboardState extends State<DeliveryDashboard> {
  int _currentIndex = 0;
  int _selectedTab = 0;
  String? _authToken;
  File? _profileImage;
  final ImagePicker _picker = ImagePicker();
  final ApiService _apiService = ApiService();

  // User profile data
  Map<String, dynamic>? _userProfile;
  bool _isLoadingProfile = false;
  String? _profileError;

  // Base URL for images
  final String _baseUrl = 'http://13.211.168.61:5000/';

  Future<void> _showImageSourceDialog() async {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return SimpleDialog(
          title: const Text('Upload Profile Picture'),
          children: <Widget>[
            SimpleDialogOption(
              onPressed: () {
                Navigator.pop(context); // Close dialog
                _pickImageFromGallery(); // Pick image
              },
              child: const Text('Choose photo from gallery'),
            ),
          ],
        );
      },
    );
  }

  // Pick image from gallery
  Future<void> _pickImageFromGallery() async {
    final XFile? image = await _picker.pickImage(source: ImageSource.gallery);
    if (image != null) {
      setState(() {
        _profileImage = File(image.path);
      });

      // Upload the new profile image
      await _updateProfileImage();
    }
  }

  // Update profile image
  Future<void> _updateProfileImage() async {
    if (_profileImage == null || _authToken == null) return;

    setState(() {
      _isLoadingProfile = true;
    });

    try {
      final result = await _apiService.updateUserProfile(
        _authToken!,
        {}, // Empty data, just updating image
        profileImage: _profileImage,
      );

      if (result['success']) {
        // Refresh profile data
        await _loadUserProfile();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Profile picture updated successfully!')),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(result['message'] ?? 'Failed to update profile picture')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error updating profile picture: $e')),
      );
    } finally {
      setState(() {
        _isLoadingProfile = false;
      });
    }
  }

  @override
  void initState() {
    super.initState();
    _loadAuthToken();
  }

  Future<void> _loadAuthToken() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _authToken = prefs.getString('authToken');
    });

    // Load user profile after getting auth token
    if (_authToken != null) {
      await _loadUserProfile();
    }
  }

  // Load user profile data
  Future<void> _loadUserProfile() async {
    if (_authToken == null) return;

    setState(() {
      _isLoadingProfile = true;
      _profileError = null;
    });

    try {
      final result = await _apiService.getUserProfile(_authToken!);

      if (result['success']) {
        setState(() {
          _userProfile = result['profile'];
        });
        print('Profile loaded: $_userProfile'); // Debug log
      } else {
        setState(() {
          _profileError = result['message'] ?? 'Failed to load profile';
        });
        print('Profile load error: ${result['message']}'); // Debug log
      }
    } catch (e) {
      setState(() {
        _profileError = 'Error loading profile: $e';
      });
      print('Profile load exception: $e'); // Debug log
    } finally {
      setState(() {
        _isLoadingProfile = false;
      });
    }
  }

  // Helper method to get full image URL
  String _getFullImageUrl(String? imagePath) {
    if (imagePath == null || imagePath.isEmpty) {
      return '';
    }

    // If it's already a full URL, return as is
    if (imagePath.startsWith('http')) {
      return imagePath;
    }

    // Remove leading slash if present to avoid double slashes
    final cleanPath = imagePath.startsWith('/') ? imagePath.substring(1) : imagePath;

    // Construct full URL
    return '$_baseUrl/$cleanPath';
  }

  List<Widget> get _orderScreens {
    return [
      ViewOrdersScreen5Tabs(authToken: _authToken ?? ''),
      ApprovedOrdersScreen(),
      CancelledOrdersScreen(),
    ];
  }

  Widget _ordersTab() {
    return SafeArea(
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 560),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 12),
                Expanded(
                  child: _authToken != null
                      ? _orderScreens[_selectedTab]
                      : const Center(child: CircularProgressIndicator()),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _accountTab() {
    return SafeArea(
      child: SingleChildScrollView(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 560),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                /// --- Profile Header ---
                _buildProfileHeader(),

                const SizedBox(height: 32),

                /// --- Account Settings Heading ---
                const Text(
                  "Options",
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 12),

                /// --- Account Options ---
                _buildAccountOptions(),

                const SizedBox(height: 24),

                /// --- Sign Out Button ---
                _buildSignOutButton(),

                // Add bottom padding to prevent overlap with bottom navigation
                const SizedBox(height: 20),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildProfileHeader() {
    if (_isLoadingProfile) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(32.0),
          child: CircularProgressIndicator(),
        ),
      );
    }

    if (_profileError != null) {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.red.shade50,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.red.shade200),
        ),
        child: Column(
          children: [
            Icon(Icons.error_outline, color: Colors.red.shade600, size: 32),
            const SizedBox(height: 8),
            Text(
              _profileError!,
              style: TextStyle(color: Colors.red.shade700),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            ElevatedButton(
              onPressed: _loadUserProfile,
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    // Extract user data from profile with better fallbacks
    final firstName = _userProfile?['first_name'] ?? '';
    final lastName = _userProfile?['last_name'] ?? '';
    final fullName = '${firstName} ${lastName}'.trim();
    final displayName = fullName.isNotEmpty ? fullName : 'Delivery Partner';

    final primaryNumber = _userProfile?['primary_number'] ?? '';
    final phoneNumber = primaryNumber.isNotEmpty ? primaryNumber : 'Phone not available';

    final email = widget.email;
    final profileImageUrl = _userProfile?['profile_picture'];
    final rating = _userProfile?['rating'] ?? 0.0;
    final status = _userProfile?['status'] ?? 'Unknown';

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Stack(
          children: [
            CircleAvatar(
              radius: 40,
              backgroundColor: Colors.grey.shade300,
              backgroundImage: _profileImage != null
                  ? FileImage(_profileImage!)
                  : profileImageUrl != null && profileImageUrl.isNotEmpty
                  ? NetworkImage(_getFullImageUrl(profileImageUrl)) as ImageProvider
                  : const AssetImage("assets/images/default_profile.png") as ImageProvider,
            ),
            if (_isLoadingProfile)
              Positioned.fill(
                child: Container(
                  decoration: BoxDecoration(
                    color: Colors.black54,
                    shape: BoxShape.circle,
                  ),
                  child: const Center(
                    child: SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    ),
                  ),
                ),
              ),
            Positioned(
              bottom: 0,
              right: 0,
              child: GestureDetector(
                onTap: _isLoadingProfile ? null : _showImageSourceDialog,
                child: Container(
                  decoration: const BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.orange,
                  ),
                  padding: const EdgeInsets.all(6),
                  child: const Icon(Icons.edit, color: Colors.white, size: 16),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                displayName,
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 4),
              Text(
                phoneNumber,
                style: const TextStyle(fontSize: 14, color: Colors.black54),
              ),
              const SizedBox(height: 4),
              Text(
                email,
                style: const TextStyle(fontSize: 14, color: Colors.black54),
              ),
              const SizedBox(height: 4),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: _getStatusColor(status).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: _getStatusColor(status)),
                ),
                child: Text(
                  _getStatusText(status),
                  style: TextStyle(
                    fontSize: 12,
                    color: _getStatusColor(status),
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
              const SizedBox(height: 6),
              Row(
                children: List.generate(5, (index) {
                  return Icon(
                    index < rating ? Icons.star : Icons.star_border,
                    color: Colors.orange.shade600,
                    size: 20,
                  );
                }),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildAccountOptions() {
    return Column(
      children: [
        _buildOptionItem(
          icon: Icons.person_outline,
          title: "Edit Profile",
          onTap: () {
            _navigateToEditProfile();
          },
        ),
        const SizedBox(height: 12),
        _buildOptionItem(
          icon: Icons.event_busy,
          title: "Leave Requests",
          onTap: () {
            _navigateToLeaveRequests();
          },
        ),
        const SizedBox(height: 12),
        _buildOptionItem(
          icon: Icons.monetization_on,
          title: "Dashboard Earnings",
          onTap: () {
            _navigateToEarning();
          },
        ),
        const SizedBox(height: 12),
        _buildOptionItem(
          icon: Icons.help_outline,
          title: "Help & Support",
          onTap: () {
            // TODO: Navigate to Help screen
            print("Help & Support tapped");
          },
        ),
        const SizedBox(height: 12),
        _buildOptionItem(
          icon: Icons.privacy_tip_outlined,
          title: "Privacy Policy",
          onTap: () {
            // TODO: Navigate to Privacy Policy screen
            print("Privacy Policy tapped");
          },
        ),
      ],
    );
  }

  Widget _buildOptionItem({
    required IconData icon,
    required String title,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        decoration: BoxDecoration(
          color: Colors.grey.shade100,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.grey.shade300),
        ),
        child: Row(
          children: [
            Icon(icon, color: Colors.orange.shade700),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                title,
                style: const TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
            Icon(Icons.chevron_right, color: Colors.grey.shade600),
          ],
        ),
      ),
    );
  }

  Widget _buildSignOutButton() {
    return OutlinedButton(
      onPressed: () async {
        final prefs = await SharedPreferences.getInstance();
        await prefs.remove('authToken');
        await prefs.remove('email');
        if (!mounted) return;
        Navigator.pushAndRemoveUntil(
          context,
          MaterialPageRoute(builder: (_) => const LoginScreen()),
              (route) => false,
        );
      },
      style: OutlinedButton.styleFrom(
        minimumSize: const Size(double.infinity, 48),
        side: BorderSide(color: Colors.red.shade400),
      ),
      child: Text(
        "Sign Out",
        style: TextStyle(color: Colors.red.shade600),
      ),
    );
  }

  Color _getStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'approved':
        return Colors.green;
      case 'pending':
        return Colors.orange;
      case 'rejected':
        return Colors.red;
      case 'profile_incomplete':
        return Colors.blue;
      case 'documents_pending_verification':
        return Colors.purple;
      default:
        return Colors.grey;
    }
  }

  String _getStatusText(String status) {
    switch (status.toLowerCase()) {
      case 'approved':
        return 'Active';
      case 'pending':
        return 'Pending Approval';
      case 'rejected':
        return 'Rejected';
      case 'profile_incomplete':
        return 'Profile Incomplete';
      case 'documents_pending_verification':
        return 'Documents Pending';
      default:
        return status;
    }
  }

  // Navigate to edit profile screen
  Future<void> _navigateToEditProfile() async {
    if (_authToken == null) return;

    final result = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => EditProfileScreen(
          authToken: _authToken!,
          currentProfile: _userProfile,
          onProfileUpdated: (updatedProfile) {
            setState(() {
              _userProfile = updatedProfile;
            });
          },
        ),
      ),
    );

    // Refresh profile data after returning from edit screen
    if (result != null) {
      await _loadUserProfile();
    }
  }

  // Navigate to leave requests screen
  Future<void> _navigateToLeaveRequests() async {
    if (_authToken == null) return;

    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => LeaveRequestScreen(
          authToken: _authToken!,
        ),
      ),
    );
  }

  Future<void> _navigateToEarning() async {
    if (_authToken == null) return;

    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => EarningsManagementScreen(
          authToken: _authToken!,
        ),
      ),
    );
  }

  Widget _customBottomNav() {
    return Container(
      height: 80,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(24),
          topRight: Radius.circular(24),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
          ),
        ],
      ),
      child: Row(
        children: [
          _buildNavItem(
            icon: Icons.shopping_basket_outlined,
            label: "Orders",
            index: 0,
          ),
          _buildNavItem(
            icon: Icons.person_outline,
            label: "Account",
            index: 1,
          ),
        ],
      ),
    );
  }

  Widget _buildNavItem({
    required IconData icon,
    required String label,
    required int index,
  }) {
    final bool isSelected = _currentIndex == index;
    final color = isSelected ? Colors.orange.shade600 : Colors.grey.shade600;

    return Expanded(
      child: InkWell(
        onTap: () => setState(() => _currentIndex = index),
        child: Container(
          color: Colors.transparent,
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, color: color, size: 28),
              const SizedBox(height: 1),
              Text(
                label,
                style: TextStyle(
                  color: color,
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                  fontSize: 12,
                ),
              ),
              if (isSelected)
                Container(
                  margin: const EdgeInsets.only(top: 6),
                  height: 3,
                  width: 24,
                  decoration: BoxDecoration(
                    color: Colors.orange.shade600,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext ctx) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        automaticallyImplyLeading: false,
        title: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Image.asset("assets/images/logo.jpeg", height: 110),
            Stack(
              clipBehavior: Clip.none,
              children: [
                IconButton(
                  iconSize: 30,
                  icon: const Icon(Icons.notifications_none, color: Colors.black87),
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => Scaffold(
                          appBar: AppBar(
                            title: const Text('Notifications'),
                            backgroundColor: Colors.blue,
                            foregroundColor: Colors.white,
                          ),
                          body: const Center(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(
                                  Icons.notifications,
                                  size: 80,
                                  color: Colors.blue,
                                ),
                                SizedBox(height: 20),
                                Text(
                                  'Notification Screen',
                                  style: TextStyle(
                                    fontSize: 24,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                SizedBox(height: 10),
                                Text(
                                  'This is where notifications will be displayed',
                                  style: TextStyle(
                                    fontSize: 16,
                                    color: Colors.grey,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    );
                  },
                ),
                Positioned(
                  top: 8,
                  right: 8,
                  child: Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: Colors.red,
                      shape: BoxShape.circle,
                      border: Border.all(color: Colors.white, width: 1.2),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
      body: _currentIndex == 0 ? _ordersTab() : _accountTab(),
      bottomNavigationBar: _customBottomNav(),
    );
  }
}