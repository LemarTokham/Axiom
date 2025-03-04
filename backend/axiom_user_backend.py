"""
Revised Axiom User Schema with Course and Module Hierarchy
"""
from pymongo import MongoClient, ASCENDING
from datetime import datetime
import bcrypt
import re
import os
import uuid
from dotenv import load_dotenv
from bson.objectid import ObjectId
from typing import Dict, List, Tuple, Union, Optional, Any

# Load environment variables
load_dotenv()

class AxiomUserManager:
    """Manager class for Axiom user authentication and management"""
    
    def __init__(self, connection_string=None):
        """Initialize the user manager with MongoDB connection"""
        # Use provided connection string or get from environment
        self.connection_string = connection_string or os.getenv("MONGODB_URI")
        if not self.connection_string:
            raise ValueError("MongoDB connection string not provided or found in environment")
        
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
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return bool(re.match(pattern, email))
    
    def _validate_password(self, password: str) -> Tuple[bool, str]:
        """
        Validate password strength requirements
        Returns: (is_valid, message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        return True, "Password is valid"

    # === USER MANAGEMENT ===
    
    def create_user(self, username: str, email: str, password: str, is_admin: bool = False) -> Tuple[bool, Dict]:
        """Create a new user in the system"""
        # Input validation
        if not username or not email or not password:
            return False, "All fields are required"
        
        if not self._validate_email(email):
            return False, "Invalid email format"
        
        password_valid, password_message = self._validate_password(password)
        if not password_valid:
            return False, password_message
        
        # Check for existing user
        if self.users.find_one({"username": username}):
            return False, "Username already taken"
        
        if self.users.find_one({"email": email}):
            return False, "Email already registered"
        
        # Hash the password
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        # Create the user document
        new_user = {
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "created_at": datetime.now(),
            "last_login": None,
            "is_admin": is_admin,
            "preferences": {
                "theme": "light",
                "notification_email": True,
                "language": "en"
            }
        }
        
        try:
            result = self.users.insert_one(new_user)
            return True, {
                "id": str(result.inserted_id),
                "username": username,
                "email": email,
                "is_admin": is_admin
            }
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def authenticate_user(self, username_or_email: str, password: str) -> Tuple[bool, Dict]:
        """Authenticate a user with username/email and password"""
        # Find user by username or email
        user = self.users.find_one({
            "$or": [
                {"username": username_or_email},
                {"email": username_or_email}
            ]
        })
        
        if not user:
            return False, "Invalid username or email"
        
        # Verify password
        if bcrypt.checkpw(password.encode('utf-8'), user["password_hash"]):
            # Update last login timestamp
            self.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.now()}}
            )
            
            # Return user info
            return True, {
                "id": str(user["_id"]),
                "username": user["username"],
                "email": user["email"],
                "is_admin": user["is_admin"]
            }
        else:
            return False, "Invalid password"
    
    def get_user(self, user_id: str) -> Dict:
        """Get user by ID"""
        user = self.users.find_one({"_id": ObjectId(user_id)})
        if user:
            user["_id"] = str(user["_id"])
            user.pop("password_hash", None)
            return user
        return None
    
    def update_user(self, user_id: str, updates: Dict) -> Tuple[bool, str]:
        """Update user information"""
        allowed_fields = {"email", "username", "preferences"}
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not filtered_updates:
            return False, "No valid fields to update"
        
        try:
            result = self.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": filtered_updates}
            )
            
            if result.matched_count == 0:
                return False, "User not found"
                
            return True, "User updated successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def change_password(self, user_id: str, current_password: str, new_password: str) -> Tuple[bool, str]:
        """Change a user's password"""
        # Get user
        user = self.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return False, "User not found"
        
        # Verify current password
        if not bcrypt.checkpw(current_password.encode('utf-8'), user["password_hash"]):
            return False, "Current password is incorrect"
        
        # Validate new password
        password_valid, password_message = self._validate_password(new_password)
        if not password_valid:
            return False, password_message
        
        # Hash and save new password
        salt = bcrypt.gensalt()
        new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), salt)
        
        try:
            self.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"password_hash": new_password_hash}}
            )
            return True, "Password updated successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    # === COURSE MANAGEMENT ===
    
    def create_course(self, user_id: str, title: str, description: str = "") -> Tuple[bool, Dict]:
        """Create a new course for a user"""
        # Validate user exists
        user = self.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return False, "User not found"
        
        # Create course document
        new_course = {
            "user_id": ObjectId(user_id),
            "title": title,
            "description": description,
            "created_at": datetime.now(),
            "last_updated": datetime.now()
        }
        
        try:
            result = self.courses.insert_one(new_course)
            return True, {
                "id": str(result.inserted_id),
                "title": title,
                "description": description
            }
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def get_user_courses(self, user_id: str) -> List[Dict]:
        """Get all courses for a user"""
        try:
            courses = list(self.courses.find({"user_id": ObjectId(user_id)}))
            
            # Format the courses for JSON
            for course in courses:
                course["_id"] = str(course["_id"])
                course["user_id"] = str(course["user_id"])
            
            return courses
        except Exception as e:
            print(f"Error fetching courses: {str(e)}")
            return []
    
    def get_course(self, course_id: str) -> Dict:
        """Get a course by ID"""
        course = self.courses.find_one({"_id": ObjectId(course_id)})
        if course:
            course["_id"] = str(course["_id"])
            course["user_id"] = str(course["user_id"])
            return course
        return None
    
    def update_course(self, course_id: str, user_id: str, updates: Dict) -> Tuple[bool, str]:
        """Update a course"""
        allowed_fields = {"title", "description"}
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not filtered_updates:
            return False, "No valid fields to update"
        
        # Verify ownership
        course = self.courses.find_one({"_id": ObjectId(course_id)})
        if not course:
            return False, "Course not found"
        
        if str(course["user_id"]) != user_id:
            return False, "You don't have permission to update this course"
        
        # Add last_updated timestamp
        filtered_updates["last_updated"] = datetime.now()
        
        try:
            self.courses.update_one(
                {"_id": ObjectId(course_id)},
                {"$set": filtered_updates}
            )
            return True, "Course updated successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def delete_course(self, course_id: str, user_id: str) -> Tuple[bool, str]:
        """Delete a course and all its modules and content"""
        # Verify ownership
        course = self.courses.find_one({"_id": ObjectId(course_id)})
        if not course:
            return False, "Course not found"
        
        if str(course["user_id"]) != user_id:
            return False, "You don't have permission to delete this course"
        
        try:
            # First get all modules in this course
            modules = list(self.modules.find({"course_id": ObjectId(course_id)}))
            
            # Delete all content in each module
            for module in modules:
                module_id = module["_id"]
                self.flashcard_decks.delete_many({"module_id": module_id})
                self.quizzes.delete_many({"module_id": module_id})
                self.video_chapters.delete_many({"module_id": module_id})
            
            # Delete all modules
            self.modules.delete_many({"course_id": ObjectId(course_id)})
            
            # Finally delete the course
            self.courses.delete_one({"_id": ObjectId(course_id)})
            
            return True, "Course and all its content deleted successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    # === MODULE MANAGEMENT ===
    
    def create_module(self, course_id: str, user_id: str, title: str, description: str = "") -> Tuple[bool, Dict]:
        """Create a new module in a course"""
        # Verify course ownership
        course = self.courses.find_one({"_id": ObjectId(course_id)})
        if not course:
            return False, "Course not found"
        
        if str(course["user_id"]) != user_id:
            return False, "You don't have permission to add modules to this course"
        
        # Create module document
        new_module = {
            "course_id": ObjectId(course_id),
            "title": title,
            "description": description,
            "created_at": datetime.now(),
            "last_updated": datetime.now()
        }
        
        try:
            result = self.modules.insert_one(new_module)
            
            # Update the course's last_updated timestamp
            self.courses.update_one(
                {"_id": ObjectId(course_id)},
                {"$set": {"last_updated": datetime.now()}}
            )
            
            return True, {
                "id": str(result.inserted_id),
                "course_id": course_id,
                "title": title,
                "description": description
            }
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def get_course_modules(self, course_id: str) -> List[Dict]:
        """Get all modules for a course"""
        try:
            modules = list(self.modules.find({"course_id": ObjectId(course_id)}))
            
            # Format the modules for JSON
            for module in modules:
                module["_id"] = str(module["_id"])
                module["course_id"] = str(module["course_id"])
            
            return modules
        except Exception as e:
            print(f"Error fetching modules: {str(e)}")
            return []
    
    # === CONTENT MANAGEMENT ===
    
    def create_flashcard_deck(self, module_id: str, user_id: str, title: str, cards: List[Dict]) -> Tuple[bool, Dict]:
        """Create a flashcard deck in a module"""
        # Verify module exists and user has permission
        module = self.modules.find_one({"_id": ObjectId(module_id)})
        if not module:
            return False, "Module not found"
        
        # Get the course to check ownership
        course = self.courses.find_one({"_id": module["course_id"]})
        if str(course["user_id"]) != user_id:
            return False, "You don't have permission to add content to this module"
        
        # Validate cards structure
        for card in cards:
            if "front" not in card or "back" not in card:
                return False, "All cards must have 'front' and 'back' fields"
        
        # Create flashcard deck
        new_deck = {
            "module_id": ObjectId(module_id),
            "title": title,
            "cards": cards,
            "created_at": datetime.now(),
            "last_updated": datetime.now()
        }
        
        try:
            result = self.flashcard_decks.insert_one(new_deck)
            
            # Update module and course last_updated timestamps
            self.modules.update_one(
                {"_id": ObjectId(module_id)},
                {"$set": {"last_updated": datetime.now()}}
            )
            
            self.courses.update_one(
                {"_id": module["course_id"]},
                {"$set": {"last_updated": datetime.now()}}
            )
            
            return True, {
                "id": str(result.inserted_id),
                "module_id": module_id,
                "title": title,
                "card_count": len(cards)
            }
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def create_quiz(self, module_id: str, user_id: str, title: str, questions: List[Dict]) -> Tuple[bool, Dict]:
        """Create a quiz in a module"""
        # Verify module exists and user has permission
        module = self.modules.find_one({"_id": ObjectId(module_id)})
        if not module:
            return False, "Module not found"
        
        # Get the course to check ownership
        course = self.courses.find_one({"_id": module["course_id"]})
        if str(course["user_id"]) != user_id:
            return False, "You don't have permission to add content to this module"
        
        # Validate questions structure
        for question in questions:
            if "question" not in question or "options" not in question or "correct_answer" not in question:
                return False, "All questions must have 'question', 'options', and 'correct_answer' fields"
        
        # Create quiz
        new_quiz = {
            "module_id": ObjectId(module_id),
            "title": title,
            "questions": questions,
            "created_at": datetime.now(),
            "last_updated": datetime.now()
        }
        
        try:
            result = self.quizzes.insert_one(new_quiz)
            
            # Update module and course last_updated timestamps
            self.modules.update_one(
                {"_id": ObjectId(module_id)},
                {"$set": {"last_updated": datetime.now()}}
            )
            
            self.courses.update_one(
                {"_id": module["course_id"]},
                {"$set": {"last_updated": datetime.now()}}
            )
            
            return True, {
                "id": str(result.inserted_id),
                "module_id": module_id,
                "title": title,
                "question_count": len(questions)
            }
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def create_video_chapter(self, module_id: str, user_id: str, title: str, video_url: str, 
                             start_time: int, end_time: int, transcript: str = "") -> Tuple[bool, Dict]:
        """Create a video chapter (short clip) in a module"""
        # Verify module exists and user has permission
        module = self.modules.find_one({"_id": ObjectId(module_id)})
        if not module:
            return False, "Module not found"
        
        # Get the course to check ownership
        course = self.courses.find_one({"_id": module["course_id"]})
        if str(course["user_id"]) != user_id:
            return False, "You don't have permission to add content to this module"
        
        # Create video chapter
        new_chapter = {
            "module_id": ObjectId(module_id),
            "title": title,
            "video_url": video_url,
            "start_time": start_time,
            "end_time": end_time,
            "transcript": transcript,
            "created_at": datetime.now(),
            "last_updated": datetime.now()
        }
        
        try:
            result = self.video_chapters.insert_one(new_chapter)
            
            # Update module and course last_updated timestamps
            self.modules.update_one(
                {"_id": ObjectId(module_id)},
                {"$set": {"last_updated": datetime.now()}}
            )
            
            self.courses.update_one(
                {"_id": module["course_id"]},
                {"$set": {"last_updated": datetime.now()}}
            )
            
            return True, {
                "id": str(result.inserted_id),
                "module_id": module_id,
                "title": title,
                "video_url": video_url,
                "duration": end_time - start_time
            }
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def get_module_content(self, module_id: str) -> Dict:
        """Get all content (flashcards, quizzes, video chapters) for a module"""
        try:
            # Get flashcard decks
            flashcards = list(self.flashcard_decks.find({"module_id": ObjectId(module_id)}))
            for deck in flashcards:
                deck["_id"] = str(deck["_id"])
                deck["module_id"] = str(deck["module_id"])
            
            # Get quizzes
            quizzes = list(self.quizzes.find({"module_id": ObjectId(module_id)}))
            for quiz in quizzes:
                quiz["_id"] = str(quiz["_id"])
                quiz["module_id"] = str(quiz["module_id"])
            
            # Get video chapters
            chapters = list(self.video_chapters.find({"module_id": ObjectId(module_id)}))
            for chapter in chapters:
                chapter["_id"] = str(chapter["_id"])
                chapter["module_id"] = str(chapter["module_id"])
            
            return {
                "flashcard_decks": flashcards,
                "quizzes": quizzes,
                "video_chapters": chapters
            }
        except Exception as e:
            print(f"Error fetching module content: {str(e)}")
            return {
                "flashcard_decks": [],
                "quizzes": [],
                "video_chapters": []
            }

