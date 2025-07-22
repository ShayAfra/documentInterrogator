import 'package:flutter/material.dart';
import 'package:app/theme/colors.dart';
import 'package:app/theme/spacing.dart';
import 'package:app/theme/typography.dart';
import 'package:app/theme/app_theme.dart';
import 'package:file_picker/file_picker.dart';
import 'package:http/http.dart' as http;
import 'package:flongo_client/utilities/http_client.dart';
import 'package:flongo_client/pages/api_page.dart';
import 'package:flongo_client/widgets/navbar/app_navbar.dart';
import 'dart:typed_data';
import 'dart:convert';
import 'package:flongo_client/pages/api_page.dart';
import '../../navbar.dart';
import 'widgets/shared_navbar.dart';

void main() => runApp(CoreApp());

class CoreApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Core Page',
      theme: darkTheme,
      home: CorePage(),
    );
  }
}


class CorePage extends API_Page {
  @override
  final AppNavBar navbar = NavBar();

  CorePage({super.key});

  @override
  _CorePageState createState() => _CorePageState();
}

class _CorePageState extends API_PageState<CorePage> {
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();
  List<Map<String, dynamic>> historyItems = [];
  
  // Fetch history from backend
  Future<void> fetchHistory() async {
    HTTPClient("/history").get(
      onSuccess: (response) {
        final List<dynamic> history = jsonDecode(response.body)["history"];
        setState(() {
          historyItems = history.cast<Map<String, dynamic>>();
        });
      },
      onError: (response) {
        print('Failed to fetch history: \\${response.toString()}');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to fetch history.', style: Theme.of(context).textTheme.bodyMedium)),
        );
      }
    );
  }
  String? selectedFile;
  List<String> uploadedFiles = [];
  String? currentQuestion;
  String? returnedAnswer;
  final TextEditingController questionController = TextEditingController();

  // Tab index: 0 = Upload File, 1 = Wikipedia Article
  int _tabIndex = 0;
  String? _wikiTitleInput;
  final TabController? _tabController = null; // Will be set in build


  @override
  void initState() {
    super.initState();
    fetchFiles();
    fetchHistory();
  }

  // Updated uploadFile function
  Future<void> uploadFile(
      String fileName, String fileExtension, String fileBytesBase64) async {

    HTTPClient("/files").post(
        body: {
          'fileName': fileName,
          'fileExtension': fileExtension,
          'fileData': fileBytesBase64,
        },
        onSuccess: (response) {
          print('File uploaded successfully: ${response.body}');
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('File uploaded successfully!', style: Theme.of(context).textTheme.bodyMedium)),
          );
        },
        onError: (response) {
          print('Failed to upload file: ${response.statusCode}');
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Failed to upload file.', style: Theme.of(context).textTheme.bodyMedium)),
          );
        });

    // Removed user_id from the body since it's handled on the server-side
    // var response = await http.post(url,
    //     body: jsonEncode({
    //       'fileName': fileName,
    //       'fileExtension': fileExtension,
    //       'fileData': fileBytesBase64,
    //     }),
    //     headers: {
    //       'Content-Type': 'application/json',
    //     });

    // if (response.statusCode == 200) {
    //   print('File uploaded successfully: ${response.body}');
    //   ScaffoldMessenger.of(context).showSnackBar(
    //     SnackBar(content: Text('File uploaded successfully!')),
    //   );
    // } else {
    //   print('Failed to upload file: ${response.statusCode}');
    //   ScaffoldMessenger.of(context).showSnackBar(
    //     SnackBar(content: Text('Failed to upload file.')),
    //   );
    // }
  }

  // Updated sendQuestion function
  Future<void> sendQuestion() async {
    if (_tabIndex == 0) {
      // Upload File tab
      HTTPClient("/getAnswer").post(
        body: {
          'docName': selectedFile,
          'question': currentQuestion,
        },
        onSuccess: (response) {
          print('Question sent successfully: ${response.body}');
          setState(() {
            returnedAnswer = jsonDecode(response.body)['Answer'];
          });
        },
        onError: (response) {
          print('Failed to send question: ${response.statusCode}');
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Failed to send question.', style: Theme.of(context).textTheme.bodyMedium)),
          );
        }
      );
    } else {
      // Wikipedia Article tab
      if (_wikiTitleInput == null || _wikiTitleInput!.trim().isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Please enter a Wikipedia article title.', style: Theme.of(context).textTheme.bodyMedium)),
        );
        return;
      }
      HTTPClient("/getAnswer").post(
        body: {
          'docName': _wikiTitleInput,
          'question': currentQuestion,
          'wiki': true, // Optional: signal backend this is a wiki request
        },
        onSuccess: (response) {
          print('Wiki question sent successfully: ${response.body}');
          setState(() {
            returnedAnswer = jsonDecode(response.body)['Answer'];
          });
        },
        onError: (response) {
          print('Failed to send wiki question: ${response.statusCode}');
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Failed to send Wikipedia question.', style: Theme.of(context).textTheme.bodyMedium)),
          );
        }
      );
    }
  }

  // Add a new function to fetch the file list
  // Updated fetchFiles function
  Future<void> fetchFiles() async {
    HTTPClient("/files").get(
      // Function that runs on API call success
      onSuccess: (response) {
        List<dynamic> files = jsonDecode(response.body);
        setState(() {
          uploadedFiles =
              files.map((file) => file['file_name'] as String).toList();
        });
      },
      // Function that runs on API 
      onError: (response) {
        print('Failed to fetch files: ${response.toString()}');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to fetch files.', style: Theme.of(context).textTheme.bodyMedium)),
        );
      } 
    );

  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: _scaffoldKey,
      appBar: SharedNavBar(
        showHamburger: true,
        onHamburgerPressed: () => _scaffoldKey.currentState?.openDrawer(),
        onNewQuestion: () {
          setState(() {
            currentQuestion = null;
            returnedAnswer = null;
            questionController.clear();
          });
        },
      ),
      drawer: _buildDrawer(),
      body: _buildMainContent(),
    );
  }

  Widget _buildDrawer() {
    return Drawer(
      child: ListView(
        children: [
          DrawerHeader(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Question History', style: Theme.of(context).textTheme.headlineMedium),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    icon: Icon(Icons.add, color: Theme.of(context).colorScheme.primary),
                    label: Text('New Question', style: Theme.of(context).textTheme.labelLarge?.copyWith(color: Theme.of(context).colorScheme.primary)),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Theme.of(context).colorScheme.primary,
                      side: BorderSide(color: Theme.of(context).colorScheme.primary),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    onPressed: () {
                      setState(() {
                        currentQuestion = null;
                        returnedAnswer = null;
                        questionController.clear();
                      });
                    },
                  ),
                ),
              ],
            ),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surface,
            ),
          ),
          for (final item in historyItems.reversed)
            ListTile(
              title: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(item['question'] ?? '', style: Theme.of(context).textTheme.bodyMedium),
                  if (item['doc_name'] != null && item['doc_name'].toString().isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 2.0),
                      child: Text('File: ${item['doc_name']}', style: Theme.of(context).textTheme.labelLarge?.copyWith(color: Theme.of(context).colorScheme.secondary)),
                    ),
                  if (item['answer'] != null && item['answer'].toString().isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 2.0),
                      child: Text(item['answer'], style: Theme.of(context).textTheme.labelLarge),
                    ),
                ],
              ),
              trailing: IconButton(
                icon: Icon(Icons.delete, color: Theme.of(context).colorScheme.error),
                tooltip: 'Delete history entry',
                onPressed: () async {
                  final entryId = item['_id'];
                  HTTPClient('/history').post(
                    body: {'entry_id': entryId},
                    onSuccess: (response) {
                      setState(() {
                        historyItems.removeWhere((h) => h['_id'] == entryId);
                      });
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('History entry deleted.', style: Theme.of(context).textTheme.bodyMedium)),
                      );
                    },
                    onError: (response) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('Failed to delete history entry.', style: Theme.of(context).textTheme.bodyMedium)),
                      );
                    },
                  );
                },
              ),
              onTap: () {
                setState(() {
                  currentQuestion = item['question'];
                  returnedAnswer = item['answer'];
                  questionController.text = item['question'] ?? '';
                });
                Navigator.of(context).pop(); // Close the drawer
              },
            ),
        ],
      ),
    );
  }

  Widget _buildFileUploadAndSelectorSection(TabController tabController) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: AppSpacing.spacingXL + AppSpacing.spacingL),
      child: Row(
        children: <Widget>[
          // Tab selector on the left
          Container(
            width: MediaQuery.of(context).size.width * 0.25,
            child: TabBar(
              controller: tabController,
              tabs: const [
                Tab(text: 'Upload File'),
                Tab(text: 'Wikipedia Article'),
              ],
              labelColor: Theme.of(context).colorScheme.primary,
              unselectedLabelColor: Theme.of(context).colorScheme.onSurface,
              indicatorColor: Theme.of(context).colorScheme.primary,
            ),
          ),
          // Spacer
          const SizedBox(width: AppSpacing.spacingL),
          // File upload and dropdown (only show if Upload File tab is active)
          if (_tabIndex == 0) ...[
            Expanded(
              child: Row(
                children: [
                  Expanded(child: Container()),
                  Container(
                    width: MediaQuery.of(context).size.width * 0.1,
                    alignment: Alignment.center,
                    child: OutlinedButton(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: Theme.of(context).colorScheme.primary,
                        textStyle: Theme.of(context).textTheme.labelLarge,
                        side: BorderSide(color: Theme.of(context).colorScheme.primary),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      onPressed: () async {
                        FilePickerResult? result =
                            await FilePicker.platform.pickFiles();
                        if (result != null) {
                          PlatformFile file = result.files.first;
                          String? fileName = file.name;
                          String? fileExtension = file.extension;
                          Uint8List? fileBytes = file.bytes;
                          String fileBytesBase64 = base64Encode(
                              fileBytes!);

                          uploadFile(fileName!, fileExtension!, fileBytesBase64)
                              .then((_) {
                            setState(() {
                              uploadedFiles.add(fileName);
                              selectedFile = fileName;
                            });
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('File uploaded successfully!')),
                            );
                          }).catchError((error) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('Failed to upload file.')),
                            );
                          });
                        } else {
                          print("No file selected");
                        }
                      },
                      child: const Text('Upload File'),
                    ),
                  ),
                  SizedBox(width: 256),
                  Container(
                    width: MediaQuery.of(context).size.width * 0.1,
                    alignment: Alignment.center,
                    child: _buildFileSelectorDropdown(),
                  ),
                  Expanded(child: Container()),
                ],
              ),
            ),
          ],
          // Wikipedia input (only show if Wikipedia Article tab is active)
          if (_tabIndex == 1) ...[
            Expanded(
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    width: MediaQuery.of(context).size.width * 0.75 * 0.5, // 75% of previous Expanded width (which was about 50% of axis)
                    child: TextField(
                      onChanged: (text) => setState(() => _wikiTitleInput = text),
                      decoration: InputDecoration(
                        labelText: 'Wikipedia Article Title',
                        border: const OutlineInputBorder(),
                        labelStyle: Theme.of(context).textTheme.labelLarge,
                      ),
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildMainContent() {
    return DefaultTabController(
      length: 2,
      initialIndex: _tabIndex,
      child: Builder(
        builder: (context) {
          final TabController tabController = DefaultTabController.of(context);
          tabController.addListener(() {
            if (_tabIndex != tabController.index) {
              setState(() {
                _tabIndex = tabController.index;
              });
            }
          });
          return Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              children: [
                Expanded(
                  child: _buildAnswerSection(),
                  flex: 2,
                ),
                const SizedBox(height: AppSpacing.spacingL),
                _buildFileUploadAndSelectorSection(tabController),
                const SizedBox(height: AppSpacing.spacingL + AppSpacing.spacingS),
                _buildQuestionInputSection(),
                const SizedBox(height: AppSpacing.spacingXL + AppSpacing.spacingS),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildAnswerSection() {
    // Adjusting the width of the returned answer section
    return Container(
      padding: const EdgeInsets.all(AppSpacing.spacingS),
      margin: EdgeInsets.symmetric(
          horizontal: 50.0), // Adds buffer space on the left and right
      decoration: BoxDecoration(
        border: Border.all(color: Theme.of(context).dividerColor),
        borderRadius: BorderRadius.circular(12.0),
      ),
      child: Center(
        child: Text(
          returnedAnswer ?? 'Your answer will appear here.',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
      ),
    );
  }

  Widget _buildFileSelectorDropdown() {
    // Placeholder for file selection dropdown
    return Container(
  decoration: BoxDecoration(
    border: Border.all(
      color: Theme.of(context).colorScheme.primary,
      width: 1.5,
    ),
    borderRadius: BorderRadius.circular(12),
  ),
  padding: const EdgeInsets.all(AppSpacing.spacingXS),
  child: DropdownButtonHideUnderline(
    child: DropdownButton<String>(
      hint: Padding(
        padding: const EdgeInsets.only(left: AppSpacing.spacingS),
        child: Text("Choose a file", style: Theme.of(context).textTheme.labelLarge),
      ),
      value: selectedFile,
      onChanged: (String? newValue) {
        setState(() {
          selectedFile = newValue;
        });
      },
      items: uploadedFiles.map<DropdownMenuItem<String>>((String value) {
        return DropdownMenuItem<String>(
          value: value,
          child: Text(value, style: Theme.of(context).textTheme.labelLarge),
        );
      }).toList(),
      isExpanded: true,
      dropdownColor: Theme.of(context).colorScheme.surface,
    ),
  ),
);
  }

  Widget _buildQuestionInputSection() {
    // Adjusting the width of the question input section
    bool isInputValid = _tabIndex == 0
        ? (selectedFile != null && selectedFile!.isNotEmpty && (currentQuestion != null && currentQuestion!.isNotEmpty))
        : (_wikiTitleInput != null && _wikiTitleInput!.isNotEmpty && (currentQuestion != null && currentQuestion!.isNotEmpty));
    return Container(
      margin: EdgeInsets.symmetric(
          horizontal: 50.0),
      child: Row(
        children: <Widget>[
          Expanded(
            child: TextField(
              controller: questionController,
              onChanged: (text) => setState(() => currentQuestion = text),
              decoration: InputDecoration(
                labelText: 'Enter your question',
                border: const OutlineInputBorder(),
                labelStyle: Theme.of(context).textTheme.labelLarge,
              ),
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
          const SizedBox(width: AppSpacing.spacingS),
          ElevatedButton(
            onPressed: isInputValid ? sendQuestion : null,
            style: ElevatedButton.styleFrom(
              backgroundColor: Theme.of(context).colorScheme.primary,
              foregroundColor: Theme.of(context).colorScheme.onPrimary,
              textStyle: Theme.of(context).textTheme.labelLarge,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              elevation: 2,
            ),
            child: const Text('Send'),
          ),
        ],
      ),
    );
  }
}
