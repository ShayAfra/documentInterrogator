import 'package:app/theme/colors.dart';
import 'package:app/theme/spacing.dart';
import 'package:app/theme/typography.dart';
import 'package:app/theme/app_theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

class SignUpForm extends StatelessWidget {
  final Function(Map<String, String>) onSubmit;
  final String? errorMessage;

  SignUpForm({super.key, required this.onSubmit, this.errorMessage});

  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _emailController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return ConstrainedBox(
      constraints: const BoxConstraints(
        minWidth: 500, // Set a minimum width for the form
        maxWidth: 800, // And a maximum width
      ),
      child: Form(
        key: _formKey,
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.spacingL),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (errorMessage != null) 
                  ...[
                    Text(errorMessage!, style: AppTypography.labelLarge.copyWith(color: AppColors.clrError)),
                    const SizedBox(height: AppSpacing.spacingXL - AppSpacing.spacingS),
                  ],
                SvgPicture.asset('assets/images/logo_growing.svg', width: 100, height: 100),
                TextFormField(
                  controller: _emailController,
                  decoration: const InputDecoration(labelText: 'Email Address'),
                ),
                Row(
                  children: [
                    Expanded(
                      child: TextFormField(
                        controller: _firstNameController,
                        decoration: const InputDecoration(labelText: 'First Name'),
                      ),
                    ),
                    const SizedBox(width: AppSpacing.spacingS + AppSpacing.spacingXS),
                    Expanded(
                      child: TextFormField(
                        controller: _lastNameController,
                        decoration: const InputDecoration(labelText: 'Last Name'),
                      ),
                    ),
                  ],
                ),
                TextFormField(
                  controller: _usernameController,
                  decoration: const InputDecoration(labelText: 'Username'),
                ),
                TextFormField(
                  controller: _passwordController,
                  decoration: const InputDecoration(labelText: 'Password'),
                  obscureText: true,
                ),
                const SizedBox(height: AppSpacing.spacingL + AppSpacing.spacingS),
                ElevatedButton(
                  onPressed: () {
                    if (_formKey.currentState!.validate()) {
                      onSubmit({
                        'username': _usernameController.text,
                        'password': _passwordController.text,
                        'first_name': _firstNameController.text,
                        'last_name': _lastNameController.text,
                        'email_address': _emailController.text,
                      });
                    }
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Theme.of(context).colorScheme.primary,
                    foregroundColor: Theme.of(context).colorScheme.onPrimary,
                    minimumSize: const Size(200, 65),
                    textStyle: Theme.of(context).textTheme.labelLarge,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    elevation: 2,
                  ),
                  child: Text('Sign Up', style: Theme.of(context).textTheme.labelLarge),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
