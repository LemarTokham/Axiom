"""
Axiom Authentication Manager
Handles user registration, login, and basic authentication functions
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

class AxiomAuthManager:
    """Handles user authentication, registration, and account verification"""
    
    def __init__(self, db_connection=None):
        """Initialize with optional database connection"""
        # Use provided DB connection or create a new one
        if db_connection is not None:  # This is the fix - changed from if db_connection:
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
        
        # Set up indexes
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Set up necessary indexes for user collection"""
        self.users.create_index([("username", ASCENDING)], unique=True)
        self.users.create_index([("email", ASCENDING)], unique=True)
    
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
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, "Password is valid"
    
    def register_user(self, username: str, email: str, password: str, 
                     first_name: str, last_name: str) -> Tuple[bool, Dict]:
        """Register a new user with validation"""
        # Input validation
        if not username or not email or not password or not first_name or not last_name:
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
        
        # Generate verification token
        verification_token = str(uuid.uuid4())
        
        # Create the user document with enhanced profile
        new_user = {
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "first_name": first_name,
            "last_name": last_name,
            "created_at": datetime.now(),
            "last_login": None,
            "is_admin": False,
            "is_active": True,
            "is_verified": False,
            "verification_token": verification_token,
            "verification_token_expiry": datetime.now().timestamp() + 86400,  # 24 hour expiry
            "profile": {
                "avatar": None,
                "bio": None,
                "education_level": None,
                "subjects": []
            },
            "preferences": {
                "theme": "light",
                "notification_email": True,
                "language": "en",
                "study_reminder": False
            },
            "study_stats": {
                "total_study_time": 0,
                "quizzes_completed": 0,
                "flashcards_reviewed": 0,
                "last_activity": None
            },
            "security": {
                "password_reset_token": None,
                "password_reset_expiry": None,
                "failed_login_attempts": 0,
                "last_password_change": datetime.now()
            }
        }
        
        try:
            result = self.users.insert_one(new_user)
            return True, {
                "id": str(result.inserted_id),
                "username": username,
                "email": email,
                "is_admin": False,
                "verification_token": verification_token
            }
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def login(self, username_or_email: str, password: str) -> Tuple[bool, Dict]:
        """Authenticate a user and handle login tracking"""
        # Find user by username or email
        user = self.users.find_one({
            "$or": [
                {"username": username_or_email},
                {"email": username_or_email}
            ]
        })
        
        if not user:
            return False, "Invalid username or email"
        
        # Check if account is active
        if not user.get("is_active", True):
            return False, "Account is disabled"
        
        # Check for too many failed login attempts
        failed_attempts = user.get("security", {}).get("failed_login_attempts", 0)
        if failed_attempts >= 5:
            return False, "Account temporarily locked due to too many failed login attempts"
        
        # Verify password
        if bcrypt.checkpw(password.encode('utf-8'), user["password_hash"]):
            # Update last login timestamp and reset failed attempts
            self.users.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "last_login": datetime.now(),
                        "security.failed_login_attempts": 0,
                        "study_stats.last_activity": datetime.now()
                    }
                }
            )
            
            # Return user info
            return True, {
                "id": str(user["_id"]),
                "username": user["username"],
                "email": user["email"],
                "is_admin": user.get("is_admin", False),
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "is_verified": user.get("is_verified", False)
            }
        else:
            # Increment failed login attempts
            self.users.update_one(
                {"_id": user["_id"]},
                {"$inc": {"security.failed_login_attempts": 1}}
            )
            return False, "Invalid password"
    
    def verify_email(self, verification_token: str) -> Tuple[bool, str]:
        """Verify a user's email using the verification token"""
        user = self.users.find_one({"verification_token": verification_token})
        
        if not user:
            return False, "Invalid verification token"
        
        # Check if token has expired
        if datetime.now().timestamp() > user.get("verification_token_expiry", 0):
            return False, "Verification token has expired"
        
        try:
            self.users.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "is_verified": True,
                        "verification_token": None
                    }
                }
            )
            return True, "Email verified successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def request_password_reset(self, email: str) -> Tuple[bool, Union[str, Dict]]:
        """Create a password reset token for a user"""
        user = self.users.find_one({"email": email})
        if not user:
            # Don't reveal if email exists for security
            return True, "If a user with this email exists, a password reset link has been sent"
        
        # Check if account is active
        if not user.get("is_active", True):
            # Still don't reveal the account exists, but log this for admin
            print(f"Password reset attempted for inactive account: {email}")
            return True, "If a user with this email exists, a password reset link has been sent"
        
        # Generate reset token and expiry (24 hours)
        reset_token = str(uuid.uuid4())
        expiry = datetime.now().timestamp() + 86400
        
        try:
            self.users.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "security.password_reset_token": reset_token,
                        "security.password_reset_expiry": expiry
                    }
                }
            )
            # In a real app, would send email here
            return True, {
                "message": "Password reset requested",
                "token": reset_token,  # Would be sent via email not returned directly
                "user_id": str(user["_id"])
            }
        except Exception as e:
            return False, f"Database error: {str(e)}"
            
    def refresh_password_reset(self, email: str) -> Tuple[bool, Union[str, Dict]]:
        """
        Generate a new password reset token, replacing any existing one.
        
        This is useful when a user didn't receive the original reset email
        or when the previous token is lost.
        
        Args:
            email: The user's email address
            
        Returns:
            Tuple[bool, Union[str, Dict]]: (success, message or token info)
        """
        return self.request_password_reset(email)  # Simply reuse the existing method
    
    def reset_password(self, reset_token: str, new_password: str) -> Tuple[bool, str]:
        """Reset a user's password using a valid reset token"""
        user = self.users.find_one({"security.password_reset_token": reset_token})
        
        if not user:
            return False, "Invalid reset token"
        
        # Check if token has expired
        expiry = user.get("security", {}).get("password_reset_expiry", 0)
        if datetime.now().timestamp() > expiry:
            return False, "Password reset token has expired"
        
        # Validate new password
        password_valid, password_message = self._validate_password(new_password)
        if not password_valid:
            return False, password_message
        
        # Hash and save new password
        salt = bcrypt.gensalt()
        new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), salt)
        
        try:
            self.users.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "password_hash": new_password_hash,
                        "security.password_reset_token": None,
                        "security.password_reset_expiry": None,
                        "security.last_password_change": datetime.now(),
                        "security.failed_login_attempts": 0
                    }
                }
            )
            return True, "Password reset successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
            
    def cancel_password_reset(self, user_id: str, current_password: str) -> Tuple[bool, str]:
        """
        Cancel an ongoing password reset process by invalidating the reset token.
        
        This is useful when a user suspects their reset token might be compromised
        or when they want to start a fresh password reset process.
        
        Args:
            user_id: The ID of the user
            current_password: The current password for verification
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        # Find the user
        try:
            user = self.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                return False, "User not found"
            
            # Verify current password
            if not bcrypt.checkpw(current_password.encode('utf-8'), user["password_hash"]):
                return False, "Current password is incorrect"
            
            # Check if there's an active reset token
            if not user.get("security", {}).get("password_reset_token"):
                return False, "No active password reset to cancel"
            
            # Invalidate the reset token
            self.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "security.password_reset_token": None,
                        "security.password_reset_expiry": None
                    }
                }
            )
            
            return True, "Password reset process canceled successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def change_password(self, user_id: str, current_password: str, new_password: str) -> Tuple[bool, str]:
        """Change a user's password with security tracking"""
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
                {
                    "$set": {
                        "password_hash": new_password_hash,
                        "security.last_password_change": datetime.now()
                    }
                }
            )
            return True, "Password updated successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
            
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get basic user info by ID"""
        try:
            user = self.users.find_one({"_id": ObjectId(user_id)})
            if user:
                # Remove sensitive information
                user.pop("password_hash", None)
                user.pop("verification_token", None)
                user.pop("security", None)
                
                user["_id"] = str(user["_id"])
                return user
            return None
        except Exception:
            return None
    
    def delete_user_account(self, user_id: str, password: str = None) -> Tuple[bool, str]:
        """
        Permanently delete a user account and all associated data from the database.
        
        This function performs a complete deletion, removing:
        1. All flashcard decks, quizzes, and video chapters created by the user
        2. All modules created by the user
        3. All courses created by the user
        4. The user's profile and all personal information
        
        Args:
            user_id: The ID of the user to delete
            password: Optional password for verification. If None, skips password verification
                     (should only be None for admin actions)
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        # Find the user
        try:
            user = self.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                return False, "User not found"
            
            # Verify password if provided
            if password is not None:
                if not bcrypt.checkpw(password.encode('utf-8'), user["password_hash"]):
                    return False, "Invalid password"
            
            # Track deletion metrics for reporting
            deletion_counts = {
                "flashcard_decks": 0,
                "quizzes": 0,
                "video_chapters": 0,
                "modules": 0,
                "courses": 0
            }
            
            # Get all courses created by the user
            courses = list(self.db['courses'].find({"user_id": ObjectId(user_id)}))
            
            # For each course, delete all modules and their content
            for course in courses:
                # Get modules for this course
                modules = list(self.db['modules'].find({"course_id": course["_id"]}))
                
                # For each module, delete all content
                for module in modules:
                    # Delete flashcards, quizzes, video chapters
                    result = self.db['flashcard_decks'].delete_many({"module_id": module["_id"]})
                    deletion_counts["flashcard_decks"] += result.deleted_count
                    
                    result = self.db['quizzes'].delete_many({"module_id": module["_id"]})
                    deletion_counts["quizzes"] += result.deleted_count
                    
                    result = self.db['video_chapters'].delete_many({"module_id": module["_id"]})
                    deletion_counts["video_chapters"] += result.deleted_count
                
                # Delete all modules in this course
                result = self.db['modules'].delete_many({"course_id": course["_id"]})
                deletion_counts["modules"] += result.deleted_count
            
            # Delete all courses
            result = self.db['courses'].delete_many({"user_id": ObjectId(user_id)})
            deletion_counts["courses"] += result.deleted_count
            
            # Finally, delete the user
            self.users.delete_one({"_id": ObjectId(user_id)})
            
            # Prepare detailed report
            report = (
                f"Account deleted successfully. Removed: "
                f"{deletion_counts['courses']} courses, "
                f"{deletion_counts['modules']} modules, "
                f"{deletion_counts['flashcard_decks']} flashcard decks, "
                f"{deletion_counts['quizzes']} quizzes, "
                f"{deletion_counts['video_chapters']} video chapters."
            )
            
            return True, report
        
        except Exception as e:
            return False, f"Error deleting account: {str(e)}"

    def admin_delete_user(self, admin_user_id: str, target_user_id: str) -> Tuple[bool, str]:
        """
        Administrator function to delete a user account.
        
        Args:
            admin_user_id: The ID of the admin user performing the deletion
            target_user_id: The ID of the user to delete
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        # Verify admin status
        admin = self.users.find_one({"_id": ObjectId(admin_user_id)})
        if not admin:
            return False, "Admin user not found"
        
        if not admin.get("is_admin", False):
            return False, "Permission denied: Admin privileges required"
        
        # Call the main delete function without password verification
        return self.delete_user_account(target_user_id, password=None)

    def deactivate_user_account(self, user_id: str, password: str) -> Tuple[bool, str]:
        """
        Soft-delete a user account by deactivating it.
        The data remains in the database but the user cannot log in.
        
        Args:
            user_id: The ID of the user to deactivate
            password: The password for verification
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        # Find the user
        try:
            user = self.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                return False, "User not found"
            
            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), user["password_hash"]):
                return False, "Invalid password"
            
            # Deactivate the account
            self.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"is_active": False, "deactivated_at": datetime.now()}}
            )
            
            return True, "Account deactivated successfully. You can contact support to reactivate it."
        
        except Exception as e:
            return False, f"Error deactivating account: {str(e)}"