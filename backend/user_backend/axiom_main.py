"""
Axiom Integrated Example - Shows how to use all the manager classes together
"""
from axiom_database import AxiomDatabase
from axiom_auth_manager import AxiomAuthManager
from axiom_profile_manager import AxiomProfileManager
from axiom_course_manager import AxiomCourseManager
from axiom_content_manager import AxiomContentManager

def main():
    """Example of how to use the Axiom classes together"""
    # First get the shared database connection
    db_manager = AxiomDatabase()
    db = db_manager.get_db()
    
    # Initialize all managers with the same database connection
    auth_manager = AxiomAuthManager(db)
    profile_manager = AxiomProfileManager(db)
    course_manager = AxiomCourseManager(db)
    content_manager = AxiomContentManager(db)
    
    print("==== AXIOM LEARNING PLATFORM DEMO ====")
    print("\n1. User Registration")
    
    # Register a new test user
    success, result = auth_manager.register_user(
        username="student_demo",
        email="student@example.com",
        password="Secure123!",
        first_name="Student",
        last_name="Demo"
    )
    
    if not success:
        print(f"Registration failed: {result}")
        return
    
    user_id = result["id"]
    verification_token = result["verification_token"]
    print(f"User created successfully with ID: {user_id}")
    print(f"Verification token: {verification_token}")
    
    # Verify the user's email
    print("\n2. Email Verification")
    success, message = auth_manager.verify_email(verification_token)
    print(f"Email verification: {message}")
    
    # Login with the new user
    print("\n3. User Login")
    success, result = auth_manager.login("student_demo", "Secure123!")
    
    if not success:
        print(f"Login failed: {result}")
        return
    
    print(f"Login successful for: {result['first_name']} {result['last_name']}")
    
    # Update user profile
    print("\n4. Update User Profile")
    profile_updates = {
        "profile": {
            "education_level": "University",
            "bio": "Computer Science student interested in machine learning"
        }
    }
    
    success, message = profile_manager.update_profile(user_id, profile_updates)
    print(f"Profile update: {message}")
    
    # Create a new course
    print("\n5. Create a New Course")
    success, course_result = course_manager.create_course(
        user_id=user_id,
        title="Introduction to Python",
        description="Learn Python programming basics"
    )
    
    if not success:
        print(f"Course creation failed: {course_result}")
        return
    
    course_id = course_result["id"]
    print(f"Course created: {course_result['title']}")
    
    # Create a module in the course
    print("\n6. Create a Module")
    success, module_result = course_manager.create_module(
        course_id=course_id,
        user_id=user_id,
        title="Variables and Data Types",
        description="Understanding Python variables and basic data types"
    )
    
    if not success:
        print(f"Module creation failed: {module_result}")
        return
    
    module_id = module_result["id"]
    print(f"Module created: {module_result['title']}")
    
    # Create a flashcard deck
    print("\n7. Create Flashcards")
    cards = [
        {"front": "What is a variable?", "back": "A named location in memory that stores a value"},
        {"front": "What is an integer?", "back": "A whole number without a decimal point"}
    ]
    
    success, deck_result = content_manager.create_flashcard_deck(
        module_id=module_id,
        user_id=user_id,
        title="Python Basics Flashcards",
        cards=cards
    )
    
    if success:
        deck_id = deck_result["id"]
        print(f"Created flashcard deck with {deck_result['card_count']} cards")
    
    # Create a quiz
    print("\n8. Create a Quiz")
    questions = [
        {
            "question": "Which of the following is not a Python data type?",
            "options": ["Integer", "Float", "Character", "Boolean"],
            "correct_answer": "Character"
        },
        {
            "question": "What will print(type(10.5)) return?",
            "options": ["<class 'int'>", "<class 'float'>", "<class 'str'>", "<class 'bool'>"],
            "correct_answer": "<class 'float'>"
        }
    ]
    
    success, quiz_result = content_manager.create_quiz(
        module_id=module_id,
        user_id=user_id,
        title="Python Data Types Quiz",
        questions=questions
    )
    
    if success:
        quiz_id = quiz_result["id"]
        print(f"Created quiz with {quiz_result['question_count']} questions")
    
    # Create a video chapter
    print("\n9. Create a Video Chapter")
    success, chapter_result = content_manager.create_video_chapter(
        module_id=module_id,
        user_id=user_id,
        title="Introduction to Variables",
        video_url="https://www.youtube.com/watch?v=example",
        start_time=120,  # 2 minutes in
        end_time=240,    # 4 minutes in
        transcript="In this section, we'll learn about variables in Python..."
    )
    
    if success:
        chapter_id = chapter_result["id"]
        print(f"Created video chapter: {chapter_result['title']} (Duration: {chapter_result['duration']} seconds)")
    
    # Track study activities
    print("\n10. Track Study Activities")
    profile_manager.track_study_time(user_id, 45)  # 45 minutes of study
    profile_manager.track_quiz_completion(user_id)
    profile_manager.track_flashcard_review(user_id, 10)
    
    print("Recorded study activities")
    
    # Get user's stats
    stats = profile_manager.get_study_statistics(user_id)
    print("\n11. User Study Statistics")
    print(f"Total Study Time: {stats['total_study_time']} minutes")
    print(f"Quizzes Completed: {stats['quizzes_completed']}")
    print(f"Flashcards Reviewed: {stats['flashcards_reviewed']}")
    
    # Get all module content
    print("\n12. Module Content Summary")
    content = content_manager.get_module_content(module_id)
    print(f"Flashcard Decks: {len(content['flashcard_decks'])}")
    print(f"Quizzes: {len(content['quizzes'])}")
    print(f"Video Chapters: {len(content['video_chapters'])}")
    
    print("\n==== DEMO COMPLETED SUCCESSFULLY ====")

if __name__ == "__main__":
    main()