# ====================================
# SETUP AND PREREQUISITES
# ====================================

# 1. Install Required Dependencies
# Run this in your terminal:
# pip install pymongo bcrypt python-dotenv

# 2. Create a .env file in your project directory
# Add your MongoDB connection string (replace with your actual credentials):
"""
MONGODB_URI=mongodb+srv://your_username:your_password@your_cluster_address/
"""

# 3. Save the main script as "axiom_user_auth.py"

# ====================================
# TEST SCRIPT FOR AXIOM USER AUTH
# ====================================
# Save this as "test_axiom_auth.py"

from axiom_user_auth import get_database_connection, setup_user_collection, create_user, authenticate_user
import random
import string

def generate_random_string(length=8):
    """Generate a random string for testing"""
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))

def test_user_creation_and_auth():
    """Test user creation and authentication flow"""
    # Connect to the database
    db = get_database_connection()
    users = setup_user_collection(db)
    
    # Generate unique test user data
    random_suffix = generate_random_string()
    test_username = f"test_user_{random_suffix}"
    test_email = f"test_{random_suffix}@example.com"
    test_password = f"TestPass123!_{random_suffix}"
    
    # Step 1: Create a user with valid data
    print("\n=== Testing User Creation with Valid Data ===")
    success, result = create_user(
        users,
        username=test_username,
        email=test_email,
        password=test_password,
        first_name="Test",
        last_name="User"
    )
    
    print(f"User creation success: {success}")
    if success:
        print(f"User ID: {result['id']}")
        print(f"Verification token: {result['verification_token']}")
    else:
        print(f"Error: {result}")
    
    # Step 2: Try to create a duplicate user (should fail)
    print("\n=== Testing Duplicate User Creation ===")
    dup_success, dup_result = create_user(
        users,
        username=test_username,
        email=test_email,
        password=test_password,
        first_name="Test",
        last_name="User"
    )
    
    print(f"Duplicate user creation success: {dup_success}")
    print(f"Expected error message: {dup_result}")
    
    # Step 3: Test authentication with correct credentials
    print("\n=== Testing Authentication with Correct Credentials ===")
    auth_success, auth_result = authenticate_user(
        users,
        test_username,
        test_password
    )
    
    print(f"Authentication success: {auth_success}")
    if auth_success:
        print(f"Authenticated user: {auth_result['username']}")
    else:
        print(f"Error: {auth_result}")
    
    # Step 4: Test authentication with incorrect password
    print("\n=== Testing Authentication with Incorrect Password ===")
    wrong_auth_success, wrong_auth_result = authenticate_user(
        users,
        test_username,
        "WrongPassword123!"
    )
    
    print(f"Wrong password authentication success: {wrong_auth_success}")
    print(f"Expected error message: {wrong_auth_result}")
    
    # Step 5: Test authentication with non-existent user
    print("\n=== Testing Authentication with Non-existent User ===")
    nonexist_auth_success, nonexist_auth_result = authenticate_user(
        users,
        "nonexistent_user",
        "SomePassword123!"
    )
    
    print(f"Non-existent user authentication success: {nonexist_auth_success}")
    print(f"Expected error message: {nonexist_auth_result}")
    
    # Step 6: Test various invalid inputs for user creation
    test_invalid_user_creation(users)

def test_invalid_user_creation(users):
    """Test various invalid inputs for user creation"""
    print("\n=== Testing Invalid User Creation Scenarios ===")
    
    # Test case 1: Invalid email format
    print("\nTest: Invalid email format")
    success, result = create_user(
        users,
        username="test_invalid_email",
        email="not_an_email",
        password="ValidPass123!",
        first_name="Test",
        last_name="User"
    )
    print(f"Creation success (should be False): {success}")
    print(f"Expected error message: {result}")
    
    # Test case 2: Weak password
    print("\nTest: Weak password")
    success, result = create_user(
        users,
        username="test_weak_pass",
        email="test_weak@example.com",
        password="weak",
        first_name="Test",
        last_name="User"
    )
    print(f"Creation success (should be False): {success}")
    print(f"Expected error message: {result}")
    
    # Test case 3: Missing required fields
    print("\nTest: Missing fields")
    success, result = create_user(
        users,
        username="",
        email="test_missing@example.com",
        password="ValidPass123!",
        first_name="Test",
        last_name="User"
    )
    print(f"Creation success (should be False): {success}")
    print(f"Expected error message: {result}")

def test_consecutive_failed_logins():
    """Test account lockout after multiple failed login attempts"""
    # Connect to the database
    db = get_database_connection()
    users = setup_user_collection(db)
    
    # Create a test user
    random_suffix = generate_random_string()
    test_username = f"test_lockout_{random_suffix}"
    test_email = f"lockout_{random_suffix}@example.com"
    test_password = f"TestPass123!_{random_suffix}"
    
    # Step 1: Create user
    print("\n=== Testing Account Lockout ===")
    success, result = create_user(
        users,
        username=test_username,
        email=test_email,
        password=test_password,
        first_name="Test",
        last_name="Lockout"
    )
    
    if not success:
        print(f"Failed to create test user: {result}")
        return
    
    # Step 2: Attempt multiple failed logins
    print("\nAttempting multiple failed logins:")
    
    for i in range(6):  # We set lockout at 5 attempts
        auth_success, auth_result = authenticate_user(
            users,
            test_username,
            "WrongPassword123!"
        )
        print(f"Attempt {i+1}: Success={auth_success}, Message={auth_result}")
    
    # Step 3: Try with correct password (should still be locked)
    print("\nAttempting login with correct password after lockout:")
    auth_success, auth_result = authenticate_user(
        users,
        test_username,
        test_password
    )
    print(f"Correct password login: Success={auth_success}, Message={auth_result}")

if __name__ == "__main__":
    print("===== TESTING AXIOM USER AUTHENTICATION SYSTEM =====")
    
    # Run creation and authentication tests
    test_user_creation_and_auth()
    
    # Run account lockout tests
    test_consecutive_failed_logins()
    
    print("\n===== TEST COMPLETE =====")