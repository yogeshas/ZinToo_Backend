import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:zintoomobile/features/dashboard/widgets/order_tab_button.dart';
import 'package:zintoomobile/features/dashboard/widgets/section_header.dart';
import 'package:zintoomobile/features/dashboard/screens/view_orders.dart';
import 'package:zintoomobile/features/dashboard/screens/approved_orders.dart';
import 'package:zintoomobile/features/dashboard/screens/cancelled_orders.dart';
import '../../auth/screens/login_screen.dart';
import './account_screen.dart';

class DeliveryDashboard extends StatefulWidget {
  final String email;
  const DeliveryDashboard({Key? key, required this.email}) : super(key: key);

  @override
  State<DeliveryDashboard> createState() => _DeliveryDashboardState();
}

class _DeliveryDashboardState extends State<DeliveryDashboard> {
  int _currentIndex = 0;
  int _selectedTab = 0;
  DateTime _selectedDate = DateTime.now();
  String? _authToken;

  @override
  void initState() {
    super.initState();
    _loadAuthToken();
  }

  Future<void> _loadAuthToken() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('authToken');
    setState(() {
      _authToken = token;
    });
  }

  List<Widget> get _orderScreens {
    return [
      ViewOrdersScreen(authToken: _authToken ?? ''),
      ApprovedOrdersScreen(),
      CancelledOrdersScreen(),
    ];
  }

  void _onDatePicked() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime(2020),
      lastDate: DateTime(2100),
    );
    if (picked != null && picked != _selectedDate) setState(() => _selectedDate = picked);
  }

  @override
  Widget build(BuildContext context) {
    // Helper: pill-style tab
    Widget _pillTab(String label, int idx) {
      final bool selected = _selectedTab == idx;
      return GestureDetector(
        onTap: () => setState(() => _selectedTab = idx),
        child: Container(
          margin: const EdgeInsets.only(right: 8),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          decoration: BoxDecoration(
            color: selected ? Colors.orange.shade600 : Colors.white,
            borderRadius: BorderRadius.circular(24),
            border: Border.all(
              color: selected ? Colors.orange.shade600 : const Color(0xFFE8EAEC),
            ),
            boxShadow: [
              BoxShadow(
                color: selected ? Colors.orange.shade50 : Colors.black.withOpacity(0.03),
                blurRadius: selected ? 14 : 8,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Text(
            label,
            style: TextStyle(
              fontWeight: FontWeight.w600,
              color: selected ? Colors.white : Colors.black87,
              fontSize: 14,
            ),
          ),
        ),
      );
    }

    // Main Orders tab content
    Widget _ordersTab() {
      return SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 560),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: SingleChildScrollView(
                          scrollDirection: Axis.horizontal,
                          child: Row(
                            children: [
                              _pillTab("View Order", 0),
                              _pillTab("Approve Order", 1),
                              _pillTab("Reject Order", 2),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                    ],
                  ),
                  const SizedBox(height: 18),
                  Expanded(
                    child: Container(
                      width: double.infinity,
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(18),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.04),
                            blurRadius: 18,
                            offset: const Offset(0, 8),
                          )
                        ],
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(18.0),
                        child: _authToken != null 
                            ? _orderScreens[_selectedTab]
                            : const Center(
                                child: Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    CircularProgressIndicator(),
                                    SizedBox(height: 16),
                                    Text('Loading...'),
                                  ],
                                ),
                              ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      );
    }

    // Account tab UI
    Widget _accountTab() {
      return SafeArea(
        child: Center(
          child: SingleChildScrollView(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 560),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
                child: Column(
                  children: [
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(18),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.04),
                            blurRadius: 18,
                            offset: const Offset(0, 8),
                          )
                        ],
                      ),
                      child: Column(
                        children: [
                          Container(
                            height: 92,
                            width: 92,
                            decoration: BoxDecoration(
                              color: Colors.orange.shade50,
                              shape: BoxShape.circle,
                            ),
                            child: Icon(Icons.person, size: 46, color: Colors.orange.shade700),
                          ),
                          const SizedBox(height: 12),
                          Text(widget.email, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                          const SizedBox(height: 8),
                          Text(
                            "Member since Jan 2023",
                            style: TextStyle(color: Colors.black.withOpacity(0.6)),
                          ),
                          const SizedBox(height: 16),
                          ElevatedButton.icon(
                            onPressed: () {},
                            icon: const Icon(Icons.mail_outline),
                            label: const Text("Manage Account"),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.orange.shade600,
                              foregroundColor: Colors.white,
                              minimumSize: const Size(double.infinity, 48),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                            ),
                          ),
                          const SizedBox(height: 12),
                          OutlinedButton(
                            onPressed: () async {
                              final prefs = await SharedPreferences.getInstance();
                              await prefs.remove('authToken');
                              await prefs.remove('email');

                              if (!mounted) return;

                              // Navigate back to login screen and clear history stack
                              Navigator.pushAndRemoveUntil(
                                context,
                                MaterialPageRoute(builder: (_) => const LoginScreen()),
                                    (route) => false,
                              );
                            },
                            child: const Text("Sign Out"),
                            style: OutlinedButton.styleFrom(
                              minimumSize: const Size(double.infinity, 48),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 18),
                    Row(
                      children: [
                        Expanded(
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 18),
                            margin: const EdgeInsets.only(right: 8),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(14),
                              boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.03), blurRadius: 10, offset: const Offset(0, 6))],
                            ),
                            child: Column(
                              children: const [
                                Icon(Icons.shopping_basket_outlined, size: 28),
                                SizedBox(height: 8),
                                Text("Orders", style: TextStyle(fontWeight: FontWeight.w700)),
                              ],
                            ),
                          ),
                        ),
                        Expanded(
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 18),
                            margin: const EdgeInsets.only(left: 8),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(14),
                              boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.03), blurRadius: 10, offset: const Offset(0, 6))],
                            ),
                            child: Column(
                              children: const [
                                Icon(Icons.mail_outline, size: 28),
                                SizedBox(height: 8),
                                Text("Messages", style: TextStyle(fontWeight: FontWeight.w700)),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      );
    }

    final bottomTabs = [
      _ordersTab(),
      _accountTab(),
    ];

    Widget _customBottomNav() {
      return Padding(
        padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        child: Container(
          height: 72,
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(24),
            boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.06), blurRadius: 18, offset: const Offset(0, 8))],
          ),
          child: Row(
            children: [
              Expanded(
                child: InkWell(
                  borderRadius: BorderRadius.circular(30),
                  onTap: () => setState(() => _currentIndex = 0),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 300),
                    curve: Curves.easeInOut,
                    padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                    decoration: BoxDecoration(
                      gradient: _currentIndex == 0
                          ? LinearGradient(
                        colors: [Colors.orange.shade600, Colors.deepOrangeAccent],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      )
                          : null,
                      color: _currentIndex == 0 ? null : Colors.white.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(30),
                      border: Border.all(
                        color: _currentIndex == 0 ? Colors.transparent : Colors.grey.shade300,
                        width: 1.2,
                      ),
                      boxShadow: _currentIndex == 0
                          ? [
                        BoxShadow(
                          color: Colors.orange.withOpacity(0.4),
                          blurRadius: 12,
                          offset: Offset(0, 4),
                        ),
                      ]
                          : [],
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          _currentIndex == 0 ? Icons.shopping_basket : Icons.shopping_basket_outlined,
                          color: _currentIndex == 0 ? Colors.white : Colors.black87,
                        ),
                        const SizedBox(width: 10),
                        Text(
                          "Orders",
                          style: TextStyle(
                            color: _currentIndex == 0 ? Colors.white : Colors.black87,
                            fontWeight: FontWeight.w600,
                            fontSize: 16,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: InkWell(
                  borderRadius: BorderRadius.circular(30),
                  onTap: () => setState(() => _currentIndex = 1),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 300),
                    curve: Curves.easeInOut,
                    padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                    decoration: BoxDecoration(
                      gradient: _currentIndex == 1
                          ? LinearGradient(
                        colors: [Colors.orange.shade600, Colors.deepOrangeAccent],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      )
                          : null,
                      color: _currentIndex == 1 ? null : Colors.white.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(30),
                      border: Border.all(
                        color: _currentIndex == 1 ? Colors.transparent : Colors.grey.shade300,
                        width: 1.2,
                      ),
                      boxShadow: _currentIndex == 1
                          ? [
                        BoxShadow(
                          color: Colors.orange.withOpacity(0.4),
                          blurRadius: 12,
                          offset: Offset(0, 4),
                        ),
                      ]
                          : [],
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          _currentIndex == 1 ? Icons.person : Icons.person_outline,
                          color: _currentIndex == 1 ? Colors.white : Colors.black87,
                        ),
                        const SizedBox(width: 10),
                        Text(
                          "Account",
                          style: TextStyle(
                            color: _currentIndex == 1 ? Colors.white : Colors.black87,
                            fontWeight: FontWeight.w600,
                            fontSize: 16,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: const Color(0xFFF6F7F9),
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(72),
        child: AppBar(
          backgroundColor: Colors.white,
          elevation: 0,
          automaticallyImplyLeading: false,
          title: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Image.asset("assets/images/logo.jpeg", height: 100),
                ],
              ),
              IconButton(
                icon: const Icon(Icons.notifications_none, color: Colors.black87),
                onPressed: () {},
              ),
            ],
          ),
        ),
      ),
      body: bottomTabs[_currentIndex],
      bottomNavigationBar: SafeArea(child: _customBottomNav()),
    );
  }
}
