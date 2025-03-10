"""
Axiom Database Manager
Handles database connection and provides shared access to MongoDB collections
"""
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class AxiomDatabase:
    """Singleton database manager for the Axiom platform"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AxiomDatabase, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize database connection and collections"""
        # Get MongoDB connection string
        self.connection_string = os.getenv("MONGODB_URI")
        if not self.connection_string:
            raise ValueError("MongoDB connection string not found in environment variables")
        
        # Connect to MongoDB
        self.client = MongoClient(self.connection_string)
        self.db = self.client['axiom_db']
        
        # Set up collections
        self.users = self.db['users']
        self.courses = self.db['courses']
        self.modules = self.db['modules']
        self.flashcard_decks = self.db['flashcard_decks']
        self.quizzes = self.db['quizzes']
        self.video_chapters = self.db['video_chapters']
        
        # Set up indexes
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Set up necessary indexes for all collections"""
        # User collection indexes
        self.users.create_index([("username", ASCENDING)], unique=True)
        self.users.create_index([("email", ASCENDING)], unique=True)
        
        # Course indexes
        self.courses.create_index([("user_id", ASCENDING)])
        self.courses.create_index([("title", ASCENDING)])
        
        # Module indexes
        self.modules.create_index([("course_id", ASCENDING)])
        self.modules.create_index([("title", ASCENDING)])
        
        # Content indexes
        self.flashcard_decks.create_index([("module_id", ASCENDING)])
        self.quizzes.create_index([("module_id", ASCENDING)])
        self.video_chapters.create_index([("module_id", ASCENDING)])
    
    def get_db(self):
        """Get the database object"""
        return self.db
