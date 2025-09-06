import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'models/order_models.dart';
import 'api_service_updated.dart';

class ViewOrdersScreen extends StatefulWidget {
  final String authToken;
  
  const ViewOrdersScreen({
    super.key,
    required this.authToken,
  });

  @override
  State<ViewOrdersScreen> createState() => _ViewOrdersScreenState();
}

class _ViewOrdersScreenState extends State<ViewOrdersScreen> {
  final ApiService _apiService = ApiService();
  final ScrollController _scrollController = ScrollController();
  
  List<Order> _orders = [];
  List<Order> _filteredOrders = [];
  OrderStatus _selectedStatus = OrderStatus.all;
  bool _isLoading = false;
  bool _isLoadingMore = false;
  int _currentPage = 1;
  final int _itemsPerPage = 10;
  String? _errorMessage;
  Map<int, bool> _expandedOrders = {};

  @override
  void initState() {
    super.initState();
    _loadOrders();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent - 200) {
      _loadMoreOrders();
    }
  }

  Future<void> _loadOrders({bool refresh = false}) async {
    if (refresh) {
      setState(() {
        _currentPage = 1;
        _orders.clear();
        _filteredOrders.clear();
        _expandedOrders.clear();
      });
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final response = await _apiService.getOrders(
        widget.authToken,
        status: _selectedStatus.apiValue,
      );

      if (response['success']) {
        final List<dynamic> ordersData = response['orders'] ?? [];
        final List<Order> newOrders = ordersData
            .map((orderData) => Order.fromJson(orderData))
            .toList();

        setState(() {
          if (refresh) {
            _orders = newOrders;
          } else {
            _orders.addAll(newOrders);
          }
          _filteredOrders = List.from(_orders);
          _isLoading = false;
        });
      } else {
        setState(() {
          _errorMessage = response['message'] ?? 'Failed to load orders';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Network error: $e';
        _isLoading = false;
      });
    }
  }

  Future<void> _loadMoreOrders() async {
    if (_isLoadingMore || _isLoading) return;

    setState(() {
      _isLoadingMore = true;
    });

    // Simulate pagination - in real implementation, you'd pass page number to API
    await Future.delayed(const Duration(seconds: 1));
    
    setState(() {
      _isLoadingMore = false;
    });
  }

  Future<void> _approveOrder(Order order) async {
    try {
      final response = await _apiService.approveOrder(widget.authToken, order.id);
      
      if (response['success']) {
        _showSuccessSnackBar('Order ${order.orderNumber} approved successfully');
        _loadOrders(refresh: true);
      } else {
        _showErrorSnackBar(response['message'] ?? 'Failed to approve order');
      }
    } catch (e) {
      _showErrorSnackBar('Error approving order: $e');
    }
  }

  Future<void> _rejectOrder(Order order) async {
    final TextEditingController reasonController = TextEditingController();
    
    final result = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Reject Order'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Order: ${order.orderNumber}'),
            const SizedBox(height: 16),
            TextField(
              controller: reasonController,
              decoration: const InputDecoration(
                labelText: 'Rejection Reason',
                hintText: 'Enter reason for rejection',
                border: OutlineInputBorder(),
              ),
              maxLines: 3,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(context).pop(reasonController.text),
            child: const Text('Reject'),
          ),
        ],
      ),
    );

    if (result != null && result.isNotEmpty) {
      try {
        final response = await _apiService.rejectOrder(
          widget.authToken,
          order.id,
          result,
        );
        
        if (response['success']) {
          _showSuccessSnackBar('Order ${order.orderNumber} rejected');
          _loadOrders(refresh: true);
        } else {
          _showErrorSnackBar(response['message'] ?? 'Failed to reject order');
        }
      } catch (e) {
        _showErrorSnackBar('Error rejecting order: $e');
      }
    }
  }

  void _showSuccessSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.green,
        duration: const Duration(seconds: 3),
      ),
    );
  }

  void _showErrorSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
        duration: const Duration(seconds: 3),
      ),
    );
  }

  void _toggleOrderExpansion(int orderId) {
    setState(() {
      _expandedOrders[orderId] = !(_expandedOrders[orderId] ?? false);
    });
  }

  void _onStatusFilterChanged(OrderStatus status) {
    setState(() {
      _selectedStatus = status;
    });
    _loadOrders(refresh: true);
  }

  Widget _buildStatusChip(OrderStatus status, String displayName) {
    final isSelected = _selectedStatus == status;
    return FilterChip(
      label: Text(displayName),
      selected: isSelected,
      onSelected: (selected) {
        if (selected) {
          _onStatusFilterChanged(status);
        }
      },
      selectedColor: Colors.blue[100],
      checkmarkColor: Colors.blue[700],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('View Orders'),
        backgroundColor: Colors.blue[600],
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => _loadOrders(refresh: true),
          ),
        ],
      ),
      body: Column(
        children: [
          // Status Filter Chips - Show only relevant tabs
          Container(
            padding: const EdgeInsets.all(16),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  // All Orders
                  _buildStatusChip(OrderStatus.all, 'All Orders'),
                  const SizedBox(width: 8),
                  // Approved Orders
                  _buildStatusChip(OrderStatus.confirmed, 'Approved'),
                  const SizedBox(width: 8),
                  // Cancelled Orders
                  _buildStatusChip(OrderStatus.cancelled, 'Cancelled'),
                  const SizedBox(width: 8),
                  // Delivered Orders
                  _buildStatusChip(OrderStatus.delivered, 'Delivered'),
                  const SizedBox(width: 8),
                  // Exchange Orders
                  _buildStatusChip(OrderStatus.exchange, 'Exchange'),
                ],
              ),
            ),
          ),
          
          // Orders List
          Expanded(
            child: _buildOrdersList(),
          ),
        ],
      ),
    );
  }

  Widget _buildOrdersList() {
    if (_isLoading && _orders.isEmpty) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    if (_errorMessage != null && _orders.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.error_outline,
              size: 64,
              color: Colors.red[300],
            ),
            const SizedBox(height: 16),
            Text(
              _errorMessage!,
              style: TextStyle(
                fontSize: 16,
                color: Colors.red[600],
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => _loadOrders(refresh: true),
              child: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (_filteredOrders.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Image.asset(
              'assets/images/view.png',
              width: 200,
              height: 200,
              fit: BoxFit.contain,
            ),
            const SizedBox(height: 20),
            Text(
              "No ${_selectedStatus.displayName.toLowerCase()} yet.",
              style: const TextStyle(fontSize: 18),
            ),
            const SizedBox(height: 8),
            Text(
              "Orders will appear here once assigned to you.",
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[600],
              ),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => _loadOrders(refresh: true),
      child: ListView.builder(
        controller: _scrollController,
        padding: const EdgeInsets.all(16),
        itemCount: _filteredOrders.length + (_isLoadingMore ? 1 : 0),
        itemBuilder: (context, index) {
          if (index == _filteredOrders.length) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(16),
                child: CircularProgressIndicator(),
              ),
            );
          }

          final order = _filteredOrders[index];
          return _buildOrderCard(order);
        },
      ),
    );
  }

  Widget _buildOrderCard(Order order) {
    final isExpanded = _expandedOrders[order.id] ?? false;
    final canApprove = order.status.toLowerCase() == 'pending' || order.status.toLowerCase() == 'assigned';
    final canReject = ['pending', 'assigned', 'confirmed', 'processing', 'shipped', 'out_for_delivery']
        .contains(order.status.toLowerCase());

    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          // Order Header
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.grey[50],
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(12),
                topRight: Radius.circular(12),
              ),
            ),
            child: Row(
              children: [
                // Order ID
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Order #${order.orderNumber}',
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '₹${order.totalAmount.toStringAsFixed(2)}',
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.green[600],
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
                
                // Status Badge
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: _getStatusColor(order.status),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    order.statusDisplayName,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
          ),
          
          // Order Details
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                // Customer Info
                Row(
                  children: [
                    const Icon(Icons.person, size: 16, color: Colors.grey),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        order.customer?.username ?? 'Unknown Customer',
                        style: const TextStyle(fontSize: 14),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                
                // Payment Info
                Row(
                  children: [
                    const Icon(Icons.payment, size: 16, color: Colors.grey),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '${order.paymentMethodDisplayName} - ${order.paymentStatusDisplayName}',
                        style: const TextStyle(fontSize: 14),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                
                // Delivery Type and Track
                Row(
                  children: [
                    const Icon(Icons.local_shipping, size: 16, color: Colors.grey),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        order.deliveryTrackDisplay ?? '${order.deliveryType.toUpperCase()} Delivery',
                        style: const TextStyle(fontSize: 14),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                
                // Delivery Assignment
                if (order.deliveryGuyId != null)
                  Row(
                    children: [
                      const Icon(Icons.person_pin, size: 16, color: Colors.grey),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'Assigned to Delivery ID: ${order.deliveryGuyId}',
                          style: const TextStyle(fontSize: 14),
                        ),
                      ),
                    ],
                  ),
                
                // Action Buttons
                const SizedBox(height: 16),
                Row(
                  children: [
                    // Expand/Collapse Button
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () => _toggleOrderExpansion(order.id),
                        icon: Icon(isExpanded ? Icons.expand_less : Icons.expand_more),
                        label: Text(isExpanded ? 'Less Details' : 'More Details'),
                      ),
                    ),
                    
                    const SizedBox(width: 8),
                    
                    // Approve Button
                    if (canApprove)
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: () => _approveOrder(order),
                          icon: const Icon(Icons.check, size: 16),
                          label: const Text('Approve'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.green,
                            foregroundColor: Colors.white,
                          ),
                        ),
                      ),
                    
                    if (canApprove) const SizedBox(width: 8),
                    
                    // Reject Button
                    if (canReject)
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: () => _rejectOrder(order),
                          icon: const Icon(Icons.close, size: 16),
                          label: const Text('Reject'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.red,
                            foregroundColor: Colors.white,
                          ),
                        ),
                      ),
                  ],
                ),
              ],
            ),
          ),
          
          // Expanded Details
          if (isExpanded)
            Container(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Divider(),
                  const SizedBox(height: 16),
                  
                  // Delivery Address
                  _buildDetailRow(
                    'Delivery Address',
                    order.deliveryAddress,
                    Icons.location_on,
                  ),
                  const SizedBox(height: 12),
                  
                  // Order Items
                  const Text(
                    'Order Items:',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                    ),
                  ),
                  const SizedBox(height: 8),
                  
                  // Show assigned items if available, otherwise show all items
                  ...(order.assignedItems.isNotEmpty ? order.assignedItems : order.items).map((item) => Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.grey[100],
                      borderRadius: BorderRadius.circular(8),
                      border: item.deliveryGuyId != null ? Border.all(color: Colors.blue, width: 1) : null,
                    ),
                    child: Column(
                      children: [
                        Row(
                          children: [
                            if (item.productImage != null)
                              ClipRRect(
                                borderRadius: BorderRadius.circular(4),
                                child: Image.network(
                                  item.productImage!,
                                  width: 40,
                                  height: 40,
                                  fit: BoxFit.cover,
                                  errorBuilder: (context, error, stackTrace) {
                                    return Container(
                                      width: 40,
                                      height: 40,
                                      color: Colors.grey[300],
                                      child: const Icon(Icons.image),
                                    );
                                  },
                                ),
                              )
                            else
                              Container(
                                width: 40,
                                height: 40,
                                color: Colors.grey[300],
                                child: const Icon(Icons.image),
                              ),
                            
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    item.productName,
                                    style: const TextStyle(
                                      fontWeight: FontWeight.w500,
                                      fontSize: 14,
                                    ),
                                  ),
                                  Text(
                                    'Qty: ${item.quantity} × ₹${item.unitPrice.toStringAsFixed(2)}',
                                    style: TextStyle(
                                      color: Colors.grey[600],
                                      fontSize: 12,
                                    ),
                                  ),
                                  if (item.selectedSize != null)
                                    Text(
                                      'Size: ${item.selectedSize}',
                                      style: TextStyle(
                                        color: Colors.grey[600],
                                        fontSize: 12,
                                      ),
                                    ),
                                ],
                              ),
                            ),
                            Text(
                              '₹${item.totalPrice.toStringAsFixed(2)}',
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 14,
                              ),
                            ),
                          ],
                        ),
                        
                        // Item Status and Delivery Info
                        if (item.deliveryGuyId != null || item.deliveryTrack != null)
                          Container(
                            margin: const EdgeInsets.only(top: 8),
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: Colors.blue[50],
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Row(
                              children: [
                                if (item.deliveryGuyId != null) ...[
                                  const Icon(Icons.person, size: 14, color: Colors.blue),
                                  const SizedBox(width: 4),
                                  Text(
                                    'Delivery ID: ${item.deliveryGuyId}',
                                    style: const TextStyle(fontSize: 12, color: Colors.blue),
                                  ),
                                  const SizedBox(width: 12),
                                ],
                                if (item.deliveryTrack != null) ...[
                                  const Icon(Icons.track_changes, size: 14, color: Colors.orange),
                                  const SizedBox(width: 4),
                                  Text(
                                    item.deliveryTrackDisplay ?? item.deliveryTrack!,
                                    style: const TextStyle(fontSize: 12, color: Colors.orange),
                                  ),
                                ],
                                const Spacer(),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: _getItemStatusColor(item.status),
                                    borderRadius: BorderRadius.circular(10),
                                  ),
                                  child: Text(
                                    item.status.toUpperCase(),
                                    style: const TextStyle(
                                      fontSize: 10,
                                      color: Colors.white,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                      ],
                    ),
                  )).toList(),
                  
                  const SizedBox(height: 16),
                  
                  // Order Summary
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.blue[50],
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Column(
                      children: [
                        _buildSummaryRow('Subtotal', order.subtotal),
                        _buildSummaryRow('Delivery Fee', order.deliveryFeeAmount),
                        _buildSummaryRow('Platform Fee', order.platformFee),
                        if (order.discountAmount > 0)
                          _buildSummaryRow('Discount', -order.discountAmount, isDiscount: true),
                        const Divider(),
                        _buildSummaryRow('Total', order.totalAmount, isTotal: true),
                      ],
                    ),
                  ),
                  
                  // Order Timestamps
                  const SizedBox(height: 16),
                  _buildDetailRow(
                    'Order Date',
                    _formatDateTime(order.createdAt),
                    Icons.calendar_today,
                  ),
                  if (order.assignedAt != null)
                    _buildDetailRow(
                      'Assigned Date',
                      _formatDateTime(order.assignedAt!),
                      Icons.assignment,
                    ),
                  if (order.estimatedDelivery != null)
                    _buildDetailRow(
                      'Estimated Delivery',
                      _formatDateTime(order.estimatedDelivery!),
                      Icons.schedule,
                    ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildDetailRow(String label, String value, IconData icon) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 16, color: Colors.grey),
        const SizedBox(width: 8),
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
                style: const TextStyle(fontSize: 14),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildSummaryRow(String label, double amount, {bool isDiscount = false, bool isTotal = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: isTotal ? 16 : 14,
              fontWeight: isTotal ? FontWeight.bold : FontWeight.normal,
            ),
          ),
          Text(
            '${isDiscount ? '-' : ''}₹${amount.toStringAsFixed(2)}',
            style: TextStyle(
              fontSize: isTotal ? 16 : 14,
              fontWeight: isTotal ? FontWeight.bold : FontWeight.normal,
              color: isDiscount ? Colors.green : null,
            ),
          ),
        ],
      ),
    );
  }

  Color _getStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'pending':
        return Colors.orange;
      case 'assigned':
        return Colors.blue;
      case 'confirmed':
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
        return Colors.red;
      case 'rejected':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  Color _getItemStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'pending':
        return Colors.orange;
      case 'assigned':
        return Colors.blue;
      case 'confirmed':
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
        return Colors.red;
      case 'rejected':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  String _formatDateTime(DateTime dateTime) {
    return '${dateTime.day}/${dateTime.month}/${dateTime.year} ${dateTime.hour}:${dateTime.minute.toString().padLeft(2, '0')}';
  }
}
