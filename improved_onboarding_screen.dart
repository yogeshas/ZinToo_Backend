import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

// Import your API service - adjust the path as needed
import '../../../core/services/api_service.dart';
// Import your document upload screen - adjust the path as needed
import './documents_screen.dart';

class OnboardingScreen extends StatefulWidget {
  final String email;
  final String? authToken;

  const OnboardingScreen({
    super.key,
    required this.email,
    required this.authToken,
  });

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final _formKey = GlobalKey<FormState>();

  // Controllers for text inputs
  final TextEditingController _firstNameController = TextEditingController();
  final TextEditingController _lastNameController = TextEditingController();
  final TextEditingController _primaryNumberController = TextEditingController();
  final TextEditingController _secondaryNumberController = TextEditingController();
  final TextEditingController _addressController = TextEditingController();
  final TextEditingController _languageController = TextEditingController();
  final TextEditingController _referralCodeController = TextEditingController();
  final TextEditingController _vehicleNumberController = TextEditingController();
  final TextEditingController _bankaccountNumberController = TextEditingController();
  final TextEditingController _bankaccountNameController = TextEditingController();
  final TextEditingController _bankaccountIFSCController = TextEditingController();

  DateTime? _dob;
  String? _bloodGroup;
  File? _profileImageFile;
  String? _profileImagePath;

  // Blood group options
  final List<String> bloodGroups = [
    'A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-'
  ];

  // Add API service
  final ApiService _apiService = ApiService();

