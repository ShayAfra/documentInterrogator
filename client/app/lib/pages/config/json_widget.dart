
import 'package:flongo_client/widgets/json_list_widget.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:app/theme/colors.dart';
import 'package:app/theme/spacing.dart';
import 'package:app/theme/typography.dart';
import 'package:app/theme/app_theme.dart';

class ConfigJSONWidget extends JSON_List_Widget {
  const ConfigJSONWidget({Key? key, required data, required apiURL, onRefresh}) : super(
    key: key, 
    data: data, 
    apiURL: apiURL,
    onRefresh: onRefresh
  );

  @override
  _ConfigJSONWidgetState createState() => _ConfigJSONWidgetState();
}

class MouseScrollBehavior extends MaterialScrollBehavior {
  // Override behavior methods and getters like dragDevices
  @override
  Set<PointerDeviceKind> get dragDevices => { 
    PointerDeviceKind.touch,
    PointerDeviceKind.mouse,
    PointerDeviceKind.trackpad
  };
}

class _ConfigJSONWidgetState extends JSONWidgetState {
  final ScrollController controller = ScrollController();

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(AppSpacing.spacingS),
          child: TextField(
            onChanged: filterData,
            decoration: InputDecoration(
              labelText: 'Search',
              border: const OutlineInputBorder(),
              labelStyle: Theme.of(context).textTheme.labelLarge,
            ),
          ),
        ),
        Expanded(
        child: RefreshIndicator(
          onRefresh: () async {
            if (widget.onRefresh != null) {
              await widget.onRefresh!();
              setState(() {
                data = filter(widget.data, currentSearchTerm);
              });
            }
            return Future.value();
          },
          child: ScrollConfiguration(
            behavior: MouseScrollBehavior(),
            child: ListView.builder(
            physics: const AlwaysScrollableScrollPhysics(),
            itemCount: data.length,
            itemBuilder: (BuildContext context, int index) {
              var item = data[index];
              return ListTile(
                leading: Icon(Icons.settings, color: Theme.of(context).iconTheme.color),
                title: Text(item['name'] ?? '', style: Theme.of(context).textTheme.bodyMedium),
                subtitle: Text('${item['value']}', style: Theme.of(context).textTheme.labelLarge),
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    IconButton(
                      icon: Icon(Icons.edit, color: Theme.of(context).colorScheme.primary),
                      onPressed: () => updateItem(item, index),
                    ),
                    IconButton(
                      icon: Icon(Icons.delete, color: Theme.of(context).colorScheme.error),
                      onPressed: () => deleteItem(item, index),
                    ),
                  ],
                ),
              );
            },
          )),
        )),
      ],
    );
  }
}