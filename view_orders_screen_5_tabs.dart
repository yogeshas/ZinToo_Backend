import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:qr_code_scanner/qr_code_scanner.dart';
import 'models/order_models.dart';
import 'api_service_5_tabs.dart';

class ViewOrdersScreen5Tabs extends StatefulWidget {
  final String authToken;

  const ViewOrdersScreen5Tabs({
    super.key,
    required this.authToken,
  });

  @override
  State<ViewOrdersScreen5Tabs> createState() => _ViewOrdersScreen5TabsState();
}

class _ViewOrdersScreen5TabsState extends State<ViewOrdersScreen5Tabs>
    with TickerProviderStateMixin {
  final ApiService5Tabs _apiService = ApiService5Tabs();
  final ScrollController _scrollController = ScrollController();

  // Base URL for backend images
  final String _baseUrl = 'http://127.0.0.1:5000';

  // Tab management
  late TabController _tabController;
  int _currentTabIndex = 0;

  // Data storage
  List<dynamic> _orders = [];
  List<dynamic> _exchanges = [];
  List<dynamic> _cancelledItems = [];
  List<dynamic> _approvedItems = [];
  List<dynamic> _rejectedItems = [];

  // Loading states
  bool _isLoading = false;
  bool _isLoadingMore = false;
  String? _errorMessage;
  String? _successMessage;

  // UI state
  Map<int, bool> _expandedItems = {};
  
  // Barcode scanning
  bool _isScanning = false;
  QRViewController? _qrController;
  final GlobalKey qrKey = GlobalKey(debugLabel: 'QR');

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 5, vsync: this);
    _tabController.addListener(_onTabChanged);
    _loadData();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _tabController.dispose();
    _scrollController.dispose();
    _qrController?.dispose();
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
      case 0: // Orders
        await _loadOrders();
        break;
      case 1: // Exchanges
        await _loadExchanges();
        break;
      case 2: // Cancelled
        await _loadCancelledItems();
        break;
      case 3: // Approved
        await _loadApprovedItems();
        break;
      case 4: // Rejected
        await _loadRejectedItems();
        break;
    }
  }

  Future<void> _loadOrders() async {
    try {
      final response = await _apiService.getDeliveryOrders(widget.authToken);
      if (response['success']) {
        setState(() {
          _orders = response['orders'] ?? [];
        });
      } else {
        setState(() {
          _errorMessage = response['error'] ?? 'Failed to load orders';
        });
      }
    } catch (e) {
      print('Error loading orders: $e');
      setState(() {
        _errorMessage = 'Error loading orders: $e';
      });
    }
  }

  Future<void> _loadExchanges() async {
    try {
      final response = await _apiService.getDeliveryExchanges(widget.authToken);
      if (response['success']) {
        setState(() {
          _exchanges = response['exchanges'] ?? [];
        });
      } else {
        setState(() {
          _errorMessage = response['error'] ?? 'Failed to load exchanges';
        });
      }
    } catch (e) {
      print('Error loading exchanges: $e');
      setState(() {
        _errorMessage = 'Error loading exchanges: $e';
      });
    }
  }

  Future<void> _loadCancelledItems() async {
    try {
      final response = await _apiService.getCancelledOrderItems(widget.authToken);
      if (response['success']) {
        setState(() {
          _cancelledItems = response['cancelled_items'] ?? [];
        });
      } else {
        setState(() {
          _errorMessage = response['error'] ?? 'Failed to load cancelled items';
        });
      }
    } catch (e) {
      print('Error loading cancelled items: $e');
      setState(() {
        _errorMessage = 'Error loading cancelled items: $e';
      });
    }
  }

  Future<void> _loadApprovedItems() async {
    try {
      final response = await _apiService.getApprovedItems(widget.authToken);
      if (response['success']) {
        setState(() {
          _approvedItems = response['approved_items'] ?? [];
        });
      } else {
        setState(() {
          _errorMessage = response['error'] ?? 'Failed to load approved items';
        });
      }
    } catch (e) {
      print('Error loading approved items: $e');
      setState(() {
        _errorMessage = 'Error loading approved items: $e';
      });
    }
  }

  Future<void> _loadRejectedItems() async {
    try {
      final response = await _apiService.getRejectedItems(widget.authToken);
      if (response['success']) {
        setState(() {
          _rejectedItems = response['rejected_items'] ?? [];
        });
      } else {
        setState(() {
          _errorMessage = response['error'] ?? 'Failed to load rejected items';
        });
      }
    } catch (e) {
      print('Error loading rejected items: $e');
      setState(() {
        _errorMessage = 'Error loading rejected items: $e';
      });
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

  void _toggleItemExpansion(int itemId) {
    setState(() {
      _expandedItems[itemId] = !(_expandedItems[itemId] ?? false);
    });
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
          isScrollable: true,
          tabs: [
            Tab(text: 'Orders', icon: Icon(Icons.shopping_bag)),
            Tab(text: 'Exchanges', icon: Icon(Icons.swap_horiz)),
            Tab(text: 'Cancelled', icon: Icon(Icons.cancel)),
            Tab(text: 'Approved', icon: Icon(Icons.check_circle)),
            Tab(text: 'Rejected', icon: Icon(Icons.close)),
          ],
        ),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh),
            onPressed: _loadData,
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildOrdersTab(),
          _buildExchangesTab(),
          _buildCancelledTab(),
          _buildApprovedTab(),
          _buildRejectedTab(),
        ],
      ),
    );
  }

  Widget _buildOrdersTab() {
    return _buildTabContent(
      items: _orders,
      itemType: 'orders',
      emptyMessage: 'No orders assigned to you yet',
      emptyIcon: Icons.shopping_bag_outlined,
    );
  }

  Widget _buildExchangesTab() {
    return _buildTabContent(
      items: _exchanges,
      itemType: 'exchanges',
      emptyMessage: 'No exchanges assigned to you yet',
      emptyIcon: Icons.swap_horiz,
    );
  }

  Widget _buildCancelledTab() {
    return _buildTabContent(
      items: _cancelledItems,
      itemType: 'cancelled_items',
      emptyMessage: 'No cancelled items assigned to you yet',
      emptyIcon: Icons.cancel,
    );
  }

  Widget _buildApprovedTab() {
    return _buildTabContent(
      items: _approvedItems,
      itemType: 'approved_items',
      emptyMessage: 'No approved items yet',
      emptyIcon: Icons.check_circle,
    );
  }

  Widget _buildRejectedTab() {
    return _buildTabContent(
      items: _rejectedItems,
      itemType: 'rejected_items',
      emptyMessage: 'No rejected items yet',
      emptyIcon: Icons.close,
    );
  }

  Widget _buildTabContent({
    required List<dynamic> items,
    required String itemType,
    required String emptyMessage,
    required IconData emptyIcon,
  }) {
    if (_isLoading && items.isEmpty) {
      return Center(
        child: CircularProgressIndicator(),
      );
    }

    if (_errorMessage != null && items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 64, color: Colors.red[300]),
            SizedBox(height: 16),
            Text(
              _errorMessage!,
              style: TextStyle(fontSize: 16, color: Colors.red[600]),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadData,
              child: Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(emptyIcon, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text(emptyMessage, style: TextStyle(fontSize: 18, color: Colors.grey)),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadData,
      child: ListView.builder(
        controller: _scrollController,
        padding: EdgeInsets.all(16),
        itemCount: items.length + (_isLoadingMore ? 1 : 0),
        itemBuilder: (context, index) {
          if (index >= items.length) {
            return Center(
              child: Padding(
                padding: EdgeInsets.all(16),
                child: CircularProgressIndicator(),
              ),
            );
          }

          final item = items[index];
          return _buildItemCard(item, itemType);
        },
      ),
    );
  }

  Widget _buildItemCard(dynamic item, String itemType) {
    final isExpanded = _expandedItems[item['id']] ?? false;

    return Card(
      margin: EdgeInsets.only(bottom: 16),
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Column(
        children: [
          // Header with ID and Status
          Container(
            padding: EdgeInsets.all(16),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [Colors.blue[50]!, Colors.blue[100]!],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.only(
                topLeft: Radius.circular(12),
                topRight: Radius.circular(12),
              ),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${_getItemTypeDisplay(itemType)} #${item['id']}',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.blue[800],
                        ),
                      ),
                      SizedBox(height: 4),
                      if (item['total_amount'] != null)
                        Text(
                          '₹${item['total_amount'].toStringAsFixed(2)}',
                          style: TextStyle(
                            fontSize: 16,
                            color: Colors.green[700],
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                    ],
                  ),
                ),
                Container(
                  padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: _getStatusColor(item['status']),
                    borderRadius: BorderRadius.circular(20),
                    boxShadow: [
                      BoxShadow(
                        color: _getStatusColor(item['status']).withOpacity(0.3),
                        blurRadius: 4,
                        offset: Offset(0, 2),
                      ),
                    ],
                  ),
                  child: Text(
                    item['status']?.toString().toUpperCase() ?? 'UNKNOWN',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Customer Information Section
          Container(
            padding: EdgeInsets.all(16),
            child: Column(
              children: [
                // Customer Name and Photo
                Row(
                  children: [
                    // Customer Photo
                    Container(
                      width: 50,
                      height: 50,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(color: Colors.blue[300]!, width: 2),
                      ),
                      child: ClipOval(
                        child: _buildCustomerPhoto(item),
                      ),
                    ),
                    SizedBox(width: 12),
                    // Customer Name
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            item['customer']?['name'] ?? 'Unknown Customer',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: Colors.grey[800],
                            ),
                          ),
                          SizedBox(height: 4),
                          Text(
                            'Customer ID: ${item['customer']?['id'] ?? 'N/A'}',
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.grey[600],
                            ),
                          ),
                        ],
                      ),
                    ),
                    // Call Button
                    if (item['customer']?['phone'] != null)
                      Container(
                        decoration: BoxDecoration(
                          color: Colors.green,
                          shape: BoxShape.circle,
                          boxShadow: [
                            BoxShadow(
                              color: Colors.green.withOpacity(0.3),
                              blurRadius: 4,
                              offset: Offset(0, 2),
                            ),
                          ],
                        ),
                        child: IconButton(
                          icon: Icon(Icons.phone, color: Colors.white),
                          onPressed: () => _makePhoneCall(item['customer']['phone']),
                          tooltip: 'Call Customer',
                        ),
                      ),
                  ],
                ),

                SizedBox(height: 16),

                // Address Section
                _buildAddressSection(item),

                SizedBox(height: 16),

                // Product Scan Section
                _buildProductScanSection(item, itemType),

                SizedBox(height: 16),

                // OTP Section (for orders and exchanges)
                if (itemType == 'orders' || itemType == 'exchanges')
                  _buildOTPSection(item, itemType),

                SizedBox(height: 16),

                // Action Buttons
                Row(
                  children: [
                    // Expand/Collapse Button
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () => _toggleItemExpansion(item['id']),
                        icon: Icon(isExpanded ? Icons.expand_less : Icons.expand_more),
                        label: Text(isExpanded ? 'Less Details' : 'More Details'),
                        style: OutlinedButton.styleFrom(
                          side: BorderSide(color: Colors.blue),
                          foregroundColor: Colors.blue,
                        ),
                      ),
                    ),

                    SizedBox(width: 8),

                    // Action buttons based on item type and status
                    ..._buildActionButtons(item, itemType),
                  ],
                ),
              ],
            ),
          ),

          // Expanded Details
          if (isExpanded)
            Container(
              padding: EdgeInsets.fromLTRB(16, 0, 16, 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Divider(color: Colors.grey[300]),
                  SizedBox(height: 16),
                  _buildExpandedDetails(item, itemType),
                ],
              ),
            ),
        ],
      ),
    );
  }


  List<Widget> _buildActionButtons(dynamic item, String itemType) {
    List<Widget> buttons = [];
    String status = item['status']?.toString().toLowerCase() ?? '';

    // Show buttons based on status and item type
    if (itemType == 'orders') {
      if (status == 'pending' || status == 'assigned') {
        // Approve button for pending/assigned orders
        buttons.add(
          Expanded(
            child: ElevatedButton.icon(
              onPressed: () => _approveOrder(item),
              icon: Icon(Icons.check, size: 16),
              label: Text('Approve'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.green,
                foregroundColor: Colors.white,
              ),
            ),
          ),
        );
      }

      if (status == 'shipped' || status == 'approved' || status == 'confirmed') {
        // Out for Delivery button for shipped/approved orders
        buttons.add(
          Expanded(
            child: ElevatedButton.icon(
              onPressed: () => _markOutForDelivery(item, itemType),
              icon: Icon(Icons.local_shipping, size: 16),
              label: Text('Out for Delivery'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.orange,
                foregroundColor: Colors.white,
              ),
            ),
          ),
        );
      }

      if (status == 'out_for_delivery') {
        // Delivered button for out for delivery orders
        buttons.add(
          Expanded(
            child: ElevatedButton.icon(
              onPressed: () => _markDelivered(item, itemType),
              icon: Icon(Icons.done_all, size: 16),
              label: Text('Mark Delivered'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.green,
                foregroundColor: Colors.white,
              ),
            ),
          ),
        );
      }
    }

    if (itemType == 'exchanges') {
      if (status == 'pending' || status == 'assigned') {
        // Approve button for pending/assigned exchanges
        buttons.add(
          Expanded(
            child: ElevatedButton.icon(
              onPressed: () => _approveExchange(item),
              icon: Icon(Icons.check, size: 16),
              label: Text('Approve'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.green,
                foregroundColor: Colors.white,
              ),
            ),
          ),
        );
      }

      if (status == 'shipped' || status == 'approved' || status == 'confirmed') {
        // Out for Delivery button for shipped/approved exchanges
        buttons.add(
          Expanded(
            child: ElevatedButton.icon(
              onPressed: () => _markOutForDelivery(item, itemType),
              icon: Icon(Icons.local_shipping, size: 16),
              label: Text('Out for Delivery'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.orange,
                foregroundColor: Colors.white,
              ),
            ),
          ),
        );
      }

      if (status == 'out_for_delivery') {
        // Delivered button for out for delivery exchanges
        buttons.add(
          Expanded(
            child: ElevatedButton.icon(
              onPressed: () => _markDelivered(item, itemType),
              icon: Icon(Icons.done_all, size: 16),
              label: Text('Mark Delivered'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.green,
                foregroundColor: Colors.white,
              ),
            ),
          ),
        );
      }
    }

    if (itemType == 'cancelled_items') {
      if (status == 'assigned') {
        // Out for Delivery button for assigned cancelled items
        buttons.add(
          Expanded(
            child: ElevatedButton.icon(
              onPressed: () => _markOutForDelivery(item, itemType),
              icon: Icon(Icons.local_shipping, size: 16),
              label: Text('Out for Delivery'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.orange,
                foregroundColor: Colors.white,
              ),
            ),
          ),
        );
      }

      if (status == 'out_for_delivery') {
        // Delivered button for out for delivery cancelled items
        buttons.add(
          Expanded(
            child: ElevatedButton.icon(
              onPressed: () => _markDelivered(item, itemType),
              icon: Icon(Icons.done_all, size: 16),
              label: Text('Mark Delivered'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.green,
                foregroundColor: Colors.white,
              ),
            ),
          ),
        );
      }
    }

    // Reject button for pending/assigned items (except cancelled items)
    if ((itemType == 'orders' || itemType == 'exchanges') &&
        (status == 'pending' || status == 'assigned' || status == 'confirmed')) {
      if (buttons.isNotEmpty) buttons.add(SizedBox(width: 8));
      buttons.add(
        Expanded(
          child: ElevatedButton.icon(
            onPressed: () => _rejectItem(item, itemType),
            icon: Icon(Icons.close, size: 16),
            label: Text('Reject'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red,
              foregroundColor: Colors.white,
            ),
          ),
        ),
      );
    }

    return buttons;
  }

  bool _canApproveOrder(dynamic order) {
    String status = order['status']?.toString().toLowerCase() ?? '';
    return ['pending', 'assigned'].contains(status);
  }

  bool _canRejectItem(dynamic item) {
    String status = item['status']?.toString().toLowerCase() ?? '';
    return ['pending', 'assigned', 'confirmed'].contains(status);
  }

  Widget _buildExpandedDetails(dynamic item, String itemType) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Common details
        _buildDetailRow('ID', item['id'].toString(), Icons.tag),
        if (item['customer'] != null)
          _buildDetailRow('Customer', item['customer']['name'] ?? 'N/A', Icons.person),
        if (item['customer'] != null && item['customer']['phone'] != null)
          _buildDetailRow('Phone', item['customer']['phone'], Icons.phone),
        if (item['customer'] != null && item['customer']['email'] != null)
          _buildDetailRow('Email', item['customer']['email'], Icons.email),
        _buildDetailRow('Status', item['status']?.toString() ?? 'N/A', Icons.info),
        if (item['created_at'] != null)
          _buildDetailRow('Created', _formatDateTime(item['created_at']), Icons.calendar_today),
        if (item['updated_at'] != null)
          _buildDetailRow('Updated', _formatDateTime(item['updated_at']), Icons.update),

        // Item-specific expanded details
        if (itemType == 'orders')
          _buildOrderExpandedDetails(item)
        else if (itemType == 'exchanges')
          _buildExchangeExpandedDetails(item)
        else if (itemType == 'cancelled_items')
            _buildCancelledItemExpandedDetails(item)
          else if (itemType == 'approved_items' || itemType == 'rejected_items')
              _buildTrackExpandedDetails(item),
      ],
    );
  }

  Widget _buildOrderExpandedDetails(dynamic order) {
    return Column(
      children: [
        if (order['delivery_address'] != null)
          _buildDetailRow('Address', _parseAddressFromJson(order['delivery_address']), Icons.location_on),
        if (order['payment_method'] != null)
          _buildDetailRow('Payment', order['payment_method'], Icons.payment),
        if (order['delivery_type'] != null)
          _buildDetailRow('Delivery Type', order['delivery_type'], Icons.local_shipping),
        if (order['order_number'] != null)
          _buildDetailRow('Order Number', order['order_number'], Icons.receipt),
        if (order['payment_status'] != null)
          _buildDetailRow('Payment Status', order['payment_status'], Icons.payment),
      ],
    );
  }

  Widget _buildExchangeExpandedDetails(dynamic exchange) {
    return Column(
      children: [
        if (exchange['original_product'] != null)
          _buildDetailRow('Original Product', exchange['original_product']['name'] ?? 'N/A', Icons.inventory),
        if (exchange['exchange_product'] != null)
          _buildDetailRow('Exchange Product', exchange['exchange_product']['name'] ?? 'N/A', Icons.swap_horiz),
        if (exchange['reason'] != null)
          _buildDetailRow('Reason', exchange['reason'], Icons.info),
      ],
    );
  }

  Widget _buildCancelledItemExpandedDetails(dynamic item) {
    return Column(
      children: [
        if (item['product'] != null)
          _buildDetailRow('Product', item['product']['name'] ?? 'N/A', Icons.inventory),
        if (item['quantity'] != null)
          _buildDetailRow('Quantity', item['quantity'].toString(), Icons.shopping_cart),
        if (item['price'] != null)
          _buildDetailRow('Price', '₹${item['price']}', Icons.attach_money),
      ],
    );
  }

  Widget _buildTrackExpandedDetails(dynamic track) {
    return Column(
      children: [
        if (track['notes'] != null)
          _buildDetailRow('Notes', track['notes'], Icons.note),
        if (track['order'] != null)
          _buildDetailRow('Order ID', track['order']['id'].toString(), Icons.shopping_bag),
        if (track['exchange'] != null)
          _buildDetailRow('Exchange ID', track['exchange']['id'].toString(), Icons.swap_horiz),
      ],
    );
  }

  Widget _buildDetailRow(String label, String value, IconData icon) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 16, color: Colors.grey),
          SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey[600],
                    fontWeight: FontWeight.w500,
                  ),
                ),
                Text(
                  value,
                  style: TextStyle(fontSize: 14),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Color _getStatusColor(String? status) {
    if (status == null) return Colors.grey;

    switch (status.toLowerCase()) {
      case 'pending':
        return Colors.orange;
      case 'assigned':
        return Colors.blue;
      case 'confirmed':
      case 'approved':
        return Colors.green;
      case 'processing':
        return Colors.blue;
      case 'shipped':
        return Colors.purple;
      case 'out_for_delivery':
        return Colors.deepOrange;
      case 'delivered':
        return Colors.green;
      case 'cancelled':
      case 'rejected':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  String _getItemTypeDisplay(String itemType) {
    switch (itemType) {
      case 'orders':
        return 'Order';
      case 'exchanges':
        return 'Exchange';
      case 'cancelled_items':
        return 'Item';
      case 'approved_items':
        return 'Approved';
      case 'rejected_items':
        return 'Rejected';
      default:
        return 'Item';
    }
  }

  String _formatDateTime(String? dateTimeString) {
    if (dateTimeString == null) return 'N/A';
    try {
      final dateTime = DateTime.parse(dateTimeString);
      return '${dateTime.day}/${dateTime.month}/${dateTime.year} ${dateTime.hour}:${dateTime.minute.toString().padLeft(2, '0')}';
    } catch (e) {
      return dateTimeString;
    }
  }

  // Helper methods for enhanced design
  Widget _buildCustomerPhoto(dynamic item) {
    // Try to get customer photo from various sources
    String? photoUrl;

    if (item['customer']?['photo'] != null) {
      photoUrl = item['customer']['photo'];
    } else if (item['customer']?['profile_picture'] != null) {
      photoUrl = item['customer']['profile_picture'];
    }

    if (photoUrl != null && photoUrl.isNotEmpty) {
      // Handle both relative and absolute URLs
      String fullUrl = photoUrl.startsWith('http')
          ? photoUrl
          : '$_baseUrl/$photoUrl';

      return Image.network(
        fullUrl,
        fit: BoxFit.cover,
        errorBuilder: (context, error, stackTrace) {
          return _buildDefaultCustomerPhoto();
        },
        loadingBuilder: (context, child, loadingProgress) {
          if (loadingProgress == null) return child;
          return Container(
            color: Colors.grey[200],
            child: Center(
              child: CircularProgressIndicator(
                value: loadingProgress.expectedTotalBytes != null
                    ? loadingProgress.cumulativeBytesLoaded / loadingProgress.expectedTotalBytes!
                    : null,
              ),
            ),
          );
        },
      );
    }

    return _buildDefaultCustomerPhoto();
  }

  Widget _buildDefaultCustomerPhoto() {
    return Container(
      color: Colors.blue[100],
      child: Icon(
        Icons.person,
        color: Colors.blue[600],
        size: 30,
      ),
    );
  }

  Widget _buildAddressSection(dynamic item) {
    String addressText = 'Address not available';

    if (item['delivery_address'] != null) {
      try {
        // Try to parse JSON address
        if (item['delivery_address'].toString().startsWith('{')) {
          // It's a JSON string, extract readable address
          addressText = _parseAddressFromJson(item['delivery_address']);
        } else {
          // It's a plain text address
          addressText = item['delivery_address'].toString();
        }
      } catch (e) {
        // If parsing fails, use the raw text
        addressText = item['delivery_address'].toString();
      }
    }

    return Container(
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.grey[300]!),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.location_on, color: Colors.red[600], size: 20),
          SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Delivery Address',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey[600],
                    fontWeight: FontWeight.w500,
                  ),
                ),
                SizedBox(height: 4),
                Text(
                  addressText,
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey[800],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _parseAddressFromJson(String jsonAddress) {
    try {
      // Simple JSON parsing for address
      String address = jsonAddress
          .replaceAll('{', '')
          .replaceAll('}', '')
          .replaceAll('"', '')
          .replaceAll(',', ', ');

      // Extract key address components
      List<String> parts = address.split(', ');
      List<String> addressParts = [];

      for (String part in parts) {
        if (part.contains('address_line1:') ||
            part.contains('city:') ||
            part.contains('state:') ||
            part.contains('postal_code:')) {
          addressParts.add(part.split(':')[1].trim());
        }
      }

      return addressParts.join(', ');
    } catch (e) {
      return jsonAddress;
    }
  }

  Widget _buildProductScanSection(dynamic item, String itemType) {
    // Get product information based on item type
    String? productName;
    String? barcode;
    int? quantity;

    if (itemType == 'orders') {
      if (item['order_items'] != null && item['order_items'].isNotEmpty) {
        productName = item['order_items'][0]['product']?['name'];
        barcode = item['order_items'][0]['product']?['barcode'];
        quantity = item['order_items'][0]['quantity'];
      }
    } else if (itemType == 'exchanges') {
      if (item['exchange_product'] != null) {
        productName = item['exchange_product']['name'];
        barcode = item['exchange_product']['barcode'];
        quantity = 1;
      } else if (item['original_product'] != null) {
        productName = item['original_product']['name'];
        barcode = item['original_product']['barcode'];
        quantity = 1;
      }
    } else if (itemType == 'cancelled_items') {
      if (item['product'] != null) {
        productName = item['product']['name'];
        barcode = item['product']['barcode'];
        quantity = item['quantity'];
      }
    }

    return Container(
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.blue[50],
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.blue[300]!),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Icon(Icons.qr_code_scanner, color: Colors.blue[600], size: 20),
              SizedBox(width: 8),
              Text(
                'Product Scan',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: Colors.blue[800],
                ),
              ),
            ],
          ),
          SizedBox(height: 8),

          // Product Information
          if (productName != null) ...[
            Container(
              width: double.infinity,
              padding: EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(6),
                border: Border.all(color: Colors.grey[300]!),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    productName,
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color: Colors.grey[800],
                    ),
                  ),
                  if (quantity != null) ...[
                    SizedBox(height: 4),
                    Text(
                      'Quantity: $quantity',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                  if (barcode != null) ...[
                    SizedBox(height: 4),
                    Text(
                      'Barcode: $barcode',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.blue[600],
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            SizedBox(height: 8),
          ],

          // Scan Button
          Row(
            children: [
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () => _scanProduct(item, itemType),
                  icon: Icon(Icons.qr_code_scanner, size: 16),
                  label: Text('Scan Barcode'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue[600],
                    foregroundColor: Colors.white,
                    padding: EdgeInsets.symmetric(vertical: 12),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildOTPSection(dynamic item, String itemType) {
    String status = item['status']?.toString().toLowerCase() ?? '';

    return Container(
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: status == 'out_for_delivery'
            ? Colors.blue[50]
            : status == 'approved' || status == 'confirmed'
            ? Colors.green[50]
            : status == 'rejected'
            ? Colors.red[50]
            : Colors.orange[50],
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
            color: status == 'out_for_delivery'
                ? Colors.blue[300]!
                : status == 'approved' || status == 'confirmed'
                ? Colors.green[300]!
                : status == 'rejected'
                ? Colors.red[300]!
                : Colors.orange[300]!
        ),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Icon(
                status == 'out_for_delivery'
                    ? Icons.qr_code_scanner
                    : status == 'approved' || status == 'confirmed'
                    ? Icons.check_circle
                    : status == 'rejected'
                    ? Icons.cancel
                    : Icons.security,
                color: status == 'out_for_delivery'
                    ? Colors.blue[600]
                    : status == 'approved' || status == 'confirmed'
                    ? Colors.green[600]
                    : status == 'rejected'
                    ? Colors.red[600]
                    : Colors.orange[600],
                size: 20
              ),
              SizedBox(width: 8),
              Text(
                status == 'out_for_delivery'
                    ? 'Scan Product'
                    : status == 'approved' || status == 'confirmed'
                    ? 'Status: Approved'
                    : status == 'rejected'
                    ? 'Status: Rejected'
                    : 'Quick Actions',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: status == 'out_for_delivery'
                      ? Colors.blue[800]
                      : status == 'approved' || status == 'confirmed'
                      ? Colors.green[800]
                      : status == 'rejected'
                      ? Colors.red[800]
                      : Colors.orange[800],
                ),
              ),
            ],
          ),
          SizedBox(height: 8),
          Row(
            children: [
              // Show appropriate button based on status
              if (status == 'out_for_delivery') ...[
                // Show only scan barcode button for out_for_delivery status
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () => _scanProduct(item, itemType),
                    icon: Icon(Icons.qr_code_scanner, size: 16),
                    label: Text('Scan Barcode'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blue[600],
                      foregroundColor: Colors.white,
                      padding: EdgeInsets.symmetric(vertical: 8),
                    ),
                  ),
                ),
              ] else if (status == 'approved' || status == 'confirmed') ...[
                // Show approved status button
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: null, // Disabled button
                    icon: Icon(Icons.check_circle, size: 16),
                    label: Text('Approved'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green[600],
                      foregroundColor: Colors.white,
                      padding: EdgeInsets.symmetric(vertical: 8),
                    ),
                  ),
                ),
              ] else if (status == 'rejected') ...[
                // Show rejected status button
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: null, // Disabled button
                    icon: Icon(Icons.cancel, size: 16),
                    label: Text('Rejected'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red[600],
                      foregroundColor: Colors.white,
                      padding: EdgeInsets.symmetric(vertical: 8),
                    ),
                  ),
                ),
              ] else ...[
                // Show approve and reject buttons for pending/assigned items
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () => _sendApprove(item, itemType),
                    icon: Icon(Icons.check, size: 16),
                    label: Text('Approve'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green[600],
                      foregroundColor: Colors.white,
                      padding: EdgeInsets.symmetric(vertical: 8),
                    ),
                  ),
                ),
                SizedBox(width: 8),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () => _rejectorder(item, itemType),
                    icon: Icon(Icons.close, size: 16),
                    label: Text('Reject'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red[600],
                      foregroundColor: Colors.white,
                      padding: EdgeInsets.symmetric(vertical: 8),
                    ),
                  ),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }

  // Action methods
  Future<void> _makePhoneCall(String phoneNumber) async {
    try {
      final Uri phoneUri = Uri(scheme: 'tel', path: phoneNumber);
      if (await canLaunchUrl(phoneUri)) {
        await launchUrl(phoneUri);
      } else {
        _showErrorSnackBar('Could not launch phone dialer');
      }
    } catch (e) {
      _showErrorSnackBar('Error making phone call: $e');
    }
  }

  Future<void> _scanProduct(dynamic item, String itemType) async {
    // Get expected barcode based on item type
    String? expectedBarcode;
    String productName = 'Product';

    if (itemType == 'orders') {
      if (item['order_items'] != null && item['order_items'].isNotEmpty) {
        expectedBarcode = item['order_items'][0]['product']?['barcode'];
        productName = item['order_items'][0]['product']?['name'] ?? 'Product';
      }
    } else if (itemType == 'exchanges') {
      if (item['exchange_product'] != null) {
        expectedBarcode = item['exchange_product']['barcode'];
        productName = item['exchange_product']['name'] ?? 'Exchange Product';
      } else if (item['original_product'] != null) {
        expectedBarcode = item['original_product']['barcode'];
        productName = item['original_product']['name'] ?? 'Original Product';
      }
    } else if (itemType == 'cancelled_items') {
      if (item['product'] != null) {
        expectedBarcode = item['product']['barcode'];
        productName = item['product']['name'] ?? 'Product';
      }
    }

    // Show barcode scanning dialog
    final scanResult = await _showBarcodeScanDialog(item, itemType, expectedBarcode, productName);

    if (scanResult == true) {
      _showSuccessSnackBar('Product barcode verified successfully!');
    }
  }

  Future<bool> _showBarcodeScanDialog(dynamic item, String itemType, String? expectedBarcode, String productName) async {
    return await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: Row(
            children: [
              Icon(Icons.qr_code_scanner, color: Colors.blue),
              SizedBox(width: 8),
              Text('Scan Product Barcode'),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Scan the barcode for:',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
              ),
              SizedBox(height: 8),
              Container(
                padding: EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.grey[50],
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.grey[300]!),
                ),
                child: Text(
                  productName,
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: Colors.grey[800],
                  ),
                  textAlign: TextAlign.center,
                ),
              ),
              SizedBox(height: 16),
              if (expectedBarcode != null) ...[
                Container(
                  padding: EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.blue[50],
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.blue[300]!),
                  ),
                  child: Column(
                    children: [
                      Text(
                        'Expected Barcode:',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.blue[600],
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      SizedBox(height: 4),
                      Text(
                        expectedBarcode,
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: Colors.blue[800],
                          fontSize: 16,
                          letterSpacing: 1,
                        ),
                      ),
                    ],
                  ),
                ),
                SizedBox(height: 16),
              ],
              // Camera scanner
              Container(
                height: 300,
                width: double.infinity,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.grey[300]!),
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: QRView(
                    key: qrKey,
                    onQRViewCreated: (QRViewController controller) {
                      _qrController = controller;
                      controller.scannedDataStream.listen((scanData) {
                        _handleBarcodeScanned(scanData.code, expectedBarcode, context);
                      });
                    },
                    overlay: QrScannerOverlayShape(
                      borderColor: Colors.blue,
                      borderRadius: 10,
                      borderLength: 30,
                      borderWidth: 10,
                      cutOutSize: 250,
                    ),
                  ),
                ),
              ),
              SizedBox(height: 16),
              Text(
                'Position the barcode within the frame to scan',
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey[600],
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () {
                _qrController?.dispose();
                Navigator.of(context).pop(false);
              },
              child: Text('Cancel'),
            ),
            TextButton.icon(
              onPressed: () {
                // Toggle flash
                _qrController?.toggleFlash();
              },
              icon: Icon(Icons.flash_on),
              label: Text('Flash'),
            ),
          ],
        ),
      ),
    ) ?? false;
  }

  void _handleBarcodeScanned(String? scannedBarcode, String? expectedBarcode, BuildContext context) {
    if (scannedBarcode == null) return;
    
    _qrController?.dispose();
    
    // Verify the scanned barcode
    if (expectedBarcode != null && scannedBarcode == expectedBarcode) {
      _showSuccessSnackBar('Barcode verified successfully! ✅');
      Navigator.of(context).pop(true);
    } else if (expectedBarcode == null) {
      // If no expected barcode, just record the scan
      _showSuccessSnackBar('Barcode scanned successfully! ✅');
      Navigator.of(context).pop(true);
    } else {
      _showErrorSnackBar('Barcode mismatch! Expected: $expectedBarcode, Scanned: $scannedBarcode');
      // Don't close the dialog, let user try again
    }
  }

  Future<void> _sendOTP(dynamic item, String itemType) async {
    try {
      // TODO: Implement OTP sending functionality
      _showSuccessSnackBar('OTP sent to customer successfully!');
    } catch (e) {
      _showErrorSnackBar('Error sending OTP: $e');
    }
  }

  Future<void> _verifyOTP(dynamic item, String itemType) async {
    // Show OTP input dialog
    final otpController = TextEditingController();

    final result = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Enter OTP'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Please enter the OTP received by the customer:'),
            SizedBox(height: 16),
            TextField(
              controller: otpController,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(
                labelText: 'OTP',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.security),
              ),
              maxLength: 6,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: Text('Verify'),
          ),
        ],
      ),
    );

    if (result == true && otpController.text.isNotEmpty) {
      try {
        // TODO: Implement OTP verification functionality
        _showSuccessSnackBar('OTP verified successfully!');
      } catch (e) {
        _showErrorSnackBar('Error verifying OTP: $e');
      }
    }
  }

  Future<void> _approveOrder(dynamic order) async {
    try {
      final response = await _apiService.approveOrder(widget.authToken, order['id'].toString());
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

  Future<void> _approveExchange(dynamic exchange) async {
    try {
      final response = await _apiService.approveExchange(widget.authToken, exchange['id'].toString());
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

  Future<void> _markOutForDelivery(dynamic item, String itemType) async {
    // Get expected barcode based on item type
    String? expectedBarcode;
    String productName = 'Product';

    if (itemType == 'orders') {
      if (item['order_items'] != null && item['order_items'].isNotEmpty) {
        expectedBarcode = item['order_items'][0]['product']?['barcode'];
        productName = item['order_items'][0]['product']?['name'] ?? 'Product';
      }
    } else if (itemType == 'exchanges') {
      if (item['exchange_product'] != null) {
        expectedBarcode = item['exchange_product']['barcode'];
        productName = item['exchange_product']['name'] ?? 'Exchange Product';
      } else if (item['original_product'] != null) {
        expectedBarcode = item['original_product']['barcode'];
        productName = item['original_product']['name'] ?? 'Original Product';
      }
    } else if (itemType == 'cancelled_items') {
      if (item['product'] != null) {
        expectedBarcode = item['product']['barcode'];
        productName = item['product']['name'] ?? 'Product';
      }
    }

    // Show scan product dialog first
    final scanResult = await _showBarcodeScanDialog(item, itemType, expectedBarcode, productName);
    if (scanResult == true) {
      // Product scanned successfully, now mark as out for delivery
      try {
        // Show loading dialog
        showDialog(
          context: context,
          barrierDismissible: false,
          builder: (context) => AlertDialog(
            content: Row(
              children: [
                CircularProgressIndicator(),
                SizedBox(width: 16),
                Text('Updating status...'),
              ],
            ),
          ),
        );

        Map<String, dynamic> response;
        if (itemType == 'orders') {
          // Update order table status to 'out_for_delivery'
          response = await _apiService.markOrderOutForDelivery(widget.authToken, item['id'].toString());
        } else if (itemType == 'exchanges') {
          // Update exchange table status to 'out_for_delivery'
          response = await _apiService.markExchangeOutForDelivery(widget.authToken, item['id'].toString());
        } else if (itemType == 'cancelled_items') {
          // Update order_item table status to 'out_for_delivery' for cancelled items
          response = await _apiService.markCancelledItemOutForDelivery(widget.authToken, item['id'].toString());
        } else {
          Navigator.of(context).pop(); // Close loading dialog
          _showErrorSnackBar('Invalid item type for out for delivery');
          return;
        }

        Navigator.of(context).pop(); // Close loading dialog

        if (response['success']) {
          _showSuccessSnackBar('${_getItemTypeDisplay(itemType)} marked as out for delivery');
          _loadData();
        } else {
          _showErrorSnackBar(response['error'] ?? 'Failed to mark as out for delivery');
        }
      } catch (e) {
        Navigator.of(context).pop(); // Close loading dialog
        _showErrorSnackBar('Error marking as out for delivery: $e');
      }
    }
  }

  Future<void> _markDelivered(dynamic item, String itemType) async {
    // Show OTP verification dialog
    final otpResult = await _showOTPVerificationDialog(item, itemType);
    if (otpResult == true) {
      // OTP verified successfully, now mark as delivered
      try {
        // Show loading dialog
        showDialog(
          context: context,
          barrierDismissible: false,
          builder: (context) => AlertDialog(
            content: Row(
              children: [
                CircularProgressIndicator(),
                SizedBox(width: 16),
                Text('Marking as delivered...'),
              ],
            ),
          ),
        );

        Map<String, dynamic> response;
        if (itemType == 'orders') {
          // Update order table status to 'delivered'
          response = await _apiService.markOrderDelivered(widget.authToken, item['id'].toString());
        } else if (itemType == 'exchanges') {
          // Update exchange table status to 'delivered'
          response = await _apiService.markExchangeDelivered(widget.authToken, item['id'].toString());
        } else if (itemType == 'cancelled_items') {
          // Update order_item table status to 'delivered' for cancelled items
          response = await _apiService.markCancelledItemDelivered(widget.authToken, item['id'].toString());
        } else {
          Navigator.of(context).pop(); // Close loading dialog
          _showErrorSnackBar('Invalid item type for delivery');
          return;
        }

        Navigator.of(context).pop(); // Close loading dialog

        if (response['success']) {
          _showSuccessSnackBar('${_getItemTypeDisplay(itemType)} marked as delivered successfully');
          _loadData();
        } else {
          _showErrorSnackBar(response['error'] ?? 'Failed to mark as delivered');
        }
      } catch (e) {
        Navigator.of(context).pop(); // Close loading dialog
        _showErrorSnackBar('Error marking as delivered: $e');
      }
    }
  }


  Future<bool> _showOTPVerificationDialog(dynamic item, String itemType) async {
    final otpController = TextEditingController();
    bool isSendingOTP = false;
    bool isVerifyingOTP = false;
    bool otpSent = false;

    // Get customer phone number
    String? customerPhone = item['customer']?['phone'];
    String customerName = item['customer']?['name'] ?? 'Customer';

    // Automatically send OTP when dialog opens
    Future<void> _sendInitialOTP() async {
      setState(() {
        isSendingOTP = true;
      });

      try {
        final response = await _apiService.sendDeliveryOTP(
            widget.authToken,
            item['id'].toString(),
            itemType
        );

        if (response['success']) {
          setState(() {
            otpSent = true;
          });
          _showSuccessSnackBar('OTP sent to customer successfully');
        } else {
          _showErrorSnackBar(response['error'] ?? 'Failed to send OTP');
        }
      } catch (e) {
        _showErrorSnackBar('Error sending OTP: $e');
      } finally {
        setState(() {
          isSendingOTP = false;
        });
      }
    }

    return await showDialog<bool>(
        context: context,
        barrierDismissible: false,
        builder: (context) => StatefulBuilder(
            builder: (context, setState) {
              // Send OTP automatically when dialog opens
              WidgetsBinding.instance.addPostFrameCallback((_) {
                if (!otpSent && !isSendingOTP) {
                  _sendInitialOTP();
                }
              });

              return AlertDialog(
                title: Text('Delivery OTP Verification'),
                content: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.security, size: 64, color: Colors.orange),
                    SizedBox(height: 16),
                    if (isSendingOTP) ...[
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          ),
                          SizedBox(width: 12),
                          Text(
                            'Sending OTP...',
                            style: TextStyle(
                                fontSize: 16, fontWeight: FontWeight.w500),
                          ),
                        ],
                      ),
                    ] else
                      if (otpSent) ...[
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.check_circle, color: Colors.green,
                                size: 20),
                            SizedBox(width: 8),
                            Text(
                              'OTP sent successfully!',
                              style: TextStyle(fontSize: 16,
                                  fontWeight: FontWeight.w500,
                                  color: Colors.green),
                            ),
                          ],
                        ),
                        SizedBox(height: 16),
                        Text(
                          'OTP has been sent to:',
                          style: TextStyle(fontSize: 14, color: Colors
                              .grey[600]),
                        ),
                        SizedBox(height: 4),
                        Text(
                          customerName,
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight
                              .bold),
                        ),
                        if (customerPhone != null) ...[
                          SizedBox(height: 4),
                          Text(
                            customerPhone,
                            style: TextStyle(
                                fontSize: 14, color: Colors.grey[600]),
                          ),
                        ],
                      ] else
                        ...[
                          Text(
                            'Preparing to send OTP...',
                            style: TextStyle(
                                fontSize: 16, fontWeight: FontWeight.w500),
                          ),
                        ],
                    SizedBox(height: 16),
                    if (otpSent) ...[
                      Text(
                        'Please enter the 6-digit OTP received by the customer:',
                        style: TextStyle(fontSize: 14),
                        textAlign: TextAlign.center,
                      ),
                    ],
                    if (otpSent) ...[
                      SizedBox(height: 16),
                      TextField(
                        controller: otpController,
                        keyboardType: TextInputType.number,
                        decoration: InputDecoration(
                          labelText: 'OTP',
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.security),
                          hintText: 'Enter 6-digit OTP',
                        ),
                        maxLength: 6,
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 2,
                        ),
                      ),
                      SizedBox(height: 8),
                      TextButton.icon(
                        onPressed: isSendingOTP ? null : () async {
                          setState(() {
                            isSendingOTP = true;
                          });

                          try {
                            // Send OTP to customer
                            final response = await _apiService.sendDeliveryOTP(
                                widget.authToken,
                                item['id'].toString(),
                                itemType
                            );

                            if (response['success']) {
                              _showSuccessSnackBar(
                                  'OTP sent to customer successfully');
                            } else {
                              _showErrorSnackBar(
                                  response['error'] ?? 'Failed to send OTP');
                            }
                          } catch (e) {
                            _showErrorSnackBar('Error sending OTP: $e');
                          } finally {
                            setState(() {
                              isSendingOTP = false;
                            });
                          }
                        },
                        icon: isSendingOTP
                            ? SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                            : Icon(Icons.send),
                        label: Text(isSendingOTP ? 'Sending...' : 'Resend OTP'),
                      ),
                    ],
                  ],
                ),
                actions: [
                  TextButton(
                    onPressed: () => Navigator.of(context).pop(false),
                    child: Text('Cancel'),
                  ),
                  if (otpSent)
                    ElevatedButton.icon(
                      onPressed: isVerifyingOTP ? null : () async {
                        if (otpController.text.length != 6) {
                          _showErrorSnackBar(
                              'Please enter a valid 6-digit OTP');
                          return;
                        }

                        setState(() {
                          isVerifyingOTP = true;
                        });

                        try {
                          // Verify OTP
                          final response = await _apiService.verifyDeliveryOTP(
                              widget.authToken,
                              item['id'].toString(),
                              itemType,
                              otpController.text
                          );

                          if (response['success']) {
                            _showSuccessSnackBar('OTP verified successfully!');
                            Navigator.of(context).pop(true);
                          } else {
                            _showErrorSnackBar(response['error'] ??
                                'Invalid OTP');
                          }
                        } catch (e) {
                          _showErrorSnackBar('Error verifying OTP: $e');
                        } finally {
                          setState(() {
                            isVerifyingOTP = false;
                          });
                        }
                      },
                      icon: isVerifyingOTP
                          ? SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                          : Icon(Icons.verified),
                      label: Text(
                          isVerifyingOTP ? 'Verifying...' : 'Verify OTP'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green,
                        foregroundColor: Colors.white,
                      ),
                    ),
                ],
              );
            }
              ),
              ) ?? false;
            }

            Future<void> _rejectItem(dynamic item, String itemType) async {
    final reason = await _showRejectionReasonDialog();
    if (reason == null) return;

    try {
    Map<String, dynamic> response;
    if (itemType == 'orders') {
    response = await _apiService.rejectOrder(widget.authToken, item['id'].toString(), reason);
    } else if (itemType == 'exchanges') {
    response = await _apiService.rejectExchange(widget.authToken, item['id'].toString(), reason);
    } else {
    _showErrorSnackBar('Cannot reject this item type');
    return;
    }

    if (response['success']) {
    _showSuccessSnackBar('${_getItemTypeDisplay(itemType)} rejected successfully');
    _loadData();
    } else {
    _showErrorSnackBar(response['error'] ?? 'Failed to reject ${_getItemTypeDisplay(itemType)}');
    }
    } catch (e) {
    _showErrorSnackBar('Error rejecting ${_getItemTypeDisplay(itemType)}: $e');
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

    Future<void> _sendApprove(dynamic item, String itemType) async {
      try {
        // Show loading dialog
        showDialog(
          context: context,
          barrierDismissible: false,
          builder: (context) => AlertDialog(
            content: Row(
              children: [
                CircularProgressIndicator(),
                SizedBox(width: 16),
                Text('Approving...'),
              ],
            ),
          ),
        );

        Map<String, dynamic> response;
        if (itemType == 'orders') {
          response = await _apiService.approveOrder(widget.authToken, item['id'].toString());
        } else if (itemType == 'exchanges') {
          response = await _apiService.approveExchange(widget.authToken, item['id'].toString());
        } else {
          Navigator.of(context).pop(); // Close loading dialog
          _showErrorSnackBar('Cannot approve this item type');
          return;
        }

        Navigator.of(context).pop(); // Close loading dialog

        if (response['success']) {
          _showSuccessSnackBar('${_getItemTypeDisplay(itemType)} approved successfully');
          _loadData();
        } else {
          _showErrorSnackBar(response['error'] ?? 'Failed to approve ${_getItemTypeDisplay(itemType)}');
        }
      } catch (e) {
        Navigator.of(context).pop(); // Close loading dialog
        _showErrorSnackBar('Error approving ${_getItemTypeDisplay(itemType)}: $e');
      }
    }

    Future<void> _rejectorder(dynamic item, String itemType) async {
      final reason = await _showRejectionReasonDialog();
      if (reason == null || reason.trim().isEmpty) return;

      try {
        // Show loading dialog
        showDialog(
          context: context,
          barrierDismissible: false,
          builder: (context) => AlertDialog(
            content: Row(
              children: [
                CircularProgressIndicator(),
                SizedBox(width: 16),
                Text('Rejecting...'),
              ],
            ),
          ),
        );

        Map<String, dynamic> response;
        if (itemType == 'orders') {
          response = await _apiService.rejectOrder(widget.authToken, item['id'].toString(), reason);
        } else if (itemType == 'exchanges') {
          response = await _apiService.rejectExchange(widget.authToken, item['id'].toString(), reason);
        } else {
          Navigator.of(context).pop(); // Close loading dialog
          _showErrorSnackBar('Cannot reject this item type');
          return;
        }

        Navigator.of(context).pop(); // Close loading dialog

        if (response['success']) {
          _showSuccessSnackBar('${_getItemTypeDisplay(itemType)} rejected successfully');
          _loadData();
        } else {
          _showErrorSnackBar(response['error'] ?? 'Failed to reject ${_getItemTypeDisplay(itemType)}');
        }
      } catch (e) {
        Navigator.of(context).pop(); // Close loading dialog
        _showErrorSnackBar('Error rejecting ${_getItemTypeDisplay(itemType)}: $e');
      }
    }
  }
