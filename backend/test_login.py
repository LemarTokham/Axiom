from axiom_user_auth import get_database_connection, setup_user_collection, authenticate_user

# Connect to database
db = get_database_connection()
users = setup_user_collection(db)

# Get login credentials
username_or_email = input("Enter username or email: ")
password = input("Enter password: ")

# Attempt authentication
success, result = authenticate_user(
    users,
    username_or_email,
    password
)

# Show the result
if success:
    print(f"Authentication successful!")
    print(f"User ID: {result['user_id']}")
    print(f"Username: {result['username']}")
else:
    print(f"Authentication failed: {result}")