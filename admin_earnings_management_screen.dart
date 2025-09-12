import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'api_service_earnings.dart';

class AdminEarningsManagementScreen extends StatefulWidget {
  final String authToken;

  const AdminEarningsManagementScreen({
    Key? key,
    required this.authToken,
  }) : super(key: key);

  @override
  State<AdminEarningsManagementScreen> createState() => _AdminEarningsManagementScreenState();
}

class _AdminEarningsManagementScreenState extends State<AdminEarningsManagementScreen> with TickerProviderStateMixin {
  final ApiServiceEarnings _apiService = ApiServiceEarnings();
  late TabController _tabController;
  
  // Data
  List<Map<String, dynamic>> _earnings = [];
  List<Map<String, dynamic>> _deliveryGuys = [];
  Map<String, dynamic> _summary = {};
  List<Map<String, dynamic>> _weeklyBreakdown = [];
  List<Map<String, dynamic>> _dailyBreakdown = [];
  
  bool _isLoading = false;
  String? _errorMessage;
  String _selectedPeriod = 'monthly';
  String _selectedType = 'all';
  String _selectedStatus = 'all';

  final List<String> _periods = ['daily', 'weekly', 'monthly'];
  final List<Map<String, dynamic>> _paymentTypes = [
    {'value': 'all', 'label': 'All', 'icon': Icons.all_inclusive},
    {'value': 'salary', 'label': 'Salary', 'icon': Icons.attach_money},
    {'value': 'bonus', 'label': 'Bonus', 'icon': Icons.trending_up},
    {'value': 'payout', 'label': 'Payout', 'icon': Icons.account_balance_wallet},
  ];

  final List<Map<String, dynamic>> _statuses = [
    {'value': 'all', 'label': 'All', 'color': Colors.grey},
    {'value': 'pending', 'label': 'Pending', 'color': Colors.orange},
    {'value': 'approved', 'label': 'Approved', 'color': Colors.green},
    {'value': 'paid', 'label': 'Paid', 'color': Colors.blue},
    {'value': 'rejected', 'label': 'Rejected', 'color': Colors.red},
  ];

  // Form state for creating new earning
  final _formKey = GlobalKey<FormState>();
  final Map<String, dynamic> _formData = {
    'delivery_guy_id': null,
    'payment_type': 'salary',
    'amount': '',
    'payment_period': 'monthly',
    'start_date': '',
    'end_date': '',
    'description': '',
    'admin_notes': '',
  };

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadEarnings();
    _loadDeliveryGuys();
    _loadSummary();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadEarnings() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final response = await _apiService.getAllEarnings(
        widget.authToken,
        type: _selectedType == 'all' ? null : _selectedType,
        status: _selectedStatus == 'all' ? null : _selectedStatus,
      );
      
