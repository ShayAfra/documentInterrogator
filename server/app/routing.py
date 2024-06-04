from flongo_framework.api.routing import App_Routes, Route, Route_Handler, Default_Route_Handler

from flongo_framework.api.routing.route_permissions import Route_Permissions
from flongo_framework.api.responses import API_Message_Response
from flongo_framework.database import MongoDB_Database
from flongo_framework.config.enums.logs.log_levels import LOG_LEVELS

# User Management
from .routes.user.route import UserRouteHandler
from .routes.user.schema import  USER_ROUTE_REQUEST_SCHEMA
from .routes.user.transformer import USER_ROUTE_REQUEST_TRANSFORMER, USER_ROUTE_RESPONSE_TRANSFORMER

# User Authentication
from .routes.authenticate.route import AuthenticateRouteHandler
from .routes.authenticate.schema import AUTHENTICATION_ROUTE_REQUEST_SCHEMA
from .routes.authenticate.transformer import AUTHENTICATION_ROUTE_RESPONSE_TRANSFORMER

# Email Confirmation
from .routes.email_confirmation.route import Email_Confirmation_Route_Handler
from .routes.email_confirmation.schema import EMAIL_CONFIRMATION_ROUTE_REQUEST_SCHEMA

#LOOK HERE ITS IMPORTANT
#shays integrated server side- pre-format matching
#app
from flongo_framework.application import Application
#chatbot
from openai_client import Chat_Bot_Client
from openai_client import ROLE
# utils
from flongo_framework.api.routing.utils import Authentication_Util
#Routing
from flongo_framework.api.routing import App_Routes, Route, Route_Handler, Default_Route_Handler, Route_Permissions
from flongo_framework.api.responses import API_JSON_Response, API_Message_Response
from flongo_framework.config.settings import App_Settings, Flask_Settings, MongoDB_Settings
from flongo_framework.config.enums.logs.log_levels import LOG_LEVELS
from werkzeug.utils import secure_filename
import os
import shutil
import base64
import tempfile
from tempfile import NamedTemporaryFile
from pymongo import MongoClient
from bson import Binary
from dotenv import load_dotenv
from datetime import datetime
from .utilities.document_extract import ManagerDriver


load_dotenv()  # Load environment variables

