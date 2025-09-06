import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'api_service_earnings.dart';

class EarningsManagementScreen extends StatefulWidget {
  final String authToken;

  const EarningsManagementScreen({
    Key? key,
    required this.authToken,
  }) : super(key: key);

  @override
  State<EarningsManagementScreen> createState() => _EarningsManagementScreenState();
}

class _EarningsManagementScreenState extends State<EarningsManagementScreen> with TickerProviderStateMixin {
  final ApiServiceEarnings _apiService = ApiServiceEarnings();
  late TabController _tabController;
  
  // Data
  List<Map<String, dynamic>> _earnings = [];
  Map<String, dynamic> _summary = {};
  List<Map<String, dynamic>> _weeklyBreakdown = [];
  List<Map<String, dynamic>> _dailyBreakdown = [];
  
  bool _isLoading = false;
  String? _errorMessage;
  String _selectedPeriod = 'monthly';
  String _selectedType = 'all';

  final List<String> _periods = ['daily', 'weekly', 'monthly'];
  final List<Map<String, dynamic>> _paymentTypes = [
    {'value': 'all', 'label': 'All', 'icon': Icons.all_inclusive},
    {'value': 'salary', 'label': 'Salary', 'icon': Icons.attach_money},
    {'value': 'bonus', 'label': 'Bonus', 'icon': Icons.trending_up},
    {'value': 'payout', 'label': 'Payout', 'icon': Icons.account_balance_wallet},
  ];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadEarnings();
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
      final response = await _apiService.getDeliveryEarnings(
        widget.authToken,
        type: _selectedType == 'all' ? null : _selectedType,
        period: _selectedPeriod == 'all' ? null : _selectedPeriod,
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

  Future<void> _loadSummary() async {
    try {
      final response = await _apiService.getDeliveryEarningsSummary(
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

    // Handle different possible data structures
    double totalAmount = 0.0;
    int count = 0;
    
    if (data.containsKey('total_amount')) {
      totalAmount = data['total_amount']?.toDouble() ?? 0.0;
    } else if (data.containsKey('amount')) {
      totalAmount = data['amount']?.toDouble() ?? 0.0;
    } else if (data.containsKey('total')) {
      totalAmount = data['total']?.toDouble() ?? 0.0;
    }
    
    if (data.containsKey('count')) {
      count = data['count'] ?? 0;
    } else if (data.containsKey('entries')) {
      count = data['entries'] ?? 0;
    } else if (data.containsKey('total_count')) {
      count = data['total_count'] ?? 0;
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              children: [
                Icon(typeInfo['icon'], color: _getPaymentTypeColor(type)),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Total ${typeInfo['label']}',
                    style: const TextStyle(
                      fontSize: 14,
                      color: Colors.grey,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              _formatCurrency(totalAmount),
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 4),
            Text(
              '$count entries',
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
                children: [
                  Expanded(
                    flex: 2,
                    child: Text(
                      _formatDate(item['week_start']),
                      style: const TextStyle(fontSize: 14),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Flexible(
                    child: Chip(
                      label: Text(
                        item['payment_type'].toString().toUpperCase(),
                        style: const TextStyle(fontSize: 10),
                      ),
                      backgroundColor: _getPaymentTypeColor(item['payment_type']).withOpacity(0.1),
                      labelStyle: TextStyle(
                        color: _getPaymentTypeColor(item['payment_type']),
                        fontSize: 10,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Flexible(
                    child: Text(
                      _formatCurrency(item['total_amount']?.toDouble() ?? 0.0),
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                      ),
                      overflow: TextOverflow.ellipsis,
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
                children: [
                  Expanded(
                    flex: 2,
                    child: Text(
                      _formatDate(item['date'] ?? item['start_date']),
                      style: const TextStyle(fontSize: 14),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Flexible(
                    child: Chip(
                      label: Text(
                        item['payment_type'].toString().toUpperCase(),
                        style: const TextStyle(fontSize: 10),
                      ),
                      backgroundColor: _getPaymentTypeColor(item['payment_type']).withOpacity(0.1),
                      labelStyle: TextStyle(
                        color: _getPaymentTypeColor(item['payment_type']),
                        fontSize: 10,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Flexible(
                    child: Text(
                      _formatCurrency(item['total_amount']?.toDouble() ?? 0.0),
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                      ),
                      overflow: TextOverflow.ellipsis,
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
      padding: const EdgeInsets.symmetric(vertical: 8),
      itemCount: _earnings.length,
      itemBuilder: (context, index) {
        final earning = _earnings[index];
        final paymentType = earning['payment_type']?.toString() ?? 'unknown';
        final status = earning['status']?.toString() ?? 'unknown';
        final amount = earning['amount']?.toDouble() ?? 0.0;
        final startDate = earning['start_date']?.toString() ?? '';
        final endDate = earning['end_date']?.toString() ?? '';
        final description = earning['description']?.toString() ?? '';
        
        return Card(
          margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
          child: Padding(
            padding: const EdgeInsets.all(12.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    CircleAvatar(
                      backgroundColor: _getPaymentTypeColor(paymentType).withOpacity(0.1),
                      child: Icon(
                        _getPaymentTypeIcon(paymentType),
                        color: _getPaymentTypeColor(paymentType),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            paymentType.toUpperCase(),
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Status: ${status.toUpperCase()}',
                            style: TextStyle(
                              color: _getStatusColor(status),
                              fontWeight: FontWeight.w500,
                              fontSize: 14,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          _formatCurrency(amount),
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 18,
                            color: _getPaymentTypeColor(paymentType),
                          ),
                        ),
                        const SizedBox(height: 4),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: _getStatusColor(status).withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            status.toUpperCase(),
                            style: TextStyle(
                              color: _getStatusColor(status),
                              fontSize: 10,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
                if (startDate.isNotEmpty || endDate.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text(
                    'Period: ${_formatDate(startDate)} - ${_formatDate(endDate)}',
                    style: const TextStyle(
                      fontSize: 12,
                      color: Colors.grey,
                    ),
                  ),
                ],
                if (description.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(
                    'Description: $description',
                    style: const TextStyle(
                      fontSize: 12,
                      color: Colors.grey,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ],
            ),
          ),
        );
      },
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
                LayoutBuilder(
                  builder: (context, constraints) {
                    int crossAxisCount = 2;
                    if (constraints.maxWidth < 600) {
                      crossAxisCount = 1;
                    } else if (constraints.maxWidth > 900) {
                      crossAxisCount = 3;
                    }
                    
                    return GridView.count(
                      crossAxisCount: crossAxisCount,
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      childAspectRatio: 1.3,
                      crossAxisSpacing: 8,
                      mainAxisSpacing: 8,
                      children: _summary.entries.map((entry) => 
                        _buildSummaryCard(entry.key, entry.value)
                      ).toList(),
                    );
                  },
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
              // Type Filter
              Container(
                padding: const EdgeInsets.all(16.0),
                child: SingleChildScrollView(
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
                // Period Filter for Breakdown
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Breakdown Period',
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
                // Weekly Breakdown (for weekly period)
                if (_selectedPeriod == 'weekly') _buildWeeklyBreakdown(),
                // Daily Breakdown (for daily and monthly periods)
                if (_selectedPeriod == 'daily' || _selectedPeriod == 'monthly') _buildDailyBreakdown(),
              ],
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _loadEarnings,
        child: const Icon(Icons.refresh),
      ),
    );
  }
}
