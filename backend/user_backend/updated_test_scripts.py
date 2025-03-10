"""
Updated test scripts for testing the new Axiom class structure
1. test_registration.py - Tests user registration functionality
2. test_login.py - Tests login functionality
3. test_course_creation.py - Tests course creation
"""

# 1. test_registration.py
"""
Tests the user registration functionality with the new structure.
"""

from axiom_database import AxiomDatabase
from axiom_auth_manager import AxiomAuthManager
import random
import string

def generate_random_string(length=6):
    """Generate a random string for testing"""
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(length))

def main():
    # Initialize
    db = AxiomDatabase().get_db()
    auth_manager = AxiomAuthManager(db)
    
    # Generate unique test user data
    random_suffix = generate_random_string()
    test_username = f"test_user_{random_suffix}"
    test_email = f"test_{random_suffix}@example.com"
    test_password = f"TestPass123!"
    
    # Get user input or use test data
    use_test_data = input("Use test data? (y/n): ").lower() == 'y'
    
    if not use_test_data:
        test_username = input("Enter username: ")
        test_email = input("Enter email: ")
        test_password = input("Enter password: ")
        first_name = input("Enter first name: ")
        last_name = input("Enter last name: ")
    else:
        first_name = "Test"
        last_name = "User"
    
    # Register user
    success, result = auth_manager.register_user(
        username=test_username,
        email=test_email,
        password=test_password,
        first_name=first_name,
        last_name=last_name
    )
    
    # Show the result
    if success:
        print(f"User created successfully!")
        print(f"User ID: {result['id']}")
        print(f"Verification token: {result['verification_token']}")
        
        # Test email verification
        verify = input("Verify email now? (y/n): ").lower() == 'y'
        if verify:
            success, message = auth_manager.verify_email(result['verification_token'])
            print(f"Email verification: {success}, {message}")
    else:
        print(f"User creation failed: {result}")

if __name__ == "__main__":
    main()

# 2. test_login.py
"""
Tests the login functionality with the new structure.
"""

from axiom_database import AxiomDatabase
from axiom_auth_manager import AxiomAuthManager

def main():
    # Initialize
    db = AxiomDatabase().get_db()
    auth_manager = AxiomAuthManager(db)
    
    # Get login credentials
    username_or_email = input("Enter username or email: ")
    password = input("Enter password: ")
    
    # Attempt authentication
    success, result = auth_manager.login(
        username_or_email,
        password
    )
    
    # Show the result
    if success:
        print(f"Authentication successful!")
        print(f"User ID: {result['id']}")
        print(f"Username: {result['username']}")
        print(f"Name: {result['first_name']} {result['last_name']}")
        print(f"Email verified: {'Yes' if result['is_verified'] else 'No'}")
    else:
        print(f"Authentication failed: {result}")

if __name__ == "__main__":
    main()

# 3. test_course_creation.py
"""
Tests course creation functionality with the new structure.
"""

from axiom_database import AxiomDatabase
from axiom_auth_manager import AxiomAuthManager
from axiom_course_manager import AxiomCourseManager

def main():
    # Initialize
    db = AxiomDatabase().get_db()
    auth_manager = AxiomAuthManager(db)
    course_manager = AxiomCourseManager(db)
    
    # First, login
    username_or_email = input("Enter username or email: ")
    password = input("Enter password: ")
    
    # Attempt authentication
    success, result = auth_manager.login(
        username_or_email,
        password
    )
    
    if not success:
        print(f"Authentication failed: {result}")
        return
    
    user_id = result['id']
    print(f"Authentication successful for {result['username']}!")
    
    # Now create a course
    course_title = input("Enter course title: ")
    course_description = input("Enter course description: ")
    
    success, course_result = course_manager.create_course(
        user_id=user_id,
        title=course_title,
        description=course_description
    )
    
    # Show the result
    if success:
        print(f"Course created successfully!")
        print(f"Course ID: {course_result['id']}")
        print(f"Title: {course_result['title']}")
        
        # Get all user courses
        print("\nYour courses:")
        courses = course_manager.get_user_courses(user_id)
        for i, course in enumerate(courses, 1):
            print(f"{i}. {course['title']} - {course['description']}")
    else:
        print(f"Course creation failed: {course_result}")

if __name__ == "__main__":
    main()
