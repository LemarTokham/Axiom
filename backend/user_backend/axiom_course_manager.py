"""
Axiom Course Manager
Handles creation and management of courses and their modules
"""
from pymongo import MongoClient, ASCENDING
from datetime import datetime
import os
from dotenv import load_dotenv
from bson.objectid import ObjectId
from typing import Dict, List, Tuple, Union, Optional, Any

# Load environment variables
load_dotenv()

class AxiomCourseManager:
    """Manages courses and modules for the Axiom platform"""
    
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
        
        # Set up indexes
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Set up necessary indexes for collections"""
        # Course indexes
        self.courses.create_index([("user_id", ASCENDING)])
        self.courses.create_index([("title", ASCENDING)])
        
        # Module indexes
        self.modules.create_index([("course_id", ASCENDING)])
        self.modules.create_index([("title", ASCENDING)])
    
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
    
    def get_course(self, course_id: str) -> Optional[Dict]:
        """Get a course by ID"""
        try:
            course = self.courses.find_one({"_id": ObjectId(course_id)})
            if course:
                course["_id"] = str(course["_id"])
                course["user_id"] = str(course["user_id"])
                return course
            return None
        except Exception as e:
            print(f"Error fetching course: {str(e)}")
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
        """Delete a course and all its modules"""
        # Verify ownership
        course = self.courses.find_one({"_id": ObjectId(course_id)})
        if not course:
            return False, "Course not found"
        
        if str(course["user_id"]) != user_id:
            return False, "You don't have permission to delete this course"
        
        try:
            # Delete all modules in this course
            self.modules.delete_many({"course_id": ObjectId(course_id)})
            
            # Delete the course
            self.courses.delete_one({"_id": ObjectId(course_id)})
            
            return True, "Course and modules deleted successfully"
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
    
    def get_module(self, module_id: str) -> Optional[Dict]:
        """Get a module by ID"""
        try:
            module = self.modules.find_one({"_id": ObjectId(module_id)})
            if module:
                module["_id"] = str(module["_id"])
                module["course_id"] = str(module["course_id"])
                return module
            return None
        except Exception as e:
            print(f"Error fetching module: {str(e)}")
            return None
    
    def update_module(self, module_id: str, user_id: str, updates: Dict) -> Tuple[bool, str]:
        """Update a module with ownership verification"""
        allowed_fields = {"title", "description"}
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not filtered_updates:
            return False, "No valid fields to update"
        
        # Get module
        module = self.modules.find_one({"_id": ObjectId(module_id)})
        if not module:
            return False, "Module not found"
        
        # Verify course ownership
        course = self.courses.find_one({"_id": module["course_id"]})
        if not course:
            return False, "Associated course not found"
        
        if str(course["user_id"]) != user_id:
            return False, "You don't have permission to update this module"
        
        # Add last_updated timestamp
        filtered_updates["last_updated"] = datetime.now()
        
        try:
            # Update module
            self.modules.update_one(
                {"_id": ObjectId(module_id)},
                {"$set": filtered_updates}
            )
            
            # Update course last_updated timestamp
            self.courses.update_one(
                {"_id": module["course_id"]},
                {"$set": {"last_updated": datetime.now()}}
            )
            
            return True, "Module updated successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def delete_module(self, module_id: str, user_id: str) -> Tuple[bool, str]:
        """Delete a module with ownership verification"""
        # Get module
        module = self.modules.find_one({"_id": ObjectId(module_id)})
        if not module:
            return False, "Module not found"
        
        # Verify course ownership
        course = self.courses.find_one({"_id": module["course_id"]})
        if not course:
            return False, "Associated course not found"
        
        if str(course["user_id"]) != user_id:
            return False, "You don't have permission to delete this module"
        
        try:
            # Delete module
            self.modules.delete_one({"_id": ObjectId(module_id)})
            
            # Update course last_updated timestamp
            self.courses.update_one(
                {"_id": module["course_id"]},
                {"$set": {"last_updated": datetime.now()}}
            )
            
            return True, "Module deleted successfully"
        except Exception as e:
            return False, f"Database error: {str(e)}"