"""
Axiom Backend Test Script
This script tests the core functionality of the Axiom backend:
1. User registration
2. Email verification
3. User login
4. Profile management
5. Course creation
6. Password reset functionality
7. Account deletion
"""
from axiom_database import AxiomDatabase
from axiom_auth_manager import AxiomAuthManager
from axiom_profile_manager import AxiomProfileManager
from axiom_course_manager import AxiomCourseManager
import random
import string
import os
from datetime import datetime
from bson.objectid import ObjectId

def generate_random_string(length=6):
    """Generate a random string for testing"""
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(length))

def print_separator(title):
    """Print a section separator with title"""
    print("\n" + "=" * 40)
    print(f"  {title}")
    print("=" * 40)

def main():
    print_separator("AXIOM BACKEND TEST")
    
    # Initialize database connection
    try:
        print("Initializing database connection...")
        db = AxiomDatabase().get_db()
        print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return
    
    # Initialize managers
    auth_manager = AxiomAuthManager(db)
    profile_manager = AxiomProfileManager(db)
    course_manager = AxiomCourseManager(db)
    
    # Generate unique test user data
    random_suffix = generate_random_string()
    test_username = f"test_user_{random_suffix}"
    test_email = f"test_{random_suffix}@example.com"
    test_password = "Test123!@#"
    
    # 1. Test user registration
    print_separator("USER REGISTRATION")
    print(f"Creating user: {test_username} / {test_email}")
    
    success, result = auth_manager.register_user(
        username=test_username,
        email=test_email,
        password=test_password,
        first_name="Test",
        last_name="User"
    )
    
    if not success:
        print(f"✗ User registration failed: {result}")
        return
    
    user_id = result["id"]
    verification_token = result["verification_token"]
    print(f"✓ User created successfully with ID: {user_id}")
    print(f"✓ Verification token: {verification_token}")
    
    # 2. Test email verification
    print_separator("EMAIL VERIFICATION")
    print(f"Verifying email for {test_email}")
    
    success, message = auth_manager.verify_email(verification_token)
    if not success:
        print(f"✗ Email verification failed: {message}")
        return
    
    print(f"✓ {message}")
    
    # 3. Test user login
    print_separator("USER LOGIN")
    print(f"Logging in as {test_username}")
    
    # First try with wrong password
    print("Testing with incorrect password...")
    success, result = auth_manager.login(test_username, "WrongPassword123!")
    if success:
        print("✗ Login succeeded with incorrect password (should have failed)")
    else:
        print(f"✓ Login correctly failed: {result}")
    
    # Then try with correct password
    print("Testing with correct password...")
    success, result = auth_manager.login(test_username, test_password)
    if not success:
        print(f"✗ Login failed: {result}")
        return
    
    print(f"✓ Login successful for {result['username']}")
    print(f"✓ User data: {result}")
    
    # 4. Test profile management
    print_separator("PROFILE MANAGEMENT")
    print(f"Updating profile for {test_username}")
    
    profile_updates = {
        "profile": {
            "avatar": "https://example.com/avatar.jpg",
            "bio": "This is a test user profile for the Axiom learning platform",
            "education_level": "University",
            "subjects": ["Computer Science", "Mathematics"]
        }
    }
    
    success, message = profile_manager.update_profile(user_id, profile_updates)
    if not success:
        print(f"✗ Profile update failed: {message}")
    else:
        print(f"✓ {message}")
    
    # Get updated profile
    user_profile = profile_manager.get_user_profile(user_id)
    if not user_profile:
        print("✗ Failed to retrieve user profile")
    else:
        print(f"✓ Retrieved user profile:")
        print(f"  Name: {user_profile['first_name']} {user_profile['last_name']}")
        print(f"  Bio: {user_profile['profile']['bio']}")
        print(f"  Education: {user_profile['profile']['education_level']}")
        print(f"  Subjects: {', '.join(user_profile['profile']['subjects'])}")
    
    # 5. Test preference management
    print_separator("PREFERENCE MANAGEMENT")
    print(f"Updating preferences for {test_username}")
    
    preference_updates = {
        "theme": "dark",
        "notification_email": False,
        "language": "es",
        "study_reminder": True
    }
    
    success, message = profile_manager.update_preferences(user_id, preference_updates)
    if not success:
        print(f"✗ Preference update failed: {message}")
    else:
        print(f"✓ {message}")
    
    # Get updated profile to check preferences
    user_profile = profile_manager.get_user_profile(user_id)
    if user_profile and 'preferences' in user_profile:
        print(f"✓ Updated preferences:")
        print(f"  Theme: {user_profile['preferences']['theme']}")
        print(f"  Language: {user_profile['preferences']['language']}")
        print(f"  Email notifications: {user_profile['preferences']['notification_email']}")
        print(f"  Study reminders: {user_profile['preferences']['study_reminder']}")
    
    # 6. Test course creation
    print_separator("COURSE CREATION")
    print(f"Creating a course for {test_username}")
    
    course_title = f"Test Course {random_suffix}"
    course_description = "This is an automatically generated test course"
    
    success, course_result = course_manager.create_course(
        user_id=user_id,
        title=course_title,
        description=course_description
    )
    
    if not success:
        print(f"✗ Course creation failed: {course_result}")
        return
    
    course_id = course_result["id"]
    print(f"✓ Course created successfully with ID: {course_id}")
    print(f"✓ Title: {course_result['title']}")
    print(f"✓ Description: {course_result['description']}")
    
    # 7. Test module creation
    print_separator("MODULE CREATION")
    print(f"Creating a module in course: {course_title}")
    
    module_title = f"Test Module {random_suffix}"
    module_description = "This is an automatically generated test module"
    
    success, module_result = course_manager.create_module(
        course_id=course_id,
        user_id=user_id,
        title=module_title,
        description=module_description
    )
    
    if not success:
        print(f"✗ Module creation failed: {module_result}")
        return
    
    module_id = module_result["id"]
    print(f"✓ Module created successfully with ID: {module_id}")
    print(f"✓ Title: {module_result['title']}")
    print(f"✓ Description: {module_result['description']}")
    
    # 8. Get all user's courses
    print_separator("RETRIEVING USER COURSES")
    print(f"Getting all courses for {test_username}")
    
    courses = course_manager.get_user_courses(user_id)
    if not courses:
        print("✗ Failed to retrieve user courses or no courses found")
    else:
        print(f"✓ Found {len(courses)} courses:")
        for i, course in enumerate(courses, 1):
            print(f"  {i}. {course['title']} - {course['description']}")
            
            # Get modules for this course
            modules = course_manager.get_course_modules(course['_id'])
            if modules:
                print(f"    Found {len(modules)} modules:")
                for j, module in enumerate(modules, 1):
                    print(f"      {j}. {module['title']}")
    
    # 9. Track study statistics
    print_separator("STUDY STATISTICS")
    print(f"Tracking study activities for {test_username}")
    
    # Track study time (45 minutes)
    success, message = profile_manager.track_study_time(user_id, 45)
    if success:
        print(f"✓ Tracked 45 minutes of study time")
    else:
        print(f"✗ Failed to track study time: {message}")
    
    # Track a quiz completion
    success, message = profile_manager.track_quiz_completion(user_id)
    if success:
        print(f"✓ Tracked quiz completion")
    else:
        print(f"✗ Failed to track quiz completion: {message}")
    
    # Track flashcard review (10 cards)
    success, message = profile_manager.track_flashcard_review(user_id, 10)
    if success:
        print(f"✓ Tracked review of 10 flashcards")
    else:
        print(f"✗ Failed to track flashcard review: {message}")
    
    # Get study statistics
    stats = profile_manager.get_study_statistics(user_id)
    if not stats:
        print("✗ Failed to retrieve study statistics")
    else:
        print(f"✓ Study statistics retrieved:")
        print(f"  Total study time: {stats['total_study_time']} minutes")
        print(f"  Quizzes completed: {stats['quizzes_completed']}")
        print(f"  Flashcards reviewed: {stats['flashcards_reviewed']}")
        print(f"  Last activity: {stats['last_activity']}")
    
    # 10. Test password reset functionality
    print_separator("PASSWORD RESET FUNCTIONALITY")
    print(f"Testing password reset for {test_username}")
    
    # Request a password reset
    print("Requesting password reset...")
    success, reset_result = auth_manager.request_password_reset(test_email)
    
    if not success:
        print(f"✗ Password reset request failed: {reset_result}")
    else:
        if isinstance(reset_result, dict) and "token" in reset_result:
            reset_token = reset_result["token"]
            print(f"✓ Password reset requested successfully")
            print(f"✓ Reset token: {reset_token}")
            
            # Test cancel password reset
            print("\nTesting password reset cancellation...")
            success, message = auth_manager.cancel_password_reset(user_id, test_password)
            
            if success:
                print(f"✓ {message}")
                
                # Verify reset token is invalidated by trying to use it
                new_password = "NewTest456!@#"
                success, message = auth_manager.reset_password(reset_token, new_password)
                
                if not success:
                    print(f"✓ Reset token correctly invalidated: {message}")
                else:
                    print(f"✗ Reset token should have been invalidated but still worked")
            else:
                print(f"✗ Failed to cancel password reset: {message}")
            
            # Test refreshing password reset
            print("\nTesting password reset refresh...")
            success, refresh_result = auth_manager.refresh_password_reset(test_email)
            
            if success and isinstance(refresh_result, dict) and "token" in refresh_result:
                new_reset_token = refresh_result["token"]
                print(f"✓ Password reset refreshed successfully")
                print(f"✓ New reset token: {new_reset_token}")
                
                # Test using the new token to reset password
                new_password = "NewTest456!@#"
                success, message = auth_manager.reset_password(new_reset_token, new_password)
                
                if success:
                    print(f"✓ Password reset with new token: {message}")
                    
                    # Test login with new password
                    success, login_result = auth_manager.login(test_username, new_password)
                    
                    if success:
                        print(f"✓ Login successful with new password")
                        # Update the test_password variable for later use
                        test_password = new_password
                    else:
                        print(f"✗ Login failed with new password: {login_result}")
                else:
                    print(f"✗ Failed to reset password with new token: {message}")
            else:
                print(f"✗ Failed to refresh password reset")
        else:
            print(f"✓ Password reset requested (token not returned in test mode)")
    
    # 11. Test account deactivation and reactivation
    print_separator("ACCOUNT DEACTIVATION")
    print(f"Testing account deactivation for {test_username}")
    
    # Create a second test user to keep testing with
    second_random_suffix = generate_random_string()
    second_username = f"test_user_{second_random_suffix}"
    second_email = f"test_{second_random_suffix}@example.com"
    second_password = "Test789!@#"
    
    print(f"First creating a second test user: {second_username}")
    success, second_user_result = auth_manager.register_user(
        username=second_username,
        email=second_email,
        password=second_password,
        first_name="Second",
        last_name="Testuser"
    )
    
    if not success:
        print(f"✗ Second user creation failed: {second_user_result}")
    else:
        second_user_id = second_user_result["id"]
        print(f"✓ Second user created with ID: {second_user_id}")
        
        # Verify second user email
        auth_manager.verify_email(second_user_result["verification_token"])
        
        # Now deactivate the first test user
        success, message = auth_manager.deactivate_user_account(user_id, test_password)
        
        if success:
            print(f"✓ {message}")
            
            # Try to log in with the deactivated account
            print("Attempting to log in with deactivated account...")
            success, result = auth_manager.login(test_username, test_password)
            
            if not success and "disabled" in result:
                print(f"✓ Login correctly failed for deactivated account: {result}")
            else:
                print(f"✗ Login should have failed for deactivated account")
        else:
            print(f"✗ Account deactivation failed: {message}")
    
    # 12. Test account deletion
    print_separator("ACCOUNT DELETION")
    print(f"Testing account deletion for {second_username}")
    
    # Count data before deletion
    user_exists = db['users'].count_documents({"_id": ObjectId(second_user_id)}) > 0
    
    if user_exists:
        print(f"✓ User exists in database before deletion")
        
        # Delete the second test account
        success, message = auth_manager.delete_user_account(second_user_id, second_password)
        
        if success:
            print(f"✓ {message}")
            
            # Verify the user no longer exists
            user_exists = db['users'].count_documents({"_id": ObjectId(second_user_id)}) > 0
            
            if not user_exists:
                print(f"✓ User successfully deleted from database")
            else:
                print(f"✗ User still exists in database after deletion attempt")
        else:
            print(f"✗ Account deletion failed: {message}")
    else:
        print(f"✗ Second test user does not exist in database")
    
    print_separator("TEST COMPLETED")
    print("All tests completed!")
    print(f"First test user: {test_username} / {test_email} (deactivated)")
    print(f"Second test user: {second_username} / {second_email} (deleted)")

if __name__ == "__main__":
    main()