# MongoDB setup
# MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
# client = MongoClient(MONGO_URI)
# db = client.your_database_name  # Use your actual database name
# files_collection = db.files  # Use your actual collection name for storing file data
client = MongoClient('mongodb://localhost:27017/')
db = client['file_db']  # Use your preferred DB name
files_collection = db['files']  # Use your preferred collection name
history_collection = db['history']
#VERY IMPORTANT
#PLEASE READ
#SHAYS ROUTE DEFINITONS PRE FORMAT MATCHING
ALLOWED_EXTENSIONS = {'doc', 'docx', 'pdf'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_get(request):
    file_name_with_extension = request.payload.get('docName')
    file_name_without_extension = os.path.splitext(file_name_with_extension)[0]
    directory = 'chroma_store'
    file_path = os.path.join(directory, file_name_without_extension)
    return API_Message_Response(file_path)

def delete_file(request):
    file_name = request.payload.get('file_name')
    directory = 'docs'
    file_path = os.path.join(directory, file_name)
    # Check if file exists
    if not os.path.isfile(file_path):
        return API_Message_Response(f"File {file_name} not found", status_code=404)
    # Attempt to delete the file
    try:
        os.remove(file_path)
        return API_Message_Response(f"File {file_name} deleted successfully")
    except Exception as e:
        return API_Message_Response(f"An error occurred: {e}", status_code=500)

# double check with Pete that logic order is
# also should i keep the old logic like is the file = request.files['file'] even necessary now, that the argument is different
def handle_file_upload(request):
    # Check if the post request has the file part
    if 'fileName' not in request.payload:
        return 'No file part in the request', 400
    file_name = request.payload['fileName']
    file_extension = request.payload['fileExtension']
    file_data_base64 = request.payload['fileData']
    # Decode the Base64 file data
    file_data_binary = base64.b64decode(file_data_base64)
    
    # Here you can choose to save the file directly to the filesystem,
    # but as per the requirement, we're storing the content in MongoDB.
    # MongoDB document schema example
    file_document = {
        'file_name': file_name,
        'file_extension': file_extension,
        'file_content': Binary(file_data_binary),
    }

    # Insert the document into MongoDB
    result = files_collection.insert_one(file_document)

    if result.inserted_id:
        return {'message': 'File uploaded successfully', 'id': str(result.inserted_id)}, 200
    else:
        return {'message': 'Failed to upload file'}, 500
    
    # filename = secure_filename(file.filename)
    # file.save(os.path.join('docs', filename))
    # return 'File uploaded successfully', 201
    
def list_files(request):
    # directory = '/Users/shay/Desktop/repo/documentInterrogator/server/app/utilities/docs'  # Folder where files are stored
    # files = os.listdir(directory)
    # # Create a numbered list of files
    # files_list = ' AP'.join(f"{index + 1}. {file}" for index, file in enumerate(files))
    # return API_Message_Response(files_list)
    files = files_collection.find({}, {'file_content': 0})  # Exclude file_content from the results
    file_list = [{
        'file_name': file['file_name'],
        'file_extension': file['file_extension'],
        'id': str(file['_id'])
    } for file in files]
    return API_Message_Response(file_list)


def delete_embedding(request):
    file_name_with_extension = request.payload.get('fileName')
    file_name_without_extension = os.path.splitext(file_name_with_extension)[0]
    directory = 'chroma_store'
    file_path = os.path.join(directory, file_name_without_extension)
    # Check if file exists
    # if not os.path.isfile(file_path):
    #     return API_Message_Response(f"File {file_name_without_extension} not found", status_code=404)
    # Attempt to delete the file
    try:
        shutil.rmtree(file_path)
        return API_Message_Response(f"Folder {file_name_without_extension} deleted successfully")
    except Exception as e:
        return API_Message_Response(f"An error occurred: {e}", status_code=500)

def handle_embedding_upload(request):
    # Check if the post request has the file part
    question = request.payload.get("question")
    file_name_with_extension = request.payload.get("docName")
    manager = ManagerDriver(file_name_with_extension, question)
    embedding = manager.get_embedding()
    # file_name_without_extension = os.path.splitext(file_name_with_extension)[0]
    # directory = 'chroma_store'
    # file_path = os.path.join(directory, file_name_without_extension)
    # with open(file_path, 'w') as file:
    #     file.write(embedding)  # Assuming embedding is a string or can be converted to a string
    return API_Message_Response(f"Embedding saved as {embedding}")
    
def list_embeddings(request):
    directory = 'chroma_store'  # Folder where files are stored
    embeddings = os.listdir(directory)
    # Create a numbered list of files
    embeddings_list = ' AP'.join(f"{index + 1}. {embedding}" for index, embedding in enumerate(embeddings))
    return API_Message_Response(embeddings_list)

def getDate(request):
    return API_Message_Response(datetime.now())

def makeAnswer(request):
    question = request.payload.get("question")
    docName = request.payload.get("docName")

    # Get binary file and its extension from DB
    with MongoDB_Database("files", "file_db") as filedb:
        result = filedb.find_one({"file_name": docName})
    
    file_content = result["file_content"]  # Assuming this is a base64 encoded string
    file_extension = result["file_extension"]  # Retrieve the file extension from the database

    temp_file_path = None
    try:        
        # Create a temporary file with the appropriate file extension
        with NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
            # Write the binary content to the temporary file
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        # Pass the file path and the question to get answer
        manager = ManagerDriver(temp_file_path, question)
        answer = manager.make_answer()

        return API_JSON_Response({"Answer": answer})
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return API_JSON_Response({"Error": str(e)})

    finally:
        # Ensure the temporary file is deleted after use
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

# def makeAnswer(request):
#     question = request.payload.get("question")
#     docName = request.payload.get("docName")
#     # Get binary file from DB
#     with MongoDB_Database("files", "file_db") as filedb:
#         result = filedb.find_one({"file_name": docName})
    
#     encoded_data = result["file_content"]
#     try:
#         file_binary = base64.b64decode(encoded_data)
#     except base64.binascii.Error as e:
#         print("Base64 decoding failed:", str(e))
#         return API_JSON_Response({"Error": "Failed to decode PDF data from base64."}, status=400)


# # # test start
# # # Create a temporary file to write the binary data
# #     temp_file = None
# #     try:
# #         # Create a temporary file, ensuring it's deleted on close if not explicitly saved
# #         temp_file = tempfile.NamedTemporaryFile(delete=False)
# #         temp_file.write(file_binary)
# #         temp_file_path = temp_file.name
# #         temp_file.close()  # Make sure to close the file handle to allow other processes to access the file
# #     except IOError as e:
# #         print("Failed to write to temporary file:", str(e))
# #         return API_JSON_Response({"Error": "Failed to write PDF data to a temporary file."}, status=500)

# #     # Check if the temporary file is correctly created
# #     if not os.path.exists(temp_file_path):
# #         print("Temporary file does not exist.")
# #         return API_JSON_Response({"Error": "Temporary PDF file not found after creation."}, status=500)

# #     print("Temporary PDF file created at:", temp_file_path)

# #     # Pass the file and the question to get answer
# #     manager = ManagerDriver(temp_file_path, question)
# #     answer = manager.make_answer()

# #     # Clean up: Remove the temporary file after processing
# #     os.unlink(temp_file_path)  # Use unlink for removing the file

# # # test end

#     # file_binary = base64.b64decode(result["file_content"])

#     # Create a temporary file to write the binary data
#     # Write binary data to a temporary file
#     temp_dir = tempfile.mkdtemp()
#     temp_file_path = os.path.join(temp_dir, docName)
#     print(temp_file_path)
#     with open(temp_file_path, 'wb') as file:
#         file.write(file_binary)
# # Save the path to use outside the 'with' block
# #get file from db and save it to temporary directory here , then reference the temporary directory in managerDriver
#     # TODO - Change manager to take the file binary directy
#     # rather than loading the file from the os
    
#     # Pass the file and the question to get answer
#     manager = ManagerDriver(temp_file_path,question)
#     answer = manager.make_answer()
#     return API_JSON_Response({"Answer": answer})

def getEmbedding(request):
    question = request.payload.get("question")
    docName = request.payload.get("docName")
    manager = ManagerDriver(docName,question)
    embedding = manager.get_embedding()
    return API_Message_Response(f"Embedding: {embedding}")

def makeEmbedding(request):
    question = request.payload.get("question")
    docName = request.payload.get("docName")
    manager = ManagerDriver(docName,question)
    embedding = manager.create_embedding()
    return API_Message_Response(f"Embedding: {embedding}")






# Application Endpoints/Routes
APP_ROUTES = App_Routes(
    # Ping
    Route(
        url='/ping',
        handler=Route_Handler(
            GET=lambda request: API_Message_Response("It's alive!")
        ),
        log_level=LOG_LEVELS.DEBUG
    ),

    # Authentication
    Route(
        url='/authenticate',
        handler=AuthenticateRouteHandler(),
        permissions=Route_Permissions(DELETE=['user', 'admin']),
        collection_name='users',
        request_schema=AUTHENTICATION_ROUTE_REQUEST_SCHEMA,
        response_transformer=AUTHENTICATION_ROUTE_RESPONSE_TRANSFORMER,
        log_level=LOG_LEVELS.DEBUG
    ),

    # API Accessible Config
    Route(
        url='/config',
        handler=Default_Route_Handler(),
        permissions=Route_Permissions(GET='admin', POST='admin', PUT='admin', PATCH='admin', DELETE='admin'),
        collection_name='config',
        log_level=LOG_LEVELS.DEBUG
    ),

    # User Management
    Route(
        url='/user',
        handler=UserRouteHandler(PUT=None),
        permissions=Route_Permissions(GET=['user', 'admin'], PATCH=['user', 'admin'], DELETE=['user', 'admin']),
        collection_name='users',
        request_schema=USER_ROUTE_REQUEST_SCHEMA,
        request_transformer=USER_ROUTE_REQUEST_TRANSFORMER,
        response_transformer=USER_ROUTE_RESPONSE_TRANSFORMER,
        log_level=LOG_LEVELS.DEBUG
    ),

    # Admin user management
    Route(
        url='/users',
        handler=Default_Route_Handler(),
        permissions=Route_Permissions(GET='admin', POST='admin', PUT='admin', PATCH='admin', DELETE='admin'),
        collection_name='users',
        request_transformer=USER_ROUTE_REQUEST_TRANSFORMER,
        response_transformer=USER_ROUTE_RESPONSE_TRANSFORMER,
        log_level=LOG_LEVELS.DEBUG
    ),

    # Email Confirmation
    Route(
        url='/email_confirmation',
        handler=Email_Confirmation_Route_Handler(),
        collection_name='email_confirmations',
        request_schema=EMAIL_CONFIRMATION_ROUTE_REQUEST_SCHEMA,
        log_level=LOG_LEVELS.DEBUG
    ),

#VERY IMPORTANT
#READ HERE
#SHAYS ADDED ROUTES PRE-FORMAT MATCHING

    Route(
        url = '/sample',
        handler=Route_Handler(
            GET= handle_get
        ),
        log_level= LOG_LEVELS.DEBUG
    ),
        Route(
        url = '/files',
        handler=Route_Handler(
            POST= handle_file_upload,
            GET= list_files
        ),
        # permissions=Route_Permissions(POST='user'),
        log_level= LOG_LEVELS.DEBUG
    ),
    Route(
        url = '/delete-file',
        handler=Route_Handler(
            DELETE= delete_file
        ),
        permissions=Route_Permissions(POST='user'),
        log_level= LOG_LEVELS.DEBUG
    ),
    Route(
        url = '/embedding',
        handler=Route_Handler(
            POST= handle_embedding_upload,
            GET= list_embeddings
        ),
        permissions=Route_Permissions(POST='user'),
        log_level= LOG_LEVELS.DEBUG
    ),
    Route(
        url = '/delete-embedding',
        handler=Route_Handler(
            DELETE= delete_embedding
        ),
        permissions=Route_Permissions(POST='user'),
        log_level= LOG_LEVELS.DEBUG
    ),
    Route(
        url = '/currentTime',
        handler=Route_Handler(
            GET= getDate
        ),
        log_level= LOG_LEVELS.DEBUG
    ),    
    Route(
        # Route that demonstrates built-in permissions handling
        url='/permissions',
        handler=Default_Route_Handler(
            # Authentication route that sets the JWT in response cookies
            GET=lambda request: Authentication_Util.set_identity_cookies(
                response=API_Message_Response("Authenticated!"),
                _id="1234",
                username="test",
                roles="user"
            ),
            # De-authentication route that removes the JWT in response cookies
            DELETE=lambda request: Authentication_Util.unset_identity_cookies(
                response=API_Message_Response("Logged out!"),
            )
        ),
        log_level=LOG_LEVELS.DEBUG,
        permissions=Route_Permissions(POST='user', PUT='admin')
    ),
    Route(
        url = '/getAnswer',
        handler=Route_Handler(
            POST= makeAnswer

        ),
        log_level= LOG_LEVELS.DEBUG
    ),
    Route(
        url = '/getEmbedding',
        handler=Route_Handler(
            GET= getEmbedding
        ),
        log_level= LOG_LEVELS.DEBUG
    ),
        Route(
        url = '/makeEmbedding',
        handler=Route_Handler(
            GET= makeEmbedding
        ),
        log_level= LOG_LEVELS.DEBUG
    ),
)
