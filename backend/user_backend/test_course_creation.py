"""
Tests the course creation functionality with the Axiom structure.
"""

from axiom_database import AxiomDatabase
from axiom_auth_manager import AxiomAuthManager
from axiom_course_manager import AxiomCourseManager
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
    course_manager = AxiomCourseManager(db)
    
    # First, login or create a test user
    user_action = input("Do you want to (l)ogin or (c)reate a test user? ").lower()
    
    if user_action == 'c':
        # Generate unique test user data
        random_suffix = generate_random_string()
        test_username = f"test_user_{random_suffix}"
        test_email = f"test_{random_suffix}@example.com"
        test_password = f"TestPass123!"
        
        print("\n--- Creating Test User ---")
        success, result = auth_manager.register_user(
            username=test_username,
            email=test_email,
            password=test_password,
            first_name="Test",
            last_name="User"
        )
        
        if not success:
            print(f"User creation failed: {result}")
            return
            
        user_id = result["id"]
        print(f"User created successfully with ID: {user_id}")
        
        # Verify the user's email automatically for testing
        success, message = auth_manager.verify_email(result["verification_token"])
        print(f"Email verification: {message}")
        
    else:  # login
        print("\n--- Login ---")
        username_or_email = input("Enter username or email: ")
        password = input("Enter password: ")
        
        success, result = auth_manager.login(username_or_email, password)
        
        if not success:
            print(f"Login failed: {result}")
            return
            
        user_id = result["id"]
        print(f"Login successful for: {result['username']}")
    
    # Now create a course
    print("\n--- Course Creation ---")
    random_suffix = generate_random_string()
    default_title = f"Test Course {random_suffix}"
    default_description = f"This is an automatically generated test course {random_suffix}"
    
    use_default = input("Use default course data? (y/n): ").lower() == 'y'
    
    if use_default:
        course_title = default_title
        course_description = default_description
    else:
        course_title = input("Enter course title: ")
        course_description = input("Enter course description: ")
    
    # Create the course
    success, course_result = course_manager.create_course(
        user_id=user_id,
        title=course_title,
        description=course_description
    )
    
    # Show the result
    if success:
        course_id = course_result["id"]
        print(f"\nCourse created successfully!")
        print(f"Course ID: {course_id}")
        print(f"Title: {course_result['title']}")
        print(f"Description: {course_result['description']}")
        
        # Create a module?
        create_module = input("\nDo you want to create a module in this course? (y/n): ").lower() == 'y'
        
        if create_module:
            module_title = input("Enter module title: ") or f"Test Module {generate_random_string()}"
            module_description = input("Enter module description: ") or f"Test module description"
            
            success, module_result = course_manager.create_module(
                course_id=course_id,
                user_id=user_id,
                title=module_title,
                description=module_description
            )
            
            if success:
                module_id = module_result["id"]
                print(f"\nModule created successfully!")
                print(f"Module ID: {module_id}")
                print(f"Title: {module_result['title']}")
                print(f"Description: {module_result['description']}")
            else:
                print(f"Module creation failed: {module_result}")
        
        # Get user's courses
        print("\n--- User's Courses ---")
        courses = course_manager.get_user_courses(user_id)
        
        if courses:
            print(f"Found {len(courses)} courses:")
            for i, course in enumerate(courses, 1):
                print(f"{i}. {course['title']} - {course['description']}")
        else:
            print("No courses found for this user.")
    else:
        print(f"Course creation failed: {course_result}")

if __name__ == "__main__":
    main()
