import 'package:flongo_client/utilities/http_client.dart';
import 'package:flongo_client/utilities/transitions/fade_to_black_transition.dart';
import 'package:flongo_client/widgets/widgets.dart';
import 'package:flutter/material.dart';
import 'package:app/theme/colors.dart';
import 'package:app/theme/spacing.dart';
import 'package:app/theme/typography.dart';
import 'package:app/theme/app_theme.dart';

class NavBar extends AppNavBar {
  @override
  List<NavBarItem> getNavbarItems() => [
        NavBarItem(
            icon: Icons.home,
            title: 'Home',
            routeName: '/home',
            routeArguments: {
              "_animation": FadeToBlackTransition.transitionsBuilder,
              "_animation_duration": 400
            },
            inaccessibleRoutes: [
              '/'
            ]),
        if (HTTPClient.isAuthenticated()) ...[
          NavBarItem(
              icon: Icons.person,
              title: 'User',
              routeName: '/user',
              routeArguments: {
                "_animation": FadeToBlackTransition.transitionsBuilder,
                "_animation_duration": 400
              }),
        ],
        if (HTTPClient.isAdminAuthenticated()) ...[
          NavBarItem(
              icon: Icons.people,
              title: 'Users',
              routeName: '/users',
              routeArguments: {
                "_animation": FadeToBlackTransition.transitionsBuilder,
                "_animation_duration": 400
              }),
          NavBarItem(
              icon: Icons.settings,
              title: 'Config',
              routeName: '/config',
              routeArguments: {
                "_animation": FadeToBlackTransition.transitionsBuilder,
                "_animation_duration": 400
              }),
        ]
      ];

  @override
  Widget getNavbarHeader() => Builder(
    builder: (context) => UserAccountsDrawerHeader(
      accountName: Text(
        HTTPClient.getUsername() ?? 'Guest',
        style: Theme.of(context).textTheme.bodyMedium,
      ),
      accountEmail: Text(
        HTTPClient.isAuthenticated()
            ? "Email: ${HTTPClient.getEmail() ?? 'None'}"
            : 'Please Login',
        style: Theme.of(context).textTheme.labelLarge,
      ),
      currentAccountPicture: CircleAvatar(
        backgroundColor: Theme.of(context).colorScheme.surface,
      ),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.primary,
      ),
    ),
  );
}
