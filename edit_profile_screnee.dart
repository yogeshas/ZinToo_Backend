import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:url_launcher/url_launcher.dart';
import 'dart:io';
import 'api_service_updated.dart';

class EditProfileScreen extends StatefulWidget {
  final String authToken;
  final Map<String, dynamic>? currentProfile;
  final Function(Map<String, dynamic>) onProfileUpdated;

  const EditProfileScreen({
    Key? key,
    required this.authToken,
    this.currentProfile,
    required this.onProfileUpdated,
  }) : super(key: key);

  @override
  State<EditProfileScreen> createState() => _EditProfileScreenState();
}

class _EditProfileScreenState extends State<EditProfileScreen> with TickerProviderStateMixin {
  final _formKey = GlobalKey<FormState>();
  final _apiService = ApiService();
  final ImagePicker _picker = ImagePicker();
  late TabController _tabController;

  // Base URL for images and documents
  final String _baseUrl = 'http://dev.zintoo.in:5000/'; // Update this with your actual base URL

  // Form controllers for Profile Tab
  late TextEditingController _firstNameController;
  late TextEditingController _lastNameController;
  late TextEditingController _emailController;
  late TextEditingController _primaryNumberController;
  late TextEditingController _secondaryNumberController;
  late TextEditingController _addressController;
  late TextEditingController _languageController;
  late TextEditingController _referralCodeController;
  late TextEditingController _aadharCardController;
  late TextEditingController _panCardController;
  late TextEditingController _dlController;
  late TextEditingController _vehicleNumberController;
  late TextEditingController _bankAccountNumberController;
  late TextEditingController _ifscCodeController;
  late TextEditingController _nameAsPerBankController;

