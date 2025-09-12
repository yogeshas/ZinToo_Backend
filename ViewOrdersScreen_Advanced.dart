import 'package:flutter/material.dart';
import 'models/order_models.dart';
import '../../../../core/services/api_service.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:slide_to_confirm/slide_to_confirm.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

class ViewOrdersScreen extends StatefulWidget {
  final String authToken;

  const ViewOrdersScreen({super.key, required this.authToken});

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
  String? _errorMessage;
  Map<int, bool> _expandedOrders = {};
  Map<int, bool> _deliveryStarted = {};
  Map<int, GoogleMapController?> _mapControllers = {};

  @override
  void initState() {
    super.initState();
    _loadOrders();
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    _mapControllers.values.forEach((controller) => controller?.dispose());
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
        _deliveryStarted.clear();
      });
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final response =
      await _apiService.getOrders(widget.authToken, status: _selectedStatus.apiValue);

      if (response['success']) {
        final List<dynamic> ordersData = response['orders'] ?? [];
        final List<Order> newOrders =
        ordersData.map((orderData) => Order.fromJson(orderData)).toList();

        setState(() {
          if (refresh) {
            _orders = newOrders;
          } else {
            _orders.addAll(newOrders);
          }
          _filteredOrders = List.from(_orders);
          _isLoading = false;

          // Initialize delivery started map for orders with status "out_for_delivery"
          for (var o in _orders) {
            _deliveryStarted[o.id] = o.status.toLowerCase() == "out_for_delivery";
          }
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
        backgroundColor: Colors.white,
        title: const Text('Reject Order'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Align(alignment: Alignment.centerLeft, child: Text('Order: ${order.orderNumber}')),
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
          TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () => Navigator.of(context).pop(reasonController.text),
            style: ElevatedButton.styleFrom(
                backgroundColor: Colors.redAccent, foregroundColor: Colors.white),
            child: const Text('Reject'),
          ),
        ],
      ),
    );

    if (result != null && result.isNotEmpty) {
      try {
        final response = await _apiService.rejectOrder(widget.authToken, order.id, result);
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
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(message),
      backgroundColor: Colors.green,
      duration: const Duration(seconds: 3),
    ));
  }

  void _showErrorSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(message),
      backgroundColor: Colors.red,
      duration: const Duration(seconds: 3),
    ));
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

  void _openMaps(String address) async {
    final query = Uri.encodeComponent(address);
    final googleUrl = 'https://www.google.com/maps/search/?api=1&query=$query';
    if (await canLaunch(googleUrl)) {
      await launch(googleUrl);
    } else {
      print('Could not open the map.');
    }
  }

  void _launchPhone(String phoneNumber) async {
    if (phoneNumber.isEmpty) return;
    final telUri = Uri(scheme: 'tel', path: phoneNumber);
    if (await canLaunchUrl(telUri)) {
      await launchUrl(telUri);
    } else {
      print('Could not launch phone dialer for: $phoneNumber');
    }
  }

  Future<void> _startDelivery(Order order) async {
    setState(() {
      _isLoading = true;
    });
    try {
      final response = await _apiService.OutForDeliveryOrder(widget.authToken, order.id, 'out_for_delivery');
      if (response['success']) {
        setState(() {
          _deliveryStarted[order.id] = true;
        });
        _showSuccessSnackBar('Delivery started for order ${order.orderNumber}');
        _loadOrders(refresh: true);
      } else {
        _showErrorSnackBar(response['message'] ?? 'Failed to start delivery');
      }
    } catch (e) {
      _showErrorSnackBar('Error starting delivery: $e');
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _scanProduct(int orderId) {
    final TextEditingController scanController = TextEditingController();

    showDialog(
        context: context,
        builder: (_) {
          return AlertDialog(
            title: const Text('Scan Product'),
            content: TextField(
              controller: scanController,
              decoration: const InputDecoration(
                labelText: 'Enter scanned product code',
                border: OutlineInputBorder(),
              ),
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
              ElevatedButton(
                  onPressed: () {
                    Navigator.pop(context);
                    ScaffoldMessenger.of(context)
                        .showSnackBar(const SnackBar(content: Text('Product submitted')));
                  },
                  child: const Text('Submit')),
            ],
          );
        });
  }

  Widget _buildDeliveryTrackBadge(String deliveryTrack) {
    Color color;
    IconData icon;
    String text;

    switch (deliveryTrack.toLowerCase()) {
      case 'cancel_pickup':
        color = Colors.red;
        icon = Icons.cancel_outlined;
        text = 'Cancel Pickup';
        break;
      case 'exchange_pickup':
        color = Colors.blue;
        icon = Icons.swap_horiz;
        text = 'Exchange Pickup';
        break;
      default:
        color = Colors.green;
        icon = Icons.local_shipping;
        text = 'Normal Delivery';
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 4),
          Text(
            text,
            style: TextStyle(
              color: color,
              fontSize: 12,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      body: SafeArea(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          // Enhanced Header with gradient
          Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [Colors.orange[600]!, Colors.orange[400]!],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.orange.withOpacity(0.3),
                  blurRadius: 10,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      Icon(Icons.local_shipping, color: Colors.white, size: 28),
                      const SizedBox(width: 12),
                      const Text(
                        'Delivery Orders',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const Spacer(),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          '${_filteredOrders.length} Orders',
                          style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                // Status filter chips
                Container(
                  height: 60,
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      itemCount: OrderStatus.values.length,
                      separatorBuilder: (_, __) => const SizedBox(width: 8),
                      itemBuilder: (context, index) {
                        final status = OrderStatus.values[index];
                        final isSelected = _selectedStatus == status;
                        return ChoiceChip(
                          label: Text(status.displayName,
                              style: TextStyle(
                                  color: isSelected ? Colors.orange[700] : Colors.white,
                                  fontWeight: FontWeight.w500)),
                          selected: isSelected,
                          onSelected: (_) => _onStatusFilterChanged(status),
                          selectedColor: Colors.white,
                          backgroundColor: Colors.white.withOpacity(0.2),
                          elevation: 2,
                          padding: const EdgeInsets.symmetric(horizontal: 12),
                          showCheckmark: false,
                        );
                      }),
                ),
                const SizedBox(height: 16),
              ],
            ),
          ),
          Expanded(child: _buildOrdersList()),
        ]),
      ),
    );
  }

  Widget _buildOrdersList() {
    if (_isLoading && _orders.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_errorMessage != null && _orders.isEmpty) {
      return Center(
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          Icon(Icons.error_outline, size: 64, color: Colors.red[300]),
          const SizedBox(height: 16),
          Text(_errorMessage!,
              style: TextStyle(fontSize: 16, color: Colors.red[600]),
              textAlign: TextAlign.center),
          const SizedBox(height: 16),
          ElevatedButton(onPressed: () => _loadOrders(refresh: true), child: const Text('Retry')),
        ]),
      );
    }

    if (_filteredOrders.isEmpty) {
      return Center(
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          Image.asset('assets/images/view.png', width: 200, height: 200, fit: BoxFit.contain),
          const SizedBox(height: 20),
          Text("No ${_selectedStatus.displayName.toLowerCase()} yet.",
              style: const TextStyle(fontSize: 18)),
          const SizedBox(height: 8),
          Text("Orders will appear here once assigned to you.",
              style: TextStyle(fontSize: 14, color: Colors.grey[600])),
        ]),
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
                child: Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator()));
          }
          final order = _filteredOrders[index];
          return _buildOrderCard(order);
        },
      ),
    );
  }

  Widget _buildOrderCard(Order order) {
    final isExpanded = _expandedOrders[order.id] ?? false;
    final canApprove = order.status.toLowerCase() == 'pending';
    final deliveryTrack = order.deliveryTrack ?? 'normal';

    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Column(children: [
        // Header with gradient
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [Colors.white, Colors.grey[50]!],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(16),
                topRight: Radius.circular(16),
              )),
          child: Column(
            children: [
              Row(children: [
                Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Row(
                        children: [
                          Icon(Icons.receipt_long, color: Colors.orange[600], size: 20),
                          const SizedBox(width: 8),
                          const Text('Order ID #', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: Colors.grey)),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(order.orderNumber, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                    ])),
                Column(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: _getStatusColor(order.status),
                        borderRadius: BorderRadius.circular(20),
                        boxShadow: [
                          BoxShadow(
                            color: _getStatusColor(order.status).withOpacity(0.3),
                            blurRadius: 4,
                            offset: const Offset(0, 2),
                          ),
                        ],
                      ),
                      child: Text(order.statusDisplayName,
                          style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600)),
                    ),
                    const SizedBox(height: 8),
                    _buildDeliveryTrackBadge(deliveryTrack),
                  ],
                ),
              ]),
            ],
          ),
        ),

        // Action buttons
        Container(
          color: Colors.white,
          padding: const EdgeInsets.all(16),
          child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
            if (canApprove)
              Expanded(
                child: Container(
                  height: 40,
                  child: ElevatedButton.icon(
                    onPressed: () => _approveOrder(order),
                    icon: const Icon(Icons.check_circle, size: 18),
                    label: const Text('Approve'),
                    style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green[600],
                        foregroundColor: Colors.white,
                        elevation: 2,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20))),
                  ),
                ),
              ),
            if (canApprove) const SizedBox(width: 12),
            if (order.status.toLowerCase() == 'pending')
              Expanded(
                child: Container(
                  height: 40,
                  child: ElevatedButton.icon(
                    onPressed: () => _rejectOrder(order),
                    icon: const Icon(Icons.cancel, size: 18),
                    label: const Text('Reject'),
                    style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.red[600],
                        foregroundColor: Colors.white,
                        elevation: 2,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20))),
                  ),
                ),
              ),
          ]),
        ),

        // Expand button
        Container(
          color: Colors.grey[100],
          child: Center(
            child: IconButton(
                icon: Icon(
                  isExpanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
                  color: Colors.orange[600],
                  size: 28,
                ),
                onPressed: () => _toggleOrderExpansion(order.id)),
          ),
        ),

        // Expanded content
        if (isExpanded)
          Container(
              color: Colors.white,
              padding: const EdgeInsets.all(20),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                // Customer info with enhanced design
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.blue[50],
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.blue[200]!),
                  ),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Colors.blue[600],
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Icon(Icons.person, size: 20, color: Colors.white),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              order.customer?.username ?? 'Unknown Customer',
                              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                            ),
                            if ((order.customer?.phoneNumber ?? '').isNotEmpty)
                              Text(
                                order.customer!.phoneNumber!,
                                style: TextStyle(fontSize: 14, color: Colors.grey[600]),
                              ),
                          ],
                        ),
                      ),
                      if ((order.customer?.phoneNumber ?? '').isNotEmpty)
                        Container(
                          decoration: BoxDecoration(
                            color: Colors.green[600],
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: IconButton(
                            icon: const Icon(Icons.phone, color: Colors.white),
                            onPressed: () => _launchPhone(order.customer!.phoneNumber!),
                          ),
                        ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),

                // Delivery address with map
                _buildDetailRow('Delivery Address', order.deliveryAddress, Icons.location_on),
                const SizedBox(height: 16),

                // Order items with enhanced design
                const Text('Order Items:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                const SizedBox(height: 12),
                ...order.items.map((item) => Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.grey[50],
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.grey[200]!),
                  ),
                  child: Row(
                    children: [
                      if (item.productImage != null)
                        ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: Image.network(item.productImage!,
                              width: 50,
                              height: 50,
                              fit: BoxFit.cover,
                              errorBuilder: (context, error, stackTrace) {
                                return Container(
                                  width: 50,
                                  height: 50,
                                  decoration: BoxDecoration(
                                    color: Colors.grey[300],
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: const Icon(Icons.image),
                                );
                              }),
                        )
                      else
                        Container(
                          width: 50,
                          height: 50,
                          decoration: BoxDecoration(
                            color: Colors.grey[300],
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Icon(Icons.image),
                        ),
                      const SizedBox(width: 16),
                      Expanded(
                          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            Text(item.productName, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
                            const SizedBox(height: 4),
                            Text('Qty: ${item.quantity} × ₹${item.unitPrice.toStringAsFixed(2)}',
                                style: TextStyle(color: Colors.grey[600], fontSize: 13)),
                            if (item.deliveryTrack != null && item.deliveryTrack != 'normal')
                              Padding(
                                padding: const EdgeInsets.only(top: 4),
                                child: _buildDeliveryTrackBadge(item.deliveryTrack!),
                              ),
                          ])),
                      Text('₹${item.totalPrice.toStringAsFixed(2)}',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.orange)),
                    ],
                  ),
                )),
                const SizedBox(height: 16),

                // Order summary with enhanced design
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.orange[50],
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.orange[200]!),
                  ),
                  child: Column(
                    children: [
                      _buildSummaryRow('Subtotal', order.subtotal),
                      _buildSummaryRow('Delivery Fee', order.deliveryFeeAmount),
                      _buildSummaryRow('Platform Fee', order.platformFee),
                      if (order.discountAmount > 0) _buildSummaryRow('Discount', -order.discountAmount, isDiscount: true),
                      const Divider(),
                      _buildSummaryRow('Total', order.totalAmount, isTotal: true),
                    ],
                  ),
                ),
                const SizedBox(height: 24),

                // Delivery action with enhanced design
                _buildDeliveryAction(order),
                const SizedBox(height: 16),

                // Scan product button
                if ((_deliveryStarted[order.id] ?? false) == true || order.status.toLowerCase() == 'out_for_delivery')
                  Container(
                    width: double.infinity,
                    height: 50,
                    child: ElevatedButton.icon(
                      onPressed: () => _scanProduct(order.id),
                      icon: const Icon(Icons.camera_alt_outlined),
                      label: const Text('Scan Product'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.orange[600],
                        foregroundColor: Colors.white,
                        elevation: 2,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(25)),
                      ),
                    ),
                  ),
              ])),
      ],
      ),
    );
  }

  Widget _buildDeliveryAction(Order order) {
    final isDeliveryStarted = (_deliveryStarted[order.id] ?? false);
    final isDelivered = order.status.toLowerCase() == 'delivered';
    final deliveryTrack = order.deliveryTrack ?? 'normal';

    if (isDelivered) {
      return Container(
        padding: const EdgeInsets.symmetric(vertical: 16),
        width: double.infinity,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [Colors.green[600]!, Colors.green[500]!],
            begin: Alignment.centerLeft,
            end: Alignment.centerRight,
          ),
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.green.withOpacity(0.3),
              blurRadius: 8,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: const Center(
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.check_circle, color: Colors.white, size: 24),
              SizedBox(width: 8),
              Text(
                'Delivered Successfully',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
              ),
            ],
          ),
        ),
      );
    } else if (isDeliveryStarted || order.status.toLowerCase() == 'out_for_delivery') {
      return Container(
        padding: const EdgeInsets.symmetric(vertical: 16),
        width: double.infinity,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [Colors.blue[600]!, Colors.blue[500]!],
            begin: Alignment.centerLeft,
            end: Alignment.centerRight,
          ),
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.blue.withOpacity(0.3),
              blurRadius: 8,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Center(
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.local_shipping, color: Colors.white, size: 24),
              const SizedBox(width: 8),
              Text(
                _getDeliveryStatusText(deliveryTrack),
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
              ),
            ],
          ),
        ),
      );
    } else {
      return ConfirmationSlider(
        text: _getDeliveryActionText(deliveryTrack),
        textStyle: const TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.bold,
          fontSize: 16,
        ),
        backgroundColor: _getDeliveryActionColor(deliveryTrack),
        foregroundColor: Colors.white,
        iconColor: Colors.white,
        onConfirmation: () => _startDelivery(order),
      );
    }
  }

  String _getDeliveryStatusText(String deliveryTrack) {
    switch (deliveryTrack.toLowerCase()) {
      case 'cancel_pickup':
        return 'Cancel Pickup in Progress';
      case 'exchange_pickup':
        return 'Exchange Pickup in Progress';
      default:
        return 'Delivery in Progress';
    }
  }

  String _getDeliveryActionText(String deliveryTrack) {
    switch (deliveryTrack.toLowerCase()) {
      case 'cancel_pickup':
        return 'Slide to Start Cancel Pickup';
      case 'exchange_pickup':
        return 'Slide to Start Exchange Pickup';
      default:
        return 'Slide to Start Delivery';
    }
  }

  Color _getDeliveryActionColor(String deliveryTrack) {
    switch (deliveryTrack.toLowerCase()) {
      case 'cancel_pickup':
        return Colors.red[600]!;
      case 'exchange_pickup':
        return Colors.blue[600]!;
      default:
        return Colors.orange[600]!;
    }
  }

  Widget _buildDetailRow(String label, String address, IconData icon) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.grey[200]!),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.orange[600],
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, color: Colors.white, size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(label, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.black87)),
                const SizedBox(height: 8),
                Text(address, style: const TextStyle(fontSize: 14, color: Colors.black87)),
              ])),
          Container(
            decoration: BoxDecoration(
              color: Colors.orange[600],
              borderRadius: BorderRadius.circular(8),
            ),
            child: IconButton(
                icon: const Icon(Icons.map, color: Colors.white),
                onPressed: () => _openMaps(address),
                tooltip: 'Open in Maps'),
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryRow(String label, double amount, {bool isDiscount = false, bool isTotal = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        Text(label, style: TextStyle(fontSize: isTotal ? 16 : 14, fontWeight: isTotal ? FontWeight.bold : FontWeight.normal)),
        Text('${isDiscount ? '-' : ''}₹${amount.toStringAsFixed(2)}',
            style: TextStyle(fontSize: isTotal ? 16 : 14, fontWeight: isTotal ? FontWeight.bold : FontWeight.normal, color: isDiscount ? Colors.green : (isTotal ? Colors.orange : null))),
      ]),
    );
  }

  Color _getStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'pending':
        return Colors.orange;
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
}
