import 'package:app/theme/colors.dart';
import 'package:app/theme/spacing.dart';
import 'package:app/theme/typography.dart';
import 'package:app/theme/app_theme.dart';
import 'package:app/utils/scroll_behavior.dart';
import 'package:flongo_client/utilities/http_client.dart';
import 'package:flongo_client/utilities/transitions/fade_to_black_transition.dart';
import 'package:flongo_client/widgets/json_widget.dart';
import 'package:flutter/material.dart';

class UserJSONWidget extends JSON_Widget {
  final Map data;
  final String apiURL;

  const UserJSONWidget({Key? key, required this.data, required this.apiURL})
      : super(key: key, data: data, apiURL: apiURL);

  @override
  UserJSONWidgetState createState() => UserJSONWidgetState();
}

class UserJSONWidgetState extends JSON_WidgetState<UserJSONWidget> {
  final List<String> updateFilter = [
    'username',
    'email_address',
    'createdOn',
    'roles',
    'is_email_validated'
  ];
  late Map data;

  @override
  void initState() {
    super.initState();
    data = widget.data;
  }

  @override
  Widget build(BuildContext context) {
    if (data.isNotEmpty) {
      return Scaffold(
          body: ScrollConfiguration(
        behavior: MouseScrollBehavior(),
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.spacingM),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: AppSpacing.spacingS + AppSpacing.spacingXS),
              _buildUserNameAndId(),
              _buildCreatedOn(),
              const SizedBox(height: AppSpacing.spacingS),
              const Divider(),
              _buildDetailRow('First Name', data['first_name']),
              const Divider(),
              _buildDetailRow('Last Name', data['last_name']),
              const Divider(),
              _buildDetailRow('Email Address', data['email_address']),
              const Divider(),
              _buildDetailRow(
                  'Email Validated', data['is_email_validated'].toString()),
              const Divider(),
              _buildDetailRow('Roles', data['roles'].join(', ')),
              const Divider(),
              const SizedBox(height: AppSpacing.spacingM - AppSpacing.spacingXS),
              _buildActionButtons(),
            ],
          ),
        ),
      ));
    }
    return const Center(child: Text("User has been deleted!"));
  }

  Widget _buildUserNameAndId() {
    return RichText(
      text: TextSpan(
        text: data['username'],
        style: AppTypography.headlineMedium,
        children: [
          TextSpan(
            text: ' (${data['_id']})',
            style: AppTypography.bodyMedium.copyWith(color: Colors.grey),
          ),
        ],
      ),
    );
  }

  Widget _buildCreatedOn() {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.spacingS),
      child: Text(
        "Created On: ${data['createdOn'] ?? ''}",
        style: AppTypography.labelLarge.copyWith(color: AppColors.clrLightA0),
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.spacingS + AppSpacing.spacingXS),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label.toUpperCase(), style: AppTypography.labelLarge.copyWith(fontWeight: FontWeight.bold)),
          const SizedBox(height: AppSpacing.spacingS),
          Text(value, style: AppTypography.bodyMedium),
        ],
      ),
    );
  }

  Widget _buildActionButtons() {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.spacingM),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _buildButton(
            Icons.edit,
            'Edit',
            AppColors.clrAccentA1,
            ["first_name", "last_name", "password"],
            updateItem,
            updateStateData,
          ),
          _buildButton(
            Icons.delete,
            'Delete',
            AppColors.clrError,
            ["_id"],
            deleteItem,
            (Map<String, dynamic> item, dynamic response) {
              deleteStateData(item, response);
              HTTPClient('/authenticate').logout(
                (response) {
                  Navigator.pushNamed(context, '/', arguments: {
                    "_animation": FadeToBlackTransition.transitionsBuilder,
                    "_animation_duration": 800
                  });
                },
                (response) {
                  Navigator.pushNamed(context, '/', arguments: {
                    "_animation": FadeToBlackTransition.transitionsBuilder,
                    "_animation_duration": 800
                  });
                },
              );
            },
          ),
        ],
      ),
    );
  }

  Map<String, dynamic> _buildDataSnippet(List<String> keys) {
    Map<String, dynamic> snippet = {};
    for (var key in keys) {
      snippet[key] = data[key];
    }

    return snippet;
  }

  Widget _buildButton(IconData icon, String label, Color color,
      List<String> dataKeys, Function callback, Function onSuccess) {
    return ElevatedButton.icon(
      icon: Icon(icon, size: 20, color: Theme.of(context).colorScheme.onPrimary),
      label: Text(label, style: Theme.of(context).textTheme.labelLarge),
      onPressed: () => callback(_buildDataSnippet(dataKeys),
          onSuccess: onSuccess),
      style: ElevatedButton.styleFrom(
        backgroundColor: color,
        foregroundColor: Theme.of(context).colorScheme.onPrimary,
        minimumSize: const Size(200, 65),
        textStyle: Theme.of(context).textTheme.labelLarge,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        elevation: 2,
      ),
    );
  }
}
