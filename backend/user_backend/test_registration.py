"""
Tests the user registration functionality with the new Axiom structure.
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