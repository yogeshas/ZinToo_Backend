import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:qr_code_scanner/qr_code_scanner.dart';
import 'models/order_models.dart';
import 'api_service_enhanced.dart';

class ViewOrdersScreenEnhanced extends StatefulWidget {
  final String authToken;

  const ViewOrdersScreenEnhanced({
    super.key,
    required this.authToken,
  });

  @override
  State<ViewOrdersScreenEnhanced> createState() => _ViewOrdersScreenEnhancedState();
}

class _ViewOrdersScreenEnhancedState extends State<ViewOrdersScreenEnhanced>
    with TickerProviderStateMixin {
  final ApiServiceEnhanced _apiService = ApiServiceEnhanced();
  final ScrollController _scrollController = ScrollController();

  // Tab management
  late TabController _tabController;
  int _currentTabIndex = 0;

  // Data storage
  List<Order> _orders = [];
  List<Exchange> _exchanges = [];
  List<OrderItem> _cancelledItems = [];
  List<dynamic> _approvedItems = [];
  List<dynamic> _rejectedItems = [];

  // Loading states
  bool _isLoading = false;
  bool _isLoadingMore = false;
  String? _errorMessage;
  String? _successMessage;

  // Barcode scanning
  bool _isScanning = false;
  QRViewController? _qrController;
  final GlobalKey qrKey = GlobalKey(debugLabel: 'QR');

  // OTP verification
  bool _isVerifyingOTP = false;
  String? _currentOrderId;
  String _otpCode = '';
  int _otpExpiresIn = 0;
  Timer? _otpTimer;

  // UI state
  Map<int, bool> _expandedOrders = {};
  final TextEditingController _otpController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _tabController.addListener(_onTabChanged);
    _loadData();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _tabController.dispose();
    _scrollController.dispose();
    _qrController?.dispose();
    _otpTimer?.cancel();
    _otpController.dispose();
    super.dispose();
  }

  void _onTabChanged() {
    if (_tabController.indexIsChanging) {
      setState(() {
        _currentTabIndex = _tabController.index;
      });
      _loadDataForCurrentTab();
    }
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      _loadMoreData();
    }
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      await _loadDataForCurrentTab();
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to load data: $e';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _loadDataForCurrentTab() async {
    switch (_currentTabIndex) {
      case 0: // All Orders
        await _loadAllOrders();
        break;
      case 1: // Exchanges
        await _loadExchanges();
        break;
      case 2: // Cancelled
        await _loadCancelledItems();
        break;
      case 3: // Approved/Rejected
        await _loadApprovedRejectedItems();
        break;
    }
  }

  Future<void> _loadAllOrders() async {
    try {
      final response = await _apiService.getDeliveryOrders(widget.authToken);
      if (response['success']) {
        setState(() {
          _orders = (response['orders'] as List)
              .map((order) => Order.fromJson(order))
              .toList();
        });
      }
    } catch (e) {
      print('Error loading orders: $e');
    }
  }

  Future<void> _loadExchanges() async {
    try {
      final response = await _apiService.getDeliveryExchanges(widget.authToken);
      if (response['success']) {
        setState(() {
          _exchanges = (response['exchanges'] as List)
              .map((exchange) => Exchange.fromJson(exchange))
              .toList();
        });
      }
    } catch (e) {
      print('Error loading exchanges: $e');
    }
  }

  Future<void> _loadCancelledItems() async {
    try {
      final response = await _apiService.getCancelledOrderItems(widget.authToken);
      if (response['success']) {
        setState(() {
          _cancelledItems = (response['cancelled_items'] as List)
              .map((item) => OrderItem.fromJson(item))
              .toList();
        });
      }
    } catch (e) {
      print('Error loading cancelled items: $e');
    }
  }

  Future<void> _loadApprovedRejectedItems() async {
    try {
      // Load approved items
      final approvedResponse = await _apiService.getCombinedOrders(
        widget.authToken,
        status: 'approved',
      );
      if (approvedResponse['success']) {
        setState(() {
          _approvedItems = approvedResponse['data']['orders'] ?? [];
        });
      }

      // Load rejected items
      final rejectedResponse = await _apiService.getCombinedOrders(
        widget.authToken,
        status: 'rejected',
      );
      if (rejectedResponse['success']) {
        setState(() {
          _rejectedItems = rejectedResponse['data']['orders'] ?? [];
        });
      }
    } catch (e) {
      print('Error loading approved/rejected items: $e');
    }
  }

  Future<void> _loadMoreData() async {
    if (_isLoadingMore) return;

    setState(() {
      _isLoadingMore = true;
    });

    try {
      // Implement pagination logic here
      await Future.delayed(Duration(seconds: 1)); // Simulate loading
    } finally {
      setState(() {
        _isLoadingMore = false;
      });
    }
  }

  void _startBarcodeScanning() {
    setState(() {
      _isScanning = true;
    });
  }

  void _stopBarcodeScanning() {
    setState(() {
      _isScanning = false;
    });
    _qrController?.dispose();
  }

  void _onQRViewCreated(QRViewController controller) {
    setState(() {
      _qrController = controller;
    });
    controller.scannedDataStream.listen((scanData) {
      _handleBarcodeScanned(scanData.code);
    });
  }

  Future<void> _handleBarcodeScanned(String? barcode) async {
    if (barcode == null) return;

    _stopBarcodeScanning();

    try {
      setState(() {
        _isLoading = true;
      });

      final response = await _apiService.scanBarcode(widget.authToken, barcode);
      if (response['success']) {
        final order = response['order'];
        _showOrderDetailsDialog(order);
      } else {
        _showErrorSnackBar(response['error'] ?? 'Order not found');
      }
    } catch (e) {
      _showErrorSnackBar('Error scanning barcode: $e');
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _sendOTP(String orderId) async {
    try {
      setState(() {
        _isVerifyingOTP = true;
        _currentOrderId = orderId;
      });

      final response = await _apiService.sendDeliveryOTP(widget.authToken, orderId);
      if (response['success']) {
        setState(() {
          _otpExpiresIn = response['expires_in'] ?? 600;
          _successMessage = response['message'];
        });
        _startOTPTimer();
        _showOTPDialog();
      } else {
        _showErrorSnackBar(response['error'] ?? 'Failed to send OTP');
      }
    } catch (e) {
      _showErrorSnackBar('Error sending OTP: $e');
    } finally {
      setState(() {
        _isVerifyingOTP = false;
      });
    }
  }

  void _startOTPTimer() {
    _otpTimer?.cancel();
    _otpTimer = Timer.periodic(Duration(seconds: 1), (timer) {
      if (_otpExpiresIn > 0) {
        setState(() {
          _otpExpiresIn--;
        });
      } else {
        timer.cancel();
      }
    });
  }

  Future<void> _verifyOTP() async {
    if (_otpController.text.isEmpty) {
      _showErrorSnackBar('Please enter OTP');
      return;
    }

    try {
      setState(() {
        _isVerifyingOTP = true;
      });

      final response = await _apiService.verifyDeliveryOTP(
        widget.authToken,
        _currentOrderId!,
        _otpController.text,
      );

      if (response['success']) {
        _showSuccessSnackBar('Order delivered successfully!');
        _otpController.clear();
        Navigator.of(context).pop(); // Close OTP dialog
        _loadData(); // Refresh data
      } else {
        _showErrorSnackBar(response['error'] ?? 'Invalid OTP');
      }
    } catch (e) {
      _showErrorSnackBar('Error verifying OTP: $e');
    } finally {
      setState(() {
        _isVerifyingOTP = false;
      });
    }
  }

  void _showOrderDetailsDialog(Map<String, dynamic> order) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Order Details'),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              _buildOrderInfoRow('Order ID', order['id']?.toString() ?? 'N/A'),
              _buildOrderInfoRow('Customer', order['customer']?['name'] ?? 'N/A'),
              _buildOrderInfoRow('Phone', order['customer']?['phone'] ?? 'N/A'),
              _buildOrderInfoRow('Status', order['status'] ?? 'N/A'),
              _buildOrderInfoRow('Total', '₹${order['total_amount'] ?? '0'}'),
              SizedBox(height: 16),
              Text(
                'Order Items:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              ...(order['items'] as List? ?? []).map((item) => Padding(
                padding: EdgeInsets.symmetric(vertical: 4),
                child: Text('• ${item['product']?['name'] ?? 'Unknown'} x${item['quantity'] ?? 1}'),
              )),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: Text('Close'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.of(context).pop();
              _sendOTP(order['id']?.toString() ?? '');
            },
            child: Text('Send OTP'),
          ),
        ],
      ),
    );
  }

  Widget _buildOrderInfoRow(String label, String value) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 80,
            child: Text(
              '$label:',
              style: TextStyle(fontWeight: FontWeight.w500),
            ),
          ),
          Expanded(
            child: Text(value),
          ),
        ],
      ),
    );
  }

  void _showOTPDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: Text('Enter OTP'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Please enter the OTP sent to customer\'s email'),
            SizedBox(height: 16),
            TextField(
              controller: _otpController,
              keyboardType: TextInputType.number,
              maxLength: 6,
              decoration: InputDecoration(
                labelText: 'OTP',
                border: OutlineInputBorder(),
                counterText: '',
              ),
            ),
            if (_otpExpiresIn > 0)
              Padding(
                padding: EdgeInsets.only(top: 8),
                child: Text(
                  'Expires in: ${_otpExpiresIn}s',
                  style: TextStyle(color: Colors.red),
                ),
              ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              _otpTimer?.cancel();
              _otpController.clear();
              Navigator.of(context).pop();
            },
            child: Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: _isVerifyingOTP ? null : _verifyOTP,
            child: _isVerifyingOTP
                ? SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
                : Text('Verify'),
          ),
        ],
      ),
    );
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Order Management'),
        backgroundColor: Colors.blue[600],
        foregroundColor: Colors.white,
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: Colors.white,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          tabs: [
            Tab(text: 'Orders', icon: Icon(Icons.shopping_bag)),
            Tab(text: 'Exchanges', icon: Icon(Icons.swap_horiz)),
            Tab(text: 'Cancelled', icon: Icon(Icons.cancel)),
            Tab(text: 'Approved/Rejected', icon: Icon(Icons.check_circle)),
          ],
        ),
        actions: [
          IconButton(
            icon: Icon(Icons.qr_code_scanner),
            onPressed: _startBarcodeScanning,
            tooltip: 'Scan Barcode',
          ),
          IconButton(
            icon: Icon(Icons.refresh),
            onPressed: _loadData,
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: Stack(
        children: [
          TabBarView(
            controller: _tabController,
            children: [
              _buildOrdersTab(),
              _buildExchangesTab(),
              _buildCancelledTab(),
              _buildApprovedRejectedTab(),
            ],
          ),
          if (_isScanning) _buildBarcodeScanner(),
          if (_isLoading) _buildLoadingOverlay(),
        ],
      ),
    );
  }

  Widget _buildOrdersTab() {
    if (_orders.isEmpty && !_isLoading) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.shopping_bag_outlined, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text('No orders found', style: TextStyle(fontSize: 18, color: Colors.grey)),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadData,
      child: ListView.builder(
        controller: _scrollController,
        padding: EdgeInsets.all(16),
        itemCount: _orders.length + (_isLoadingMore ? 1 : 0),
        itemBuilder: (context, index) {
          if (index >= _orders.length) {
            return Center(
              child: Padding(
                padding: EdgeInsets.all(16),
                child: CircularProgressIndicator(),
              ),
            );
          }

          final order = _orders[index];
          return _buildOrderCard(order);
        },
      ),
    );
  }

  Widget _buildExchangesTab() {
    if (_exchanges.isEmpty && !_isLoading) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.swap_horiz, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text('No exchanges found', style: TextStyle(fontSize: 18, color: Colors.grey)),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadData,
      child: ListView.builder(
        padding: EdgeInsets.all(16),
        itemCount: _exchanges.length,
        itemBuilder: (context, index) {
          final exchange = _exchanges[index];
          return _buildExchangeCard(exchange);
        },
      ),
    );
  }

  Widget _buildCancelledTab() {
    if (_cancelledItems.isEmpty && !_isLoading) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.cancel, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text('No cancelled items found', style: TextStyle(fontSize: 18, color: Colors.grey)),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadData,
      child: ListView.builder(
        padding: EdgeInsets.all(16),
        itemCount: _cancelledItems.length,
        itemBuilder: (context, index) {
          final item = _cancelledItems[index];
          return _buildCancelledItemCard(item);
        },
      ),
    );
  }

  Widget _buildApprovedRejectedTab() {
    return DefaultTabController(
      length: 2,
      child: Column(
        children: [
          TabBar(
            tabs: [
              Tab(text: 'Approved', icon: Icon(Icons.check_circle)),
              Tab(text: 'Rejected', icon: Icon(Icons.cancel)),
            ],
          ),
          Expanded(
            child: TabBarView(
              children: [
                _buildApprovedItemsList(),
                _buildRejectedItemsList(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildApprovedItemsList() {
    if (_approvedItems.isEmpty && !_isLoading) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.check_circle, size: 64, color: Colors.green),
            SizedBox(height: 16),
            Text('No approved items found', style: TextStyle(fontSize: 18, color: Colors.grey)),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: EdgeInsets.all(16),
      itemCount: _approvedItems.length,
      itemBuilder: (context, index) {
        final item = _approvedItems[index];
        return _buildApprovedRejectedCard(item, true);
      },
    );
  }

  Widget _buildRejectedItemsList() {
    if (_rejectedItems.isEmpty && !_isLoading) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.cancel, size: 64, color: Colors.red),
            SizedBox(height: 16),
            Text('No rejected items found', style: TextStyle(fontSize: 18, color: Colors.grey)),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: EdgeInsets.all(16),
      itemCount: _rejectedItems.length,
      itemBuilder: (context, index) {
        final item = _rejectedItems[index];
        return _buildApprovedRejectedCard(item, false);
      },
    );
  }

  Widget _buildOrderCard(Order order) {
    return Card(
      margin: EdgeInsets.only(bottom: 16),
      elevation: 4,
      child: ExpansionTile(
        title: Text(
          'Order #${order.id}',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Customer: ${order.customer?.name ?? 'N/A'}'),
            Text('Status: ${order.status}'),
            Text('Total: ₹${order.totalAmount}'),
          ],
        ),
        trailing: _buildOrderStatusChip(order.status),
        children: [
          Padding(
            padding: EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildOrderInfoRow('Order ID', order.id.toString()),
                _buildOrderInfoRow('Customer', order.customer?.name ?? 'N/A'),
                _buildOrderInfoRow('Phone', order.customer?.phone ?? 'N/A'),
                _buildOrderInfoRow('Email', order.customer?.email ?? 'N/A'),
                _buildOrderInfoRow('Status', order.status),
                _buildOrderInfoRow('Total', '₹${order.totalAmount}'),
                SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    ElevatedButton.icon(
                      onPressed: () => _sendOTP(order.id.toString()),
                      icon: Icon(Icons.email),
                      label: Text('Send OTP'),
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.blue),
                    ),
                    ElevatedButton.icon(
                      onPressed: () => _approveOrder(order.id.toString()),
                      icon: Icon(Icons.check),
                      label: Text('Approve'),
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                    ),
                    ElevatedButton.icon(
                      onPressed: () => _rejectOrder(order.id.toString()),
                      icon: Icon(Icons.close),
                      label: Text('Reject'),
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildExchangeCard(Exchange exchange) {
    return Card(
      margin: EdgeInsets.only(bottom: 16),
      elevation: 4,
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Exchange #${exchange.id}',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                ),
                _buildExchangeStatusChip(exchange.status),
              ],
            ),
            SizedBox(height: 8),
            Text('Original Product: ${exchange.originalProduct?.name ?? 'N/A'}'),
            Text('Exchange Product: ${exchange.exchangeProduct?.name ?? 'N/A'}'),
            Text('Reason: ${exchange.reason ?? 'N/A'}'),
            SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                ElevatedButton.icon(
                  onPressed: () => _approveExchange(exchange.id.toString()),
                  icon: Icon(Icons.check),
                  label: Text('Approve'),
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                ),
                ElevatedButton.icon(
                  onPressed: () => _rejectExchange(exchange.id.toString()),
                  icon: Icon(Icons.close),
                  label: Text('Reject'),
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCancelledItemCard(OrderItem item) {
    return Card(
      margin: EdgeInsets.only(bottom: 16),
      elevation: 4,
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Item #${item.id}',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                ),
                Chip(
                  label: Text('Cancelled'),
                  backgroundColor: Colors.red[100],
                  labelStyle: TextStyle(color: Colors.red[800]),
                ),
              ],
            ),
            SizedBox(height: 8),
            Text('Product: ${item.product?.name ?? 'N/A'}'),
            Text('Quantity: ${item.quantity}'),
            Text('Price: ₹${item.price}'),
            Text('Order: #${item.orderId}'),
          ],
        ),
      ),
    );
  }

  Widget _buildApprovedRejectedCard(Map<String, dynamic> item, bool isApproved) {
    return Card(
      margin: EdgeInsets.only(bottom: 16),
      elevation: 4,
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '${item['type'] ?? 'Item'} #${item['id']}',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                ),
                Chip(
                  label: Text(isApproved ? 'Approved' : 'Rejected'),
                  backgroundColor: isApproved ? Colors.green[100] : Colors.red[100],
                  labelStyle: TextStyle(
                    color: isApproved ? Colors.green[800] : Colors.red[800],
                  ),
                ),
              ],
            ),
            SizedBox(height: 8),
            Text('Status: ${item['status'] ?? 'N/A'}'),
            Text('Notes: ${item['notes'] ?? 'N/A'}'),
            if (item['created_at'] != null)
              Text('Date: ${DateTime.parse(item['created_at']).toString().split(' ')[0]}'),
          ],
        ),
      ),
    );
  }

  Widget _buildOrderStatusChip(String status) {
    Color backgroundColor;
    Color textColor;

    switch (status.toLowerCase()) {
      case 'pending':
        backgroundColor = Colors.orange[100]!;
        textColor = Colors.orange[800]!;
        break;
      case 'confirmed':
        backgroundColor = Colors.blue[100]!;
        textColor = Colors.blue[800]!;
        break;
      case 'delivered':
        backgroundColor = Colors.green[100]!;
        textColor = Colors.green[800]!;
        break;
      case 'cancelled':
        backgroundColor = Colors.red[100]!;
        textColor = Colors.red[800]!;
        break;
      default:
        backgroundColor = Colors.grey[100]!;
        textColor = Colors.grey[800]!;
    }

    return Chip(
      label: Text(status.toUpperCase()),
      backgroundColor: backgroundColor,
      labelStyle: TextStyle(color: textColor, fontSize: 12),
    );
  }

  Widget _buildExchangeStatusChip(String status) {
    Color backgroundColor;
    Color textColor;

    switch (status.toLowerCase()) {
      case 'pending':
        backgroundColor = Colors.orange[100]!;
        textColor = Colors.orange[800]!;
        break;
      case 'approved':
        backgroundColor = Colors.green[100]!;
        textColor = Colors.green[800]!;
        break;
      case 'rejected':
        backgroundColor = Colors.red[100]!;
        textColor = Colors.red[800]!;
        break;
      default:
        backgroundColor = Colors.grey[100]!;
        textColor = Colors.grey[800]!;
    }

    return Chip(
      label: Text(status.toUpperCase()),
      backgroundColor: backgroundColor,
      labelStyle: TextStyle(color: textColor, fontSize: 12),
    );
  }

  Widget _buildBarcodeScanner() {
    return Container(
      color: Colors.black,
      child: QRView(
        key: qrKey,
        onQRViewCreated: _onQRViewCreated,
        overlay: QrScannerOverlayShape(
          borderColor: Colors.blue,
          borderRadius: 10,
          borderLength: 30,
          borderWidth: 10,
          cutOutSize: 300,
        ),
      ),
    );
  }

  Widget _buildLoadingOverlay() {
    return Container(
      color: Colors.black54,
      child: Center(
        child: Card(
          child: Padding(
            padding: EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                CircularProgressIndicator(),
                SizedBox(height: 16),
                Text('Loading...'),
              ],
            ),
          ),
        ),
      ),
    );
  }

  // Action methods
  Future<void> _approveOrder(String orderId) async {
    try {
      final response = await _apiService.approveOrderEnhanced(widget.authToken, orderId);
      if (response['success']) {
        _showSuccessSnackBar('Order approved successfully');
        _loadData();
      } else {
        _showErrorSnackBar(response['error'] ?? 'Failed to approve order');
      }
    } catch (e) {
      _showErrorSnackBar('Error approving order: $e');
    }
  }

  Future<void> _rejectOrder(String orderId) async {
    final reason = await _showRejectionReasonDialog();
    if (reason == null) return;

    try {
      final response = await _apiService.rejectOrderEnhanced(widget.authToken, orderId, reason);
      if (response['success']) {
        _showSuccessSnackBar('Order rejected successfully');
        _loadData();
      } else {
        _showErrorSnackBar(response['error'] ?? 'Failed to reject order');
      }
    } catch (e) {
      _showErrorSnackBar('Error rejecting order: $e');
    }
  }

  Future<void> _approveExchange(String exchangeId) async {
    try {
      final response = await _apiService.approveExchangeEnhanced(widget.authToken, exchangeId);
      if (response['success']) {
        _showSuccessSnackBar('Exchange approved successfully');
        _loadData();
      } else {
        _showErrorSnackBar(response['error'] ?? 'Failed to approve exchange');
      }
    } catch (e) {
      _showErrorSnackBar('Error approving exchange: $e');
    }
  }

  Future<void> _rejectExchange(String exchangeId) async {
    final reason = await _showRejectionReasonDialog();
    if (reason == null) return;

    try {
      final response = await _apiService.rejectExchangeEnhanced(widget.authToken, exchangeId, reason);
      if (response['success']) {
        _showSuccessSnackBar('Exchange rejected successfully');
        _loadData();
      } else {
        _showErrorSnackBar(response['error'] ?? 'Failed to reject exchange');
      }
    } catch (e) {
      _showErrorSnackBar('Error rejecting exchange: $e');
    }
  }

  Future<String?> _showRejectionReasonDialog() async {
    final controller = TextEditingController();
    return showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Rejection Reason'),
        content: TextField(
          controller: controller,
          decoration: InputDecoration(
            labelText: 'Please provide a reason for rejection',
            border: OutlineInputBorder(),
          ),
          maxLines: 3,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(context).pop(controller.text),
            child: Text('Submit'),
          ),
        ],
      ),
    );
  }
}

// Model classes (you may need to adjust these based on your existing models)
class Exchange {
  final int id;
  final String status;
  final String? reason;
  final Product? originalProduct;
  final Product? exchangeProduct;

  Exchange({
    required this.id,
    required this.status,
    this.reason,
    this.originalProduct,
    this.exchangeProduct,
  });

  factory Exchange.fromJson(Map<String, dynamic> json) {
    return Exchange(
      id: json['id'] ?? 0,
      status: json['status'] ?? 'pending',
      reason: json['reason'],
      originalProduct: json['original_product'] != null
          ? Product.fromJson(json['original_product'])
          : null,
      exchangeProduct: json['exchange_product'] != null
          ? Product.fromJson(json['exchange_product'])
          : null,
    );
  }
}

class Product {
  final int id;
  final String name;
  final String? barcode;
  final double price;

  Product({
    required this.id,
    required this.name,
    this.barcode,
    required this.price,
  });

  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      id: json['id'] ?? 0,
      name: json['name'] ?? '',
      barcode: json['barcode'],
      price: (json['price'] ?? 0).toDouble(),
    );
  }
}