  // Loading state
  bool _isLoading = true;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    _loadSavedData();
    _checkBackendStatus();
  }

  // Load saved data from local storage
  Future<void> _loadSavedData() async {
    try {
      final prefs = await SharedPreferences.getInstance();

      // Load form data
      _firstNameController.text = prefs.getString('onboarding_first_name') ?? '';
      _lastNameController.text = prefs.getString('onboarding_last_name') ?? '';
      _primaryNumberController.text = prefs.getString('onboarding_primary_number') ?? '';
      _secondaryNumberController.text = prefs.getString('onboarding_secondary_number') ?? '';
      _addressController.text = prefs.getString('onboarding_address') ?? '';
      _languageController.text = prefs.getString('onboarding_language') ?? '';
      _referralCodeController.text = prefs.getString('onboarding_referral_code') ?? '';
      _vehicleNumberController.text = prefs.getString('onboarding_vehicle_number') ?? '';
      _bankaccountNumberController.text = prefs.getString('onboarding_bankaccount_number') ?? '';
      _bankaccountNameController.text = prefs.getString('onboarding_bankaccount_name') ?? '';
      _bankaccountIFSCController.text = prefs.getString('onboarding_bankaccount_ifsc') ?? '';

      // Load date of birth
      final dobString = prefs.getString('onboarding_dob');
      if (dobString != null && dobString.isNotEmpty) {
        _dob = DateTime.tryParse(dobString);
      }

      // Load blood group (map empty string to null)
      final savedBloodGroup = prefs.getString('onboarding_blood_group');
      _bloodGroup = (savedBloodGroup != null && savedBloodGroup.isNotEmpty)
          ? savedBloodGroup
          : null;

      // Load profile image path (map empty string to null)
      final savedProfilePath = prefs.getString('onboarding_profile_image_path');
      _profileImagePath = (savedProfilePath != null && savedProfilePath.isNotEmpty)
          ? savedProfilePath
          : null;

      setState(() {});

      print('Loaded saved data from local storage');
    } catch (e) {
      print('Error loading saved data: $e');
    }
  }

  // Check backend status to see if user already has onboarding data
  Future<void> _checkBackendStatus() async {
    if (widget.authToken == null) {
      setState(() => _isLoading = false);
      return;
    }

    try {
      final result = await _apiService.getOnboardingStatus(widget.authToken!);

      if (result['success'] && result['onboarding'] != null) {
        // User already has onboarding data, load it
        await _loadBackendData(result['onboarding']);
      }
    } catch (e) {
      print('Error checking backend status: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  // Load data from backend
  Future<void> _loadBackendData(Map<String, dynamic> onboardingData) async {
    try {
      // Update form fields with backend data
      _firstNameController.text = onboardingData['first_name'] ?? '';
      _lastNameController.text = onboardingData['last_name'] ?? '';
      _primaryNumberController.text = onboardingData['primary_number'] ?? '';
      _secondaryNumberController.text = onboardingData['secondary_number'] ?? '';
      _addressController.text = onboardingData['address'] ?? '';
      _languageController.text = onboardingData['language'] ?? '';
      _referralCodeController.text = onboardingData['referral_code'] ?? '';
      _vehicleNumberController.text = onboardingData['vehicle_number'] ?? '';
      _bankaccountNumberController.text = onboardingData['bank_account_number'] ?? '';
      _bankaccountNameController.text = onboardingData['name_as_per_bank'] ?? '';
      _bankaccountIFSCController.text = onboardingData['ifsc_code'] ?? '';

      // Update date of birth
      if (onboardingData['dob'] != null && (onboardingData['dob'] as String).isNotEmpty) {
        _dob = DateTime.tryParse(onboardingData['dob']);
      } else {
        _dob = null;
      }

      // Update blood group (map empty string to null)
      final bg = onboardingData['blood_group'];
      _bloodGroup = (bg != null && (bg as String).isNotEmpty) ? bg : null;

      // Update profile image path (map empty string to null)
      final pic = onboardingData['profile_picture'];
      _profileImagePath = (pic != null && (pic as String).isNotEmpty) ? pic : null;

      // Save to local storage
      await _saveDataToLocal();

      setState(() {});

      print('Loaded data from backend');
    } catch (e) {
      print('Error loading backend data: $e');
    }
  }

  // Save data to local storage
  Future<void> _saveDataToLocal() async {
    try {
      final prefs = await SharedPreferences.getInstance();

      // Save form data
      await prefs.setString('onboarding_first_name', _firstNameController.text);
      await prefs.setString('onboarding_last_name', _lastNameController.text);
      await prefs.setString('onboarding_primary_number', _primaryNumberController.text);
      await prefs.setString('onboarding_secondary_number', _secondaryNumberController.text);
      await prefs.setString('onboarding_address', _addressController.text);
      await prefs.setString('onboarding_language', _languageController.text);
      await prefs.setString('onboarding_referral_code', _referralCodeController.text);
      await prefs.setString('onboarding_vehicle_number', _vehicleNumberController.text);
      await prefs.setString('onboarding_bank_account_number', _bankaccountNumberController.text);
      await prefs.setString('onboarding_name_as_per_bank', _bankaccountNameController.text);
      await prefs.setString('onboarding_ifsc_code', _bankaccountIFSCController.text);

      // Save date of birth
      if (_dob != null) {
        await prefs.setString('onboarding_dob', _dob!.toIso8601String());
      } else {
        await prefs.remove('onboarding_dob');
      }

      // Save blood group
      if (_bloodGroup != null && _bloodGroup!.isNotEmpty) {
        await prefs.setString('onboarding_blood_group', _bloodGroup!);
      } else {
        await prefs.remove('onboarding_blood_group');
      }

      // Save profile image path
      if (_profileImagePath != null && _profileImagePath!.isNotEmpty) {
        await prefs.setString('onboarding_profile_image_path', _profileImagePath!);
      } else {
        await prefs.remove('onboarding_profile_image_path');
      }

      print('Data saved to local storage');
    } catch (e) {
      print('Error saving data to local storage: $e');
    }
  }

  // Clear saved data (call this after successful submission)
  Future<void> _clearSavedData() async {
    try {
      final prefs = await SharedPreferences.getInstance();

      // Clear all onboarding keys
      await prefs.remove('onboarding_first_name');
      await prefs.remove('onboarding_last_name');
      await prefs.remove('onboarding_primary_number');
      await prefs.remove('onboarding_secondary_number');
      await prefs.remove('onboarding_address');
      await prefs.remove('onboarding_language');
      await prefs.remove('onboarding_referral_code');
      await prefs.remove('onboarding_dob');
      await prefs.remove('onboarding_blood_group');
      await prefs.remove('onboarding_vehicle_number');
      await prefs.remove('onboarding_bank_account_number');
      await prefs.remove('onboarding_name_as_per_bank');
      await prefs.remove('onboarding_ifsc_code');
      await prefs.remove('onboarding_profile_image_path');

      print('Cleared saved data');
    } catch (e) {
      print('Error clearing saved data: $e');
    }
  }

  // Fixed method implementations
  Future<void> _pickDOB() async {
    try {
      final picked = await showDatePicker(
        context: context,
        initialDate: _dob ?? DateTime(1990, 1, 1),
        firstDate: DateTime(1900),
        lastDate: DateTime.now(),
      );
      if (picked != null && picked != _dob) {
        setState(() {
          _dob = picked;
        });
        await _saveDataToLocal(); // Save immediately
        print('Date selected: ${_formatDate(picked)}');
      }
    } catch (e) {
      print('Error picking date: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error selecting date: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  // Fixed profile image picker with proper error handling
  Future<void> _pickProfileImage() async {
    try {
      print('Starting image picker...');

      final ImagePicker picker = ImagePicker();

      // Show source selection dialog
      final ImageSource? source = await _showImageSourceDialog();
      if (source == null) return; // User cancelled

      print('Image source selected: $source');

      final XFile? image = await picker.pickImage(
        source: source,
        maxWidth: 1024,
        maxHeight: 1024,
        imageQuality: 80,
      );

      if (image != null) {
        print('Image selected: ${image.path}');

        setState(() {
          _profileImageFile = File(image.path);
          _profileImagePath = image.path;
        });

        // Save to local storage
        await _saveDataToLocal();

        // Show success message
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Profile picture selected successfully!'),
            backgroundColor: Colors.green,
          ),
        );
      } else {
        print('No image selected');
      }
    } catch (e) {
      print('Error picking image: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error selecting image: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  // Helper method to show image source selection dialog
  Future<ImageSource?> _showImageSourceDialog() async {
    return showDialog<ImageSource>(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('Select Image Source'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                leading: const Icon(Icons.photo_library),
                title: const Text('Gallery'),
                onTap: () => Navigator.of(context).pop(ImageSource.gallery),
              ),
              ListTile(
                leading: const Icon(Icons.camera_alt),
                title: const Text('Camera'),
                onTap: () => Navigator.of(context).pop(ImageSource.camera),
              ),
            ],
          ),
        );
      },
    );
  }

  // Form submission method with improved error handling
  Future<void> _submitForm() async {
    if (!_formKey.currentState!.validate()) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please fill in all required fields'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    if (widget.authToken == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Authentication token missing'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    setState(() {
      _isSubmitting = true;
    });

    try {
      // Prepare form data
      final formData = {
        'first_name': _firstNameController.text.trim(),
        'last_name': _lastNameController.text.trim(),
        'dob': _dob?.toIso8601String().split('T')[0],
        'primary_number': _primaryNumberController.text.trim(),
        'secondary_number': _secondaryNumberController.text.trim(),
        'blood_group': _bloodGroup,
        'address': _addressController.text.trim(),
        'language': _languageController.text.trim(),
        'profile_picture': _profileImagePath,
        'referral_code': _referralCodeController.text.trim(),
        'vehicle_number': _vehicleNumberController.text.trim(),
        'bank_account_number': _bankaccountNumberController.text.trim(),
        'name_as_per_bank': _bankaccountNameController.text.trim(),
        'ifsc_code': _bankaccountIFSCController.text.trim(),
      };

      // Prepare files for profile picture
      final files = <http.MultipartFile>[];

      if (_profileImageFile != null) {
        try {
          // Create multipart file from the selected image
          final fileBytes = await _profileImageFile!.readAsBytes();
          final multipartFile = http.MultipartFile.fromBytes(
            'profile_picture',
            fileBytes,
            filename: 'profile_${DateTime.now().millisecondsSinceEpoch}.jpg',
          );
          files.add(multipartFile);
          print('Profile image file added to request');
        } catch (e) {
          print('Error creating multipart file: $e');
        }
      }

      print('Submitting onboarding with token: ${widget.authToken}');
      print('Form data: $formData');
      print('Date of birth: ${_dob?.toIso8601String().split('T')[0]}');
      print('Profile image file: ${_profileImageFile?.path}');
      print('Number of files: ${files.length}');

      // Submit onboarding
      final result = await _apiService.submitOnboarding(
        widget.authToken!,
        formData,
        files,
      );

      print('Onboarding result: $result');

      if (result['success']) {
        // Clear saved data after successful submission
        await _clearSavedData();

        // Show success message
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result['message'] ?? 'Profile created successfully!'),
            backgroundColor: Colors.green,
            duration: const Duration(seconds: 3),
          ),
        );

        // Navigate to document upload screen
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (context) => DocumentUploadScreen(
              email: widget.email,
              authToken: widget.authToken!,
              onboardingId: result['onboarding_id']?.toString(),
            ),
          ),
        );
      } else {
        // Show error message
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result['message'] ?? 'Failed to create profile'),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 5),
          ),
        );
      }
    } catch (e) {
      print('Onboarding error: $e');

      // Show error message
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Network error: $e'),
          backgroundColor: Colors.red,
          duration: const Duration(seconds: 5),
        ),
      );
    } finally {
      setState(() {
        _isSubmitting = false;
      });
    }
  }

  // Helper method to format date properly
  String _formatDate(DateTime date) {
    return '${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')}/${date.year}';
  }

  // Section header widget
  Widget _buildSectionHeader(String title, IconData icon, Color color) {
    return Container(
      margin: const EdgeInsets.only(top: 24, bottom: 16),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 24),
          const SizedBox(width: 12),
          Text(
            title,
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w600,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  // Form section widget
  Widget _buildFormSection({
    required String title,
    required IconData icon,
    required Color color,
    required List<Widget> children,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 24),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.1),
            spreadRadius: 1,
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionHeader(title, icon, color),
          ...children,
        ],
      ),
    );
  }

  // Profile Picture Section
  Widget _buildProfilePictureSection() {
    final hasLocalImage = _profileImageFile != null;
    final hasStoredPath = _profileImagePath != null && _profileImagePath!.isNotEmpty;

    ImageProvider? _resolveImageProvider() {
      if (hasLocalImage) return FileImage(_profileImageFile!);
      if (hasStoredPath) {
        final p = _profileImagePath!;
        if (p.startsWith('http')) return NetworkImage(p);
        try {
          final f = File(p);
          if (f.existsSync()) return FileImage(f);
        } catch (_) {}
      }
      return null;
    }

    final imageProvider = _resolveImageProvider();

    return _buildFormSection(
      title: 'Profile Picture',
      icon: Icons.camera_alt,
      color: Colors.indigo,
      children: [
        Row(
          children: [
            CircleAvatar(
              radius: 40,
              backgroundColor: imageProvider == null
                  ? Colors.grey.shade300
                  : Colors.transparent,
              backgroundImage: imageProvider,
              child: imageProvider == null
                  ? Icon(Icons.person, size: 40, color: Colors.grey.shade600)
                  : null,
            ),
            const SizedBox(width: 16),
            Expanded(
              child: ElevatedButton.icon(
                onPressed: _isSubmitting ? null : _pickProfileImage,
                icon: const Icon(Icons.camera_alt),
                label: const Text('Select Profile Picture'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.indigo.shade100,
                  foregroundColor: Colors.indigo.shade700,
                ),
              ),
            ),
          ],
        ),
        if (hasLocalImage || hasStoredPath) ...[
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.green.shade50,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.green.shade200),
            ),
            child: Row(
              children: [
                const Icon(Icons.check_circle, color: Colors.green, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Profile picture selected: '
                        '${_profileImageFile?.path.split('/').last ?? _profileImagePath?.split('/').last ?? 'Saved'}',
                    style: TextStyle(
                      color: Colors.green.shade700,
                      fontSize: 14,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        backgroundColor: Colors.grey.shade50,
        body: const Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    return Scaffold(
      backgroundColor: Colors.grey.shade50,
      body: CustomScrollView(
        slivers: [
          // Header with gradient background
          SliverToBoxAdapter(
            child: Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    Colors.blue.shade700,
                    Colors.blue.shade500,
                  ],
                ),
              ),
              child: SafeArea(
                child: Padding(
                  padding: const EdgeInsets.all(24.0),
                  child: Column(
                    children: [
                      Row(
                        children: [
                          IconButton(
                            onPressed: _isSubmitting ? null : () => Navigator.pop(context),
                            icon: const Icon(Icons.arrow_back, color: Colors.white),
                          ),
                          const SizedBox(width: 16),
                          const Expanded(
                            child: Text(
                              'Complete Your Profile',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 24,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      const Text(
                        'Please fill in all required information to complete your delivery partner profile',
                        style: TextStyle(
                          color: Colors.white70,
                          fontSize: 16,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),

          // Form content
          SliverPadding(
            padding: const EdgeInsets.all(20),
            sliver: SliverToBoxAdapter(
              child: Form(
                key: _formKey,
                child: Column(
                  children: [
                    // Personal Information Section
                    _buildFormSection(
                      title: 'Personal Information',
                      icon: Icons.person,
                      color: Colors.blue,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: TextFormField(
                                controller: _firstNameController,
                                enabled: !_isSubmitting,
                                decoration: const InputDecoration(
                                  labelText: 'First Name *',
                                  border: OutlineInputBorder(),
                                  prefixIcon: Icon(Icons.person_outline),
                                ),
                                validator: (value) => (value == null || value.trim().isEmpty)
                                    ? 'Please enter first name'
                                    : null,
                                onChanged: (value) => _saveDataToLocal(),
                              ),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: TextFormField(
                                controller: _lastNameController,
                                enabled: !_isSubmitting,
                                decoration: const InputDecoration(
                                  labelText: 'Last Name *',
                                  border: OutlineInputBorder(),
                                  prefixIcon: Icon(Icons.person_outline),
                                ),
                                validator: (value) => (value == null || value.trim().isEmpty)
                                    ? 'Please enter last name'
                                    : null,
                                onChanged: (value) => _saveDataToLocal(),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),

                        // Date of Birth
                        GestureDetector(
                          onTap: _isSubmitting ? null : _pickDOB,
                          child: AbsorbPointer(
                            child: TextFormField(
                              enabled: !_isSubmitting,
                              decoration: InputDecoration(
                                labelText: 'Date of Birth *',
                                border: const OutlineInputBorder(),
                                hintText: _dob == null
                                    ? '-- Select Date --'
                                    : _formatDate(_dob!),
                                prefixIcon: const Icon(Icons.calendar_today),
                              ),
                              validator: (value) => _dob == null
                                  ? 'Please select date of birth'
                                  : null,
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),

                        // Blood Group
                        DropdownButtonFormField<String>(
                          value: (_bloodGroup != null && _bloodGroup!.isNotEmpty)
                              ? _bloodGroup
                              : null,
                          items: bloodGroups
                              .map((bg) => DropdownMenuItem(value: bg, child: Text(bg)))
                              .toList(),
                          hint: const Text('-- Select Blood Group --'),
                          decoration: const InputDecoration(
                            labelText: 'Blood Group *',
                            border: OutlineInputBorder(),
                            prefixIcon: Icon(Icons.bloodtype),
                          ),
                          onChanged: _isSubmitting ? null : (value) async {
                            setState(() {
                              _bloodGroup = value;
                            });
                            await _saveDataToLocal();
                          },
                          validator: (value) => value == null
                              ? 'Please select blood group'
                              : null,
                        ),
                      ],
                    ),

                    // Contact Information Section
                    _buildFormSection(
                      title: 'Contact Information',
                      icon: Icons.contact_phone,
                      color: Colors.green,
                      children: [
                        TextFormField(
                          controller: _primaryNumberController,
                          enabled: !_isSubmitting,
                          keyboardType: TextInputType.phone,
                          decoration: const InputDecoration(
                            labelText: 'Primary Number *',
                            border: OutlineInputBorder(),
                            prefixIcon: Icon(Icons.phone),
                          ),
                          validator: (value) => (value == null || value.trim().isEmpty)
                              ? 'Please enter primary phone number'
                              : null,
                          onChanged: (value) => _saveDataToLocal(),
                        ),
                        const SizedBox(height: 16),

                        TextFormField(
                          controller: _secondaryNumberController,
                          enabled: !_isSubmitting,
                          keyboardType: TextInputType.phone,
                          decoration: const InputDecoration(
                            labelText: 'Secondary Number (Optional)',
                            border: OutlineInputBorder(),
                            prefixIcon: Icon(Icons.phone_forwarded),
                          ),
                          onChanged: (value) => _saveDataToLocal(),
                        ),
                        const SizedBox(height: 16),

                        TextFormField(
                          controller: _addressController,
                          enabled: !_isSubmitting,
                          decoration: const InputDecoration(
                            labelText: 'Address *',
                            border: OutlineInputBorder(),
                            prefixIcon: Icon(Icons.location_on),
                          ),
                          maxLines: 3,
                          validator: (value) => (value == null || value.trim().isEmpty)
                              ? 'Please enter address'
                              : null,
                          onChanged: (value) => _saveDataToLocal(),
                        ),
                        const SizedBox(height: 16),

                        Row(
                          children: [
                            Expanded(
                              child: TextFormField(
                                controller: _languageController,
                                enabled: !_isSubmitting,
                                decoration: const InputDecoration(
                                  labelText: 'Language *',
                                  border: OutlineInputBorder(),
                                  prefixIcon: Icon(Icons.language),
                                ),
                                validator: (value) => (value == null || value.trim().isEmpty)
                                    ? 'Please enter language'
                                    : null,
                                onChanged: (value) => _saveDataToLocal(),
                              ),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: TextFormField(
                                controller: _referralCodeController,
                                enabled: !_isSubmitting,
                                decoration: const InputDecoration(
                                  labelText: 'Referral Code (Optional)',
                                  border: OutlineInputBorder(),
                                  prefixIcon: Icon(Icons.share),
                                ),
                                onChanged: (value) => _saveDataToLocal(),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),

                    // Vehicle & Bank Information Section
                    _buildFormSection(
                      title: 'Vehicle & Bank Information',
                      icon: Icons.verified_user,
                      color: Colors.orange,
                      children: [
                        TextFormField(
                          controller: _vehicleNumberController,
                          enabled: !_isSubmitting,
                          keyboardType: TextInputType.text,
                          decoration: const InputDecoration(
                            labelText: 'Vehicle Number *',
                            border: OutlineInputBorder(),
                            prefixIcon: Icon(Icons.bike_scooter),
                          ),
                          validator: (value) => (value == null || value.trim().isEmpty)
                              ? 'Please enter vehicle number'
                              : null,
                          onChanged: (value) => _saveDataToLocal(),
                        ),
                        const SizedBox(height: 16),
                        TextFormField(
                          controller: _bankaccountNumberController,
                          enabled: !_isSubmitting,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(
                            labelText: 'Bank Account Number *',
                            border: OutlineInputBorder(),
                            prefixIcon: Icon(Icons.account_balance),
                          ),
                          validator: (value) => (value == null || value.trim().isEmpty)
                              ? 'Please enter bank account number'
                              : null,
                          onChanged: (value) => _saveDataToLocal(),
                        ),
                        const SizedBox(height: 16),
                        TextFormField(
                          controller: _bankaccountNameController,
                          enabled: !_isSubmitting,
                          keyboardType: TextInputType.name,
                          decoration: const InputDecoration(
                            labelText: 'Name as per Bank *',
                            border: OutlineInputBorder(),
                            prefixIcon: Icon(Icons.account_balance),
                          ),
                          validator: (value) => (value == null || value.trim().isEmpty)
                              ? 'Please enter name as per bank'
                              : null,
                          onChanged: (value) => _saveDataToLocal(),
                        ),
                        const SizedBox(height: 16),
                        TextFormField(
                          controller: _bankaccountIFSCController,
                          enabled: !_isSubmitting,
                          keyboardType: TextInputType.text,
                          textCapitalization: TextCapitalization.characters,
                          decoration: const InputDecoration(
                            labelText: 'IFSC Code *',
                            border: OutlineInputBorder(),
                            prefixIcon: Icon(Icons.account_balance),
                          ),
                          validator: (value) => (value == null || value.trim().isEmpty)
                              ? 'Please enter IFSC code'
                              : null,
                          onChanged: (value) => _saveDataToLocal(),
                        ),
                      ],
                    ),

                    // Profile Picture Section
                    _buildProfilePictureSection(),

                    const SizedBox(height: 32),

                    // Submit button
                    SizedBox(
                      width: double.infinity,
                      height: 56,
                      child: ElevatedButton(
                        onPressed: _isSubmitting ? null : _submitForm,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.blue.shade600,
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                          ),
                          elevation: 4,
                        ),
                        child: _isSubmitting
                            ? const Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  SizedBox(
                                    width: 20,
                                    height: 20,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                                    ),
                                  ),
                                  SizedBox(width: 12),
                                  Text(
                                    'Submitting...',
                                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
                                  ),
                                ],
                              )
                            : const Text(
                                'Complete Setup',
                                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
                              ),
                      ),
                    ),
                    const SizedBox(height: 24),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _firstNameController.dispose();
    _lastNameController.dispose();
    _primaryNumberController.dispose();
    _secondaryNumberController.dispose();
    _addressController.dispose();
    _languageController.dispose();
    _referralCodeController.dispose();
    _vehicleNumberController.dispose();
    _bankaccountNumberController.dispose();
    _bankaccountNameController.dispose();
    _bankaccountIFSCController.dispose();
    super.dispose();
  }
}
