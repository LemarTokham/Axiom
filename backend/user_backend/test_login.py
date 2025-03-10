"""
Tests the login functionality with the new Axiom structure.
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
        print(f"Email verified: {'Yes' if result.get('is_verified', False) else 'No'}")
    else:
        print(f"Authentication failed: {result}")

if __name__ == "__main__":
    main()