      if (response['success']) {
        setState(() {
          _earnings = response['earnings'] ?? [];
        });
      } else {
        setState(() {
          _errorMessage = response['error'] ?? 'Failed to load earnings';
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Error loading earnings: $e';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _loadDeliveryGuys() async {
    try {
      final response = await _apiService.getDeliveryGuys(widget.authToken);
      
      if (response['success']) {
        setState(() {
          _deliveryGuys = response['delivery_guys'] ?? [];
        });
      }
    } catch (e) {
      print('Error loading delivery guys: $e');
    }
  }

  Future<void> _loadSummary() async {
    try {
      final response = await _apiService.getAdminEarningsSummary(
        widget.authToken,
        period: _selectedPeriod,
      );
      
      if (response['success']) {
        setState(() {
          _summary = response['summary'] ?? {};
          _weeklyBreakdown = response['weekly_breakdown'] ?? [];
          _dailyBreakdown = response['daily_breakdown'] ?? [];
        });
      }
    } catch (e) {
      print('Error loading summary: $e');
    }
  }

  Future<void> _createEarning() async {
    if (!_formKey.currentState!.validate()) return;

    try {
      final response = await _apiService.createEarning(
        widget.authToken,
        _formData['delivery_guy_id'],
        _formData['payment_type'],
        double.parse(_formData['amount']),
        _formData['payment_period'],
        _formData['start_date'],
        _formData['end_date'],
        _formData['description'],
        _formData['admin_notes'],
      );
      
      if (response['success']) {
        _showSuccessSnackBar('Earning created successfully!');
        _loadEarnings();
        _loadSummary();
        _resetForm();
        Navigator.pop(context);
      } else {
        _showErrorSnackBar(response['error'] ?? 'Failed to create earning');
      }
    } catch (e) {
      _showErrorSnackBar('Error creating earning: $e');
    }
  }

  Future<void> _approveEarning(int earningId) async {
    try {
      final response = await _apiService.approveEarning(widget.authToken, earningId);
      
      if (response['success']) {
        _showSuccessSnackBar('Earning approved successfully!');
        _loadEarnings();
        _loadSummary();
      } else {
        _showErrorSnackBar(response['error'] ?? 'Failed to approve earning');
      }
    } catch (e) {
      _showErrorSnackBar('Error approving earning: $e');
    }
  }

  Future<void> _rejectEarning(int earningId, String notes) async {
    try {
      final response = await _apiService.rejectEarning(widget.authToken, earningId, notes);
      
      if (response['success']) {
        _showSuccessSnackBar('Earning rejected successfully!');
        _loadEarnings();
        _loadSummary();
      } else {
        _showErrorSnackBar(response['error'] ?? 'Failed to reject earning');
      }
    } catch (e) {
      _showErrorSnackBar('Error rejecting earning: $e');
    }
  }

  Future<void> _markEarningPaid(int earningId) async {
    try {
      final response = await _apiService.markEarningPaid(widget.authToken, earningId);
      
      if (response['success']) {
        _showSuccessSnackBar('Earning marked as paid successfully!');
        _loadEarnings();
        _loadSummary();
      } else {
        _showErrorSnackBar(response['error'] ?? 'Failed to mark earning as paid');
      }
    } catch (e) {
      _showErrorSnackBar('Error marking earning as paid: $e');
    }
  }

  void _resetForm() {
    _formData.updateAll((key, value) => 
      key == 'payment_type' ? 'salary' : 
      key == 'payment_period' ? 'monthly' : '');
  }

  void _showErrorSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
      ),
    );
  }

  void _showSuccessSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.green,
      ),
    );
  }

  String _formatCurrency(double amount) {
    return NumberFormat.currency(symbol: '₹', decimalDigits: 2).format(amount);
  }

  String _formatDate(String dateString) {
    try {
      final date = DateTime.parse(dateString);
      return DateFormat('MMM dd, yyyy').format(date);
    } catch (e) {
      return dateString;
    }
  }

  String _formatDateTime(String dateTimeString) {
    try {
      final dateTime = DateTime.parse(dateTimeString);
      return DateFormat('MMM dd, yyyy HH:mm').format(dateTime);
    } catch (e) {
      return dateTimeString;
    }
  }

  Color _getStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'approved':
        return Colors.green;
      case 'pending':
        return Colors.orange;
      case 'paid':
        return Colors.blue;
      case 'rejected':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  Color _getPaymentTypeColor(String paymentType) {
    switch (paymentType.toLowerCase()) {
      case 'salary':
        return Colors.blue;
      case 'bonus':
        return Colors.green;
      case 'payout':
        return Colors.purple;
      default:
        return Colors.grey;
    }
  }

  IconData _getPaymentTypeIcon(String type) {
    switch (type.toLowerCase()) {
      case 'salary':
        return Icons.attach_money;
      case 'bonus':
        return Icons.trending_up;
      case 'payout':
        return Icons.account_balance_wallet;
      default:
        return Icons.money;
    }
  }

  Widget _buildSummaryCard(String type, Map<String, dynamic> data) {
    final typeInfo = _paymentTypes.firstWhere(
      (t) => t['value'] == type,
      orElse: () => {'label': type.toUpperCase(), 'icon': Icons.money},
    );

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(typeInfo['icon'], color: Colors.blue),
                const SizedBox(width: 8),
                Text(
                  'Total ${typeInfo['label']}',
                  style: const TextStyle(
                    fontSize: 14,
                    color: Colors.grey,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              _formatCurrency(data['total_amount']?.toDouble() ?? 0.0),
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
            Text(
              '${data['count'] ?? 0} entries',
              style: const TextStyle(
                fontSize: 12,
                color: Colors.grey,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildWeeklyBreakdown() {
    if (_weeklyBreakdown.isEmpty) {
      return const SizedBox.shrink();
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Weekly Breakdown',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            ...(_weeklyBreakdown.take(5).map((item) => Padding(
              padding: const EdgeInsets.only(bottom: 8.0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(
                      _formatDate(item['week_start']),
                      style: const TextStyle(fontSize: 14),
                    ),
                  ),
                  Chip(
                    label: Text(item['payment_type'].toString().toUpperCase()),
                    backgroundColor: Colors.blue.withOpacity(0.1),
                    labelStyle: const TextStyle(fontSize: 12),
                  ),
                  Text(
                    _formatCurrency(item['total_amount']?.toDouble() ?? 0.0),
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            )).toList()),
          ],
        ),
      ),
    );
  }

  Widget _buildDailyBreakdown() {
    if (_dailyBreakdown.isEmpty) {
      return const SizedBox.shrink();
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Daily Breakdown',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            ...(_dailyBreakdown.take(10).map((item) => Padding(
              padding: const EdgeInsets.only(bottom: 8.0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(
                      _formatDate(item['date'] ?? item['start_date']),
                      style: const TextStyle(fontSize: 14),
                    ),
                  ),
                  Chip(
                    label: Text(item['payment_type'].toString().toUpperCase()),
                    backgroundColor: _getPaymentTypeColor(item['payment_type']).withOpacity(0.1),
                    labelStyle: const TextStyle(fontSize: 12),
                  ),
                  Text(
                    _formatCurrency(item['total_amount']?.toDouble() ?? 0.0),
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            )).toList()),
          ],
        ),
      ),
    );
  }

  Widget _buildEarningsList() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_errorMessage != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error, size: 64, color: Colors.red[300]),
            const SizedBox(height: 16),
            Text(
              _errorMessage!,
              style: const TextStyle(fontSize: 16),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadEarnings,
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (_earnings.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.money_off, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text(
              'No earnings found',
              style: TextStyle(fontSize: 16, color: Colors.grey),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      itemCount: _earnings.length,
      itemBuilder: (context, index) {
        final earning = _earnings[index];
        return Card(
          margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
          child: ListTile(
            leading: CircleAvatar(
              backgroundColor: _getStatusColor(earning['status']).withOpacity(0.1),
              child: Icon(
                _getPaymentTypeIcon(earning['payment_type']),
                color: _getStatusColor(earning['status']),
              ),
            ),
            title: Text(
              earning['delivery_guy_name'] ?? 'Unknown',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('${earning['payment_type'].toString().toUpperCase()} - ${_formatDate(earning['start_date'])} - ${_formatDate(earning['end_date'])}'),
                Text('Status: ${earning['status'].toString().toUpperCase()}'),
                if (earning['description'] != null && earning['description'].isNotEmpty)
                  Text('Description: ${earning['description']}'),
              ],
            ),
            trailing: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  _formatCurrency(earning['amount']?.toDouble() ?? 0.0),
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                    color: Colors.green,
                  ),
                ),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (earning['status'] == 'pending') ...[
                      IconButton(
                        icon: const Icon(Icons.check, color: Colors.green),
                        onPressed: () => _approveEarning(earning['id']),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close, color: Colors.red),
                        onPressed: () => _showRejectDialog(earning),
                      ),
                    ],
                    if (earning['status'] == 'approved')
                      IconButton(
                        icon: const Icon(Icons.payment, color: Colors.blue),
                        onPressed: () => _markEarningPaid(earning['id']),
                      ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _showRejectDialog(Map<String, dynamic> earning) {
    final TextEditingController notesController = TextEditingController();
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Reject Earning'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Are you sure you want to reject this earning for ${earning['delivery_guy_name']}?'),
            const SizedBox(height: 16),
            TextField(
              controller: notesController,
              decoration: const InputDecoration(
                labelText: 'Rejection Reason',
                border: OutlineInputBorder(),
              ),
              maxLines: 3,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              if (notesController.text.trim().isNotEmpty) {
                _rejectEarning(earning['id'], notesController.text.trim());
                Navigator.pop(context);
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Reject'),
          ),
        ],
      ),
    );
  }

  void _showCreateDialog() {
    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: const Text('Create New Earning'),
          content: Form(
            key: _formKey,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  DropdownButtonFormField<int>(
                    value: _formData['delivery_guy_id'],
                    decoration: const InputDecoration(labelText: 'Delivery Person'),
                    items: _deliveryGuys.map((dg) => DropdownMenuItem(
                      value: dg['id'],
                      child: Text('${dg['name']} (${dg['email']})'),
                    )).toList(),
                    onChanged: (value) => setState(() => _formData['delivery_guy_id'] = value),
                    validator: (value) => value == null ? 'Please select a delivery person' : null,
                  ),
                  const SizedBox(height: 16),
                  DropdownButtonFormField<String>(
                    value: _formData['payment_type'],
                    decoration: const InputDecoration(labelText: 'Payment Type'),
                    items: _paymentTypes.where((t) => t['value'] != 'all').map((type) => DropdownMenuItem(
                      value: type['value'],
                      child: Row(
                        children: [
                          Icon(type['icon']),
                          const SizedBox(width: 8),
                          Text(type['label']),
                        ],
                      ),
                    )).toList(),
                    onChanged: (value) => setState(() => _formData['payment_type'] = value),
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    decoration: const InputDecoration(labelText: 'Amount'),
                    keyboardType: TextInputType.number,
                    onChanged: (value) => _formData['amount'] = value,
                    validator: (value) => value?.isEmpty == true ? 'Please enter amount' : null,
                  ),
                  const SizedBox(height: 16),
                  DropdownButtonFormField<String>(
                    value: _formData['payment_period'],
                    decoration: const InputDecoration(labelText: 'Payment Period'),
                    items: _periods.map((period) => DropdownMenuItem(
                      value: period,
                      child: Text(period.toUpperCase()),
                    )).toList(),
                    onChanged: (value) => setState(() => _formData['payment_period'] = value),
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    decoration: const InputDecoration(labelText: 'Start Date'),
                    readOnly: true,
                    onTap: () async {
                      final date = await showDatePicker(
                        context: context,
                        initialDate: DateTime.now(),
                        firstDate: DateTime(2020),
                        lastDate: DateTime(2030),
                      );
                      if (date != null) {
                        setState(() {
                          _formData['start_date'] = DateFormat('yyyy-MM-dd').format(date);
                        });
                      }
                    },
                    controller: TextEditingController(
                      text: _formData['start_date'].isEmpty ? '' : _formatDate(_formData['start_date']),
                    ),
                    validator: (value) => _formData['start_date'].isEmpty ? 'Please select start date' : null,
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    decoration: const InputDecoration(labelText: 'End Date'),
                    readOnly: true,
                    onTap: () async {
                      final date = await showDatePicker(
                        context: context,
                        initialDate: DateTime.now(),
                        firstDate: DateTime(2020),
                        lastDate: DateTime(2030),
                      );
                      if (date != null) {
                        setState(() {
                          _formData['end_date'] = DateFormat('yyyy-MM-dd').format(date);
                        });
                      }
                    },
                    controller: TextEditingController(
                      text: _formData['end_date'].isEmpty ? '' : _formatDate(_formData['end_date']),
                    ),
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    decoration: const InputDecoration(labelText: 'Description'),
                    maxLines: 3,
                    onChanged: (value) => _formData['description'] = value,
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    decoration: const InputDecoration(labelText: 'Admin Notes'),
                    maxLines: 2,
                    onChanged: (value) => _formData['admin_notes'] = value,
                  ),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: _createEarning,
              child: const Text('Create'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Earnings Management'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Summary', icon: Icon(Icons.dashboard)),
            Tab(text: 'Earnings', icon: Icon(Icons.money)),
            Tab(text: 'Breakdown', icon: Icon(Icons.analytics)),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          // Summary Tab
          SingleChildScrollView(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Period Filter
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Period Filter',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 16),
                        Wrap(
                          spacing: 8,
                          children: _periods.map((period) => FilterChip(
                            label: Text(period.toUpperCase()),
                            selected: _selectedPeriod == period,
                            onSelected: (selected) {
                              if (selected) {
                                setState(() {
                                  _selectedPeriod = period;
                                });
                                _loadSummary();
                              }
                            },
                          )).toList(),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                // Summary Cards
                GridView.count(
                  crossAxisCount: 2,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  childAspectRatio: 1.5,
                  children: _summary.entries.map((entry) => 
                    _buildSummaryCard(entry.key, entry.value)
                  ).toList(),
                ),
                const SizedBox(height: 16),
                // Weekly Breakdown
                _buildWeeklyBreakdown(),
              ],
            ),
          ),
          // Earnings Tab
          Column(
            children: [
              // Filters
              Container(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    // Type Filter
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        children: _paymentTypes.map((type) => Padding(
                          padding: const EdgeInsets.only(right: 8.0),
                          child: FilterChip(
                            label: Text(type['label']),
                            selected: _selectedType == type['value'],
                            onSelected: (selected) {
                              if (selected) {
                                setState(() {
                                  _selectedType = type['value'];
                                });
                                _loadEarnings();
                              }
                            },
                            avatar: Icon(type['icon']),
                          ),
                        )).toList(),
                      ),
                    ),
                    const SizedBox(height: 8),
                    // Status Filter
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        children: _statuses.map((status) => Padding(
                          padding: const EdgeInsets.only(right: 8.0),
                          child: FilterChip(
                            label: Text(status['label']),
                            selected: _selectedStatus == status['value'],
                            onSelected: (selected) {
                              if (selected) {
                                setState(() {
                                  _selectedStatus = status['value'];
                                });
                                _loadEarnings();
                              }
                            },
                            backgroundColor: status['color'].withOpacity(0.1),
                            selectedColor: status['color'].withOpacity(0.3),
                            labelStyle: TextStyle(color: status['color']),
                          ),
                        )).toList(),
                      ),
                    ),
                  ],
                ),
              ),
              // Earnings List
              Expanded(child: _buildEarningsList()),
            ],
          ),
          // Breakdown Tab
          SingleChildScrollView(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Weekly Breakdown
                _buildWeeklyBreakdown(),
                const SizedBox(height: 16),
                // Daily Breakdown
                _buildDailyBreakdown(),
              ],
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showCreateDialog,
        child: const Icon(Icons.add),
      ),
    );
  }
}
