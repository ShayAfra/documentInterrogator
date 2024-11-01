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

from bson import ObjectId

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
# Collections
files_collection = db['files']  # Collection for storing file data
history_collection = db['history']  # Collection for storing user questions and answers
embeddings_collection = db['embeddings']  # Collection for storing document embeddings
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
    if 'file_name' not in request.payload:
        return 'File name not in the request', 400

    # Get the authenticated user's ID from request.identity._id
    user_id = request.identity._id
    file_name = request.payload['file_name']

    # Attempt to delete the file that belongs to the authenticated user
    result = files_collection.find_one_and_delete({"user_id": ObjectId(user_id), "file_name": file_name})

    if result:
        return API_Message_Response(f"File {file_name} deleted successfully")
    else:
        return API_Message_Response(f"File {file_name} not found or not owned by the user", status_code=404)

def handle_file_upload(request):
    # Check if the post request has the file part
    if 'fileName' not in request.payload:
        return 'File name not in the request', 400

    # TEST
    # Ensure the user is authenticated
    if not request.identity:
        return API_Message_Response("User not authenticated", status_code=401)

    # Get the authenticated user's ID from request.identity._id
    user_id = request.identity._id
    file_name = request.payload['fileName']
    file_extension = request.payload['fileExtension']
    file_data_base64 = request.payload['fileData']

    # Decode the Base64 file data
    file_data_binary = base64.b64decode(file_data_base64)
    
    # Create the document to insert into MongoDB
    file_document = {
        'user_id': ObjectId(user_id),  # Associate the file with the authenticated user
        'file_name': file_name,
        'file_extension': file_extension,
        'file_content': Binary(file_data_binary),
        'created_on': datetime.utcnow()
    }

    # Insert the document into MongoDB
    result = files_collection.insert_one(file_document)

    if result.inserted_id:
        return {'message': 'File uploaded successfully', 'id': str(result.inserted_id)}, 200
    else:
        return {'message': 'Failed to upload file'}, 500

    
def list_files(request):
    # directory = '/Users/shay/Desktop/repo/documentInterrogator/server/app/utilities/docs'  # Folder where files are stored
    # files = os.listdir(directory)
    # # Create a numbered list of files
    # files_list = ' AP'.join(f"{index + 1}. {file}" for index, file in enumerate(files))
    # return API_Message_Response(files_list)


    # if 'user_id' not in request.payload:
    #     return 'User ID not in the request', 400

    # user_id = request.payload['user_id']
    user_id = request.identity._id
    files = files_collection.find({"user_id": ObjectId(user_id)}, {'file_content': 0})  # Exclude file_content from the results

    file_list = [{
        'file_name': file['file_name'],
        'file_extension': file['file_extension'],
        'id': str(file['_id'])
    } for file in files]
    return API_Message_Response(file_list)


def delete_embedding(request):
    if 'fileName' not in request.payload:
        return 'Document name not in the request', 400

    # Get the authenticated user's ID from request.identity._id
    user_id = request.identity._id
    file_name_with_extension = request.payload.get('fileName')
    file_name_without_extension = os.path.splitext(file_name_with_extension)[0]

    # Ensure the embedding belongs to the authenticated user
    file_record = files_collection.find_one({"user_id": ObjectId(user_id), "file_name": file_name_with_extension})
    if not file_record:
        return API_Message_Response(f"Embedding for document {file_name_with_extension} not found or not owned by the user", status_code=404)

    # Attempt to delete the embedding
    directory = 'chroma_store'
    file_path = os.path.join(directory, file_name_without_extension)
    
    try:
        shutil.rmtree(file_path)
        return API_Message_Response(f"Embedding for {file_name_with_extension} deleted successfully")
    except Exception as e:
        return API_Message_Response(f"An error occurred: {e}", status_code=500)


def handle_embedding_upload(request):
    # Check if the post request has the necessary data
    if 'question' not in request.payload or 'docName' not in request.payload:
        return 'Question or document name not in the request', 400

    # Get the authenticated user's ID from request.identity._id
    user_id = request.identity._id
    question = request.payload.get("question")
    file_name_with_extension = request.payload.get("docName")

    # Ensure the document belongs to the authenticated user before proceeding
    file_record = files_collection.find_one({"user_id": ObjectId(user_id), "file_name": file_name_with_extension})
    if not file_record:
        return API_Message_Response(f"Document {file_name_with_extension} not found or not owned by the user", status_code=404)

    # Process the embedding
    manager = ManagerDriver(file_name_with_extension, question)
    embedding = manager.get_embedding()

    # Assuming there’s a process to store or associate the embedding with the user (if needed)
    return API_Message_Response(f"Embedding created and associated with the user: {embedding}")

    