# Example usage:
if __name__ == "__main__":
    # Initialize the user manager
    user_manager = AxiomUserManager()
    
    # Create a test user
    success, user_result = user_manager.create_user(
        username="test_student",
        email="student@example.com",
        password="TestPass123!"
    )
    
    if success:
        user_id = user_result["id"]
        print(f"Created user: {user_result}")
        
        # Create a course
        success, course_result = user_manager.create_course(
            user_id=user_id,
            title="Introduction to Python",
            description="Learn Python programming basics"
        )
        
        if success:
            course_id = course_result["id"]
            print(f"Created course: {course_result}")
            
            # Create a module
            success, module_result = user_manager.create_module(
                course_id=course_id,
                user_id=user_id,
                title="Variables and Data Types",
                description="Understanding Python variables and basic data types"
            )
            
            if success:
                module_id = module_result["id"]
                print(f"Created module: {module_result}")
                
                # Add a flashcard deck
                cards = [
                    {"front": "What is a variable?", "back": "A named location in memory that stores a value"},
                    {"front": "What is an integer?", "back": "A whole number without a decimal point"}
                ]
                
                success, deck_result = user_manager.create_flashcard_deck(
                    module_id=module_id,
                    user_id=user_id,
                    title="Python Basics Flashcards",
                    cards=cards
                )
                
                if success:
                    print(f"Created flashcard deck: {deck_result}")
                
                # Add a quiz
                questions = [
                    {
                        "question": "Which of the following is not a Python data type?",
                        "options": ["Integer", "Float", "Character", "Boolean"],
                        "correct_answer": "Character"
                    },
                    {
                        "question": "What will print(type(10.5)) return?",
                        "options": ["<class 'int'>", "<class 'float'>", "<class 'str'>", "<class 'bool'>"],
                        "correct_answer": "<class 'float'>"
                    }
                ]
                
                success, quiz_result = user_manager.create_quiz(
                    module_id=module_id,
                    user_id=user_id,
                    title="Python Data Types Quiz",
                    questions=questions
                )
                
                if success:
                    print(f"Created quiz: {quiz_result}")
                
                # Add a video chapter
                success, chapter_result = user_manager.create_video_chapter(
                    module_id=module_id,
                    user_id=user_id,
                    title="Introduction to Variables",
                    video_url="https://www.youtube.com/watch?v=example",
                    start_time=120,  # 2 minutes in
                    end_time=240,    # 4 minutes in
                    transcript="In this section, we'll learn about variables in Python..."
                )
                
                if success:
                    print(f"Created video chapter: {chapter_result}")
                
                # Get all module content
                content = user_manager.get_module_content(module_id)
                print("\nModule Content Summary:")
                print(f"- Flashcard Decks: {len(content['flashcard_decks'])}")
                print(f"- Quizzes: {len(content['quizzes'])}")
                print(f"- Video Chapters: {len(content['video_chapters'])}")