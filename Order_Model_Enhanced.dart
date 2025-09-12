class Order {
  final int id;
  final String orderNumber;
  final int customerId;
  final String status;
  final String deliveryAddress;
  final double subtotal;
  final double deliveryFeeAmount;
  final double platformFee;
  final double discountAmount;
  final double totalAmount;
  final DateTime createdAt;
  final DateTime updatedAt;
  final Customer? customer;
  final List<OrderItem> items;
  
  // New fields for delivery tracking
  final String? deliveryTrack;
  final String? overallStatus;
  final List<OrderItem>? assignedItems;

  Order({
    required this.id,
    required this.orderNumber,
    required this.customerId,
    required this.status,
    required this.deliveryAddress,
    required this.subtotal,
    required this.deliveryFeeAmount,
    required this.platformFee,
    required this.discountAmount,
    required this.totalAmount,
    required this.createdAt,
    required this.updatedAt,
    this.customer,
    required this.items,
    this.deliveryTrack,
    this.overallStatus,
    this.assignedItems,
  });

  factory Order.fromJson(Map<String, dynamic> json) {
    return Order(
      id: json['id'] ?? 0,
      orderNumber: json['order_number'] ?? '',
      customerId: json['customer_id'] ?? 0,
      status: json['status'] ?? 'pending',
      deliveryAddress: json['delivery_address_text'] ?? json['delivery_address'] ?? '',
      subtotal: (json['subtotal'] ?? 0).toDouble(),
      deliveryFeeAmount: (json['delivery_fee_amount'] ?? 0).toDouble(),
      platformFee: (json['platform_fee'] ?? 0).toDouble(),
      discountAmount: (json['discount_amount'] ?? 0).toDouble(),
      totalAmount: (json['total_amount'] ?? 0).toDouble(),
      createdAt: DateTime.tryParse(json['created_at'] ?? '') ?? DateTime.now(),
      updatedAt: DateTime.tryParse(json['updated_at'] ?? '') ?? DateTime.now(),
      customer: json['customer'] != null ? Customer.fromJson(json['customer']) : null,
      items: (json['items'] as List<dynamic>?)
          ?.map((item) => OrderItem.fromJson(item))
          .toList() ?? [],
      // New fields
      deliveryTrack: json['delivery_track'],
      overallStatus: json['overall_status'],
      assignedItems: (json['assigned_items'] as List<dynamic>?)
          ?.map((item) => OrderItem.fromJson(item))
          .toList(),
    );
  }

  String get statusDisplayName {
    switch (status.toLowerCase()) {
      case 'pending':
        return 'Pending';
      case 'confirmed':
        return 'Confirmed';
      case 'processing':
        return 'Processing';
      case 'shipped':
        return 'Shipped';
      case 'out_for_delivery':
        return 'Out for Delivery';
      case 'delivered':
        return 'Delivered';
      case 'cancelled':
        return 'Cancelled';
      case 'rejected':
        return 'Rejected';
      default:
        return status;
    }
  }

  String get deliveryTrackDisplay {
    switch (deliveryTrack?.toLowerCase()) {
      case 'cancel_pickup':
        return 'Cancel Pickup';
      case 'exchange_pickup':
        return 'Exchange Pickup';
      default:
        return 'Normal Delivery';
    }
  }
}

class OrderItem {
  final int id;
  final int orderId;
  final String productName;
  final String? productImage;
  final int quantity;
  final double unitPrice;
  final double totalPrice;
  final String? selectedSize;
  final String status;
  
  // New fields for delivery tracking
  final String? deliveryTrack;

  OrderItem({
    required this.id,
    required this.orderId,
    required this.productName,
    this.productImage,
    required this.quantity,
    required this.unitPrice,
    required this.totalPrice,
    this.selectedSize,
    required this.status,
    this.deliveryTrack,
  });

  factory OrderItem.fromJson(Map<String, dynamic> json) {
    return OrderItem(
      id: json['id'] ?? 0,
      orderId: json['order_id'] ?? 0,
      productName: json['product_name'] ?? '',
      productImage: json['product_image'],
      quantity: json['quantity'] ?? 0,
      unitPrice: (json['unit_price'] ?? 0).toDouble(),
      totalPrice: (json['total_price'] ?? 0).toDouble(),
      selectedSize: json['selected_size'],
      status: json['status'] ?? 'pending',
      deliveryTrack: json['delivery_track'],
    );
  }

  String get deliveryTrackDisplay {
    switch (deliveryTrack?.toLowerCase()) {
      case 'cancel_pickup':
        return 'Cancel Pickup';
      case 'exchange_pickup':
        return 'Exchange Pickup';
      default:
        return 'Normal Delivery';
    }
  }
}

class Customer {
  final int id;
  final String username;
  final String email;
  final String? phoneNumber;

  Customer({
    required this.id,
    required this.username,
    required this.email,
    this.phoneNumber,
  });

  factory Customer.fromJson(Map<String, dynamic> json) {
    return Customer(
      id: json['id'] ?? 0,
      username: json['username'] ?? '',
      email: json['email'] ?? '',
      phoneNumber: json['phone_number'],
    );
  }
}

enum OrderStatus {
  all('all', 'All Orders'),
  pending('pending', 'Pending'),
  confirmed('confirmed', 'Confirmed'),
  processing('processing', 'Processing'),
  shipped('shipped', 'Shipped'),
  outForDelivery('out_for_delivery', 'Out for Delivery'),
  delivered('delivered', 'Delivered'),
  cancelled('cancelled', 'Cancelled'),
  rejected('rejected', 'Rejected'),
  exchange('exchange', 'Exchange'),
  cancelPickup('cancel_pickup', 'Cancel Pickup');

  const OrderStatus(this.apiValue, this.displayName);

  final String apiValue;
  final String displayName;
}
