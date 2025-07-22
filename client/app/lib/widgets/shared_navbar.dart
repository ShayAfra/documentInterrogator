import 'package:flutter/material.dart';
import '../theme/colors.dart';
import '../theme/spacing.dart';
import '../theme/typography.dart';
import '../theme/app_theme.dart';

class SharedNavBar extends StatelessWidget implements PreferredSizeWidget {
  final bool showHamburger;
  final VoidCallback? onHamburgerPressed;
  final VoidCallback? onNewQuestion;

  const SharedNavBar({
    Key? key,
    this.showHamburger = false,
    this.onHamburgerPressed,
    this.onNewQuestion,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return AppBar(
      automaticallyImplyLeading: false,
      leadingWidth: showHamburger && onNewQuestion != null ? 150 : null,
      leading: showHamburger
          ? SizedBox(
              width: 150,
              child: Row(
                mainAxisSize: MainAxisSize.max,
                children: [
                  IconButton(
                    icon: Icon(Icons.menu, color: Theme.of(context).iconTheme.color),
                    onPressed: onHamburgerPressed,
                  ),
                  Flexible(
                    child: OutlinedButton.icon(
                      icon: Icon(Icons.add, color: Theme.of(context).colorScheme.primary, size: 18),
                      label: FittedBox(
                        fit: BoxFit.scaleDown,
                        child: Text('New', style: Theme.of(context).textTheme.labelLarge?.copyWith(color: Theme.of(context).colorScheme.primary)),
                      ),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: Theme.of(context).colorScheme.primary,
                        side: BorderSide(color: Theme.of(context).colorScheme.primary),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 0),
                        minimumSize: const Size(0, 36),
                      ),
                      onPressed: onNewQuestion,
                    ),
                  ),
                ],
              ),
            )
          : null,
      title: Text(
        'Document Interrogator',
        style: Theme.of(context).textTheme.headlineMedium,
      ),
      centerTitle: true,
      backgroundColor: Theme.of(context).colorScheme.surface,
    );
  }

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);
}
