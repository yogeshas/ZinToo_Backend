
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:convert';
import 'dart:typed_data';
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:http/http.dart' as http;
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
  final String _baseUrl = 'http://172.31.31.194:5000';

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

  // Delivery slider and photo upload
  final ImagePicker _imagePicker = ImagePicker();
  Map<int, bool> _deliverySliders = {}; // Track slider state for each item

  // Barcode scanning and verification
  String? _scannedBarcode;
  bool _isVerifyingBarcode = false;
  Map<int, bool> _barcodeVerified = {}; // Track verification status for each item
  Map<int, Map<String, dynamic>> _productImages = {}; // Store captured product images

  @override
  void initState() {
    super.initState();
    // Initialize barcode verification state
    _barcodeVerified.clear();
    _productImages.clear();
    _tabController = TabController(length: 5, vsync: this);
    _tabController.addListener(_onTabChanged);
    _loadData();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _tabController.dispose();
    _scrollController.dispose();
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
      // Reset barcode verification state when reloading data
      _barcodeVerified.clear();
      _productImages.clear();
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
        print("🔍 DEBUG: Orders loaded: ${response['orders']?.length ?? 0} orders");
        for (var order in response['orders'] ?? []) {
          print("🔍 DEBUG: Order - ID: ${order['id']}, Status: '${order['status']}'");
          print("🔍 DEBUG: Order items count: ${order['order_items']?.length ?? 0}");
          if (order['order_items'] != null && order['order_items'].isNotEmpty) {
            print("🔍 DEBUG: First order item: ${order['order_items'][0]}");
          }
        }
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
        // Filter exchanges to only show assigned status
        final allExchanges = response['exchanges'] ?? [];
        print("🔍 DEBUG: All exchanges count: ${allExchanges.length}");

        for (var exchange in allExchanges) {
          print("🔍 DEBUG: Exchange ID: ${exchange['id']}, Status: '${exchange['status']}'");
          print("🔍 DEBUG: Exchange customer data: ${exchange['customer']}");
          print("🔍 DEBUG: Exchange order data: ${exchange['order']}");
        }

        final assignedExchanges = allExchanges.where((exchange) {
          String status = exchange['status']?.toString().toLowerCase() ?? '';
          print("🔍 DEBUG: Checking exchange ${exchange['id']} with status '$status'");
          // Show exchanges that are assigned, approved, or out for delivery
          return ['assigned', 'approved', 'out_for_delivery', 'delivered'].contains(status);
        }).toList();

        print("🔍 DEBUG: Assigned exchanges count: ${assignedExchanges.length}");

        setState(() {
          _exchanges = assignedExchanges;
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
        print("🔍 DEBUG: Cancelled items loaded: ${response['cancelled_items']?.length ?? 0} items");
        for (var item in response['cancelled_items'] ?? []) {
          print("🔍 DEBUG: Cancelled item - ID: ${item['id']}, Status: ${item['status']}, Order ID: ${item['order_id']}");
        }

        // Show all cancelled items (they are already filtered by backend)
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
        print("🔍 DEBUG: Approved items loaded: ${response['approved_items']?.length ?? 0} items");
        for (var item in response['approved_items'] ?? []) {
          print("🔍 DEBUG: Approved item - ID: ${item['id']}, Status: '${item['status']}', Type: ${item['type']}");
        }
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
        print("🔍 DEBUG: Rejected items loaded: ${response['rejected_items']?.length ?? 0} items");
        for (var item in response['rejected_items'] ?? []) {
          print("🔍 DEBUG: Rejected item - ID: ${item['id']}, Type: ${item['type']}, Status: ${item['status']}, Order ID: ${item['order_id']}");
        }
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

      backgroundColor: Colors.white,
      appBar: TabBar(
        controller: _tabController,
        indicatorColor: Colors.black,
        labelColor: Colors.black,
        unselectedLabelColor: Colors.black,
        isScrollable: true,
        tabAlignment: TabAlignment.start, // Align tabs to start (removes left space)
        padding: EdgeInsets.zero,         // Removes start padding from TabBar itself (Flutter 3.7+)
        labelPadding: EdgeInsets.all(10),    // Removes padding between individual tabs
        tabs: [
          Tab(text: 'Orders', icon: Icon(Icons.shopping_bag)),
          Tab(text: 'Exchanges', icon: Icon(Icons.swap_horiz)),
          Tab(text: 'Cancelled', icon: Icon(Icons.cancel)),
          Tab(text: 'Approved', icon: Icon(Icons.check_circle)),
          Tab(text: 'Rejected', icon: Icon(Icons.close)),
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
      color: Colors.white,
      margin: EdgeInsets.only(bottom: 12),
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Column(
        children: [
          // Main Order Row - Clean Single Row Design
          Container(
            padding: EdgeInsets.all(16),
            child: Row(
              children: [
                // Product Image
                Container(
                  width: 60,
                  height: 60,
            decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.grey[300]!, width: 1),
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: _buildProductImage(item, itemType),
                  ),
                ),
                SizedBox(width: 12),
                
                // Order Details
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Order ID and Status
                      Row(
                    children: [
                      Text(
                        '${_getItemTypeDisplay(itemType)} #${_getOrderNumber(item, itemType)}',
                        style: TextStyle(
                              fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Colors.blue[800],
                        ),
                          ),
                          Spacer(),
                          Container(
                            padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: _getStatusColor(item['status']).withOpacity(0.1),
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(
                                color: _getStatusColor(item['status']),
                                width: 1,
                              ),
                            ),
                            child: Text(
                              item['status']?.toString().toUpperCase() ?? 'UNKNOWN',
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                                color: _getStatusColor(item['status']),
                              ),
                            ),
                          ),
                        ],
                      ),
                      SizedBox(height: 4),
                      
                      // Product Name
                      Text(
                        _getProductName(item, itemType),
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          color: Colors.grey[800],
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      SizedBox(height: 4),
                      
                      // Product Details Row
                      _buildProductDetailsRow(item, itemType),
                      
                      SizedBox(height: 8),
                      
                      // Customer and Amount Row
                      Row(
                        children: [
                          Icon(Icons.person, size: 14, color: Colors.grey[600]),
                          SizedBox(width: 4),
                          Expanded(
                            child: Text(
                              _getCustomerName(item, itemType),
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey[600],
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          if (item['total_amount'] != null) ...[
                        Text(
                          '₹${item['total_amount'].toStringAsFixed(2)}',
                          style: TextStyle(
                            fontSize: 16,
                            color: Colors.green[700],
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                          ],
                        ],
                      ),
                    ],
                  ),
                ),
                
                // Action Button
                Column(
                  children: [
                    IconButton(
                      onPressed: () {
                        setState(() {
                          _expandedItems[item['id']] = !isExpanded;
                        });
                      },
                      icon: Icon(
                        isExpanded ? Icons.expand_less : Icons.expand_more,
                        color: Colors.blue[600],
                      ),
                    ),
                    if (item['customer']?['phone'] != null)
                      IconButton(
                        onPressed: () => _makePhoneCall(item['customer']['phone']),
                        icon: Icon(Icons.phone, color: Colors.green[600], size: 20),
                        tooltip: 'Call Customer',
                      ),
                    ],
                  ),
              ],
            ),
          ),
          
          // Expanded Details Section
          if (isExpanded)
            Container(
              width: double.infinity,
              decoration: BoxDecoration(
                color: Colors.grey[50],
                borderRadius: BorderRadius.only(
                  bottomLeft: Radius.circular(12),
                  bottomRight: Radius.circular(12),
                ),
              ),
              child: _buildExpandedDetails(item, itemType),
            ),
        ],
      ),
    );
  }

  // Build product details row for main card display
  Widget _buildProductDetailsRow(dynamic item, String itemType) {
    List<Widget> details = [];
    
    // Get product information based on item type
    String? productName;
    String? barcode;
    int? quantity;
    String? color;
    String? size;
    double? price;

    if (itemType == 'orders') {
      if (item['order_items'] != null && item['order_items'].isNotEmpty) {
        final orderItem = item['order_items'][0];
        productName = orderItem?['product']?['name'];
        barcode = orderItem?['product']?['barcode'];
        quantity = orderItem?['quantity'];
        color = orderItem?['color'];
        size = orderItem?['size'];
        price = orderItem?['product']?['price']?.toDouble();
      }
    } else if (itemType == 'exchanges') {
      if (item['exchange_product'] != null) {
        productName = item['exchange_product']['name'];
        barcode = item['exchange_product']['barcode'];
        quantity = 1;
        color = item['exchange_product']['color'];
        size = item['exchange_product']['size'];
        price = item['exchange_product']['price']?.toDouble();
      } else if (item['original_product'] != null) {
        productName = item['original_product']['name'];
        barcode = item['original_product']['barcode'];
        quantity = 1;
        color = item['original_product']['color'];
        size = item['original_product']['size'];
        price = item['original_product']['price']?.toDouble();
      }
    } else if (itemType == 'cancelled_items') {
      if (item['product'] != null) {
        productName = item['product']['name'];
        barcode = item['product']['barcode'];
        quantity = item['quantity'];
        color = item['color'];
        size = item['size'];
        price = item['product']['price']?.toDouble();
      }
    }

    // Add quantity
    if (quantity != null) {
      details.add(
        Container(
          padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
          decoration: BoxDecoration(
            color: Colors.blue[100],
            borderRadius: BorderRadius.circular(8),
          ),
          child: Text(
            'Qty: $quantity',
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.bold,
              color: Colors.blue[800],
            ),
          ),
        ),
      );
    }

    // Add color
    if (color != null && color.isNotEmpty) {
      details.add(
        Container(
          padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
          decoration: BoxDecoration(
            color: _getColorFromString(color).withOpacity(0.2),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: _getColorFromString(color), width: 1),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 8,
                height: 8,
                decoration: BoxDecoration(
                  color: _getColorFromString(color),
                  shape: BoxShape.circle,
                ),
              ),
              SizedBox(width: 4),
              Text(
                color.toUpperCase(),
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  color: _getColorFromString(color),
                ),
              ),
            ],
          ),
        ),
      );
    }

    // Add size
    if (size != null && size.isNotEmpty) {
      details.add(
        Container(
          padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
          decoration: BoxDecoration(
            color: Colors.grey[100],
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.grey[400]!, width: 1),
          ),
          child: Text(
            'Size: $size',
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.bold,
              color: Colors.grey[700],
            ),
          ),
        ),
      );
    }

    // Add price
    if (price != null) {
      details.add(
        Container(
          padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
          decoration: BoxDecoration(
            color: Colors.green[100],
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.green[400]!, width: 1),
          ),
          child: Text(
            '₹${price.toStringAsFixed(0)}',
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.bold,
              color: Colors.green[700],
            ),
          ),
        ),
      );
    }

    // Special handling for cancelled items
    if (itemType == 'cancelled_items') {
      details.add(
        Container(
          padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
          decoration: BoxDecoration(
            color: Colors.red[100],
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.red[400]!, width: 1),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.cancel, size: 10, color: Colors.red[600]),
              SizedBox(width: 2),
              Text(
                'CANCELLED',
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  color: Colors.red[700],
                ),
              ),
            ],
          ),
        ),
      );
    }

    return Wrap(
      spacing: 4,
      runSpacing: 4,
      children: details,
    );
  }

  // Helper function to check status with multiple case variations
  bool _isStatus(dynamic item, List<String> statuses) {
    String status = item['status']?.toString().toLowerCase() ?? '';
    return statuses.contains(status);
  }

  List<Widget> _buildActionButtons(dynamic item, String itemType) {
    List<Widget> buttons = [];
    String status = item['status']?.toString().toLowerCase() ?? '';
    print("🔍 DEBUG: Item ID: ${item['id']}, Status: '${item['status']}' -> '$status', Type: $itemType");

    // Show buttons based on status and item type
    if (itemType == 'orders') {
      // Approve button for pending/assigned orders
      if (_isStatus(item, ['pending', 'assigned'])) {
        buttons.add(
          ElevatedButton.icon(
            onPressed: () => _approveOrder(item),
            icon: Icon(Icons.check, size: 16),
            label: Text('Approve'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.green,
              foregroundColor: Colors.white,
            ),
          ),
        );
      }

      // Out for Delivery button for shipped/approved/confirmed orders
      if (_isStatus(item, ['shipped', 'approved', 'confirmed'])) {
        buttons.add(
          ElevatedButton.icon(
            onPressed: () => _markOutForDelivery(item, itemType),
            icon: Icon(Icons.local_shipping, size: 16),
            label: Text('Out for Delivery'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.orange,
              foregroundColor: Colors.white,
            ),
          ),
        );
      }

    }

    if (itemType == 'exchanges') {
      // Approve button for pending/assigned exchanges
      if (_isStatus(item, ['pending', 'assigned'])) {
        buttons.add(
          ElevatedButton.icon(
            onPressed: () => _approveExchange(item),
            icon: Icon(Icons.check, size: 16),
            label: Text('Approve'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.green,
              foregroundColor: Colors.white,
            ),
          ),
        );
      }

      // Out for Delivery button for shipped/approved/confirmed exchanges
      if (_isStatus(item, ['shipped', 'approved', 'confirmed'])) {
        buttons.add(
          ElevatedButton.icon(
            onPressed: () => _markOutForDelivery(item, itemType),
            icon: Icon(Icons.local_shipping, size: 16),
            label: Text('Out for Delivery'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.orange,
              foregroundColor: Colors.white,
            ),
          ),
        );
      }

    }

    if (itemType == 'cancelled_items') {
      // Out for Delivery button for assigned cancelled items
      if (_isStatus(item, ['assigned'])) {
        buttons.add(
          ElevatedButton.icon(
            onPressed: () => _markOutForDelivery(item, itemType),
            icon: Icon(Icons.local_shipping, size: 16),
            label: Text('Out for Delivery'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.orange,
              foregroundColor: Colors.white,
            ),
          ),
        );
      }

      // Mark as Returned button for out_for_returning cancelled items
      if (_isStatus(item, ['out_for_returning'])) {
        buttons.add(
          ElevatedButton.icon(
            onPressed: () => _markAsReturned(item, itemType),
            icon: Icon(Icons.assignment_returned, size: 16),
            label: Text('Mark as Returned'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.green,
              foregroundColor: Colors.white,
            ),
          ),
        );
      }

    }

    // Reject button for pending/assigned items (except cancelled items)
    if ((itemType == 'orders' || itemType == 'exchanges') &&
        _isStatus(item, ['pending', 'assigned', 'confirmed'])) {
      if (buttons.isNotEmpty) buttons.add(SizedBox(width: 8));
      buttons.add(
        ElevatedButton.icon(
          onPressed: () => _rejectItem(item, itemType),
          icon: Icon(Icons.close, size: 16),
          label: Text('Reject'),
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.red,
            foregroundColor: Colors.white,
          ),
        ),
      );
    }

    // ADD DELIVERY BUTTON ONLY FOR OUT_FOR_DELIVERY STATUS
    if (_isStatus(item, ['out_for_delivery'])) {
      buttons.add(
        _buildDeliverySlider(item, itemType),
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
    return Container(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Customer Information Section
          _buildCustomerSection(item, itemType),
          
          SizedBox(height: 16),
          
          // Address Section
          _buildAddressSection(item),
          
          SizedBox(height: 16),
          
          // Product Details Section - Enhanced
          _buildEnhancedProductSection(item, itemType),
          
          SizedBox(height: 16),
          
          // OTP Section (for orders and exchanges)
          if (itemType == 'orders' || itemType == 'exchanges')
            _buildOTPSection(item, itemType),
          
          SizedBox(height: 16),
          
          // Action Buttons Section
          _buildActionButtonsSection(item, itemType),
        ],
      ),
    );
  }

  // Build customer section with photo and contact
  Widget _buildCustomerSection(dynamic item, String itemType) {
    return Container(
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.blue[50],
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.blue[200]!, width: 1),
      ),
      child: Row(
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
          
          // Customer Info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _getCustomerName(item, itemType),
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.grey[800],
                      ),
                    ),
                if (item['customer']?['phone'] != null) ...[
                  SizedBox(height: 4),
                  Text(
                    item['customer']['phone'],
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey[600],
                    ),
                  ),
                ],
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
                icon: Icon(Icons.phone, color: Colors.white, size: 20),
                    onPressed: () => _makePhoneCall(item['customer']['phone']),
                    tooltip: 'Call Customer',
                  ),
                ),
            ],
          ),
    );
  }

  // Build enhanced product section with better layout
  Widget _buildEnhancedProductSection(dynamic item, String itemType) {
    return Container(
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.grey[300]!, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.inventory, color: Colors.blue[600], size: 20),
              SizedBox(width: 8),
              Text(
                'Product Details',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Colors.blue[800],
                ),
              ),
            ],
          ),
          SizedBox(height: 12),
          
          // Product Image and Basic Info
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Product Image
              Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.grey[300]!, width: 1),
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: _buildProductImage(item, itemType),
                ),
              ),
              SizedBox(width: 12),
              
              // Product Information
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _getProductName(item, itemType),
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                        color: Colors.grey[800],
                      ),
                    ),
                    SizedBox(height: 8),
                    
                    // Product Details Grid
                    _buildProductDetailsGrid(item, itemType),
                  ],
                ),
              ),
            ],
          ),
          
          // Special sections for different item types
          if (itemType == 'cancelled_items') ...[
            SizedBox(height: 12),
            _buildCancelledItemDetails(item),
          ],
          
          if (itemType == 'exchanges') ...[
            SizedBox(height: 12),
            _buildExchangeItemDetails(item),
          ],
        ],
      ),
    );
  }

  // Build product details in a clean grid format
  Widget _buildProductDetailsGrid(dynamic item, String itemType) {
    List<Map<String, dynamic>> details = [];
    
    // Get product information
    int? quantity;
    String? color;
    String? size;
    double? price;
    String? barcode;

    if (itemType == 'orders') {
      if (item['order_items'] != null && item['order_items'].isNotEmpty) {
        final orderItem = item['order_items'][0];
        quantity = orderItem?['quantity'];
        color = orderItem?['color'];
        size = orderItem?['size'];
        price = orderItem?['product']?['price']?.toDouble();
        barcode = orderItem?['product']?['barcode'];
      }
    } else if (itemType == 'exchanges') {
      if (item['exchange_product'] != null) {
        quantity = 1;
        color = item['exchange_product']['color'];
        size = item['exchange_product']['size'];
        price = item['exchange_product']['price']?.toDouble();
        barcode = item['exchange_product']['barcode'];
      }
    } else if (itemType == 'cancelled_items') {
      quantity = item['quantity'];
      color = item['color'];
      size = item['size'];
      price = item['product']?['price']?.toDouble();
      barcode = item['product']?['barcode'];
    }

    // Add details to list
    if (quantity != null) {
      details.add({'label': 'Quantity', 'value': quantity.toString(), 'icon': Icons.shopping_cart});
    }
    if (color != null && color.isNotEmpty) {
      details.add({'label': 'Color', 'value': color, 'icon': Icons.palette});
    }
    if (size != null && size.isNotEmpty) {
      details.add({'label': 'Size', 'value': size, 'icon': Icons.straighten});
    }
    if (price != null) {
      details.add({'label': 'Price', 'value': '₹${price.toStringAsFixed(0)}', 'icon': Icons.attach_money});
    }
    if (barcode != null && barcode.isNotEmpty) {
      details.add({'label': 'Barcode', 'value': barcode, 'icon': Icons.qr_code});
    }

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: details.map((detail) => _buildDetailChip(detail)).toList(),
    );
  }

  // Build individual detail chip
  Widget _buildDetailChip(Map<String, dynamic> detail) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
        color: Colors.blue[100],
              borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.blue[300]!, width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(detail['icon'], size: 12, color: Colors.blue[700]),
          SizedBox(width: 4),
          Text(
            '${detail['label']}: ${detail['value']}',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: Colors.blue[800],
            ),
          ),
        ],
      ),
    );
  }

  // Build cancelled item specific details
  Widget _buildCancelledItemDetails(dynamic item) {
    return Container(
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.red[50],
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.red[200]!, width: 1),
            ),
            child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
              Icon(Icons.cancel, color: Colors.red[600], size: 18),
              SizedBox(width: 6),
              Text(
                'Cancelled Item - Return to Warehouse',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: Colors.red[700],
                ),
              ),
            ],
          ),
          if (item['reason'] != null) ...[
            SizedBox(height: 8),
            Text(
              'Reason: ${item['reason']}',
              style: TextStyle(
                fontSize: 12,
                color: Colors.red[600],
              ),
            ),
          ],
          SizedBox(height: 8),
          Text(
            'This item needs to be returned to the warehouse. Please collect it from the customer and return it.',
            style: TextStyle(
              fontSize: 11,
              color: Colors.red[600],
              fontStyle: FontStyle.italic,
            ),
          ),
        ],
      ),
    );
  }

  // Build exchange item specific details
  Widget _buildExchangeItemDetails(dynamic item) {
    return Container(
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.orange[50],
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.orange[200]!, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.swap_horiz, color: Colors.orange[600], size: 18),
              SizedBox(width: 6),
              Text(
                'Exchange Details',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: Colors.orange[700],
                ),
              ),
            ],
          ),
          SizedBox(height: 8),
          
          // Original Product
          if (item['original_product'] != null) ...[
            Text(
              'Original Product:',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: Colors.orange[700],
              ),
            ),
            SizedBox(height: 4),
            Text(
              '${item['original_product']['name']} (${item['original_product']['color'] ?? 'N/A'} - ${item['original_product']['size'] ?? 'N/A'})',
              style: TextStyle(
                fontSize: 11,
                color: Colors.orange[600],
              ),
            ),
            SizedBox(height: 8),
          ],
          
          // Exchange Product
          if (item['exchange_product'] != null) ...[
            Text(
              'New Product:',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: Colors.orange[700],
              ),
            ),
            SizedBox(height: 4),
            Text(
              '${item['exchange_product']['name']} (${item['exchange_product']['color'] ?? 'N/A'} - ${item['exchange_product']['size'] ?? 'N/A'})',
              style: TextStyle(
                fontSize: 11,
                color: Colors.orange[600],
              ),
            ),
          ],
          
          if (item['reason'] != null) ...[
            SizedBox(height: 8),
            Text(
              'Reason: ${item['reason']}',
              style: TextStyle(
                fontSize: 11,
                color: Colors.orange[600],
                fontStyle: FontStyle.italic,
              ),
            ),
          ],
        ],
      ),
    );
  }

  // Build action buttons section
  Widget _buildActionButtonsSection(dynamic item, String itemType) {
    return Container(
      padding: EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.green[50],
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.green[200]!, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.delivery_dining, color: Colors.green[700], size: 20),
                    SizedBox(width: 8),
                    Text(
                      'Delivery Actions',
                      style: TextStyle(
                  fontSize: 16,
                        fontWeight: FontWeight.bold,
                  color: Colors.green[800],
                      ),
                    ),
                  ],
                ),
          SizedBox(height: 12),

          // Action Buttons
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: _buildActionButtons(item, itemType),
                ),
        ],
      ),
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

  String _getOrderNumber(dynamic item, String itemType) {
    // For cancelled items, get order number from the order relationship
    if (itemType == 'cancelled_items') {
      if (item['order'] != null && item['order']['order_number'] != null) {
        return item['order']['order_number'].toString();
      }
      if (item['order_id'] != null) {
        return item['order_id'].toString();
      }
      return item['id'].toString(); // Fallback to item ID
    }

    // For exchanges, get order number from order_id field
    if (itemType == 'exchanges') {
      if (item['order_id'] != null) {
        return item['order_id'].toString();
      }
      if (item['order'] != null && item['order']['order_number'] != null) {
        return item['order']['order_number'].toString();
      }
      return item['id'].toString(); // Fallback to exchange ID
    }

    // For other item types, use the direct order_number field
    return item['order_number']?.toString() ?? item['id'].toString();
  }

  String _getCustomerName(dynamic item, String itemType) {
    // For cancelled items, get customer name from the order relationship
    if (itemType == 'cancelled_items') {
      if (item['order'] != null && item['order']['customer'] != null) {
        return item['order']['customer']['name'] ?? 'Unknown Customer';
      }
      if (item['customer'] != null) {
        return item['customer']['name'] ?? 'Unknown Customer';
      }
      return 'Unknown Customer';
    }

    // For exchanges, get customer name directly from the exchange object
    if (itemType == 'exchanges') {
      print("🔍 DEBUG: Exchange customer data: ${item['customer']}");
      if (item['customer'] != null) {
        String customerName = item['customer']['name'] ?? 'Unknown Customer';
        print("🔍 DEBUG: Exchange customer name: $customerName");
        return customerName;
      }
      if (item['order'] != null && item['order']['customer'] != null) {
        String customerName = item['order']['customer']['name'] ?? 'Unknown Customer';
        print("🔍 DEBUG: Exchange customer name from order: $customerName");
        return customerName;
      }
      print("🔍 DEBUG: No customer data found for exchange ${item['id']}");
      return 'Customer Data Not Available';
    }

    // For other item types, use the direct customer field
    return item['customer']?['name'] ?? 'Unknown Customer';
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

    print('🔍 DEBUG: Address section - Item order data: ${item['order']}');
    print('🔍 DEBUG: Address section - Item delivery_address: ${item['delivery_address']}');

    // For exchanges, try to get address from order relationship
    if (item['order'] != null && item['order']['delivery_address'] != null) {
      try {
        // Try to parse JSON address
        if (item['order']['delivery_address'].toString().startsWith('{')) {
          // It's a JSON string, extract readable address
          addressText = _parseAddressFromJson(item['order']['delivery_address']);
        } else {
          // It's a plain text address
          addressText = item['order']['delivery_address'].toString();
        }
      } catch (e) {
        // If parsing fails, use the raw text
        addressText = item['order']['delivery_address'].toString();
      }
    } else if (item['delivery_address'] != null) {
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

  Widget _buildProductInfoSection(dynamic item, String itemType) {
    // Get product information based on item type
    String? productName;
    String? barcode;
    int? quantity;

    if (itemType == 'orders') {
      if (item['order_items'] != null && item['order_items'].isNotEmpty) {
        productName = item['order_items'][0]?['product']?['name'];
        barcode = item['order_items'][0]?['product']?['barcode'];
        quantity = item['order_items'][0]?['quantity'];
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
              Icon(Icons.inventory, color: Colors.blue[600], size: 20),
              SizedBox(width: 8),
              Text(
                'Product Information',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: Colors.blue[800],
                ),
              ),
            ],
          ),
          SizedBox(height: 8),

          // Product Information with Image
          if (productName != null) ...[
            Container(
              width: double.infinity,
              padding: EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(6),
                border: Border.all(color: Colors.grey[300]!),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Product Image on the left
                  Container(
                    width: 80,
                    height: 80,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.grey[300]!),
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: _buildProductImage(item, itemType),
                    ),
                  ),
                  SizedBox(width: 12),
                  // Product Details on the right
                  Expanded(
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
                        // Price information
                        if (_getProductPrice(item, itemType) != null) ...[
                          SizedBox(height: 4),
                          Text(
                            'Price: ₹${_getProductPrice(item, itemType)}',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: Colors.green[700],
                            ),
                          ),
                        ],
                        // Color selection if available
                        if (item['color'] != null) ...[
                          SizedBox(height: 4),
                          Row(
                            children: [
                              Text(
                                'Color: ',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: Colors.grey[600],
                                ),
                              ),
                              Container(
                                width: 16,
                                height: 16,
                                decoration: BoxDecoration(
                                  color: _getColorFromString(item['color']),
                                  shape: BoxShape.circle,
                                  border: Border.all(color: Colors.grey[400]!),
                                ),
                              ),
                              SizedBox(width: 4),
                              Text(
                                item['color'],
                                style: TextStyle(
                                  fontSize: 12,
                                  color: Colors.grey[600],
                                ),
                              ),
                            ],
                          ),
                        ],
                        // Size if available
                        if (item['size'] != null) ...[
                          SizedBox(height: 4),
                          Text(
                            'Size: ${item['size']}',
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.grey[600],
                            ),
                          ),
                        ],
                        // Special handling for cancelled items
                        if (itemType == 'cancelled_items') ...[
                          SizedBox(height: 8),
                          Container(
                            padding: EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: Colors.red[50],
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: Colors.red[200]!),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Icon(Icons.cancel, color: Colors.red[600], size: 18),
                                    SizedBox(width: 6),
                                    Text(
                                      'Cancelled Item',
                                      style: TextStyle(
                                        fontSize: 14,
                                        fontWeight: FontWeight.bold,
                                        color: Colors.red[700],
                                      ),
                                    ),
                                  ],
                                ),
                                if (item['reason'] != null) ...[
                                  SizedBox(height: 6),
                                  Container(
                                    padding: EdgeInsets.all(8),
                                    decoration: BoxDecoration(
                                      color: Colors.white,
                                      borderRadius: BorderRadius.circular(6),
                                      border: Border.all(color: Colors.red[100]!),
                                    ),
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          'Cancellation Reason:',
                                          style: TextStyle(
                                            fontSize: 11,
                                            fontWeight: FontWeight.bold,
                                            color: Colors.red[700],
                                          ),
                                        ),
                                        SizedBox(height: 2),
                                        Text(
                                          item['reason'],
                                          style: TextStyle(
                                            fontSize: 12,
                                            color: Colors.red[600],
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                                if (item['cancelled_at'] != null) ...[
                                  SizedBox(height: 6),
                                  Row(
                                    children: [
                                      Icon(Icons.access_time, color: Colors.red[500], size: 14),
                                      SizedBox(width: 4),
                                      Text(
                                        'Cancelled: ${item['cancelled_at']}',
                                        style: TextStyle(
                                          fontSize: 11,
                                          color: Colors.red[500],
                                        ),
                                      ),
                                    ],
                                  ),
                                ],
                                // Show quantity and total value
                                if (item['quantity'] != null && item['product'] != null && item['product']['price'] != null) ...[
                                  SizedBox(height: 6),
                                  Container(
                                    padding: EdgeInsets.all(8),
                                    decoration: BoxDecoration(
                                      color: Colors.white,
                                      borderRadius: BorderRadius.circular(6),
                                      border: Border.all(color: Colors.red[100]!),
                                    ),
                                    child: Column(
                                      children: [
                                        Row(
                                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                          children: [
                                            Text(
                                              'Quantity: ${item['quantity']}',
                                              style: TextStyle(
                                                fontSize: 12,
                                                fontWeight: FontWeight.bold,
                                                color: Colors.red[700],
                                              ),
                                            ),
                                            Text(
                                              'Value: ₹${(item['quantity'] * item['product']['price']).toStringAsFixed(2)}',
                                              style: TextStyle(
                                                fontSize: 12,
                                                fontWeight: FontWeight.bold,
                                                color: Colors.red[700],
                                              ),
                                            ),
                                          ],
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                                // Additional payment information
                                if (item['additional_payment_required'] == true) ...[
                                  SizedBox(height: 8),
                                  Container(
                                    padding: EdgeInsets.all(8),
                                    decoration: BoxDecoration(
                                      color: Colors.blue[50],
                                      borderRadius: BorderRadius.circular(6),
                                      border: Border.all(color: Colors.blue[200]!),
                                    ),
                                    child: Row(
                                      children: [
                                        Icon(Icons.payment, color: Colors.blue[600], size: 16),
                                        SizedBox(width: 6),
                                        Text(
                                          'Additional Payment Required: ₹${item['additional_amount']?.toStringAsFixed(2) ?? '0.00'}',
                                          style: TextStyle(
                                            fontSize: 12,
                                            fontWeight: FontWeight.bold,
                                            color: Colors.blue[700],
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ],
                            ),
                          ),
                        ],
                        // Special handling for exchange items
                        if (itemType == 'exchanges') ...[
                          SizedBox(height: 50),
                          Container(
                            padding: EdgeInsets.all(12),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.stretch, // make containers full width
                              children: [
                                Row(
                                  children: [
                                    Icon(Icons.swap_horiz, color: Colors.orange[600], size: 18),
                                    SizedBox(width: 6),
                                    Text(
                                      'Exchange Request',
                                      style: TextStyle(
                                        fontSize: 14,
                                        fontWeight: FontWeight.bold,
                                        color: Colors.orange[700],
                                      ),
                                    ),
                                  ],
                                ),
                                SizedBox(height: 14),
                                // FROM container
                                Container(
                                  padding: EdgeInsets.all(8),
                                  decoration: BoxDecoration(
                                    color: Colors.red[50],
                                    borderRadius: BorderRadius.circular(6),
                                    border: Border.all(color: Colors.red[200]!),
                                  ),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        'FROM (Return)',
                                        style: TextStyle(
                                          fontSize: 10,
                                          fontWeight: FontWeight.bold,
                                          color: Colors.red[700],
                                        ),
                                      ),
                                      SizedBox(height: 4),
                                      if (item['original_product'] != null) ...[
                                        Text(
                                          item['original_product']['name'] ?? 'Unknown Product',
                                          style: TextStyle(
                                            fontSize: 11,
                                            fontWeight: FontWeight.bold,
                                            color: Colors.red[600],
                                          ),
                                        ),
                                        if (item['original_product']['price'] != null) ...[
                                          SizedBox(height: 2),
                                          Text(
                                            '₹${item['original_product']['price']}',
                                            style: TextStyle(
                                              fontSize: 10,
                                              color: Colors.red[600],
                                            ),
                                          ),
                                        ],
                                        if (item['original_product']['color'] != null) ...[
                                          SizedBox(height: 2),
                                          Row(
                                            children: [
                                              Container(
                                                width: 12,
                                                height: 12,
                                                decoration: BoxDecoration(
                                                  color: _getColorFromString(item['original_product']['color']),
                                                  shape: BoxShape.circle,
                                                  border: Border.all(color: Colors.grey[400]!),
                                                ),
                                              ),
                                              SizedBox(width: 4),
                                              Text(
                                                item['original_product']['color'],
                                                style: TextStyle(
                                                  fontSize: 10,
                                                  color: Colors.red[600],
                                                ),
                                              ),
                                            ],
                                          ),
                                        ],
                                        if (item['original_product']['size'] != null) ...[
                                          SizedBox(height: 2),
                                          Text(
                                            'Size: ${item['original_product']['size']}',
                                            style: TextStyle(
                                              fontSize: 10,
                                              color: Colors.red[600],
                                            ),
                                          ),
                                        ],
                                        if (item['old_quantity'] != null) ...[
                                          SizedBox(height: 2),
                                          Text(
                                            'Qty: ${item['old_quantity']}',
                                            style: TextStyle(
                                              fontSize: 10,
                                              color: Colors.red[600],
                                            ),
                                          ),
                                        ],
                                      ],
                                    ],
                                  ),
                                ),
                                SizedBox(height: 12),
                                // Arrow row indicating exchange direction
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Icon(Icons.arrow_downward, color: Colors.orange[600], size: 24),
                                  ],
                                ),
                                SizedBox(height: 12),
                                // TO container
                                Container(
                                  padding: EdgeInsets.all(8),
                                  decoration: BoxDecoration(
                                    color: Colors.green[50],
                                    borderRadius: BorderRadius.circular(6),
                                    border: Border.all(color: Colors.green[200]!),
                                  ),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        'TO (New)',
                                        style: TextStyle(
                                          fontSize: 10,
                                          fontWeight: FontWeight.bold,
                                          color: Colors.green[700],
                                        ),
                                      ),
                                      SizedBox(height: 4),
                                      if (item['exchange_product'] != null) ...[
                                        Text(
                                          item['exchange_product']['name'] ?? 'Unknown Product',
                                          style: TextStyle(
                                            fontSize: 11,
                                            fontWeight: FontWeight.bold,
                                            color: Colors.green[600],
                                          ),
                                        ),
                                        if (item['exchange_product']['price'] != null) ...[
                                          SizedBox(height: 2),
                                          Text(
                                            '₹${item['exchange_product']['price']}',
                                            style: TextStyle(
                                              fontSize: 10,
                                              color: Colors.green[600],
                                            ),
                                          ),
                                        ],
                                        if (item['exchange_product']['color'] != null) ...[
                                          SizedBox(height: 2),
                                          Row(
                                            children: [
                                              Container(
                                                width: 12,
                                                height: 12,
                                                decoration: BoxDecoration(
                                                  color: _getColorFromString(item['exchange_product']['color']),
                                                  shape: BoxShape.circle,
                                                  border: Border.all(color: Colors.grey[400]!),
                                                ),
                                              ),
                                              SizedBox(width: 4),
                                              Text(
                                                item['exchange_product']['color'],
                                                style: TextStyle(
                                                  fontSize: 10,
                                                  color: Colors.green[600],
                                                ),
                                              ),
                                            ],
                                          ),
                                        ],
                                        if (item['exchange_product']['size'] != null) ...[
                                          SizedBox(height: 2),
                                          Text(
                                            'Size: ${item['exchange_product']['size']}',
                                            style: TextStyle(
                                              fontSize: 10,
                                              color: Colors.green[600],
                                            ),
                                          ),
                                        ],
                                        if (item['new_quantity'] != null) ...[
                                          SizedBox(height: 2),
                                          Text(
                                            'Qty: ${item['new_quantity']}',
                                            style: TextStyle(
                                              fontSize: 10,
                                              color: Colors.green[600],
                                            ),
                                          ),
                                        ],
                                      ],
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],

                        // Action buttons
                        Wrap(
                          spacing: 8,
                          runSpacing: 4,
                          children: [
                            ElevatedButton.icon(
                              onPressed: () => _printProductImage(item, itemType),
                              icon: Icon(Icons.print, size: 16),
                              label: Text('Print Image', style: TextStyle(fontSize: 12)),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.blue[600],
                                foregroundColor: Colors.white,
                                padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                minimumSize: Size(0, 32),
                              ),
                            ),
                            ElevatedButton.icon(
                              onPressed: () => _scanBarcodeForProduct(item, itemType),
                              icon: Icon(Icons.camera_alt, size: 16),
                              label: Text('Capture Image', style: TextStyle(fontSize: 12)),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.green[600],
                                foregroundColor: Colors.white,
                                padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                minimumSize: Size(0, 32),
                              ),
                            ),
                          ],
                        ),
                        if (_barcodeVerified[item['id']] == true) ...[
                          SizedBox(height: 4),
                          Row(
                            children: [
                              Icon(Icons.check_circle, color: Colors.green, size: 16),
                              SizedBox(width: 4),
                              Text(
                                'Product Image Captured',
                                style: TextStyle(
                                  color: Colors.green[700],
                                  fontSize: 12,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
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
              // Show appropriate button based on status
              if (status == 'approved' || status == 'confirmed' || status == 'out_for_delivery' || status == 'delivered') ...[
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

          SizedBox(height: 8),

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

  Future<void> _markAsReturned(dynamic item, String itemType) async {
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
              Text('Marking as returned...'),
            ],
          ),
        ),
      );

      // Update order_item table status to 'returned' for cancelled items
      final response = await _apiService.markCancelledItemAsReturned(widget.authToken, item['id'].toString());

      Navigator.of(context).pop(); // Close loading dialog

      if (response['success']) {
        _showSuccessSnackBar('Item marked as returned successfully');
        // Reload the cancelled items to reflect the status change
        await _loadCancelledItems();
      } else {
        _showErrorSnackBar(response['error'] ?? 'Failed to mark as returned');
      }
    } catch (e) {
      Navigator.of(context).pop(); // Close loading dialog
      _showErrorSnackBar('Error marking as returned: $e');
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
    bool isVerifyingOTP = false;

    // Get customer phone number
    String? customerPhone = item['customer']?['phone'];
    String customerName = _getCustomerName(item, itemType);

    print("🔍 DEBUG: OTP Dialog - Customer data: ${item['customer']}");
    print("🔍 DEBUG: OTP Dialog - Customer name: $customerName, Phone: $customerPhone");

    return await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (context) => StatefulBuilder(
          builder: (context, setState) {
            return AlertDialog(
              title: Text('Delivery OTP Verification'),
              content: ConstrainedBox(
                constraints: BoxConstraints(
                  maxHeight: MediaQuery.of(context).size.height * 0.5,
                ),
                child: SingleChildScrollView(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.security, size: 40, color: Colors.orange),
                      SizedBox(height: 8),
                      Text(
                        'OTP sent to: $customerName',
                        style: TextStyle(fontSize: 14, color: Colors.grey[600]),
                        textAlign: TextAlign.center,
                      ),
                      if (customerPhone != null) ...[
                        SizedBox(height: 2),
                        Text(
                          customerPhone,
                          style: TextStyle(fontSize: 12, color: Colors.grey[500]),
                        ),
                      ],
                      SizedBox(height: 8),
                      Text(
                        'Enter 6-digit OTP:',
                        style: TextStyle(fontSize: 14),
                        textAlign: TextAlign.center,
                      ),
                      SizedBox(height: 8),
                      TextField(
                        controller: otpController,
                        keyboardType: TextInputType.number,
                        decoration: InputDecoration(
                          labelText: 'OTP',
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.security, size: 20),
                          hintText: 'Enter 6-digit OTP',
                          contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                        ),
                        maxLength: 6,
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 2,
                        ),
                      ),
                      SizedBox(height: 4),
                      TextButton(
                        onPressed: () async {
                          try {
                            // Resend OTP to customer
                            final response = await _apiService.sendDeliveryOTP(
                                widget.authToken,
                                item['id'].toString(),
                                itemType
                            );

                            if (response['success']) {
                              _showSuccessSnackBar('OTP sent to customer successfully');
                            } else {
                              _showErrorSnackBar(response['error'] ?? 'Failed to send OTP');
                            }
                          } catch (e) {
                            _showErrorSnackBar('Error sending OTP: $e');
                          }
                        },
                        child: Text('Resend OTP'),
                      ),
                    ],
                  ),
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(false),
                  child: Text('Cancel'),
                ),
                ElevatedButton(
                  onPressed: isVerifyingOTP ? null : () async {
                    if (otpController.text.length != 6) {
                      _showErrorSnackBar('Please enter a valid 6-digit OTP');
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
                        _showErrorSnackBar(response['error'] ?? 'Invalid OTP');
                      }
                    } catch (e) {
                      _showErrorSnackBar('Error verifying OTP: $e');
                    } finally {
                      setState(() {
                        isVerifyingOTP = false;
                      });
                    }
                  },
                  child: isVerifyingOTP
                      ? SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                      : Text(isVerifyingOTP ? 'Verifying...' : 'Verify'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green,
                    foregroundColor: Colors.white,
                    padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
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

  // Delivery Button Widget (converted from slider)
  Widget _buildDeliverySlider(dynamic item, String itemType) {
    final itemId = item['id'];
    final isDelivered = _deliverySliders[itemId] ?? false;
    final isBarcodeVerified = _barcodeVerified[itemId] ?? false;

    // Check if item has a valid barcode for verification
    final barcode = _getProductBarcode(item, itemType);
    final hasValidBarcode = barcode != 'N/A' && barcode.isNotEmpty;

    // Different text for cancelled items
    String buttonText = isDelivered ? 'Returned!' : 'Mark as Delivered';
    if (itemType == 'cancelled_items') {
      buttonText = isDelivered ? 'Returned!' : 'Mark as Returned';
    }

    return Row(
      children: [
        // Barcode Scan Button
        ElevatedButton.icon(
          onPressed: (isDelivered || !hasValidBarcode) ? null : () => _scanBarcodeForProduct(item, itemType),
          icon: Icon(isBarcodeVerified ? Icons.check_circle : Icons.camera_alt, size: 16),
          label: Text(isBarcodeVerified ? 'Verified' : 'Capture Image'),
          style: ElevatedButton.styleFrom(
            backgroundColor: isBarcodeVerified ? Colors.green : Colors.blue,
            foregroundColor: Colors.white,
            padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
        ),
        SizedBox(width: 8),
        // Delivery Button (only enabled after barcode verification)
        Expanded(
          child: Tooltip(
            message: !hasValidBarcode ? 'Product barcode not available' :
            !isBarcodeVerified ? 'Scan barcode first to enable delivery' :
            isDelivered ? 'Already delivered' : 'Click to deliver',
            child: ElevatedButton.icon(
              onPressed: (isDelivered || !hasValidBarcode || !isBarcodeVerified) ? null : () => _onDeliveryButtonPressed(item, itemType),
              icon: Icon(isDelivered ? Icons.check : Icons.assignment_returned, size: 16),
              label: Text(buttonText),
              style: ElevatedButton.styleFrom(
                backgroundColor: isDelivered ? Colors.green :
                !isBarcodeVerified ? Colors.grey : Colors.orange,
                foregroundColor: Colors.white,
                padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  // Handle delivery button press (only for out_for_delivery items)
  Future<void> _onDeliveryButtonPressed(dynamic item, String itemType) async {
    // Only proceed if product image is captured (replaces barcode verification)
    if (_barcodeVerified[item['id']] == true && _productImages.containsKey(item['id'])) {
      final otpVerified = await _showPhotoUploadDialog(item, itemType);
      if (otpVerified == true) {
        await _markAsDelivered(item, itemType);
        setState(() {
          _deliverySliders[item['id']] = true;
        });
      }
    } else {
      _showErrorSnackBar('Please scan barcode first before delivering');
    }
  }

  // Show delivery verification flow dialog
  Future<bool> _showDeliveryVerificationDialog(dynamic item, String itemType) async {
    return await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(Icons.local_shipping, color: Colors.blue),
            SizedBox(width: 8),
            Text('Delivery Verification Process'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'To complete the delivery, you need to verify the product:',
              style: TextStyle(fontWeight: FontWeight.w500),
            ),
            SizedBox(height: 16),

            // Product Information
            Container(
              padding: EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.blue[50],
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.blue[200]!),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Product: ${_getProductName(item, itemType)}',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  SizedBox(height: 4),
                  Text(
                    'Barcode: ${_getProductBarcode(item, itemType)}',
                    style: TextStyle(color: Colors.blue[700], fontFamily: 'monospace'),
                  ),
                ],
              ),
            ),

            SizedBox(height: 16),

            // Verification Steps
            Text('Verification Steps:', style: TextStyle(fontWeight: FontWeight.w500)),
            SizedBox(height: 8),

            Row(
              children: [
                Icon(Icons.camera_alt, color: Colors.green, size: 20),
                SizedBox(width: 8),
                Expanded(child: Text('1. Take photo of the product')),
              ],
            ),
            SizedBox(height: 4),

            Row(
              children: [
                Icon(Icons.qr_code_scanner, color: Colors.orange, size: 20),
                SizedBox(width: 8),
                Expanded(child: Text('2. Scan product barcode for verification')),
              ],
            ),
            SizedBox(height: 4),

            Row(
              children: [
                Icon(Icons.verified_user, color: Colors.blue, size: 20),
                SizedBox(width: 8),
                Expanded(child: Text('3. Verify OTP with customer')),
              ],
            ),

            SizedBox(height: 16),

            // Important Note
            Container(
              padding: EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.amber[50],
                borderRadius: BorderRadius.circular(4),
                border: Border.all(color: Colors.amber[200]!),
              ),
              child: Row(
                children: [
                  Icon(Icons.info, color: Colors.amber[700], size: 16),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Barcode verification ensures you\'re delivering the correct product to the customer.',
                      style: TextStyle(fontSize: 12, color: Colors.amber[700]),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text('Cancel'),
          ),
          ElevatedButton.icon(
            onPressed: () => Navigator.of(context).pop(true),
            icon: Icon(Icons.play_arrow),
            label: Text('Start Verification'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.green,
              foregroundColor: Colors.white,
            ),
          ),
        ],
      ),
    ) ?? false;
  }

  // Send OTP to customer
  Future<void> _sendDeliveryOTP(dynamic item, String itemType) async {
    try {
      final response = await _apiService.sendDeliveryOTP(
        widget.authToken,
        item['id'].toString(),
        itemType,
      );

      if (response['success']) {
        _showSuccessSnackBar('OTP sent to customer successfully!');
      } else {
        _showErrorSnackBar(response['error'] ?? 'Failed to send OTP');
      }
    } catch (e) {
      _showErrorSnackBar('Error sending OTP: $e');
    }
  }

  // Show photo upload dialog with automatic photo taking and barcode scanning
  Future<bool> _showPhotoUploadDialog(dynamic item, String itemType) async {
    // Only show OTP verification dialog (no camera for delivery)
    await _sendDeliveryOTP(item, itemType);

    // Show OTP verification dialog and return result
    return await _showOTPVerificationDialog(item, itemType);
  }

  // Live barcode verification with camera
  Future<bool> _liveBarcodeVerification(dynamic item, String itemType) async {
    try {
      // Reset verification state first
      setState(() {
        _barcodeVerified[item['id']] = false;
      });

      // Show live camera for barcode scanning
      final XFile? image = await _imagePicker.pickImage(
        source: ImageSource.camera,
        imageQuality: 80,
        maxWidth: 1920,
        maxHeight: 1080,
      );

      if (image != null) {
        // Show loading dialog
        showDialog(
          context: context,
          barrierDismissible: false,
          builder: (context) => AlertDialog(
            content: Row(
              children: [
                CircularProgressIndicator(),
                SizedBox(width: 16),
                Text('Verifying barcode...'),
              ],
            ),
          ),
        );

        // Send image to backend for barcode verification
        final result = await _verifyBarcodeWithBackend(image, item, itemType);

        // Close loading dialog
        Navigator.of(context).pop();

        if (result) {
          setState(() {
            _barcodeVerified[item['id']] = true;
          });
          _showSuccessSnackBar('✅ Barcode verified! Proceeding to delivery...');
          return true;
        } else {
          setState(() {
            _barcodeVerified[item['id']] = false;
          });
          _showErrorSnackBar('❌ Barcode verification failed. Please try again.');
          return false;
        }
      } else {
        // User cancelled
        setState(() {
          _barcodeVerified[item['id']] = false;
        });
        return false;
      }
    } catch (e) {
      print('Live barcode verification error: $e');
      setState(() {
        _barcodeVerified[item['id']] = false;
      });
      _showErrorSnackBar('Error scanning barcode: $e');
      return false;
    }
  }

  // Scan barcode for individual product verification with live detection
  Future<void> _scanBarcodeForProduct(dynamic item, String itemType) async {
    try {
      // Reset verification state first
      setState(() {
        _barcodeVerified[item['id']] = false;
      });

      // Show live camera with barcode detection
      await _showLiveBarcodeScanner(item, itemType);

    } catch (e) {
      print('Barcode scanning error: $e');
      setState(() {
        _barcodeVerified[item['id']] = false;
      });
      _showErrorSnackBar('Error scanning barcode: $e');
    }
  }

  // Simple image capture for product verification
  Future<void> _showLiveBarcodeScanner(dynamic item, String itemType) async {
    try {
      // Show simple camera capture dialog
      await showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => AlertDialog(
          title: Text('Capture Product Image'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.camera_alt, size: 64, color: Colors.blue),
              SizedBox(height: 16),
              Text('Take a photo of the product for verification'),
              SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  ElevatedButton.icon(
                    onPressed: () async {
                      Navigator.of(context).pop();
                      await _captureProductImage(item, itemType);
                    },
                    icon: Icon(Icons.camera_alt),
                    label: Text('Take Photo'),
                  ),
                  ElevatedButton.icon(
                    onPressed: () async {
                      Navigator.of(context).pop();
                      await _pickProductImage(item, itemType);
                    },
                    icon: Icon(Icons.photo_library),
                    label: Text('Gallery'),
                  ),
                ],
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop();
                setState(() {
                  _barcodeVerified[item['id']] = false;
                });
              },
              child: Text('Cancel'),
            ),
          ],
        ),
      );
    } catch (e) {
      _showErrorSnackBar('Error opening camera: $e');
    }
  }

  // Capture product image from camera
  Future<void> _captureProductImage(dynamic item, String itemType) async {
    try {
      final XFile? image = await _imagePicker.pickImage(
        source: ImageSource.camera,
        imageQuality: 80,
        maxWidth: 1920,
        maxHeight: 1080,
      );

      if (image != null) {
        await _processProductImage(image, item, itemType);
      }
    } catch (e) {
      _showErrorSnackBar('Error capturing image: $e');
    }
  }

  // Pick product image from gallery
  Future<void> _pickProductImage(dynamic item, String itemType) async {
    try {
      final XFile? image = await _imagePicker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 80,
        maxWidth: 1920,
        maxHeight: 1080,
      );

      if (image != null) {
        await _processProductImage(image, item, itemType);
      }
    } catch (e) {
      _showErrorSnackBar('Error picking image: $e');
    }
  }

  // Process the captured product image
  Future<void> _processProductImage(XFile image, dynamic item, String itemType) async {
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
              Text('Processing image...'),
            ],
          ),
        ),
      );

      // Read image bytes
      final bytes = await image.readAsBytes();

      // Store the image for this item
      setState(() {
        _productImages[item['id']] = {
          'image': image,
          'bytes': bytes,
          'timestamp': DateTime.now(),
        };
        _barcodeVerified[item['id']] = true; // Mark as verified since we have image
      });

      // Close loading dialog
      Navigator.of(context).pop();

      _showSuccessSnackBar('✅ Product image captured successfully!');

      // Show image preview with order details
      _showImagePreviewDialog(item, itemType, image, bytes);

    } catch (e) {
      // Close loading dialog if open
      Navigator.of(context).pop();
      _showErrorSnackBar('Error processing image: $e');
    }
  }

  // Show image preview with order details
  Future<void> _showImagePreviewDialog(dynamic item, String itemType, XFile image, Uint8List bytes) async {
    await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Product Image Captured'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Product image
              Container(
                height: 200,
                width: double.infinity,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.grey),
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: Image.memory(
                    bytes,
                    fit: BoxFit.cover,
                  ),
                ),
              ),
              SizedBox(height: 16),

              // Order details
              Container(
                padding: EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.grey[100],
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                    ]

                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
            },
            child: Text('Close'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.of(context).pop();
              // Proceed with delivery or exchange
              _proceedWithAction(item, itemType);
            },
            child: Text('Proceed'),
          ),
        ],
      ),
    );
  }

  // Proceed with delivery or exchange action
  void _proceedWithAction(dynamic item, String itemType) {
    if (itemType == 'orders') {
      // Proceed with delivery
      _showSuccessSnackBar('✅ Product verified! You can now proceed with delivery.');
    } else if (itemType == 'exchanges') {
      // Proceed with exchange
      _showSuccessSnackBar('✅ Product verified! You can now proceed with exchange.');
    }
  }

  // Build product image widget
  Widget _buildProductImage(dynamic item, String itemType) {
    // For exchanges, show a comparison of both products
    if (itemType == 'exchanges') {
      return _buildExchangeProductImages(item);
    }

    // Check if we have a captured image for this item
    if (_productImages.containsKey(item['id'])) {
      final imageData = _productImages[item['id']];
      if (imageData != null && imageData['bytes'] != null) {
        return Image.memory(
          imageData['bytes'],
          fit: BoxFit.cover,
          errorBuilder: (context, error, stackTrace) {
            return _buildDefaultProductImage();
          },
        );
      }
    }

    // Try to get product image URL
    final imageUrl = _getProductImageUrl(item, itemType);
    if (imageUrl != null && imageUrl.isNotEmpty && imageUrl != 'null') {
      return Image.network(
        imageUrl,
        fit: BoxFit.cover,
        errorBuilder: (context, error, stackTrace) {
          print('❌ Image load error for $imageUrl: $error');
          return _buildDefaultProductImage();
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
                strokeWidth: 2,
                valueColor: AlwaysStoppedAnimation<Color>(Colors.blue),
              ),
            ),
          );
        },
      );
    }

    return _buildDefaultProductImage();
  }

  // Build exchange product images (both old and new)
  Widget _buildExchangeProductImages(dynamic item) {
    return Row(
      children: [
        // Original product image
        Expanded(
          child: Container(
            height: 80,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.red[300]!, width: 2),
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(6),
              child: _buildSingleProductImage(
                item['original_product']?['image_url'],
                'Original',
                Colors.red[100]!,
              ),
            ),
          ),
        ),
        SizedBox(width: 4),
        // Arrow
        Icon(Icons.arrow_forward, color: Colors.orange[600], size: 16),
        SizedBox(width: 4),
        // Exchange product image
        Expanded(
          child: Container(
            height: 80,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.green[300]!, width: 2),
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(6),
              child: _buildSingleProductImage(
                item['exchange_product']?['image_url'],
                'New',
                Colors.green[100]!,
              ),
            ),
          ),
        ),
      ],
    );
  }

  // Build single product image with label
  Widget _buildSingleProductImage(String? imageUrl, String label, Color backgroundColor) {
    if (imageUrl != null && imageUrl.isNotEmpty && imageUrl != 'null') {
      return Stack(
        children: [
          Image.network(
            imageUrl,
            fit: BoxFit.cover,
            width: double.infinity,
            height: double.infinity,
            errorBuilder: (context, error, stackTrace) {
              return _buildDefaultProductImageWithLabel(label, backgroundColor);
            },
            loadingBuilder: (context, child, loadingProgress) {
              if (loadingProgress == null) return child;
              return Container(
                color: backgroundColor,
                child: Center(
                  child: CircularProgressIndicator(
                    value: loadingProgress.expectedTotalBytes != null
                        ? loadingProgress.cumulativeBytesLoaded / loadingProgress.expectedTotalBytes!
                        : null,
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                  ),
                ),
              );
            },
          ),
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: Container(
              padding: EdgeInsets.symmetric(horizontal: 4, vertical: 2),
              decoration: BoxDecoration(
                color: backgroundColor.withOpacity(0.8),
                borderRadius: BorderRadius.only(
                  bottomLeft: Radius.circular(6),
                  bottomRight: Radius.circular(6),
                ),
              ),
              child: Text(
                label,
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
                textAlign: TextAlign.center,
              ),
            ),
          ),
        ],
      );
    }

    return _buildDefaultProductImageWithLabel(label, backgroundColor);
  }

  // Build default product image with label
  Widget _buildDefaultProductImageWithLabel(String label, Color backgroundColor) {
    return Container(
      color: backgroundColor,
      child: Stack(
        children: [
          Center(
            child: Icon(
              Icons.inventory_2,
              color: Colors.grey[400],
              size: 24,
            ),
          ),
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: Container(
              padding: EdgeInsets.symmetric(horizontal: 4, vertical: 2),
              decoration: BoxDecoration(
                color: backgroundColor.withOpacity(0.8),
                borderRadius: BorderRadius.only(
                  bottomLeft: Radius.circular(6),
                  bottomRight: Radius.circular(6),
                ),
              ),
              child: Text(
                label,
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
                textAlign: TextAlign.center,
              ),
            ),
          ),
        ],
      ),
    );
  }

  // Build default product image placeholder
  Widget _buildDefaultProductImage() {
    return Container(
      color: Colors.grey[200],
      child: Icon(
        Icons.inventory_2,
        color: Colors.grey[400],
        size: 32,
      ),
    );
  }

  // Get product image URL based on item type
  String? _getProductImageUrl(dynamic item, String itemType) {
    String? imageUrl;

    if (itemType == 'orders') {
      if (item['order_items'] != null && item['order_items'].isNotEmpty) {
        imageUrl = item['order_items'][0]?['product']?['image_url'];
      }
    } else if (itemType == 'exchanges') {
      if (item['exchange_product'] != null) {
        imageUrl = item['exchange_product']['image_url'];
      } else if (item['original_product'] != null) {
        imageUrl = item['original_product']['image_url'];
      }
    } else if (itemType == 'cancelled_items') {
      if (item['product'] != null) {
        imageUrl = item['product']['image_url'];
      }
    }

    // Add base URL if imageUrl is not null and doesn't start with http
    if (imageUrl != null && imageUrl.isNotEmpty) {
      if (imageUrl.startsWith('http')) {
        return imageUrl;
      } else {
        return '$_baseUrl/$imageUrl';
      }
    }

    return null;
  }

  // Convert color string to Color object
  Color _getColorFromString(String colorString) {
    switch (colorString.toLowerCase()) {
      case 'red':
        return Colors.red;
      case 'blue':
        return Colors.blue;
      case 'green':
        return Colors.green;
      case 'yellow':
        return Colors.yellow;
      case 'orange':
        return Colors.orange;
      case 'purple':
        return Colors.purple;
      case 'pink':
        return Colors.pink;
      case 'black':
        return Colors.black;
      case 'white':
        return Colors.white;
      case 'grey':
      case 'gray':
        return Colors.grey;
      case 'brown':
        return Colors.brown;
      default:
        return Colors.grey[400]!;
    }
  }

  // Get product price based on item type
  double? _getProductPrice(dynamic item, String itemType) {
    if (itemType == 'orders') {
      if (item['order_items'] != null && item['order_items'].isNotEmpty) {
        return item['order_items'][0]?['product']?['price']?.toDouble();
      }
    } else if (itemType == 'exchanges') {
      if (item['exchange_product'] != null) {
        return item['exchange_product']['price']?.toDouble();
      } else if (item['original_product'] != null) {
        return item['original_product']['price']?.toDouble();
      }
    } else if (itemType == 'cancelled_items') {
      if (item['product'] != null) {
        return item['product']['price']?.toDouble();
      }
    }
    return null;
  }

  // Scan barcode specifically for delivery verification
  Future<bool> _scanBarcodeForDelivery(dynamic item, String itemType) async {
    try {
      // Show barcode scanning dialog first
      final shouldProceed = await _showDeliveryBarcodeDialog(item, itemType);
      if (!shouldProceed) return false;

      // Try to take photo directly - let image_picker handle permissions
      final XFile? image = await _imagePicker.pickImage(
        source: ImageSource.camera,
        imageQuality: 80,
        maxWidth: 1920,
        maxHeight: 1080,
      );

      if (image != null) {
        // Show loading dialog
        showDialog(
          context: context,
          barrierDismissible: false,
          builder: (context) => AlertDialog(
            content: Row(
              children: [
                CircularProgressIndicator(),
                SizedBox(width: 16),
                Text('Verifying barcode...'),
              ],
            ),
          ),
        );

        // Send image to backend for barcode verification
        final result = await _verifyBarcodeWithBackend(image, item, itemType);

        // Close loading dialog
        Navigator.of(context).pop();

        if (result) {
          _showSuccessSnackBar('✅ Barcode verified successfully! Proceeding to delivery photo...');
          return true;
        } else {
          _showErrorSnackBar('❌ Barcode verification failed. The scanned barcode does not match the expected product. Please try again.');
          return false;
        }
      } else {
        // User cancelled or no image - don't show error, just return false
        return false;
      }
    } catch (e) {
      // Check if it's a permission error
      if (e.toString().contains('permission') || e.toString().contains('camera')) {
        _showErrorSnackBar('Camera permission is required. Please enable it in settings.');
      } else {
        _showErrorSnackBar('Error scanning barcode: $e');
      }
      return false;
    }
  }

  // Show delivery barcode scanning dialog
  Future<bool> _showDeliveryBarcodeDialog(dynamic item, String itemType) async {
    return await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(Icons.qr_code_scanner, color: Colors.blue),
            SizedBox(width: 8),
            Text('Verify Product Barcode'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '⚠️ MANDATORY: Scan the product barcode to verify you\'re delivering the correct item:',
              style: TextStyle(fontWeight: FontWeight.bold, color: Colors.red[700]),
            ),
            SizedBox(height: 8),
            Text(
              'This step is required before taking the delivery photo.',
              style: TextStyle(fontWeight: FontWeight.w500, color: Colors.orange[700]),
            ),
            SizedBox(height: 16),

            // Product Information
            Container(
              padding: EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.blue[50],
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.blue[200]!),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Product: ${_getProductName(item, itemType)}',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  SizedBox(height: 4),
                  Text(
                    'Expected Barcode: ${_getProductBarcode(item, itemType)}',
                    style: TextStyle(color: Colors.blue[700], fontFamily: 'monospace'),
                  ),
                ],
              ),
            ),

            SizedBox(height: 16),

            // Instructions
            Text('Instructions:', style: TextStyle(fontWeight: FontWeight.w500)),
            SizedBox(height: 8),

            Row(
              children: [
                Icon(Icons.camera_alt, color: Colors.green, size: 20),
                SizedBox(width: 8),
                Expanded(child: Text('Point camera at the product barcode')),
              ],
            ),
            SizedBox(height: 4),

            Row(
              children: [
                Icon(Icons.visibility, color: Colors.orange, size: 20),
                SizedBox(width: 8),
                Expanded(child: Text('Ensure barcode is clearly visible')),
              ],
            ),
            SizedBox(height: 4),

            Row(
              children: [
                Icon(Icons.check_circle, color: Colors.blue, size: 20),
                SizedBox(width: 8),
                Expanded(child: Text('Barcode will be automatically verified')),
              ],
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text('Cancel'),
          ),
          ElevatedButton.icon(
            onPressed: () => Navigator.of(context).pop(true),
            icon: Icon(Icons.camera_alt),
            label: Text('Capture Image'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.blue,
              foregroundColor: Colors.white,
            ),
          ),
        ],
      ),
    ) ?? false;
  }

  // Take photo automatically
  Future<void> _takePhoto(dynamic item, String itemType) async {
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
              Text('Opening camera...'),
            ],
          ),
        ),
      );

      // Try to take photo directly - let image_picker handle permissions
      final XFile? image = await _imagePicker.pickImage(
        source: ImageSource.camera,
        imageQuality: 80,
        maxWidth: 1920,
        maxHeight: 1080,
      );

      Navigator.of(context).pop(); // Close loading dialog

      if (image != null) {
        // Upload photo to backend
        await _uploadDeliveryPhoto(item, itemType, image);
        _showSuccessSnackBar('Photo captured and uploaded successfully!');
      } else {
        // User cancelled - don't show error
        return;
      }
    } catch (e) {
      Navigator.of(context).pop(); // Close loading dialog
      // Check if it's a permission error
      if (e.toString().contains('permission') || e.toString().contains('camera')) {
        _showErrorSnackBar('Camera permission is required. Please enable it in settings.');
      } else {
        _showErrorSnackBar('Error taking photo: $e');
      }
    }
  }

  // Upload delivery photo
  Future<void> _uploadDeliveryPhoto(dynamic item, String itemType, XFile imageFile) async {
    try {
      final Uint8List imageBytes = await imageFile.readAsBytes();
      final String base64Image = base64Encode(imageBytes);

      // Upload photo to backend
      final response = await ApiService5Tabs.uploadDeliveryPhoto(
        authToken: widget.authToken,
        itemId: item['id'].toString(),
        itemType: itemType,
        imageBase64: base64Image,
      );

      if (response['success']) {
        _showSuccessSnackBar('Delivery photo uploaded successfully!');
      } else {
        _showErrorSnackBar(response['error'] ?? 'Failed to upload photo');
      }
    } catch (e) {
      _showErrorSnackBar('Error uploading photo: $e');
    }
  }

  // Verify OTP and complete delivery
  Future<void> _verifyOTPAndComplete(dynamic item, String itemType) async {
    final otpController = TextEditingController();

    final result = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Verify OTP'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Enter the OTP received by the customer:'),
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
        // Verify OTP
        final response = await _apiService.verifyDeliveryOTP(
          widget.authToken,
          item['id'].toString(),
          itemType,
          otpController.text,
        );

        if (response['success']) {
          // Mark as delivered
          await _markAsDelivered(item, itemType);
        } else {
          _showErrorSnackBar(response['error'] ?? 'Invalid OTP');
        }
      } catch (e) {
        _showErrorSnackBar('Error verifying OTP: $e');
      }
    }
  }

  // Mark item as delivered
  Future<void> _markAsDelivered(dynamic item, String itemType) async {
    try {
      Map<String, dynamic> response;
      if (itemType == 'orders') {
        response = await _apiService.markOrderDelivered(widget.authToken, item['id'].toString());
      } else if (itemType == 'exchanges') {
        response = await _apiService.markExchangeDelivered(widget.authToken, item['id'].toString());
      } else if (itemType == 'cancelled_items') {
        response = await _apiService.markCancelledItemDelivered(widget.authToken, item['id'].toString());
      } else {
        _showErrorSnackBar('Invalid item type for delivery');
        return;
      }

      if (response['success']) {
        String successMessage = '${_getItemTypeDisplay(itemType)} marked as delivered successfully!';
        if (itemType == 'cancelled_items') {
          successMessage = '${_getItemTypeDisplay(itemType)} marked as returned successfully!';
        }
        _showSuccessSnackBar(successMessage);
        _loadData();
      } else {
        _showErrorSnackBar(response['error'] ?? 'Failed to mark as delivered');
      }
    } catch (e) {
      _showErrorSnackBar('Error marking as delivered: $e');
    }
  }

  // Get product image URL based on item type

  // Print product image
  Future<void> _printProductImage(dynamic item, String itemType) async {
    try {
      String? imageUrl = _getProductImageUrl(item, itemType);
      if (imageUrl == null) {
        _showErrorSnackBar('No product image available');
        return;
      }

      // Request storage permission
      var status = await Permission.storage.request();
      if (!status.isGranted) {
        _showErrorSnackBar('Storage permission required for printing');
        return;
      }

      // Download and save image
      final response = await _apiService.downloadImage(imageUrl);
      if (response != null) {
        // Get app directory
        final directory = await getApplicationDocumentsDirectory();
        final file = File('${directory.path}/product_image_${item['id']}.jpg');
        await file.writeAsBytes(response);

        // Show print dialog
        _showPrintDialog(file, item, itemType);
      } else {
        _showErrorSnackBar('Failed to download image');
      }
    } catch (e) {
      _showErrorSnackBar('Error printing image: $e');
    }
  }

  // Show print dialog
  void _showPrintDialog(File imageFile, dynamic item, String itemType) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Print Product Image'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 200,
              height: 200,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.grey[300]!),
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: Image.file(
                  imageFile,
                  fit: BoxFit.cover,
                ),
              ),
            ),
            SizedBox(height: 16),
            Text(
              'Product: ${_getProductName(item, itemType)}',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 8),
            Text(
              'Barcode: ${_getProductBarcode(item, itemType)}',
              style: TextStyle(color: Colors.grey[600]),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.of(context).pop();
              _showSuccessSnackBar('Image ready for printing');
              // Here you would integrate with a printing service
              // For now, we'll just show a success message
            },
            child: Text('Print'),
          ),
        ],
      ),
    );
  }

  // Get product name
  String _getProductName(dynamic item, String itemType) {
    if (itemType == 'orders') {
      if (item['order_items'] != null && item['order_items'].isNotEmpty) {
        return item['order_items'][0]?['product']?['name'] ?? 'N/A';
      }
    } else if (itemType == 'exchanges') {
      return item['exchange_product']?['name'] ?? item['original_product']?['name'] ?? 'N/A';
    } else if (itemType == 'cancelled_items') {
      return item['product']?['name'] ?? 'N/A';
    }
    return 'N/A';
  }

  // Get product barcode
  String _getProductBarcode(dynamic item, String itemType) {
    if (itemType == 'orders') {
      if (item['order_items'] != null && item['order_items'].isNotEmpty) {
        return item['order_items'][0]?['product']?['barcode'] ?? 'N/A';
      }
    } else if (itemType == 'exchanges') {
      return item['exchange_product']?['barcode'] ?? item['original_product']?['barcode'] ?? 'N/A';
    } else if (itemType == 'cancelled_items') {
      return item['product']?['barcode'] ?? 'N/A';
    }
    return 'N/A';
  }

  // Scan barcode using camera
  Future<void> _scanBarcode(dynamic item, String itemType) async {
    try {
      // Show barcode scanning instructions
      final shouldProceed = await _showBarcodeInstructionsDialog();
      if (!shouldProceed) return;

      // Try to take photo directly - let image_picker handle permissions
      final XFile? image = await _imagePicker.pickImage(
        source: ImageSource.camera,
        imageQuality: 80,
        maxWidth: 1920,
        maxHeight: 1080,
      );

      if (image != null) {
        // Show loading dialog
        showDialog(
          context: context,
          barrierDismissible: false,
          builder: (context) => AlertDialog(
            content: Row(
              children: [
                CircularProgressIndicator(),
                SizedBox(width: 16),
                Text('Scanning barcode...'),
              ],
            ),
          ),
        );

        // Send image to backend for barcode verification
        final result = await _verifyBarcodeWithBackend(image, item, itemType);

        // Close loading dialog
        Navigator.of(context).pop();

        if (result) {
          setState(() {
            _barcodeVerified[item['id']] = true;
          });
          _showSuccessSnackBar('Barcode verified successfully!');

          // Update delivery status after verification
          await _updateDeliveryStatusAfterVerification(item, itemType);
        } else {
          _showErrorSnackBar('Barcode verification failed. Please try again.');
        }
      } else {
        // User cancelled - don't show error
        return;
      }
    } catch (e) {
      // Check if it's a permission error
      if (e.toString().contains('permission') || e.toString().contains('camera')) {
        _showErrorSnackBar('Camera permission is required. Please enable it in settings.');
      } else {
        _showErrorSnackBar('Error scanning barcode: $e');
      }
    }
  }


  // Show barcode scanning instructions
  Future<bool> _showBarcodeInstructionsDialog() async {
    return await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Barcode Scanning Instructions'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Please follow these steps:'),
            SizedBox(height: 12),
            Row(
              children: [
                Icon(Icons.looks_one, color: Colors.blue),
                SizedBox(width: 8),
                Expanded(child: Text('Point camera at the product barcode')),
              ],
            ),
            SizedBox(height: 8),
            Row(
              children: [
                Icon(Icons.looks_two, color: Colors.blue),
                SizedBox(width: 8),
                Expanded(child: Text('Ensure barcode is clearly visible')),
              ],
            ),
            SizedBox(height: 8),
            Row(
              children: [
                Icon(Icons.looks_3, color: Colors.blue),
                SizedBox(width: 8),
                Expanded(child: Text('Hold steady and tap capture')),
              ],
            ),
            SizedBox(height: 12),
            Container(
              padding: EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.orange[50],
                borderRadius: BorderRadius.circular(4),
                border: Border.all(color: Colors.orange[200]!),
              ),
              child: Row(
                children: [
                  Icon(Icons.info, color: Colors.orange[700], size: 16),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'The barcode will be automatically verified against the product.',
                      style: TextStyle(fontSize: 12, color: Colors.orange[700]),
                    ),
                  ),
                ],
              ),
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
            child: Text('Start Scanning'),
          ),
        ],
      ),
    ) ?? false;
  }

  // Verify barcode with backend
  Future<bool> _verifyBarcodeWithBackend(XFile? image, dynamic item, String itemType, [String? detectedBarcode]) async {
    try {
      setState(() {
        _isVerifyingBarcode = true;
      });

      // Get expected barcode
      String expectedBarcode = _getProductBarcode(item, itemType);
      if (expectedBarcode == 'N/A') {
        print('Expected barcode is N/A');
        setState(() {
          _isVerifyingBarcode = false;
        });
        return false;
      }

      print('Verifying barcode: $expectedBarcode');
      print('Detected barcode: $detectedBarcode');

      // If we have a detected barcode from live scanning, still verify with backend
      if (detectedBarcode != null) {
        print('Detected barcode from scanner: $detectedBarcode');
        print('Expected barcode: $expectedBarcode');

        // Always verify with backend even for detected barcodes
        if (image != null) {
          final response = await _apiService.verifyBarcode(image, expectedBarcode, authToken: widget.authToken);
          print('Backend verification response: $response');

          setState(() {
            _isVerifyingBarcode = false;
          });

          bool isSuccess = response['success'] == true;
          bool isVerified = response['verified'] == true;
          print('Backend verification - Success: $isSuccess, Verified: $isVerified');

          return isSuccess && isVerified;
        } else {
          // If no image, we can't verify with backend
          setState(() {
            _isVerifyingBarcode = false;
          });
          return false;
        }
      }

      // If we have an image, use backend verification
      if (image != null) {
        final response = await _apiService.verifyBarcode(image, expectedBarcode, authToken: widget.authToken);

        print('Barcode verification response: $response');

        setState(() {
          _isVerifyingBarcode = false;
        });

        // Check both success and verified fields
        bool isSuccess = response['success'] == true;
        bool isVerified = response['verified'] == true;

        print('Success: $isSuccess, Verified: $isVerified');

        return isSuccess && isVerified;
      }

      setState(() {
        _isVerifyingBarcode = false;
      });
      return false;
    } catch (e) {
      print('Barcode verification error: $e');
      setState(() {
        _isVerifyingBarcode = false;
      });
      return false;
    }
  }

  // Send image to backend for real barcode detection
  Future<Map<String, dynamic>> _sendImageForBarcodeDetection(XFile image, dynamic item, String itemType) async {
    try {
      final baseUrl = 'http://172.31.31.194:5000'; // Server IP address
      final uri = Uri.parse("$baseUrl/api/delivery-orders/detect-barcode");

      var request = http.MultipartRequest("POST", uri);
      request.headers["Authorization"] = widget.authToken.startsWith("Bearer ") ? widget.authToken : "Bearer ${widget.authToken}";

      // Add image file
      request.files.add(await http.MultipartFile.fromPath('image', image.path));

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print("🔍 Barcode Detection Response: ${response.statusCode} - ${response.body}");

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "success": true,
          "detected_barcode": data["detected_barcode"],
          "message": data["message"] ?? "Barcode detection completed"
        };
      } else {
        try {
          final errorData = jsonDecode(response.body);
          return {
            "success": false,
            "error": errorData["error"] ?? "Barcode detection failed"
          };
        } catch (_) {
          return {
            "success": false,
            "error": "Server error: ${response.statusCode} - ${response.body}"
          };
        }
      }
    } catch (e) {
      print("❌ Error detecting barcode: $e");
      return {"success": false, "error": "Network error: $e"};
    }
  }

  // Update delivery status after barcode verification
  Future<void> _updateDeliveryStatusAfterVerification(dynamic item, String itemType) async {
    try {
      // Update status to verified
      final response = await _apiService.updateDeliveryStatus(
          item['id'],
          'verified',
          'Barcode verified successfully',
          authToken: widget.authToken
      );

      if (response['success'] == true) {
        _showSuccessSnackBar('Delivery status updated to verified');
        // Refresh data
        _loadData();
      } else {
        _showErrorSnackBar(response['error'] ?? 'Failed to update delivery status');
      }
    } catch (e) {
      _showErrorSnackBar('Error updating delivery status: $e');
    }
  }
}

