import 'package:flutter/material.dart';
import 'view_orders_screen.dart';

// Example of how to use the ViewOrdersScreen in your app
class DeliveryDashboard extends StatelessWidget {
  final String authToken;
  
  const DeliveryDashboard({
    super.key,
    required this.authToken,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Delivery Dashboard'),
        backgroundColor: Colors.blue[600],
        foregroundColor: Colors.white,
      ),
      body: Column(
        children: [
          // Dashboard stats or other widgets
          Container(
            padding: const EdgeInsets.all(16),
            child: const Text(
              'Welcome to your delivery dashboard!',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
          ),
          
          // Navigation buttons
          Expanded(
            child: GridView.count(
              crossAxisCount: 2,
              padding: const EdgeInsets.all(16),
              crossAxisSpacing: 16,
              mainAxisSpacing: 16,
              children: [
                _buildDashboardCard(
                  context,
                  'View Orders',
                  Icons.list_alt,
                  Colors.blue,
                  () => _navigateToViewOrders(context),
                ),
                _buildDashboardCard(
                  context,
                  'Active Orders',
                  Icons.local_shipping,
                  Colors.green,
                  () => _navigateToActiveOrders(context),
                ),
                _buildDashboardCard(
                  context,
                  'Completed',
                  Icons.check_circle,
                  Colors.orange,
                  () => _navigateToCompletedOrders(context),
                ),
                _buildDashboardCard(
                  context,
                  'Profile',
                  Icons.person,
                  Colors.purple,
                  () => _navigateToProfile(context),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDashboardCard(
    BuildContext context,
    String title,
    IconData icon,
    Color color,
    VoidCallback onTap,
  ) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            gradient: LinearGradient(
              colors: [color.withOpacity(0.1), color.withOpacity(0.05)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 48,
                color: color,
              ),
              const SizedBox(height: 12),
              Text(
                title,
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _navigateToViewOrders(BuildContext context) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ViewOrdersScreen(authToken: authToken),
      ),
    );
  }

  void _navigateToActiveOrders(BuildContext context) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ViewOrdersScreen(
          authToken: authToken,
          // You can modify ViewOrdersScreen to accept initial status
        ),
      ),
    );
  }

  void _navigateToCompletedOrders(BuildContext context) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ViewOrdersScreen(
          authToken: authToken,
          // You can modify ViewOrdersScreen to accept initial status
        ),
      ),
    );
  }

  void _navigateToProfile(BuildContext context) {
    // Navigate to profile screen
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Profile screen not implemented yet')),
    );
  }
}

// Example of how to integrate with your existing navigation
class MainNavigationExample extends StatelessWidget {
  final String authToken;
  
  const MainNavigationExample({
    super.key,
    required this.authToken,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: ViewOrdersScreen(authToken: authToken),
      bottomNavigationBar: BottomNavigationBar(
        type: BottomNavigationBarType.fixed,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home),
            label: 'Dashboard',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.list_alt),
            label: 'Orders',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person),
            label: 'Profile',
          ),
        ],
        onTap: (index) {
          switch (index) {
            case 0:
              // Navigate to dashboard
              break;
            case 1:
              // Already on orders screen
              break;
            case 2:
              // Navigate to profile
              break;
          }
        },
      ),
    );
  }
}
