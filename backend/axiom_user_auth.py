from pymongo import MongoClient, ASCENDING
from datetime import datetime
import bcrypt
import re
import uuid
import os
from dotenv import load_dotenv

# Load environment variables for sensitive information
load_dotenv()

# Connect to MongoDB
def get_database_connection():
    """Establishes connection to MongoDB using environment variables"""
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise ValueError("MongoDB URI not found in environment variables")
    
    client = MongoClient(mongodb_uri)
    return client['axiom_db']  # Database name for Axiom application

# User collection setup
def setup_user_collection(db):
    """Sets up the user collection with proper indexes"""
    users = db['users']
    
    # Create unique indexes
    users.create_index([("username", ASCENDING)], unique=True)
    users.create_index([("email", ASCENDING)], unique=True)
    
    return users

# User validation helpers
def validate_email(email):
    """Validates email format"""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

def validate_password_strength(password):
    """
    Validates password strength requirements:
    - At least 8 characters
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one special character
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
    
    return True, "Password is strong"

# User management functions
def create_user(users_collection, username, email, password, first_name, last_name):
    """Creates a new user with proper validation and hashing"""
    # Validate inputs
    if not username or not email or not password or not first_name or not last_name:
        return False, "All fields are required"
    
    if not validate_email(email):
        return False, "Invalid email format"
    
    password_valid, password_message = validate_password_strength(password)
    if not password_valid:
        return False, password_message
    
    # Check if user already exists
    if users_collection.find_one({"username": username}):
        return False, "Username already taken"
    
    if users_collection.find_one({"email": email}):
        return False, "Email already registered"
    
    # Hash the password with bcrypt (industry standard)
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    # Generate verification token for email verification
    verification_token = str(uuid.uuid4())
    
    # User document
    new_user = {
        "username": username,
        "email": email,
        "password": hashed_password,
        "first_name": first_name,
        "last_name": last_name,
        "created_at": datetime.now(),
        "last_login": None,
        "is_active": True,
        "is_verified": False,  # Requires email verification
        "verification_token": verification_token,
        "verification_token_expiry": datetime.now().timestamp() + 86400,  # 24 hour expiry
        "profile": {
            "avatar": None,
            "bio": None,
            "education_level": None,
            "subjects": []
        },
        "preferences": {
            "notification_email": True,
            "theme": "light",
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
    
    # Insert user into database
    try:
        result = users_collection.insert_one(new_user)
        return True, {"id": str(result.inserted_id), "verification_token": verification_token}
    except Exception as e:
        return False, f"Database error: {str(e)}"

def authenticate_user(users_collection, username_or_email, password):
    """Authenticates a user by username/email and password"""
    # Query by either username or email
    user = users_collection.find_one({
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
    
    # Check for too many failed login attempts (basic rate limiting)
    failed_attempts = user.get("security", {}).get("failed_login_attempts", 0)
    if failed_attempts >= 5:
        # Could implement a time-based lockout here TODO
        return False, "Account temporarily locked due to too many failed login attempts"
    
    # Verify password
    if bcrypt.checkpw(password.encode('utf-8'), user["password"]):
        # Reset failed login attempts and update last login
        users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "last_login": datetime.now(),
                    "security.failed_login_attempts": 0
                }
            }
        )
        return True, {"user_id": str(user["_id"]), "username": user["username"]}
    else:
        # Increment failed login attempts
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$inc": {"security.failed_login_attempts": 1}}
        )
        return False, "Invalid password"

# Example usage
if __name__ == "__main__":
    try:
        # Connect to database
        db = get_database_connection()
        users = setup_user_collection(db)
        
        # Example: Create a new user
        success, result = create_user(
            users,
            username="student_demo",
            email="student@example.com",
            password="Secure123!",
            first_name="Student",
            last_name="Demo"
        )
        
        if success:
            print(f"User created successfully! ID: {result['id']}")
            print(f"Verification token: {result['verification_token']}")#?????
            
            # Example: Authenticate user
            auth_success, auth_result = authenticate_user(
                users,
                "student_demo",
                "Secure123!"
            )
            
            if auth_success:
                print(f"Authentication successful for user: {auth_result['username']}")
            else:
                print(f"Authentication failed: {auth_result}")
        else:
            print(f"User creation failed: {result}")
            
    except Exception as e:
        print(f"Error: {str(e)}")