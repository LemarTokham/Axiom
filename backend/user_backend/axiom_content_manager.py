"""
Axiom Content Manager
Handles creation and management of course content (flashcards, quizzes, video chapters)
"""
from pymongo import MongoClient, ASCENDING
from datetime import datetime
import os
from dotenv import load_dotenv
from bson.objectid import ObjectId
from typing import Dict, List, Tuple, Union, Optional, Any

# Load environment variables
load_dotenv()

class AxiomContentManager:
    """Manages educational content for the Axiom platform"""
    
    def __init__(self, db_connection=None):
        """Initialize with optional database connection"""
        # Use provided DB connection or create a new one
        if db_connection is not None:  # Fixed from if db_connection:
            self.db = db_connection
        else:
            # Connect to MongoDB
            connection_string = os.getenv("MONGODB_URI")
            if not connection_string:
                raise ValueError("MongoDB connection string not found in environment variables")
            
            self.client = MongoClient(connection_string)
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
        """Set up necessary indexes for content collections"""
        # Content indexes
        self.flashcard_decks.create_index([("module_id", ASCENDING)])
        self.quizzes.create_index([("module_id", ASCENDING)])
        self.video_chapters.create_index([("module_id", ASCENDING)])
    
    def _verify_module_ownership(self, module_id: str, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """Verify that a module exists and user has permission to modify it"""
        # Get module
        module = self.modules.find_one({"_id": ObjectId(module_id)})
        if not module:
            return False, "Module not found", None
        
        # Get course to check ownership
        course = self.courses.find_one({"_id": module["course_id"]})
        if not course:
            return False, "Associated course not found", None
        
        if str(course["user_id"]) != user_id:
            return False, "You don't have permission to modify this module", None
        
        return True, "", module
    
    # === FLASHCARD MANAGEMENT ===
    
    def create_flashcard_deck(self, module_id: str, user_id: str, title: str, cards: List[Dict]) -> Tuple[bool, Union[str, Dict]]:
        """Create a flashcard deck in a module"""
        # Verify module exists and user has permission
        success, message, module = self._verify_module_ownership(module_id, user_id)
        if not success:
            return False, message
        
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
    
    def get_flashcard_deck(self, deck_id: str) -> Optional[Dict]:
        """Get a flashcard deck by ID"""
        try:
            deck = self.flashcard_decks.find_one({"_id": ObjectId(deck_id)})
            if deck:
                deck["_id"] = str(deck["_id"])
                deck["module_id"] = str(deck["module_id"])
                return deck
            return None
        except Exception:
            return None
    
    def update_flashcard_deck(self, deck_id: str, user_id: str, updates: Dict) -> Tuple[bool, str]:
        """Update a flashcard deck"""
        # Get the deck
        deck = self.flashcard_decks.find_one({"_id": ObjectId(deck_id)})
        if not deck:
            return False, "Flashcard deck not found"
        
        # Verify ownership
        success, message, module = self._verify_module_ownership(str(deck["module_id"]), user_id)
        if not success:
            return False, message
        
        # Prepare updates
        allowed_fields = {"title", "cards"}
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not filtered_updates:
            return False, "No valid fields to update"
        
        # Add last_updated timestamp
        filtered_updates["last_updated"] = datetime.now()
        
        try:
            # Update deck
            self.flashcard_decks.update_one(
                {"_id": ObjectId(deck_id)},
                {"$set": filtered_updates}
            )
            
            # Update module and course last_updated timestamps
            self.modules.update_one(
                {"_id": deck["module_id"]},
                {"$set": {"last_updated": datetime.now()}}
            )
            
            self.courses.update_one(
                {"_id": module["course_id"]},
                {"$set": {"last_updated": datetime.now()}}
            )
            
            return True, "Flashcard deck updated successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def delete_flashcard_deck(self, deck_id: str, user_id: str) -> Tuple[bool, str]:
        """Delete a flashcard deck"""
        # Get the deck
        deck = self.flashcard_decks.find_one({"_id": ObjectId(deck_id)})
        if not deck:
            return False, "Flashcard deck not found"
        
        # Verify ownership
        success, message, module = self._verify_module_ownership(str(deck["module_id"]), user_id)
        if not success:
            return False, message
        
        try:
            # Delete deck
            self.flashcard_decks.delete_one({"_id": ObjectId(deck_id)})
            
            # Update module and course last_updated timestamps
            self.modules.update_one(
                {"_id": deck["module_id"]},
                {"$set": {"last_updated": datetime.now()}}
            )
            
            self.courses.update_one(
                {"_id": module["course_id"]},
                {"$set": {"last_updated": datetime.now()}}
            )
            
            return True, "Flashcard deck deleted successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    # === QUIZ MANAGEMENT ===
    
    def create_quiz(self, module_id: str, user_id: str, title: str, questions: List[Dict]) -> Tuple[bool, Union[str, Dict]]:
        """Create a quiz in a module"""
        # Verify module exists and user has permission
        success, message, module = self._verify_module_ownership(module_id, user_id)
        if not success:
            return False, message
        
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
    
    def get_quiz(self, quiz_id: str) -> Optional[Dict]:
        """Get a quiz by ID"""
        try:
            quiz = self.quizzes.find_one({"_id": ObjectId(quiz_id)})
            if quiz:
                quiz["_id"] = str(quiz["_id"])
                quiz["module_id"] = str(quiz["module_id"])
                return quiz
            return None
        except Exception:
            return None
    
    def update_quiz(self, quiz_id: str, user_id: str, updates: Dict) -> Tuple[bool, str]:
        """Update a quiz"""
        # Get the quiz
        quiz = self.quizzes.find_one({"_id": ObjectId(quiz_id)})
        if not quiz:
            return False, "Quiz not found"
        
        # Verify ownership
        success, message, module = self._verify_module_ownership(str(quiz["module_id"]), user_id)
        if not success:
            return False, message
        
        # Prepare updates
        allowed_fields = {"title", "questions"}
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not filtered_updates:
            return False, "No valid fields to update"
        
        # Add last_updated timestamp
        filtered_updates["last_updated"] = datetime.now()
        
        try:
            # Update quiz
            self.quizzes.update_one(
                {"_id": ObjectId(quiz_id)},
                {"$set": filtered_updates}
            )
            
            # Update module and course last_updated timestamps
            self.modules.update_one(
                {"_id": quiz["module_id"]},
                {"$set": {"last_updated": datetime.now()}}
            )
            
            self.courses.update_one(
                {"_id": module["course_id"]},
                {"$set": {"last_updated": datetime.now()}}
            )
            
            return True, "Quiz updated successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def delete_quiz(self, quiz_id: str, user_id: str) -> Tuple[bool, str]:
        """Delete a quiz"""
        # Get the quiz
        quiz = self.quizzes.find_one({"_id": ObjectId(quiz_id)})
        if not quiz:
            return False, "Quiz not found"
        
        # Verify ownership
        success, message, module = self._verify_module_ownership(str(quiz["module_id"]), user_id)
        if not success:
            return False, message
        
        try:
            # Delete quiz
            self.quizzes.delete_one({"_id": ObjectId(quiz_id)})
            
            # Update module and course last_updated timestamps
            self.modules.update_one(
                {"_id": quiz["module_id"]},
                {"$set": {"last_updated": datetime.now()}}
            )
            
            self.courses.update_one(
                {"_id": module["course_id"]},
                {"$set": {"last_updated": datetime.now()}}
            )
            
            return True, "Quiz deleted successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    # === VIDEO CHAPTER MANAGEMENT ===
    
    def create_video_chapter(self, module_id: str, user_id: str, title: str, video_url: str, 
                            start_time: int, end_time: int, transcript: str = "") -> Tuple[bool, Union[str, Dict]]:
        """Create a video chapter (short clip) in a module"""
        # Verify module exists and user has permission
        success, message, module = self._verify_module_ownership(module_id, user_id)
        if not success:
            return False, message
        
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
    
    def get_video_chapter(self, chapter_id: str) -> Optional[Dict]:
        """Get a video chapter by ID"""
        try:
            chapter = self.video_chapters.find_one({"_id": ObjectId(chapter_id)})
            if chapter:
                chapter["_id"] = str(chapter["_id"])
                chapter["module_id"] = str(chapter["module_id"])
                return chapter
            return None
        except Exception:
            return None
    
    def update_video_chapter(self, chapter_id: str, user_id: str, updates: Dict) -> Tuple[bool, str]:
        """Update a video chapter"""
        # Get the chapter
        chapter = self.video_chapters.find_one({"_id": ObjectId(chapter_id)})
        if not chapter:
            return False, "Video chapter not found"
        
        # Verify ownership
        success, message, module = self._verify_module_ownership(str(chapter["module_id"]), user_id)
        if not success:
            return False, message
        
        # Prepare updates
        allowed_fields = {"title", "video_url", "start_time", "end_time", "transcript"}
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not filtered_updates:
            return False, "No valid fields to update"
        
        # Add last_updated timestamp
        filtered_updates["last_updated"] = datetime.now()
        
        try:
            # Update chapter
            self.video_chapters.update_one(
                {"_id": ObjectId(chapter_id)},
                {"$set": filtered_updates}
            )
            
            # Update module and course last_updated timestamps
            self.modules.update_one(
                {"_id": chapter["module_id"]},
                {"$set": {"last_updated": datetime.now()}}
            )
            
            self.courses.update_one(
                {"_id": module["course_id"]},
                {"$set": {"last_updated": datetime.now()}}
            )
            
            return True, "Video chapter updated successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def delete_video_chapter(self, chapter_id: str, user_id: str) -> Tuple[bool, str]:
        """Delete a video chapter"""
        # Get the chapter
        chapter = self.video_chapters.find_one({"_id": ObjectId(chapter_id)})
        if not chapter:
            return False, "Video chapter not found"
        
        # Verify ownership
        success, message, module = self._verify_module_ownership(str(chapter["module_id"]), user_id)
        if not success:
            return False, message
        
        try:
            # Delete chapter
            self.video_chapters.delete_one({"_id": ObjectId(chapter_id)})
            
            # Update module and course last_updated timestamps
            self.modules.update_one(
                {"_id": chapter["module_id"]},
                {"$set": {"last_updated": datetime.now()}}
            )
            
            self.courses.update_one(
                {"_id": module["course_id"]},
                {"$set": {"last_updated": datetime.now()}}
            )
            
            return True, "Video chapter deleted successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    # === MODULE CONTENT MANAGEMENT ===
    
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