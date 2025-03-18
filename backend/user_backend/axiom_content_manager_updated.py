"""
Axiom Content Manager (Updated)
Handles creation and management of course content (flashcards, quizzes, video chapters)
with AI-powered content generation
"""
from pymongo import MongoClient, ASCENDING
from datetime import datetime
import os
from dotenv import load_dotenv
from bson.objectid import ObjectId
from typing import Dict, List, Tuple, Union, Optional, Any
from axiom_ai_content_generator import AxiomAIContentGenerator

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
        self.notes = self.db['notes']
        
        # Initialize AI content generator
        self.ai_generator = AxiomAIContentGenerator(self.db)
        
        # Set up indexes
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Set up necessary indexes for content collections"""
        # Content indexes
        self.flashcard_decks.create_index([("module_id", ASCENDING)])
        self.quizzes.create_index([("module_id", ASCENDING)])
        self.video_chapters.create_index([("module_id", ASCENDING)])
        self.notes.create_index([("user_id", ASCENDING)])
    
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
    
    # === NOTES MANAGEMENT ===
    
    def upload_notes(self, user_id: str, file_path: str, title: str, topic: str) -> Tuple[bool, Union[str, Dict]]:
        """Upload and parse notes from a PDF file"""
        try:
            # Parse the PDF
            content = self.ai_generator.parse_pdf(file_path)
            
            # Save the notes
            return self.ai_generator.save_notes(user_id, title, topic, content)
        except Exception as e:
            return False, f"Error processing notes: {str(e)}"
    
    def get_user_notes(self, user_id: str) -> List[Dict]:
        """Get all notes for a user"""
        try:
            notes = list(self.notes.find({"user_id": user_id}))
            
            # Format the notes for JSON
            for note in notes:
                note["_id"] = str(note["_id"])
                # Limit content preview to 200 characters
                note["content_preview"] = note["content"][:200] + "..." if len(note["content"]) > 200 else note["content"]
                # Remove full content to reduce response size
                note.pop("content", None)
            
            return notes
        except Exception as e:
            print(f"Error fetching notes: {str(e)}")
            return []
    
    def get_note(self, note_id: str, user_id: str) -> Optional[Dict]:
        """Get a note by ID with ownership verification"""
        try:
            note = self.notes.find_one({"_id": ObjectId(note_id)})
            
            if not note:
                return None
            
            # Verify ownership
            if str(note.get("user_id", "")) != user_id:
                return None
            
            note["_id"] = str(note["_id"])
            return note
        except Exception as e:
            print(f"Error fetching note: {str(e)}")
            return None
    
    # === AI-GENERATED CONTENT ===
    
    def generate_quiz_from_notes(self, note_id: str, user_id: str, module_id: str) -> Tuple[bool, Union[str, Dict]]:
        """Generate a quiz from notes using AI and attach it to a module"""
        # Verify module ownership
        success, message, module = self._verify_module_ownership(module_id, user_id)
        if not success:
            return False, message
        
        # Verify note ownership
        note = self.notes.find_one({"_id": ObjectId(note_id)})
        if not note:
            return False, "Note not found"
        
        if str(note.get("user_id", "")) != user_id:
            return False, "You don't have permission to use this note"
        
        # Generate the quiz
        success, result = self.ai_generator.generate_quiz(note_id)
        if not success:
            return False, result
        
        # Create the quiz in the module
        quiz_data = result
        
        new_quiz = {
            "module_id": ObjectId(module_id),
            "title": quiz_data["title"],
            "note_id": ObjectId(note_id),
            "questions": quiz_data["questions"],
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
                "title": quiz_data["title"],
                "question_count": len(quiz_data["questions"])
            }
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def generate_flashcards_from_notes(self, note_id: str, user_id: str, module_id: str) -> Tuple[bool, Union[str, Dict]]:
        """Generate flashcards from notes using AI and attach them to a module"""
        # Verify module ownership
        success, message, module = self._verify_module_ownership(module_id, user_id)
        if not success:
            return False, message
        
        # Verify note ownership
        note = self.notes.find_one({"_id": ObjectId(note_id)})
        if not note:
            return False, "Note not found"
        
        if str(note.get("user_id", "")) != user_id:
            return False, "You don't have permission to use this note"
        
        # Generate the flashcards
        success, result = self.ai_generator.generate_flashcards(note_id)
        if not success:
            return False, result
        
        # Create the flashcard deck in the module
        flashcard_data = result
        
        new_deck = {
            "module_id": ObjectId(module_id),
            "title": flashcard_data["title"],
            "note_id": ObjectId(note_id),
            "cards": flashcard_data["cards"],
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
                "title": flashcard_data["title"],
                "card_count": len(flashcard_data["cards"])
            }
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def suggest_video_chapters_from_notes(self, note_id: str, user_id: str, module_id: str) -> Tuple[bool, Union[str, Dict]]:
        """Generate video chapter suggestions from notes using AI"""
        # Verify module ownership
        success, message, module = self._verify_module_ownership(module_id, user_id)
        if not success:
            return False, message
        
        # Verify note ownership
        note = self.notes.find_one({"_id": ObjectId(note_id)})
        if not note:
            return False, "Note not found"
        
        if str(note.get("user_id", "")) != user_id:
            return False, "You don't have permission to use this note"
        
        # Generate the video chapter suggestions
        return self.ai_generator.generate_video_chapters(note_id)
    
    # === FLASHCARD MANAGEMENT ===
    # [Original flashcard methods remain unchanged]
    
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
                if "note_id" in deck:
                    deck["note_id"] = str(deck["note_id"])
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
    # [Original quiz methods remain unchanged]
    
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
                if "note_id" in quiz:
                    quiz["note_id"] = str(quiz["note_id"])
                return quiz
            return None
        except Exception:
            return None
    
    # [Rest of the original methods remain unchanged]
    
    # === MODULE CONTENT MANAGEMENT ===
    def get_module_content(self, module_id: str) -> Dict:
        """Get all content (flashcards, quizzes, video chapters) for a module"""
        try:
            # Get flashcard decks
            flashcards = list(self.flashcard_decks.find({"module_id": ObjectId(module_id)}))
            for deck in flashcards:
                deck["_id"] = str(deck["_id"])
                deck["module_id"] = str(deck["module_id"])
                if "note_id" in deck:
                    deck["note_id"] = str(deck["note_id"])
            
            # Get quizzes
            quizzes = list(self.quizzes.find({"module_id": ObjectId(module_id)}))
            for quiz in quizzes:
                quiz["_id"] = str(quiz["_id"])
                quiz["module_id"] = str(quiz["module_id"])
                if "note_id" in quiz:
                    quiz["note_id"] = str(quiz["note_id"])
            
            # Get video chapters
            chapters = list(self.video_chapters.find({"module_id": ObjectId(module_id)}))
            for chapter in chapters:
                chapter["_id"] = str(chapter["_id"])
                chapter["module_id"] = str(chapter["module_id"])
                if "note_id" in chapter:
                    chapter["note_id"] = str(chapter["note_id"])
            
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
