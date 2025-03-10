# Axiom Learning Platform

Axiom is an intelligent revision platform designed for students. It helps generate personalized flashcards, quizzes, and video clips to enhance learning.

## Setup Instructions

### Prerequisites

1. Python 3.8+ installed on your system
2. MongoDB installed locally or a MongoDB Atlas account
3. pip package manager

### Installation

1. Create a Python virtual environment:
   ```bash
   python -m venv axiom-env
   ```

2. Activate the virtual environment:
   - Windows:
     ```bash
     axiom-env\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source axiom-env/bin/activate
     ```

3. Install the required dependencies:
   ```bash
   pip install pymongo bcrypt python-dotenv
   ```

4. Configure the MongoDB connection:
   - Edit the `.env` file and update the `MONGODB_URI` with your MongoDB connection string
   - Example: `MONGODB_URI=mongodb://localhost:27017/`

### File Structure

Make sure all these files are in the same directory:
- `axiom_database.py` - Database connection manager (singleton)
- `axiom_auth_manager.py` - Authentication & user management
- `axiom_profile_manager.py` - User profile & study statistics
- `axiom_course_manager.py` - Course & module management
- `axiom_content_manager.py` - Learning content (flashcards, quizzes, videos)
- `axiom_main.py` - Demo that shows how all components work together

### Running the Demo

Run the main script to see the full demo:
```bash
python axiom_main.py
```

### Running Individual Tests

- Test registration: `python test_registration.py`
- Test login: `python test_login.py`
- Test course creation: `python test_course_creation.py`

## System Architecture

The Axiom platform is divided into several components:

1. **AxiomDatabase**: Singleton for database connections and collection management
2. **AxiomAuthManager**: Handles user registration, login, and security
3. **AxiomProfileManager**: Manages user profiles, preferences, and learning statistics
4. **AxiomCourseManager**: Handles courses and modules organization
5. **AxiomContentManager**: Manages learning content (flashcards, quizzes, video chapters)

## Contributing

When contributing to this project, please maintain the modular structure and follow the established patterns for database interactions and error handling.

## License

This project is licensed for educational purposes only. Copyright © 2025 Axiom Team.
