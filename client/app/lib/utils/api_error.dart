import 'package:flutter/material.dart';

/// Handles API errors, rerouting to login on 401 and showing a message.
///
/// Usage:
///   onError: (response) => handleApiError(context, response, () {
///     // Existing error handling for non-401 errors
///   }),
void handleApiError(BuildContext context, dynamic response, [void Function()? onOtherError]) {
  if (response?.statusCode == 401) {
    Navigator.pushNamedAndRemoveUntil(context, '/', (route) => false);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          'Session expired. Please log in again.',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Colors.white),
        ),
        backgroundColor: Theme.of(context).colorScheme.error,
      ),
    );
  } else {
    if (onOtherError != null) {
      onOtherError();
    }
  }
}
