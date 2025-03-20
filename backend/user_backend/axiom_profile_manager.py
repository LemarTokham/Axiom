"""
Axiom User Profile Manager
Handles user profile management, preferences, and study statistics
"""
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
from bson.objectid import ObjectId
from typing import Dict, List, Tuple, Union, Optional, Any

# Load environment variables
load_dotenv()

class AxiomProfileManager:
    """Manages user profiles, preferences, and study statistics"""
    
    def __init__(self, db_connection=None):
        """Initialize with optional database connection"""
        # Use provided DB connection or create a new one
        if db_connection is not None:  # Changed from if db_connection:
            self.db = db_connection
        else:
            # Connect to MongoDB
            connection_string = os.getenv("MONGODB_URI")
            if not connection_string:
                raise ValueError("MongoDB connection string not found in environment variables")
            
            self.client = MongoClient(connection_string)
            self.db = self.client['axiom_db']
        
        # Set up user collection
        self.users = self.db['users']
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get full user profile information"""
        try:
            user = self.users.find_one({"_id": ObjectId(user_id)})
            if user:
                # Convert ObjectId to string for serialization
                user["_id"] = str(user["_id"])
                
                # Remove sensitive information
                user.pop("password_hash", None)
                user.pop("verification_token", None)
                user.pop("security", None)
                
                return user
            return None
        except Exception as e:
            print(f"Error fetching user profile: {str(e)}")
            return None
    
    def update_profile(self, user_id: str, profile_data: Dict) -> Tuple[bool, str]:
        """Update user profile fields"""
        allowed_fields = [
            "first_name", "last_name", 
            "profile.avatar", "profile.bio", 
            "profile.education_level", "profile.subjects"
        ]
        
        # Filter updates to only allowed fields
        updates = {}
        for field in allowed_fields:
            # Handle nested fields
            if "." in field:
                main_field, sub_field = field.split(".", 1)
                if main_field in profile_data and sub_field in profile_data[main_field]:
                    if main_field not in updates:
                        updates[main_field] = {}
                    updates[main_field][sub_field] = profile_data[main_field][sub_field]
            # Handle regular fields
            elif field in profile_data:
                updates[field] = profile_data[field]
        
        if not updates:
            return False, "No valid fields to update"
        
        try:
            result = self.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": updates}
            )
            
            if result.matched_count == 0:
                return False, "User not found"
                
            return True, "Profile updated successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def update_preferences(self, user_id: str, preferences: Dict) -> Tuple[bool, str]:
        """Update user preferences"""
        allowed_preferences = [
            "theme", "notification_email", "language", "study_reminder"
        ]
        
        # Filter to only allowed preferences
        filtered_preferences = {
            f"preferences.{k}": v 
            for k, v in preferences.items() 
            if k in allowed_preferences
        }
        
        if not filtered_preferences:
            return False, "No valid preferences to update"
        
        try:
            result = self.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": filtered_preferences}
            )
            
            if result.matched_count == 0:
                return False, "User not found"
                
            return True, "Preferences updated successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def get_study_statistics(self, user_id: str) -> Optional[Dict]:
        """Get user's study statistics"""
        try:
            user = self.users.find_one(
                {"_id": ObjectId(user_id)},
                {"study_stats": 1}
            )
            
            if user and "study_stats" in user:
                return user["study_stats"]
            
            return None
        except Exception as e:
            print(f"Error fetching study stats: {str(e)}")
            return None
    
    
    
    def update_study_statistics(self, user_id, study_time, flashcards_reviewed, quizzes_completed):
        """
        Update comprehensive study statistics for a user
        
        Args:
            user_id (str): The user ID
            study_time (int): Time spent studying in minutes
            flashcards_reviewed (int): Number of flashcards reviewed
            quizzes_completed (int): Number of quizzes completed
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            # Update all stats in one operation
            updates = {
                "study_stats.total_study_time": study_time,
                "study_stats.flashcards_reviewed": flashcards_reviewed,
                "study_stats.quizzes_completed": quizzes_completed,
                "study_stats.last_activity": datetime.now()
            }
            
            # Update the user document
            result = self.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$inc": updates}
            )
            
            if result.matched_count == 0:
                return False, "User not found"
                
            return True, "Study statistics updated successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    
    
    
    def update_study_stats(self, user_id: str, stats_update: Dict) -> Tuple[bool, str]:
        """Update a user's study statistics"""
        allowed_fields = [
            "total_study_time", "quizzes_completed", 
            "flashcards_reviewed"
        ]
        
        # Filter to only allowed fields
        filtered_updates = {
            f"study_stats.{k}": v 
            for k, v in stats_update.items() 
            if k in allowed_fields
        }
        
        if not filtered_updates:
            return False, "No valid fields to update"
        
        # Always update last activity time
        filtered_updates["study_stats.last_activity"] = datetime.now()
        
        try:
            result = self.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": filtered_updates}
            )
            
            if result.matched_count == 0:
                return False, "User not found"
                
            return True, "Study stats updated successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def increment_study_stats(self, user_id: str, stats_increment: Dict) -> Tuple[bool, str]:
        """Increment user's study statistics"""
        allowed_fields = [
            "total_study_time", "quizzes_completed", 
            "flashcards_reviewed"
        ]
        
        # Filter to only allowed fields
        filtered_increments = {
            f"study_stats.{k}": v 
            for k, v in stats_increment.items() 
            if k in allowed_fields
        }
        
        if not filtered_increments:
            return False, "No valid fields to increment"
        
        try:
            # Update increments
            self.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$inc": filtered_increments,
                    "$set": {"study_stats.last_activity": datetime.now()}
                }
            )
            
            return True, "Study stats updated successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def track_study_time(self, user_id: str, minutes: int) -> Tuple[bool, str]:
        """Track time spent studying"""
        return self.increment_study_stats(user_id, {"total_study_time": minutes})
    
    def track_quiz_completion(self, user_id: str) -> Tuple[bool, str]:
        """Track completed quiz"""
        return self.increment_study_stats(user_id, {"quizzes_completed": 1})
    
    def track_flashcard_review(self, user_id: str, cards_reviewed: int) -> Tuple[bool, str]:
        """Track flashcard review activity"""
        return self.increment_study_stats(user_id, {"flashcards_reviewed": cards_reviewed})