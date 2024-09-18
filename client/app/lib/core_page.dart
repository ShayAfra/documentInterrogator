import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:http/http.dart' as http;
import 'package:flongo_client/utilities/http_client.dart';
import 'dart:typed_data';
import 'dart:convert';

void main() => runApp(CoreApp());

class CoreApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Core Page',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: CorePage(),
    );
  }
}

class CorePage extends StatefulWidget {
  @override
  _CorePageState createState() => _CorePageState();
}

class _CorePageState extends State<CorePage> {
  final GlobalKey<ScaffoldState> _scaffoldKey = new GlobalKey<ScaffoldState>();
  List<String> questionHistory = []; // This will be filled with past questions
  String? selectedFile; // Nullable now
  List<String> uploadedFiles = []; // Placeholder for uploaded files
  String? currentQuestion; // Nullable now
  String? returnedAnswer; // Nullable now

  @override
  void initState() {
    super.initState();
    fetchFiles(); // Fetch files from the server when the component loads
  }

  Future<void> uploadFile(
      String fileName, String fileExtension, String fileBytesBase64) async {
    String? userId = HTTPClient
        .getIdentity(); // Ensure you have a way to get the current user's ID

    var url = Uri.parse('http://localhost:8080/files');
    var response = await http.post(url,
        body: jsonEncode({
          'user_id': userId,
          'fileName': fileName,
          'fileExtension': fileExtension,
          'fileData': fileBytesBase64,
        }),
        headers: {
          'Content-Type': 'application/json',
        });

    if (response.statusCode == 200) {
      print('File uploaded successfully: ${response.body}');
    } else {
      print('Failed to upload file: ${response.statusCode}');
    }
  }

  Future<void> sendQuestion() async {
    String userId =
        getCurrentUserId(); // Ensure you have a way to get the current user's ID

    var url = Uri.parse('http://localhost:8080/getAnswer');
    var response = await http.post(url,
        body: jsonEncode({
          'user_id': userId,
          'docName': selectedFile,
          'question': currentQuestion,
        }),
        headers: {
          'Content-Type': 'application/json',
        });

    if (response.statusCode == 200) {
      print('Question sent successfully: ${response.body}');
      setState(() {
        returnedAnswer = jsonDecode(response.body)['Answer'][0];
      });
    } else {
      print('Failed to send question: ${response.statusCode}');
    }
  }

  // Add a new function to fetch the file list
  Future<void> fetchFiles() async {
    String userId =
        getCurrentUserId(); // Ensure you have a way to get the current user's ID

    var url = Uri.parse('http://localhost:8080/files');
    var response = await http.post(url,
        body: jsonEncode({
          'user_id': userId,
        }),
        headers: {
          'Content-Type': 'application/json',
        });

    if (response.statusCode == 200) {
      List<dynamic> files = jsonDecode(response.body);
      setState(() {
        uploadedFiles =
            files.map((file) => file['file_name'] as String).toList();
      });
    } else {
      print('Failed to fetch files');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: _scaffoldKey,
      appBar: AppBar(
        title: Text('Core Page'),
        leading: IconButton(
          icon: Icon(Icons.menu),
          onPressed: () => _scaffoldKey.currentState?.openDrawer(),
          // Using null-aware operator ?. instead of .
        ),
      ),
      drawer: _buildDrawer(), // Collapsible history of questions
      body: _buildMainContent(),
    );
  }

  Widget _buildDrawer() {
    return Drawer(
      child: ListView(
        children: [
          DrawerHeader(
            child: Text('Question History'),
            decoration: BoxDecoration(
              color: Colors.blue,
            ),
          ),
          for (String question in questionHistory)
            ListTile(title: Text(question)),
          // Add more list tiles for each historical question
        ],
      ),
    );
  }

  Widget _buildFileUploadAndSelectorSection() {
    return Container(
      margin: EdgeInsets.symmetric(horizontal: 50.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: <Widget>[
          Container(
            alignment: Alignment.center,
            width: MediaQuery.of(context).size.width * 0.1,
            child: OutlinedButton(
              onPressed: () async {
                FilePickerResult? result =
                    await FilePicker.platform.pickFiles();
                if (result != null) {
                  PlatformFile file = result.files.first;
                  String? fileName = file.name;
                  String? fileExtension = file.extension;
                  Uint8List? fileBytes = file.bytes;
                  String fileBytesBase64 = base64Encode(
                      fileBytes!); // Ensure fileBytes is not null before encoding

                  uploadFile(fileName!, fileExtension!, fileBytesBase64)
                      .then((_) {
                    setState(() {
                      uploadedFiles.add(
                          fileName); // Assuming uploadedFiles is a List<String> of filenames
                      selectedFile =
                          fileName; // Assuming selectedFile is a String? for the currently selected file
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
              child: Text('Upload File'),
            ),
          ),
          Container(
            alignment: Alignment.center,
            width: MediaQuery.of(context).size.width * 0.1,
            child: _buildFileSelectorDropdown(),
          ),
        ],
      ),
    );
  }

  Widget _buildMainContent() {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        children: [
          Expanded(
            child: _buildAnswerSection(), // Where the AI's answer will be shown
            flex: 2, // Make the answer section take more space
          ),
          _buildFileUploadAndSelectorSection(), // To upload a new file and select from uploaded files
          SizedBox(height: 20), // Adds space above the question input section
          _buildQuestionInputSection(), // To write a new question
          SizedBox(height: 50), // Adds buffer space at the bottom of the page
        ],
      ),
    );
  }

  Widget _buildAnswerSection() {
    // Adjusting the width of the returned answer section
    return Container(
      padding: EdgeInsets.all(8.0),
      margin: EdgeInsets.symmetric(
          horizontal: 50.0), // Adds buffer space on the left and right
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey),
        borderRadius: BorderRadius.circular(8.0),
      ),
      child: Center(
        child: Text(
          returnedAnswer ?? 'Your answer will appear here.',
          style: TextStyle(fontSize: 16), // Adjust text size here
        ),
      ),
    );
  }

  Widget _buildFileSelectorDropdown() {
    // Placeholder for file selection dropdown
    return DropdownButton<String>(
      hint: Text("Choose a file"),
      value: selectedFile,
      onChanged: (String? newValue) {
        // Accepting nullable String
        setState(() {
          selectedFile = newValue;
        });
      },
      items: uploadedFiles.map<DropdownMenuItem<String>>((String value) {
        return DropdownMenuItem<String>(
          value: value,
          child: Text(value),
        );
      }).toList(),
    );
  }

  Widget _buildQuestionInputSection() {
    // Adjusting the width of the question input section
    return Container(
      margin: EdgeInsets.symmetric(
          horizontal: 50.0), // Adds buffer space on the left and right
      child: Row(
        children: <Widget>[
          Expanded(
            child: TextField(
              onChanged: (text) => setState(() => currentQuestion = text),
              decoration: InputDecoration(
                labelText: 'Enter your question',
                border: OutlineInputBorder(),
              ),
              style: TextStyle(fontSize: 16), // Adjust text size here
            ),
          ),
          SizedBox(width: 8),
          ElevatedButton(
            onPressed: sendQuestion,
            child: Text('Send'),
          ),
        ],
      ),
    );
  }
}