// Live Barcode Scanner Dialog Widget
class LiveBarcodeScannerDialog extends StatefulWidget {
  final dynamic item;
  final String itemType;
  final String expectedBarcode;
  final Function(String, XFile) onBarcodeDetected;
  final Future<Map<String, dynamic>> Function(XFile) onImageCaptured;
  final VoidCallback onCancel;

  const LiveBarcodeScannerDialog({
    Key? key,
    required this.item,
    required this.itemType,
    required this.expectedBarcode,
    required this.onBarcodeDetected,
    required this.onImageCaptured,
    required this.onCancel,
  }) : super(key: key);

  @override
  _LiveBarcodeScannerDialogState createState() => _LiveBarcodeScannerDialogState();
}

class _LiveBarcodeScannerDialogState extends State<LiveBarcodeScannerDialog> {
  final ImagePicker _imagePicker = ImagePicker();
  bool _isScanning = false;
  String _detectedBarcode = '';
  String _statusMessage = 'Point camera at barcode...';
  XFile? _capturedImage;
  Uint8List? _imageBytes;

  @override
  void initState() {
    super.initState();
    _startLiveScanning();
  }

  void _startLiveScanning() {
    setState(() {
      _isScanning = true;
      _statusMessage = 'Position barcode within the green frame. Ensure barcode is clear and fully visible.';
    });
  }

