from axiom_user_auth import get_database_connection, setup_user_collection, create_user

# Connect to database
db = get_database_connection()
users = setup_user_collection(db)

# Create a test user (replace with your desired values)
username = input("Enter username: ")
email = input("Enter email: ")
password = input("Enter password: ")
first_name = input("Enter first name: ")
last_name = input("Enter last name: ")

# Create the user
success, result = create_user(
    users,
    username=username,
    email=email,
    password=password,
    first_name=first_name,
    last_name=last_name
)

# Show the result
if success:
    print(f"User created successfully!")
    print(f"User ID: {result['id']}")
    print(f"Verification token: {result['verification_token']}")
else:
    print(f"User creation failed: {result}")