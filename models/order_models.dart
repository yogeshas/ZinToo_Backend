class Order {
  final int id;
  final String orderNumber;
  final String status;
  final String deliveryAddress;
  final String deliveryType;
  final String paymentMethod;
  final String paymentStatus;
  final double subtotal;
  final double deliveryFeeAmount;
  final double platformFee;
  final double discountAmount;
  final double totalAmount;
  final DateTime createdAt;
  final DateTime? updatedAt;
  final DateTime? estimatedDelivery;
  final int? deliveryGuyId;
  final DateTime? assignedAt;
  final String? deliveryNotes;
  final Customer? customer;
  final List<OrderItem> items;
  
  // New fields for delivery tracking
  final String? deliveryTrack;
  final String? overallStatus;
  final String? deliveryTrackDisplay;
  final List<OrderItem> assignedItems;

  Order({
    required this.id,
    required this.orderNumber,
    required this.status,
    required this.deliveryAddress,
    required this.deliveryType,
    required this.paymentMethod,
    required this.paymentStatus,
    required this.subtotal,
    required this.deliveryFeeAmount,
    required this.platformFee,
    required this.discountAmount,
    required this.totalAmount,
    required this.createdAt,
    this.updatedAt,
    this.estimatedDelivery,
    this.deliveryGuyId,
    this.assignedAt,
    this.deliveryNotes,
    this.customer,
    required this.items,
    this.deliveryTrack,
    this.overallStatus,
    this.deliveryTrackDisplay,
    this.assignedItems = const [],
  });

  factory Order.fromJson(Map<String, dynamic> json) {
    return Order(
      id: json['id'] ?? 0,
      orderNumber: json['order_number'] ?? '',
      status: json['status'] ?? 'pending',
      deliveryAddress: json['delivery_address'] ?? '',
      deliveryType: json['delivery_type'] ?? 'standard',
      paymentMethod: json['payment_method'] ?? 'cod',
      paymentStatus: json['payment_status'] ?? 'pending',
      subtotal: (json['subtotal'] ?? 0.0).toDouble(),
      deliveryFeeAmount: (json['delivery_fee_amount'] ?? 0.0).toDouble(),
      platformFee: (json['platform_fee'] ?? 0.0).toDouble(),
      discountAmount: (json['discount_amount'] ?? 0.0).toDouble(),
      totalAmount: (json['total_amount'] ?? 0.0).toDouble(),
      createdAt: DateTime.tryParse(json['created_at'] ?? '') ?? DateTime.now(),
      updatedAt: json['updated_at'] != null ? DateTime.tryParse(json['updated_at']) : null,
      estimatedDelivery: json['estimated_delivery'] != null ? DateTime.tryParse(json['estimated_delivery']) : null,
      deliveryGuyId: json['delivery_guy_id'],
      assignedAt: json['assigned_at'] != null ? DateTime.tryParse(json['assigned_at']) : null,
      deliveryNotes: json['delivery_notes'],
      customer: json['customer'] != null ? Customer.fromJson(json['customer']) : null,
      items: (json['items'] as List<dynamic>? ?? [])
          .map((item) => OrderItem.fromJson(item))
          .toList(),
      deliveryTrack: json['delivery_track'],
      overallStatus: json['overall_status'],
      deliveryTrackDisplay: json['delivery_track_display'],
      assignedItems: (json['assigned_items'] as List<dynamic>? ?? [])
          .map((item) => OrderItem.fromJson(item))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'order_number': orderNumber,
      'status': status,
      'delivery_address': deliveryAddress,
      'delivery_type': deliveryType,
      'payment_method': paymentMethod,
      'payment_status': paymentStatus,
      'subtotal': subtotal,
      'delivery_fee_amount': deliveryFeeAmount,
      'platform_fee': platformFee,
      'discount_amount': discountAmount,
      'total_amount': totalAmount,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
      'estimated_delivery': estimatedDelivery?.toIso8601String(),
      'delivery_guy_id': deliveryGuyId,
      'assigned_at': assignedAt?.toIso8601String(),
      'delivery_notes': deliveryNotes,
      'customer': customer?.toJson(),
      'items': items.map((item) => item.toJson()).toList(),
      'delivery_track': deliveryTrack,
      'overall_status': overallStatus,
      'delivery_track_display': deliveryTrackDisplay,
      'assigned_items': assignedItems.map((item) => item.toJson()).toList(),
    };
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

  String get statusColor {
    switch (status.toLowerCase()) {
      case 'pending':
        return '#FFA500'; // Orange
      case 'confirmed':
        return '#4CAF50'; // Green
      case 'processing':
        return '#2196F3'; // Blue
      case 'shipped':
        return '#9C27B0'; // Purple
      case 'out_for_delivery':
        return '#FF9800'; // Deep Orange
      case 'delivered':
        return '#4CAF50'; // Green
      case 'cancelled':
        return '#F44336'; // Red
      case 'rejected':
        return '#F44336'; // Red
      default:
        return '#757575'; // Grey
    }
  }

  String get paymentStatusDisplayName {
    switch (paymentStatus.toLowerCase()) {
      case 'pending':
        return 'Pending';
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      case 'refunded':
        return 'Refunded';
      default:
        return paymentStatus;
    }
  }

  String get paymentMethodDisplayName {
    switch (paymentMethod.toLowerCase()) {
      case 'cod':
        return 'Cash on Delivery';
      case 'wallet':
        return 'Wallet';
      case 'razorpay':
        return 'Online Payment';
      default:
        return paymentMethod;
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

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'username': username,
      'email': email,
      'phone_number': phoneNumber,
    };
  }
}

class OrderItem {
  final int id;
  final int productId;
  final String productName;
  final String? productImage;
  final int quantity;
  final double unitPrice;
  final double totalPrice;
  final String? selectedSize;
  final String status;
  final String? deliveryTrack;
  final String? deliveryTrackDisplay;
  final int? deliveryGuyId;

  OrderItem({
    required this.id,
    required this.productId,
    required this.productName,
    this.productImage,
    required this.quantity,
    required this.unitPrice,
    required this.totalPrice,
    this.selectedSize,
    this.status = 'pending',
    this.deliveryTrack,
    this.deliveryTrackDisplay,
    this.deliveryGuyId,
  });

  factory OrderItem.fromJson(Map<String, dynamic> json) {
    return OrderItem(
      id: json['id'] ?? 0,
      productId: json['product_id'] ?? 0,
      productName: json['product_name'] ?? '',
      productImage: json['product_image'],
      quantity: json['quantity'] ?? 0,
      unitPrice: (json['unit_price'] ?? 0.0).toDouble(),
      totalPrice: (json['total_price'] ?? 0.0).toDouble(),
      selectedSize: json['selected_size'],
      status: json['status'] ?? 'pending',
      deliveryTrack: json['delivery_track'],
      deliveryTrackDisplay: json['delivery_track_display'],
      deliveryGuyId: json['delivery_guy_id'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'product_id': productId,
      'product_name': productName,
      'product_image': productImage,
      'quantity': quantity,
      'unit_price': unitPrice,
      'total_price': totalPrice,
      'selected_size': selectedSize,
      'status': status,
      'delivery_track': deliveryTrack,
      'delivery_track_display': deliveryTrackDisplay,
      'delivery_guy_id': deliveryGuyId,
    };
  }
}

enum OrderStatus {
  all,
  pending,
  confirmed,
  processing,
  shipped,
  outForDelivery,
  delivered,
  cancelled,
  rejected,
  exchange,
  cancelPickup,
}

extension OrderStatusExtension on OrderStatus {
  String get displayName {
    switch (this) {
      case OrderStatus.all:
        return 'All Orders';
      case OrderStatus.pending:
        return 'Pending';
      case OrderStatus.confirmed:
        return 'Confirmed';
      case OrderStatus.processing:
        return 'Processing';
      case OrderStatus.shipped:
        return 'Shipped';
      case OrderStatus.outForDelivery:
        return 'Out for Delivery';
      case OrderStatus.delivered:
        return 'Delivered';
      case OrderStatus.cancelled:
        return 'Cancelled';
      case OrderStatus.rejected:
        return 'Rejected';
      case OrderStatus.exchange:
        return 'Exchange';
      case OrderStatus.cancelPickup:
        return 'Cancel Pickup';
    }
  }

  String get apiValue {
    switch (this) {
      case OrderStatus.all:
        return 'assigned';
      case OrderStatus.pending:
        return 'pending';
      case OrderStatus.confirmed:
        return 'confirmed';
      case OrderStatus.processing:
        return 'processing';
      case OrderStatus.shipped:
        return 'shipped';
      case OrderStatus.outForDelivery:
        return 'out_for_delivery';
      case OrderStatus.delivered:
        return 'delivered';
      case OrderStatus.cancelled:
        return 'cancelled';
      case OrderStatus.rejected:
        return 'rejected';
      case OrderStatus.exchange:
        return 'exchange';
      case OrderStatus.cancelPickup:
        return 'cancel_pickup';
    }
  }
}