  // State variables
  File? _profileImage;
  File? _aadharCardImage;
  File? _panCardImage;
  File? _dlImage;
  File? _rcCardImage;
  File? _bankPassbookImage;
  bool _isLoading = false;
  String? _selectedBloodGroup;
  DateTime? _selectedDateOfBirth;
  int _refreshCounter = 0; // Counter to force image refresh

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _initializeControllers();
    // Fetch fresh profile data to ensure we have the latest URLs
    _fetchFreshProfileData();
  }

  void _initializeControllers() {
    final profile = widget.currentProfile;

    _firstNameController = TextEditingController(text: profile?['first_name'] ?? '');
    _lastNameController = TextEditingController(text: profile?['last_name'] ?? '');
    _emailController = TextEditingController(text: profile?['email'] ?? '');
    _primaryNumberController = TextEditingController(text: profile?['primary_number'] ?? '');
    _secondaryNumberController = TextEditingController(text: profile?['secondary_number'] ?? '');
    _addressController = TextEditingController(text: profile?['address'] ?? '');
    _languageController = TextEditingController(text: profile?['language'] ?? 'English');
    _referralCodeController = TextEditingController(text: profile?['referral_code'] ?? '');
    _aadharCardController = TextEditingController(text: profile?['aadhar_card'] ?? '');
    _panCardController = TextEditingController(text: profile?['pan_card'] ?? '');
    _dlController = TextEditingController(text: profile?['dl'] ?? '');
    _vehicleNumberController = TextEditingController(text: profile?['vehicle_number'] ?? '');
    _bankAccountNumberController = TextEditingController(text: profile?['bank_account_number'] ?? '');
    _ifscCodeController = TextEditingController(text: profile?['ifsc_code'] ?? '');
    _nameAsPerBankController = TextEditingController(text: profile?['name_as_per_bank'] ?? '');

    _selectedBloodGroup = profile?['blood_group'];

    // Parse date of birth if available
    if (profile?['dob'] != null) {
      try {
        _selectedDateOfBirth = DateTime.parse(profile?['dob']);
      } catch (e) {
        print('Error parsing date of birth: $e');
      }
    }
  }

  @override
  void dispose() {
    _tabController.dispose();
    _firstNameController.dispose();
    _lastNameController.dispose();
    _emailController.dispose();
    _primaryNumberController.dispose();
    _secondaryNumberController.dispose();
    _addressController.dispose();
    _languageController.dispose();
    _referralCodeController.dispose();
    _aadharCardController.dispose();
    _panCardController.dispose();
    _dlController.dispose();
    _vehicleNumberController.dispose();
    _bankAccountNumberController.dispose();
    _ifscCodeController.dispose();
    _nameAsPerBankController.dispose();
    super.dispose();
  }

  Future<void> _pickImageFromGallery(String type) async {
    final XFile? image = await _picker.pickImage(source: ImageSource.gallery);
    if (image != null) {
      setState(() {
        switch (type) {
          case 'profile':
            _profileImage = File(image.path);
            break;
          case 'aadhar_card':
            _aadharCardImage = File(image.path);
            break;
          case 'pan_card':
            _panCardImage = File(image.path);
            break;
          case 'dl':
            _dlImage = File(image.path);
            break;
          case 'rc_card':
            _rcCardImage = File(image.path);
            break;
          case 'bank_passbook':
            _bankPassbookImage = File(image.path);
            break;
        }
      });
    }
  }

  Future<void> _pickImageFromCamera(String type) async {
    final XFile? image = await _picker.pickImage(source: ImageSource.camera);
    if (image != null) {
      setState(() {
        switch (type) {
          case 'profile':
            _profileImage = File(image.path);
            break;
          case 'aadhar_card':
            _aadharCardImage = File(image.path);
            break;
          case 'pan_card':
            _panCardImage = File(image.path);
            break;
          case 'dl':
            _dlImage = File(image.path);
            break;
          case 'rc_card':
            _rcCardImage = File(image.path);
            break;
          case 'bank_passbook':
            _bankPassbookImage = File(image.path);
            break;
        }
      });
    }
  }

  Future<void> _showImageSourceDialog(String type) async {
    showModalBottomSheet(
      context: context,
      builder: (BuildContext context) {
        return SafeArea(
          child: Wrap(
            children: [
              ListTile(
                leading: const Icon(Icons.photo_library),
                title: const Text('Gallery'),
                onTap: () {
                  Navigator.pop(context);
                  _pickImageFromGallery(type);
                },
              ),
              ListTile(
                leading: const Icon(Icons.camera_alt),
                title: const Text('Camera'),
                onTap: () {
                  Navigator.pop(context);
                  _pickImageFromCamera(type);
                },
              ),
            ],
          ),
        );
      },
    );
  }

  String _getFullImageUrl(String? imagePath) {
    if (imagePath == null || imagePath.isEmpty) {
      print('🖼️ _getFullImageUrl: Empty image path');
      return '';
    }

    print('🖼️ _getFullImageUrl: Input path = $imagePath');

    // If it's already a full URL (S3 URL), add cache busting
    if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
      // Add timestamp and refresh counter for cache busting
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final separator = imagePath.contains('?') ? '&' : '?';
      final finalUrl = '$imagePath${separator}t=$timestamp&r=$_refreshCounter';
      print('🖼️ _getFullImageUrl: S3 URL generated = $finalUrl');
      return finalUrl;
    }

    // Check if it's a document number (only digits) - don't try to load as image
    if (RegExp(r'^\d+$').hasMatch(imagePath)) {
      print('🖼️ _getFullImageUrl: Document number detected, returning empty');
      return '';
    }

    // Remove leading slash if present to avoid double slashes
    final cleanPath = imagePath.startsWith('/') ? imagePath.substring(1) : imagePath;

    // Construct full URL for local assets with cache busting
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    final finalUrl = '$_baseUrl/$cleanPath?t=$timestamp&r=$_refreshCounter';
    print('🖼️ _getFullImageUrl: Local URL generated = $finalUrl');
    return finalUrl;
  }

  Future<void> _openDocument(String documentPath, String documentType) async {
    if (documentPath.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No document available')),
      );
      return;
    }

    final fullUrl = _getFullImageUrl(documentPath);

    if (documentType.toLowerCase().contains('pdf')) {
      // Open PDF in external viewer
      final Uri url = Uri.parse(fullUrl);
      if (await canLaunchUrl(url)) {
        await launchUrl(url, mode: LaunchMode.externalApplication);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not open PDF')),
        );
      }
    } else {
      // Show image in full screen
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => DocumentViewerScreen(
            imageUrl: fullUrl,
            documentType: documentType,
          ),
        ),
      );
    }
  }

  Future<void> _selectDateOfBirth() async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: _selectedDateOfBirth ?? DateTime(1990),
      firstDate: DateTime(1950),
      lastDate: DateTime.now().subtract(const Duration(days: 6570)), // 18 years ago
    );

    if (picked != null && picked != _selectedDateOfBirth) {
      setState(() {
        _selectedDateOfBirth = picked;
      });
    }
  }

  Future<void> _saveProfile() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      final profileData = {
        'first_name': _firstNameController.text.trim(),
        'last_name': _lastNameController.text.trim(),
        'email': _emailController.text.trim(),
        'primary_number': _primaryNumberController.text.trim(),
        'secondary_number': _secondaryNumberController.text.trim(),
        'address': _addressController.text.trim(),
        'language': _languageController.text.trim(),
        'referral_code': _referralCodeController.text.trim(),
        'aadhar_card': _aadharCardController.text.trim(),
        'pan_card': _panCardController.text.trim(),
        'dl': _dlController.text.trim(),
        'vehicle_number': _vehicleNumberController.text.trim(),
        'bank_account_number': _bankAccountNumberController.text.trim(),
        'ifsc_code': _ifscCodeController.text.trim(),
        'name_as_per_bank': _nameAsPerBankController.text.trim(),
        'blood_group': _selectedBloodGroup,
        'dob': _selectedDateOfBirth?.toIso8601String().split('T')[0],
      };

      final result = await _apiService.updateDeliveryOnboarding(
        widget.authToken,
        profileData,
        profileImage: _profileImage,
        aadharCardImage: _aadharCardImage,
        panCardImage: _panCardImage,
        dlImage: _dlImage,
        rcCardImage: _rcCardImage,
        bankPassbookImage: _bankPassbookImage,
      );

      if (result['success']) {
        // Force refresh images by updating the profile data
        final updatedProfile = result['profile'];
        if (updatedProfile != null) {
          // Update local profile data with new URLs
          _updateLocalProfileData(updatedProfile);
        }
        
        // Call the parent callback to refresh profile data
        widget.onProfileUpdated(result['profile']);
        
        // Show success message
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Profile updated successfully!'),
            backgroundColor: Colors.green,
          ),
        );
        
        // Navigate back to refresh the parent screen
        Navigator.pop(context, true); // Return true to indicate refresh needed
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(result['message'] ?? 'Failed to update profile')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error updating profile: $e')),
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _updateLocalProfileData(Map<String, dynamic> updatedProfile) {
    // Update the current profile with new data to force UI refresh
    widget.currentProfile?.addAll(updatedProfile);
    
    // Force a rebuild to refresh images
    setState(() {
      // This will trigger a rebuild and refresh all images
    });
  }

  void _forceImageRefresh() {
    // Increment refresh counter to force image refresh
    _refreshCounter++;
    
    // Force a complete rebuild to refresh all images
    setState(() {
      // This will trigger a rebuild and refresh all images with new URLs
    });
  }

  Future<void> _fetchFreshProfileData() async {
    try {
      print('🔄 Fetching fresh profile data...');
      final result = await _apiService.getUserProfile(widget.authToken);
      
      if (result['success'] && result['profile'] != null) {
        print('✅ Fresh profile data received');
        print('🖼️ Profile images:');
        final profile = result['profile'];
        final imageFields = ['profile_picture', 'aadhar_card', 'pan_card', 'dl', 'rc_card', 'bank_passbook'];
        for (final field in imageFields) {
          final value = profile[field];
          print('  - $field: $value');
        }
        
        // COMPLETELY REPLACE the current profile with fresh data
        widget.currentProfile?.clear();
        widget.currentProfile?.addAll(profile);
        
        // Reinitialize controllers with fresh data
        _initializeControllers();
        
        // Increment refresh counter and force complete UI refresh
        _refreshCounter++;
        setState(() {
          // This will trigger a complete rebuild with fresh data
        });
        
        print('✅ Profile data completely refreshed and UI rebuilt (refresh counter: $_refreshCounter)');
      } else {
        print('❌ Failed to fetch fresh profile data: ${result['message']}');
      }
    } catch (e) {
      print('❌ Error fetching fresh profile data: $e');
    }
  }

  Future<void> _saveDocuments() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final result = await _apiService.uploadDocuments(
        authToken: widget.authToken,
        aadharCard: _aadharCardImage,
        panCard: _panCardImage,
        dl: _dlImage,
        rcCard: _rcCardImage,
        bankPassbook: _bankPassbookImage,
      );

      if (result['success']) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result['message'] ?? 'Documents uploaded successfully'),
            backgroundColor: Colors.green,
          ),
        );
        
        // Clear the selected files after successful upload
        setState(() {
          _aadharCardImage = null;
          _panCardImage = null;
          _dlImage = null;
          _rcCardImage = null;
          _bankPassbookImage = null;
        });
        
        // Force refresh to show updated images
        _forceImageRefresh();
        
        // Fetch fresh profile data to get updated S3 URLs
        await _fetchFreshProfileData();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result['message'] ?? 'Failed to upload documents'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error uploading documents: $e'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    // Create a unique key based on profile data to force complete rebuild
    final profileKey = widget.currentProfile?['profile_picture'] ?? 'no_image';
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    
    return Scaffold(
      key: ValueKey('edit_profile_${profileKey}_$timestamp'),
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: const Text(
          'Edit Profile',
          style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.black),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          TextButton(
            onPressed: _isLoading ? null : _saveProfile,
            child: _isLoading
                ? const SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
                : const Text(
              'Save',
              style: TextStyle(
                color: Colors.orange,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          labelColor: Colors.orange,
          unselectedLabelColor: Colors.grey,
          indicatorColor: Colors.orange,
          tabs: const [
            Tab(text: 'Profile', icon: Icon(Icons.person)),
            Tab(text: 'Documents', icon: Icon(Icons.description)),
          ],
        ),
      ),
      body: Form(
        key: _formKey,
        child: TabBarView(
          controller: _tabController,
          children: [
            _buildProfileTab(),
            _buildDocumentsTab(),
          ],
        ),
      ),
    );
  }

  Widget _buildProfileTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Profile Picture Section
          _buildProfilePictureSection(),

          const SizedBox(height: 24),

          // Personal Information Section
          _buildSectionTitle('Personal Information'),
          const SizedBox(height: 16),

          Row(
            children: [
              Expanded(
                child: _buildTextField(
                  controller: _firstNameController,
                  label: 'First Name',
                  icon: Icons.person_outline,
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter your first name';
                    }
                    return null;
                  },
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: _buildTextField(
                  controller: _lastNameController,
                  label: 'Last Name',
                  icon: Icons.person_outline,
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter your last name';
                    }
                    return null;
                  },
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),

          _buildTextField(
            controller: _emailController,
            label: 'Email',
            icon: Icons.email_outlined,
            keyboardType: TextInputType.emailAddress,
            validator: (value) {
              if (value == null || value.trim().isEmpty) {
                return 'Please enter your email';
              }
              if (!value.contains('@')) {
                return 'Please enter a valid email';
              }
              return null;
            },
          ),

          const SizedBox(height: 16),

          Row(
            children: [
              Expanded(
                child: _buildTextField(
                  controller: _primaryNumberController,
                  label: 'Primary Number',
                  icon: Icons.phone_outlined,
                  keyboardType: TextInputType.phone,
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter your primary number';
                    }
                    if (value.length < 10) {
                      return 'Please enter a valid phone number';
                    }
                    return null;
                  },
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: _buildTextField(
                  controller: _secondaryNumberController,
                  label: 'Secondary Number',
                  icon: Icons.phone_outlined,
                  keyboardType: TextInputType.phone,
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),

          // Blood Group Dropdown
          _buildBloodGroupDropdown(),

          const SizedBox(height: 16),

          // Date of Birth
          _buildDateOfBirthField(),

          const SizedBox(height: 24),

          // Address Information Section
          _buildSectionTitle('Address Information'),
          const SizedBox(height: 16),

          _buildTextField(
            controller: _addressController,
            label: 'Address',
            icon: Icons.location_on_outlined,
            maxLines: 2,
            validator: (value) {
              if (value == null || value.trim().isEmpty) {
                return 'Please enter your address';
              }
              return null;
            },
          ),

          const SizedBox(height: 16),

          _buildTextField(
            controller: _languageController,
            label: 'Language',
            icon: Icons.language_outlined,
            validator: (value) {
              if (value == null || value.trim().isEmpty) {
                return 'Please enter your preferred language';
              }
              return null;
            },
          ),

          const SizedBox(height: 16),

          _buildTextField(
            controller: _referralCodeController,
            label: 'Referral Code',
            icon: Icons.card_giftcard_outlined,
          ),

          const SizedBox(height: 24),

          // Identity Documents Section
          _buildSectionTitle('Identity Documents'),
          const SizedBox(height: 16),

          _buildTextField(
            controller: _aadharCardController,
            label: 'Aadhar Card Number',
            icon: Icons.credit_card_outlined,
            validator: (value) {
              if (value == null || value.trim().isEmpty) {
                return 'Please enter your Aadhar card number';
              }
              if (value.length != 12) {
                return 'Aadhar card number must be 12 digits';
              }
              return null;
            },
          ),

          const SizedBox(height: 16),

          _buildTextField(
            controller: _panCardController,
            label: 'PAN Card Number',
            icon: Icons.credit_card_outlined,
            validator: (value) {
              if (value == null || value.trim().isEmpty) {
                return 'Please enter your PAN card number';
              }
              if (value.length != 10) {
                return 'PAN card number must be 10 characters';
              }
              return null;
            },
          ),

          const SizedBox(height: 16),

          _buildTextField(
            controller: _dlController,
            label: 'Driving License Number',
            icon: Icons.drive_eta_outlined,
            validator: (value) {
              if (value == null || value.trim().isEmpty) {
                return 'Please enter your driving license number';
              }
              return null;
            },
          ),

          const SizedBox(height: 24),

          // Vehicle Information Section
          _buildSectionTitle('Vehicle Information'),
          const SizedBox(height: 16),

          _buildTextField(
            controller: _vehicleNumberController,
            label: 'Vehicle Number',
            icon: Icons.directions_car_outlined,
            validator: (value) {
              if (value == null || value.trim().isEmpty) {
                return 'Please enter your vehicle number';
              }
              return null;
            },
          ),

          const SizedBox(height: 24),

          // Bank Information Section
          _buildSectionTitle('Bank Information'),
          const SizedBox(height: 16),

          _buildTextField(
            controller: _bankAccountNumberController,
            label: 'Bank Account Number',
            icon: Icons.account_balance_outlined,
            keyboardType: TextInputType.number,
            validator: (value) {
              if (value == null || value.trim().isEmpty) {
                return 'Please enter your bank account number';
              }
              return null;
            },
          ),

          const SizedBox(height: 16),

          _buildTextField(
            controller: _ifscCodeController,
            label: 'IFSC Code',
            icon: Icons.code_outlined,
            validator: (value) {
              if (value == null || value.trim().isEmpty) {
                return 'Please enter your IFSC code';
              }
              return null;
            },
          ),

          const SizedBox(height: 16),

          _buildTextField(
            controller: _nameAsPerBankController,
            label: 'Name as per Bank',
            icon: Icons.person_outline,
            validator: (value) {
              if (value == null || value.trim().isEmpty) {
                return 'Please enter your name as per bank records';
              }
              return null;
            },
          ),

          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildDocumentsTab() {
    // Debug: Log current profile data for documents
    print('📄 Building Documents Tab - Current Profile Data:');
    print('  - Profile Picture: ${widget.currentProfile?['profile_picture']}');
    print('  - Aadhar Card: ${widget.currentProfile?['aadhar_card']}');
    print('  - PAN Card: ${widget.currentProfile?['pan_card']}');
    print('  - DL: ${widget.currentProfile?['dl']}');
    print('  - RC Card: ${widget.currentProfile?['rc_card']}');
    print('  - Bank Passbook: ${widget.currentProfile?['bank_passbook']}');
    
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildSectionTitle('Document Management'),
              IconButton(
                onPressed: () {
                  print('🔄 Manual refresh triggered from documents tab');
                  _fetchFreshProfileData();
                },
                icon: const Icon(Icons.refresh, color: Colors.orange),
                tooltip: 'Refresh Documents',
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Profile Picture Document
          _buildDocumentCard(
            title: 'Profile Picture',
            documentPath: widget.currentProfile?['profile_picture'],
            documentType: 'image',
            onTap: () => _showImageSourceDialog('profile'),
            onView: () => _openDocument(
              widget.currentProfile?['profile_picture'] ?? '',
              'image',
            ),
            currentFile: _profileImage,
          ),

          const SizedBox(height: 16),

          // Aadhar Card Document
          _buildDocumentCard(
            title: 'Aadhar Card (Photo)',
            documentPath: widget.currentProfile?['aadhar_card'],
            documentType: 'image',
            onTap: () => _showImageSourceDialog('aadhar_card'),
            onView: () => _openDocument(
              widget.currentProfile?['aadhar_card'] ?? '',
              'image',
            ),
            currentFile: _aadharCardImage,
          ),

          const SizedBox(height: 16),

          // PAN Card Document
          _buildDocumentCard(
            title: 'PAN Card (Photo)',
            documentPath: widget.currentProfile?['pan_card'],
            documentType: 'image',
            onTap: () => _showImageSourceDialog('pan_card'),
            onView: () => _openDocument(
              widget.currentProfile?['pan_card'] ?? '',
              'image',
            ),
            currentFile: _panCardImage,
          ),

          const SizedBox(height: 16),

          // Driving License Document
          _buildDocumentCard(
            title: 'Driving License (Photo)',
            documentPath: widget.currentProfile?['dl'],
            documentType: 'image',
            onTap: () => _showImageSourceDialog('dl'),
            onView: () => _openDocument(
              widget.currentProfile?['dl'] ?? '',
              'image',
            ),
            currentFile: _dlImage,
          ),

          const SizedBox(height: 16),

          // RC Card Document
          _buildDocumentCard(
            title: 'RC Card',
            documentPath: widget.currentProfile?['rc_card'],
            documentType: 'image',
            onTap: () => _showImageSourceDialog('rc_card'),
            onView: () => _openDocument(
              widget.currentProfile?['rc_card'] ?? '',
              'image',
            ),
            currentFile: _rcCardImage,
          ),

          const SizedBox(height: 16),

          // Bank Passbook Document
          _buildDocumentCard(
            title: 'Bank Passbook',
            documentPath: widget.currentProfile?['bank_passbook'],
            documentType: 'image',
            onTap: () => _showImageSourceDialog('bank_passbook'),
            onView: () => _openDocument(
              widget.currentProfile?['bank_passbook'] ?? '',
              'image',
            ),
            currentFile: _bankPassbookImage,
          ),

          const SizedBox(height: 24),

          // Save Documents Button
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: _isLoading ? null : _saveDocuments,
              icon: _isLoading 
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.upload),
              label: Text(_isLoading ? 'Uploading...' : 'Upload Documents'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.orange,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
            ),
          ),

          const SizedBox(height: 24),

          // Document Status Section
          _buildSectionTitle('Document Status'),
          const SizedBox(height: 16),

          _buildStatusCard(
            'Profile Submitted',
            widget.currentProfile?['profile_submitted'] ?? false,
          ),

          const SizedBox(height: 8),

          _buildStatusCard(
            'Documents Submitted',
            widget.currentProfile?['documents_submitted'] ?? false,
          ),

          const SizedBox(height: 8),

          _buildStatusCard(
            'Vehicle Docs Submitted',
            widget.currentProfile?['vehicle_docs_submitted'] ?? false,
          ),

          const SizedBox(height: 8),

          _buildStatusCard(
            'Bank Docs Submitted',
            widget.currentProfile?['bank_docs_submitted'] ?? false,
          ),

          const SizedBox(height: 24),

          // Verification Status Section
          _buildSectionTitle('Verification Status'),
          const SizedBox(height: 16),

          _buildStatusCard(
            'Profile Verified',
            widget.currentProfile?['profile_verified'] ?? false,
            isVerified: true,
          ),

          const SizedBox(height: 8),

          _buildStatusCard(
            'Documents Verified',
            widget.currentProfile?['documents_verified'] ?? false,
            isVerified: true,
          ),

          const SizedBox(height: 8),

          _buildStatusCard(
            'Vehicle Verified',
            widget.currentProfile?['vehicle_verified'] ?? false,
            isVerified: true,
          ),

          const SizedBox(height: 8),

          _buildStatusCard(
            'Bank Verified',
            widget.currentProfile?['bank_verified'] ?? false,
            isVerified: true,
          ),
        ],
      ),
    );
  }

  Widget _buildProfilePictureSection() {
    return Center(
      child: Column(
        children: [
          Stack(
            children: [
              CircleAvatar(
                key: ValueKey('profile_${widget.currentProfile?['profile_picture']}_${DateTime.now().millisecondsSinceEpoch}'),
                radius: 50,
                backgroundColor: Colors.grey.shade300,
                backgroundImage: _profileImage != null
                    ? FileImage(_profileImage!)
                    : widget.currentProfile?['profile_picture'] != null
                    ? NetworkImage(_getFullImageUrl(widget.currentProfile!['profile_picture'])) as ImageProvider
                    : const AssetImage("assets/images/default_profile.png") as ImageProvider,
              ),
              Positioned(
                bottom: 0,
                right: 0,
                child: GestureDetector(
                  onTap: () => _showImageSourceDialog('profile'),
                  child: Container(
                    decoration: const BoxDecoration(
                      shape: BoxShape.circle,
                      color: Colors.orange,
                    ),
                    padding: const EdgeInsets.all(8),
                    child: const Icon(Icons.camera_alt, color: Colors.white, size: 20),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          TextButton(
            onPressed: () => _showImageSourceDialog('profile'),
            child: const Text(
              'Change Profile Picture',
              style: TextStyle(color: Colors.orange),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: const TextStyle(
        fontSize: 18,
        fontWeight: FontWeight.bold,
        color: Colors.black87,
      ),
    );
  }

  Widget _buildTextField({
    required TextEditingController controller,
    required String label,
    required IconData icon,
    TextInputType? keyboardType,
    int maxLines = 1,
    String? Function(String?)? validator,
  }) {
    return TextFormField(
      controller: controller,
      keyboardType: keyboardType,
      maxLines: maxLines,
      validator: validator,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, color: Colors.orange.shade700),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Colors.grey.shade300),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Colors.grey.shade300),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Colors.orange.shade700, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Colors.red),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Colors.red, width: 2),
        ),
        filled: true,
        fillColor: Colors.grey.shade50,
      ),
    );
  }

  Widget _buildBloodGroupDropdown() {
    return DropdownButtonFormField<String>(
      value: _selectedBloodGroup,
      decoration: InputDecoration(
        labelText: 'Blood Group',
        prefixIcon: Icon(Icons.bloodtype_outlined, color: Colors.orange.shade700),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Colors.grey.shade300),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Colors.grey.shade300),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Colors.orange.shade700, width: 2),
        ),
        filled: true,
        fillColor: Colors.grey.shade50,
      ),
      items: const [
        DropdownMenuItem(value: 'A+', child: Text('A+')),
        DropdownMenuItem(value: 'A-', child: Text('A-')),
        DropdownMenuItem(value: 'B+', child: Text('B+')),
        DropdownMenuItem(value: 'B-', child: Text('B-')),
        DropdownMenuItem(value: 'AB+', child: Text('AB+')),
        DropdownMenuItem(value: 'AB-', child: Text('AB-')),
        DropdownMenuItem(value: 'O+', child: Text('O+')),
        DropdownMenuItem(value: 'O-', child: Text('O-')),
      ],
      onChanged: (value) {
        setState(() {
          _selectedBloodGroup = value;
        });
      },
      validator: (value) {
        if (value == null || value.isEmpty) {
          return 'Please select your blood group';
        }
        return null;
      },
    );
  }

  Widget _buildDateOfBirthField() {
    return InkWell(
      onTap: _selectDateOfBirth,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        decoration: BoxDecoration(
          border: Border.all(color: Colors.grey.shade300),
          borderRadius: BorderRadius.circular(12),
          color: Colors.grey.shade50,
        ),
        child: Row(
          children: [
            Icon(Icons.calendar_today_outlined, color: Colors.orange.shade700),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Date of Birth',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey.shade600,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    _selectedDateOfBirth != null
                        ? '${_selectedDateOfBirth!.day}/${_selectedDateOfBirth!.month}/${_selectedDateOfBirth!.year}'
                        : 'Select date of birth',
                    style: TextStyle(
                      fontSize: 16,
                      color: _selectedDateOfBirth != null ? Colors.black : Colors.grey.shade600,
                    ),
                  ),
                ],
              ),
            ),
            Icon(Icons.arrow_drop_down, color: Colors.grey.shade600),
          ],
        ),
      ),
    );
  }

  Widget _buildDocumentCard({
    required String title,
    required String? documentPath,
    required String documentType,
    required VoidCallback onTap,
    required VoidCallback onView,
    File? currentFile,
  }) {
    final hasDocument = documentPath != null && documentPath.isNotEmpty;
    final hasCurrentFile = currentFile != null;
    
    // Check if documentPath is a valid image URL (not a document number)
    final isValidImageUrl = hasDocument && 
        (documentPath!.startsWith('http') || 
         (!RegExp(r'^\d+$').hasMatch(documentPath) && documentPath.isNotEmpty));

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  documentType == 'image' ? Icons.image : Icons.picture_as_pdf,
                  color: Colors.orange,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    title,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                if (isValidImageUrl || hasCurrentFile)
                  IconButton(
                    onPressed: onView,
                    icon: const Icon(Icons.visibility),
                    color: Colors.blue,
                  ),
              ],
            ),
            const SizedBox(height: 8),
            if (isValidImageUrl || hasCurrentFile)
              Container(
                height: 100,
                width: double.infinity,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.grey.shade300),
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: hasCurrentFile
                      ? Image.file(
                    currentFile!,
                    fit: BoxFit.cover,
                  )
                      : Image.network(
                    _getFullImageUrl(documentPath),
                    key: ValueKey('${documentPath}_${DateTime.now().millisecondsSinceEpoch}'),
                    fit: BoxFit.cover,
                    errorBuilder: (context, error, stackTrace) {
                      return const Center(
                        child: Icon(Icons.error, color: Colors.red),
                      );
                    },
                  ),
                ),
              )
            else
              Container(
                height: 100,
                width: double.infinity,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.grey.shade300),
                  color: Colors.grey.shade100,
                ),
                child: const Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.add_photo_alternate, color: Colors.grey, size: 32),
                      SizedBox(height: 4),
                      Text('No document uploaded', style: TextStyle(color: Colors.grey)),
                    ],
                  ),
                ),
              ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: onTap,
                icon: const Icon(Icons.upload),
                label: Text(hasDocument || hasCurrentFile ? 'Update Document' : 'Upload Document'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.orange,
                  foregroundColor: Colors.white,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusCard(String title, bool isCompleted, {bool isVerified = false}) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Icon(
              isCompleted ? Icons.check_circle : Icons.pending,
              color: isCompleted ? Colors.green : Colors.orange,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                title,
                style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
              ),
            ),
            if (isVerified)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: isCompleted ? Colors.green.withOpacity(0.1) : Colors.orange.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  isCompleted ? 'Verified' : 'Pending',
                  style: TextStyle(
                    color: isCompleted ? Colors.green : Colors.orange,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

// Document Viewer Screen
class DocumentViewerScreen extends StatelessWidget {
  final String imageUrl;
  final String documentType;

  const DocumentViewerScreen({
    Key? key,
    required this.imageUrl,
    required this.documentType,
  }) : super(key: key);

  String _getFullImageUrl(String? imagePath) {
    if (imagePath == null || imagePath.isEmpty) {
      return '';
    }

    // If it's already a full URL (S3 URL), add cache busting
    if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
      // Add timestamp for cache busting
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final separator = imagePath.contains('?') ? '&' : '?';
      return '$imagePath${separator}t=$timestamp';
    }

    // Remove leading slash if present to avoid double slashes
    final cleanPath = imagePath.startsWith('/') ? imagePath.substring(1) : imagePath;

    // Construct full URL for local assets with cache busting
    const baseUrl = 'http://127.0.0.1:5000';
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    return '$baseUrl/$cleanPath?t=$timestamp';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(documentType.toUpperCase()),
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
      ),
      backgroundColor: Colors.black,
      body: Center(
        child: InteractiveViewer(
          child: Image.network(
            _getFullImageUrl(imageUrl),
            key: ValueKey('${imageUrl}_${DateTime.now().millisecondsSinceEpoch}'),
            fit: BoxFit.contain,
            errorBuilder: (context, error, stackTrace) {
              return const Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.error, color: Colors.red, size: 64),
                    SizedBox(height: 16),
                    Text(
                      'Failed to load image',
                      style: TextStyle(color: Colors.white, fontSize: 18),
                    ),
                  ],
                ),
              );
            },
          ),
        ),
      ),
    );
  }
}
