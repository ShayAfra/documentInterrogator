from flongo_framework.database.mongodb.fixture import MongoDB_Fixtures, MongoDB_Fixture
from bson import ObjectId
from datetime import datetime  # Ensure datetime is imported

# Application Database Fixtures
FIXTURES = MongoDB_Fixtures(
    MongoDB_Fixture("config", {
        "_id": ObjectId("652790328c73b750984aee34"), 
        "name": "REQUIRE_VALIDATED_EMAIL_FOR_LOGIN",
        "value": False
    }),
    MongoDB_Fixture("config", {
        "_id": ObjectId("652790328c73b750984aee35"), 
        "name": "spoofConfig",
        "value": True
    }),
    # New fixture for files collection
    MongoDB_Fixture("files", {
        "_id": ObjectId("652790328c73b750984aee36"),
        "user_id": ObjectId("652790328c73b750984aee33"),  # Replace with an actual user ObjectId
        "file_name": "example.txt",
        "file_extension": "txt",
        "file_data": "base64encodedstring",
        "created_on": datetime.utcnow()
    })
)
