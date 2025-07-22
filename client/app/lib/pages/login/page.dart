import 'dart:convert';

import 'package:app/pages/login/signup/dialogue.dart';
import 'package:app/utils/scroll_behavior.dart';
import 'package:flongo_client/pages/api_page.dart';
import 'package:flongo_client/utilities/http_client.dart';
import 'package:flongo_client/utilities/transitions/fade_to_black_transition.dart';
import 'package:flongo_client/widgets/navbar/app_navbar.dart';
import 'package:flutter/material.dart';
import 'package:lottie/lottie.dart';

import '../../navbar.dart';
import '../../widgets/shared_navbar.dart';
import '../../theme/colors.dart';
import '../../theme/spacing.dart';
import '../../theme/typography.dart';
import '../../theme/app_theme.dart';

class LoginPage extends API_Page {
  @override
  final String apiURL = '/authenticate';
  @override
  final AppNavBar navbar = NavBar();

  final String homeURL;

  LoginPage({super.key, this.homeURL = '/home'});

  @override
  _LoginPageState createState() => _LoginPageState();
}

class _LoginPageState extends API_PageState<LoginPage>
    with TickerProviderStateMixin {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  late AnimationController _logoAnimationController =
      AnimationController(vsync: this);
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _logoAnimationController =
        AnimationController(vsync: this, duration: const Duration(seconds: 2));
  }

  @override
  void dispose() {
    _logoAnimationController.dispose();
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _onLoginSuccess() {
    _logoAnimationController.forward().then((_) {
      Navigator.pushNamed(context, widget.homeURL, arguments: {
        "_animation": FadeToBlackTransition.transitionsBuilder,
        "_animation_duration": 600
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const SharedNavBar(),
      body: ScrollConfiguration(
        behavior: MouseScrollBehavior(),
        child: SingleChildScrollView(
          child: Padding(
            padding: EdgeInsets.symmetric(
              vertical: 0.0,
              horizontal: MediaQuery.of(context).size.width * 0.1,
            ),
            child: Form(
              key: _formKey,
              child: SizedBox(
                height: MediaQuery.of(context).size.height -
                    kToolbarHeight -
                    48, // subtract navbar and a bit more
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    if (_errorMessage != null) ...[
                      Text(_errorMessage!,
                          style: AppTypography.labelLarge
                              .copyWith(color: AppColors.clrError)),
                      const SizedBox(height: AppSpacing.spacingM),
                    ],
                    Center(
                      child: SizedBox(
                        child: Container(
                          padding: const EdgeInsets.all(AppSpacing.spacingXL),
                          decoration: BoxDecoration(
                            color: AppColors.clrDarkA2,
                            borderRadius: BorderRadius.circular(24),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withOpacity(0.18),
                                blurRadius: 24,
                                offset: const Offset(0, 8),
                              ),
                            ],
                          ),
                          constraints: const BoxConstraints(
                            maxWidth: 420,
                          ),
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Lottie.asset(
                                'assets/animations/logo_animation.json',
                                controller: _logoAnimationController,
                                height: 200,
                                width: 200,
                                animate: false,
                              ),
                              const SizedBox(height: AppSpacing.spacingL),
                              TextFormField(
                                controller: _usernameController,
                                decoration: const InputDecoration(
                                    labelText: 'Username'),
                                validator: (value) =>
                                    value!.isEmpty ? 'Username required' : null,
                              ),
                              const SizedBox(height: AppSpacing.spacingM),
                              TextFormField(
                                controller: _passwordController,
                                decoration: const InputDecoration(
                                    labelText: 'Password'),
                                obscureText: true,
                                validator: (value) =>
                                    value!.isEmpty ? 'Password required' : null,
                              ),
                              const SizedBox(height: AppSpacing.spacingXL),
                              Row(
                                mainAxisAlignment:
                                    MainAxisAlignment.spaceEvenly,
                                children: [
                                  Expanded(
                                    child: ElevatedButton(
                                      onPressed: () {
                                        if (_formKey.currentState!.validate()) {
                                          HTTPClient(widget.apiURL).login(
                                              _usernameController.text,
                                              _passwordController.text,
                                              (response) => _onLoginSuccess(),
                                              (response) => setState(() {
                                                    if (response != null &&
                                                        response.body != null) {
                                                      _errorMessage =
                                                          jsonDecode(response
                                                              .body)['error'];
                                                    } else {
                                                      _errorMessage =
                                                          'Failed to authenticate!';
                                                    }
                                                  }));
                                        }
                                      },
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: Theme.of(context)
                                            .colorScheme
                                            .primary,
                                        foregroundColor: Theme.of(context)
                                            .colorScheme
                                            .onPrimary,
                                        minimumSize: const Size(120, 56),
                                        textStyle: Theme.of(context)
                                            .textTheme
                                            .labelLarge,
                                        shape: RoundedRectangleBorder(
                                            borderRadius:
                                                BorderRadius.circular(12)),
                                        elevation: 2,
                                      ),
                                      child: const Text('Login'),
                                    ),
                                  ),
                                  const SizedBox(width: AppSpacing.spacingL),
                                  Expanded(
                                    child: ElevatedButton(
                                      onPressed: () => showDialog(
                                        context: context,
                                        builder: (context) =>
                                            const SignUpDialog(),
                                      ),
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: Theme.of(context)
                                            .colorScheme
                                            .primary,
                                        foregroundColor: Theme.of(context)
                                            .colorScheme
                                            .onPrimary,
                                        minimumSize: const Size(120, 56),
                                        textStyle: Theme.of(context)
                                            .textTheme
                                            .labelLarge,
                                        shape: RoundedRectangleBorder(
                                            borderRadius:
                                                BorderRadius.circular(12)),
                                        elevation: 2,
                                      ),
                                      child: const Text('Sign Up'),
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