  Future<void> _captureAndDetect() async {
    if (_isScanning) {
      try {
        final XFile? image = await _imagePicker.pickImage(
          source: ImageSource.camera,
          imageQuality: 90, // Higher quality for better barcode detection
          maxWidth: 2048,   // Higher resolution for better detection
          maxHeight: 2048,
        );

        if (image != null) {
          // Store captured image for preview
          setState(() {
            _capturedImage = image;
            _statusMessage = 'Image captured! Analyzing...';
          });

          // Read image bytes for preview
          final bytes = await image.readAsBytes();
          setState(() {
            _imageBytes = bytes;
          });

          // Show preview for 2 seconds before detection
          await Future.delayed(Duration(seconds: 2));

          setState(() {
            _statusMessage = 'Sending to backend for detection...';
          });

          // Send image to backend for real barcode detection
          final detectionResult = await widget.onImageCaptured(image);

          if (detectionResult['success'] == true) {
            final detectedBarcode = detectionResult['detected_barcode'];

            setState(() {
              _detectedBarcode = detectedBarcode;
              _statusMessage = 'Barcode detected: $detectedBarcode';
            });

            // Auto-verify after detection
            await Future.delayed(Duration(milliseconds: 500));
            widget.onBarcodeDetected(detectedBarcode, image);
          } else {
            // Detection failed
            setState(() {
              _detectedBarcode = '';
              _statusMessage = 'Detection failed: ${detectionResult['error'] ?? 'Unknown error'}';
            });
          }
        }
      } catch (e) {
        setState(() {
          _statusMessage = 'Error: $e';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: Colors.black,
      child: Container(
        width: MediaQuery.of(context).size.width * 0.9,
        height: MediaQuery.of(context).size.height * 0.7,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Header
              Container(
                padding: EdgeInsets.all(16),
                color: Colors.black,
                child: Row(
                  children: [
                    Icon(Icons.qr_code_scanner, color: Colors.white, size: 24),
                    SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Capture Image',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          Text(
                            'Expected: ${widget.expectedBarcode}',
                            style: TextStyle(
                              color: Colors.grey,
                              fontSize: 12,
                            ),
                          ),
                          if (_capturedImage != null) ...[
                            SizedBox(height: 4),
                            Text(
                              'Image: ${_capturedImage!.name}',
                              style: TextStyle(
                                color: Colors.grey,
                                fontSize: 10,
                              ),
                            ),
                            Text(
                              'Size: ${_imageBytes?.length ?? 0} bytes',
                              style: TextStyle(
                                color: Colors.grey,
                                fontSize: 10,
                              ),
                            ),
                            if (_detectedBarcode.isNotEmpty) ...[
                              SizedBox(height: 4),
                              Text(
                                'Detected: $_detectedBarcode',
                                style: TextStyle(
                                  color: Colors.orange,
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ],
                        ],
                      ),
                    ),
                    IconButton(
                      onPressed: widget.onCancel,
                      icon: Icon(Icons.close, color: Colors.white),
                    ),
                  ],
                ),
              ),

              // Camera Preview Area
              Flexible(
                child: Container(
                  height: 400, // Fixed height instead of Expanded
                  color: Colors.grey[900],
                  child: Stack(
                    children: [
                      // Show captured image preview or camera placeholder
                      if (_imageBytes != null)
                      // Captured image preview
                        Center(
                          child: Container(
                            width: double.infinity,
                            height: double.infinity,
                            child: Image.memory(
                              _imageBytes!,
                              fit: BoxFit.contain,
                            ),
                          ),
                        )
                      else
                      // Camera placeholder (in real app, use CameraPreview)
                        Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(
                                Icons.camera_alt,
                                size: 80,
                                color: Colors.grey[600],
                              ),
                              SizedBox(height: 16),
                              Text(
                                'Camera Preview',
                                style: TextStyle(
                                  color: Colors.grey[600],
                                  fontSize: 16,
                                ),
                              ),
                              SizedBox(height: 8),
                              Text(
                                'Point camera at barcode',
                                style: TextStyle(
                                  color: Colors.grey[500],
                                  fontSize: 14,
                                ),
                              ),
                            ],
                          ),
                        ),

                      // Scanning overlay with better framing guidance
                      if (_isScanning && _imageBytes == null)
                        Center(
                          child: Container(
                            width: 250,
                            height: 150,
                            decoration: BoxDecoration(
                              border: Border.all(
                                color: Colors.green,
                                width: 3,
                              ),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Stack(
                              children: [
                                // Corner indicators
                                Positioned(
                                  top: 0,
                                  left: 0,
                                  child: Container(
                                    width: 25,
                                    height: 25,
                                    decoration: BoxDecoration(
                                      color: Colors.green,
                                      borderRadius: BorderRadius.only(
                                        topLeft: Radius.circular(12),
                                      ),
                                    ),
                                  ),
                                ),
                                Positioned(
                                  top: 0,
                                  right: 0,
                                  child: Container(
                                    width: 25,
                                    height: 25,
                                    decoration: BoxDecoration(
                                      color: Colors.green,
                                      borderRadius: BorderRadius.only(
                                        topRight: Radius.circular(12),
                                      ),
                                    ),
                                  ),
                                ),
                                Positioned(
                                  bottom: 0,
                                  left: 0,
                                  child: Container(
                                    width: 25,
                                    height: 25,
                                    decoration: BoxDecoration(
                                      color: Colors.green,
                                      borderRadius: BorderRadius.only(
                                        bottomLeft: Radius.circular(12),
                                      ),
                                    ),
                                  ),
                                ),
                                Positioned(
                                  bottom: 0,
                                  right: 0,
                                  child: Container(
                                    width: 25,
                                    height: 25,
                                    decoration: BoxDecoration(
                                      color: Colors.green,
                                      borderRadius: BorderRadius.only(
                                        bottomRight: Radius.circular(12),
                                      ),
                                    ),
                                  ),
                                ),
                                // Center guidance text
                                Center(
                                  child: Container(
                                    padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                                    decoration: BoxDecoration(
                                      color: Colors.black.withOpacity(0.7),
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: Text(
                                      'Position barcode here',
                                      style: TextStyle(
                                        color: Colors.white,
                                        fontSize: 14,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ),

              // Status and Controls
              Container(
                padding: EdgeInsets.all(16),
                color: Colors.black,
                child: Column(
                  children: [
                    Text(
                      _statusMessage,
                      style: TextStyle(
                        color: _detectedBarcode.isNotEmpty ? Colors.green : Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    SizedBox(height: 16),
                    Row(
                      children: [
                        if (_imageBytes == null) ...[
                          // Capture button (only when no image captured)
                          Flexible(
                            child: ElevatedButton.icon(
                              onPressed: _isScanning ? _captureAndDetect : null,
                              icon: Icon(Icons.camera_alt, size: 20),
                              label: Text('Capture & Detect'),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.blue,
                                foregroundColor: Colors.white,
                                padding: EdgeInsets.symmetric(vertical: 12),
                              ),
                            ),
                          ),
                          SizedBox(width: 12),
                        ] else ...[
                          // Retake button (when image is captured)
                          Flexible(
                            child: ElevatedButton.icon(
                              onPressed: () {
                                setState(() {
                                  _capturedImage = null;
                                  _imageBytes = null;
                                  _detectedBarcode = '';
                                  _statusMessage = 'Point camera at barcode...';
                                });
                              },
                              icon: Icon(Icons.refresh, size: 20),
                              label: Text('Retake'),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.orange,
                                foregroundColor: Colors.white,
                                padding: EdgeInsets.symmetric(vertical: 12),
                              ),
                            ),
                          ),
                          SizedBox(width: 12),
                        ],
                        Flexible(
                          child: ElevatedButton.icon(
                            onPressed: widget.onCancel,
                            icon: Icon(Icons.cancel, size: 20),
                            label: Text('Cancel'),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.red,
                              foregroundColor: Colors.white,
                              padding: EdgeInsets.symmetric(vertical: 12),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

