import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../core/theme/app_theme.dart';

class SentinelDrawer extends StatelessWidget {
  const SentinelDrawer({super.key, required this.currentRoute});

  final String currentRoute;

  static const _navItems = [
    _NavItem(icon: Icons.dashboard_outlined, label: 'Dashboard', route: '/dashboard'),
    _NavItem(icon: Icons.list_alt_outlined, label: 'Requests', route: '/timeline'),
    _NavItem(icon: Icons.approval_outlined, label: 'Approval Queue', route: '/approvals'),
    _NavItem(icon: Icons.timeline_outlined, label: 'Incident Timeline', route: '/timeline'),
    _NavItem(icon: Icons.policy_outlined, label: 'Policies', route: '/policies'),
    _NavItem(icon: Icons.science_outlined, label: 'Attack Lab', route: '/lab'),
    _NavItem(icon: Icons.smart_toy_outlined, label: 'Agent Chat', route: '/chat'),
  ];

  @override
  Widget build(BuildContext context) {
    return Drawer(
      child: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 24),
              child: Row(
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      color: AppTheme.amber,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.shield, color: Colors.black, size: 20),
                  ),
                  const SizedBox(width: 12),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Sentinel AI',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w700,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                      Text(
                        'Governance Platform',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const Divider(height: 1),
            const SizedBox(height: 8),
            // Nav items
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.symmetric(horizontal: 8),
                itemCount: _navItems.length,
                itemBuilder: (context, i) {
                  final item = _navItems[i];
                  final isActive = currentRoute == item.route;
                  return _NavTile(
                    item: item,
                    isActive: isActive,
                    onTap: () {
                      Navigator.of(context).pop();
                      if (!isActive) context.go(item.route);
                    },
                  );
                },
              ),
            ),
            const Divider(height: 1),
            // Footer
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  const CircleAvatar(
                    radius: 16,
                    backgroundColor: AppTheme.amberDim,
                    child: Icon(Icons.person, color: AppTheme.amber, size: 18),
                  ),
                  const SizedBox(width: 10),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Admin', style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppTheme.textPrimary)),
                      Text('Security Admin', style: Theme.of(context).textTheme.bodySmall),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _NavItem {
  const _NavItem({required this.icon, required this.label, required this.route});
  final IconData icon;
  final String label;
  final String route;
}

class _NavTile extends StatelessWidget {
  const _NavTile({required this.item, required this.isActive, required this.onTap});
  final _NavItem item;
  final bool isActive;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 2),
      decoration: BoxDecoration(
        color: isActive ? AppTheme.amberDim.withValues(alpha: 0.3) : Colors.transparent,
        borderRadius: BorderRadius.circular(8),
        border: isActive ? Border.all(color: AppTheme.amber.withValues(alpha: 0.2)) : null,
      ),
      child: ListTile(
        leading: Icon(
          item.icon,
          color: isActive ? AppTheme.amber : AppTheme.textMuted,
          size: 20,
        ),
        title: Text(
          item.label,
          style: TextStyle(
            color: isActive ? AppTheme.amber : AppTheme.textSecondary,
            fontSize: 14,
            fontWeight: isActive ? FontWeight.w600 : FontWeight.w400,
          ),
        ),
        onTap: onTap,
        dense: true,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
    );
  }
}
