"""
Axiom Admin Creation Script
This script creates an admin user for the Axiom Learning Platform
"""
from axiom_database import AxiomDatabase
from axiom_auth_manager import AxiomAuthManager
import bcrypt
from bson.objectid import ObjectId
from datetime import datetime

def create_admin_user(username, email, password, first_name, last_name):
    """Create an admin user with full privileges"""
    print("Creating admin user...")
    
    # Connect to database
    db = AxiomDatabase().get_db()
    auth_manager = AxiomAuthManager(db)
    
    # Check if user already exists
    existing_user = db['users'].find_one({
        "$or": [
            {"username": username},
            {"email": email}
        ]
    })
    
    if existing_user:
        # If user exists but is not admin, promote to admin
        if not existing_user.get("is_admin", False):
            print(f"User {username} exists but is not an admin. Promoting to admin...")
            db['users'].update_one(
                {"_id": existing_user["_id"]},
                {"$set": {"is_admin": True}}
            )
            print(f"✅ User {username} promoted to admin successfully!")
            return True
        else:
            print(f"✅ User {username} is already an admin. No changes made.")
            return True
    
    # Register new admin user
    success, result = auth_manager.register_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )
    
    if not success:
        print(f"❌ Admin creation failed: {result}")
        return False
    
    user_id = result["id"]
    verification_token = result["verification_token"]
    
    # Verify email automatically
    auth_manager.verify_email(verification_token)
    
    # Set user as admin (since register_user doesn't allow setting is_admin flag)
    db['users'].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_admin": True}}
    )
    
    print(f"✅ Admin user '{username}' created successfully with ID: {user_id}")
    print(f"Admin user has full platform privileges")
    return True

if __name__ == "__main__":
    # Create the admin user with your provided details
    create_admin_user(
        username="Admin",
        email="admin@gmail.com",
        password="AdminPass123!",  # You should change this to a more secure password
        first_name="My",
        last_name="Admin"
    )