def list_embeddings(request):
    directory = 'chroma_store'  # Folder where files are stored
    embeddings = os.listdir(directory)
    # Create a numbered list of files
    embeddings_list = ' AP'.join(f"{index + 1}. {embedding}" for index, embedding in enumerate(embeddings))
    return API_Message_Response(embeddings_list)

def getDate(request):
    return API_Message_Response(datetime.now())

def makeAnswer(request):
    # version pre request.idenity._id changes in case it doesnt work
    # if 'user_id' not in request.payload or 'docName' not in request.payload or 'question' not in request.payload:
    #     return 'User ID, document name, or question not in the request', 400
    # user_id = request.payload.get("user_id")
    if 'docName' not in request.payload or 'question' not in request.payload:
        return 'Document name or question not in the request', 400
    # Get the authenticated user's ID from request.identity._id
    user_id = request.identity._id
    # end of changes made
    question = request.payload.get("question")
    docName = request.payload.get("docName")

    # Get binary file and its extension from DB
    result = files_collection.find_one({"user_id": ObjectId(user_id), "file_name": docName})

    if not result:
        return API_JSON_Response({"Error": "File not found."}, status=404)
    
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

        # Store the question and answer in the history collection
        store_question_answer(request, question, answer, docName)
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
    if 'docName' not in request.payload or 'question' not in request.payload:
        return 'Document name or question not in the request', 400

    # Get the authenticated user's ID from request.identity._id
    user_id = request.identity._id
    docName = request.payload.get("docName")
    question = request.payload.get("question")

    # Ensure the document belongs to the authenticated user before processing
    file_record = files_collection.find_one({"user_id": ObjectId(user_id), "file_name": docName})
    if not file_record:
        return API_Message_Response(f"Document {docName} not found or not owned by the user", status_code=404)

    # Process the embedding
    manager = ManagerDriver(docName, question)
    embedding = manager.get_embedding()
    
    return API_Message_Response(f"Embedding: {embedding}")


def makeEmbedding(request):
    if 'docName' not in request.payload or 'question' not in request.payload:
        return 'Document name or question not in the request', 400

    # Get the authenticated user's ID from request.identity._id
    user_id = request.identity._id
    docName = request.payload.get("docName")
    question = request.payload.get("question")

    # Ensure the document belongs to the authenticated user before processing
    file_record = files_collection.find_one({"user_id": ObjectId(user_id), "file_name": docName})
    if not file_record:
        return API_Message_Response(f"Document {docName} not found or not owned by the user", status_code=404)

    # Create the embedding
    manager = ManagerDriver(docName, question)
    embedding = manager.create_embedding()

    # Store the embedding in the embeddings collection
    store_embedding(request, docName, embedding)
    
    return API_Message_Response(f"Embedding: {embedding}")

def store_question_answer(request, question, answer, doc_name):
    user_id = request.identity._id
    history_document = {
        'user_id': ObjectId(user_id),
        'question': question,
        'answer': answer,
        'doc_name': doc_name,
        'created_on': datetime.utcnow()
    }
    # Insert the document into the history collection
    history_collection.insert_one(history_document)

def store_embedding(request, doc_name, embedding):
    user_id = request.identity._id
    embedding_document = {
        'user_id': ObjectId(user_id),
        'doc_name': doc_name,
        'embedding': embedding,
        'created_on': datetime.utcnow()
    }
    # Insert the document into the embeddings collection
    embeddings_collection.insert_one(embedding_document)

def get_user_history(request):
    user_id = request.identity._id

    # Retrieve all history entries for the authenticated user
    history_entries = history_collection.find({"user_id": ObjectId(user_id)})

    history_list = [{
        'question': entry['question'],
        'answer': entry['answer'],
        'doc_name': entry['doc_name'],
        'created_on': entry['created_on'].isoformat()
    } for entry in history_entries]

    return API_JSON_Response({"history": history_list})

def get_user_embeddings(request):
    user_id = request.identity._id

    # Retrieve all embeddings for the authenticated user
    embeddings = embeddings_collection.find({"user_id": ObjectId(user_id)})

    embeddings_list = [{
        'doc_name': entry['doc_name'],
        'embedding': entry['embedding'],
        'created_on': entry['created_on'].isoformat()
    } for entry in embeddings]

    return API_JSON_Response({"embeddings": embeddings_list})









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
        permissions=Route_Permissions(GET='user', POST='user'),

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
        permissions=Route_Permissions(POST='user'),
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
     # Route to get user history
    Route(
        url='/history',
        handler=Route_Handler(
            GET=get_user_history
        ),
        permissions=Route_Permissions(GET='user'),
        log_level=LOG_LEVELS.DEBUG
    ),

    # Route to get user embeddings
    Route(
        url='/user-embeddings',
        handler=Route_Handler(
            GET=get_user_embeddings
        ),
        permissions=Route_Permissions(GET='user'),
        log_level=LOG_LEVELS.DEBUG
    ),
)
