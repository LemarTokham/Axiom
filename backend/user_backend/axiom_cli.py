"""
Axiom Learning Platform - Command Line Interface with AI Features
This script provides a terminal-based interface to interact with the Axiom system.
Users can register, login, manage profiles, create courses, input notes, and generate AI content.

To run this CLI:
    python axiom_cli.py
"""
from axiom_database import AxiomDatabase
from axiom_auth_manager import AxiomAuthManager
from axiom_profile_manager import AxiomProfileManager
from axiom_course_manager import AxiomCourseManager
from axiom_content_manager_updated import AxiomContentManager
from axiom_ai_content_generator import AxiomAIContentGenerator
from bson.objectid import ObjectId
import os
import getpass
import time
from datetime import datetime

class AxiomCLI:
    """Command-line interface for the Axiom learning platform"""
    
    def __init__(self):
        """Initialize the CLI with database connection and manager instances"""
        # Connect to database
        self.db = AxiomDatabase().get_db()
        
        # Initialize managers
        self.auth_manager = AxiomAuthManager(self.db)
        self.profile_manager = AxiomProfileManager(self.db)
        self.course_manager = AxiomCourseManager(self.db)
        self.content_manager = AxiomContentManager(self.db)
        self.ai_generator = AxiomAIContentGenerator(self.db)
        
        # Session state
        self.current_user = None
        self.current_course = None
        self.current_module = None
        self.current_note = None
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title):
        """Print a formatted header"""
        self.clear_screen()
        print("=" * 60)
        print(f"{title:^60}")
        print("=" * 60)
        if self.current_user:
            print(f"Logged in as: {self.current_user['username']} ({self.current_user['first_name']} {self.current_user['last_name']})")
        print()
    
    def print_menu(self, options):
        """Print a menu with numbered options"""
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")
        print()
    
    def get_menu_choice(self, options):
        """Get a valid menu choice from the user"""
        while True:
            try:
                choice = int(input("Enter your choice (0 to exit): "))
                if choice == 0:
                    return 0
                if 1 <= choice <= len(options):
                    return choice
                print(f"Please enter a number between 1 and {len(options)}, or 0 to exit.")
            except ValueError:
                print("Please enter a valid number.")
    
    def wait_for_enter(self):
        """Wait for the user to press enter to continue"""
        input("\nPress Enter to continue...")
    
    def main_menu(self):
        """Display the main menu"""
        self.clear_screen()
        
        options = [
            "Register new account",
            "Login",
            "Reset password",
            "Exit"
        ]
        
        while True:
            self.print_header("AXIOM LEARNING PLATFORM")
            print("Welcome to the Axiom Learning Platform!")
            print("Please select an option to continue:")
            print()
            self.print_menu(options)
            
            choice = self.get_menu_choice(options)
            
            if choice == 1:
                self.register_user()
            elif choice == 2:
                self.login()
                if self.current_user:
                    self.user_menu()
            elif choice == 3:
                self.reset_password()
            elif choice == 0 or choice == 4:
                self.exit_program()
                break
    
    def register_user(self):
        """Register a new user"""
        self.print_header("REGISTER NEW ACCOUNT")
        
        print("Please fill in the following information:")
        username = input("Username: ")
        email = input("Email: ")
        first_name = input("First name: ")
        last_name = input("Last name: ")
        
        # Get password with confirmation
        while True:
            password = getpass.getpass("Password: ")
            confirm_password = getpass.getpass("Confirm password: ")
            
            if password == confirm_password:
                break
            print("Passwords do not match. Please try again.")
        
        # Register the user
        success, result = self.auth_manager.register_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        if success:
            print("\n✅ Account created successfully!")
            print(f"A verification token has been generated: {result['verification_token']}")
            print("In a real system, this would be sent via email.")
            
            verify = input("\nVerify email now? (y/n): ").lower() == 'y'
            if verify:
                success, message = self.auth_manager.verify_email(result['verification_token'])
                print(f"\n{'✅' if success else '❌'} {message}")
        else:
            print(f"\n❌ Account creation failed: {result}")
        
        self.wait_for_enter()
    
    def login(self):
        """Log in a user"""
        self.print_header("LOGIN")
        
        username_or_email = input("Username or email: ")
        password = getpass.getpass("Password: ")
        
        success, result = self.auth_manager.login(username_or_email, password)
        
        if success:
            print("\n✅ Login successful!")
            self.current_user = result
        else:
            print(f"\n❌ Login failed: {result}")
            self.wait_for_enter()
    
    def reset_password(self):
        """Request a password reset"""
        self.print_header("PASSWORD RESET")
        
        email = input("Enter your email address: ")
        
        success, result = self.auth_manager.request_password_reset(email)
        
        if success:
            if isinstance(result, dict) and "token" in result:
                print("\n✅ Password reset requested successfully.")
                print(f"Reset token: {result['token']}")
                print("In a real system, this would be sent via email.")
                
                use_token = input("\nUse this token to reset your password now? (y/n): ").lower() == 'y'
                if use_token:
                    self.use_reset_token(result['token'])
            else:
                print("\n✅ If a user with this email exists, a password reset link has been sent.")
        else:
            print(f"\n❌ Password reset request failed: {result}")
        
        self.wait_for_enter()
    
    def use_reset_token(self, token):
        """Use a reset token to set a new password"""
        print("\n--- RESET PASSWORD ---")
        
        # Get new password with confirmation
        while True:
            new_password = getpass.getpass("New password: ")
            confirm_password = getpass.getpass("Confirm new password: ")
            
            if new_password == confirm_password:
                break
            print("Passwords do not match. Please try again.")
        
        success, message = self.auth_manager.reset_password(token, new_password)
        
        print(f"\n{'✅' if success else '❌'} {message}")
    
    def user_menu(self):
        """Display the main user menu after login"""
        # Check if the user is an admin and add the Admin Panel option
        is_admin = self.current_user.get('is_admin', False)
        
        options = [
            "View profile",
            "Update profile",
            "Manage courses",
            "Manage notes",  # Added direct notes management
            "Study statistics",
            "Account settings"
        ]
        
        # Add admin panel option for admin users
        if is_admin:
            options.insert(4, "Admin Panel")
        
        options.append("Logout")
        
        while self.current_user:
            self.print_header("USER MENU")
            
            # Show admin badge for admins
            if is_admin:
                print("🔑 You are logged in with ADMIN privileges")
                
            self.print_menu(options)
            
            choice = self.get_menu_choice(options)
            
            if choice == 1:
                self.view_profile()
            elif choice == 2:
                self.update_profile()
            elif choice == 3:
                self.manage_courses()
            elif choice == 4:
                self.manage_notes()
            elif choice == 5 and is_admin:
                self.admin_panel()
            elif (choice == 5 and not is_admin) or (choice == 6 and is_admin):
                self.view_study_statistics()
            elif (choice == 6 and not is_admin) or (choice == 7 and is_admin):
                self.account_settings()
            elif (choice == 7 and not is_admin) or (choice == 8 and is_admin) or choice == 0:
                self.logout()
                break
    
    def generate_ai_content_menu(self):
        """Menu for AI content generation"""
        options = [
            "Generate flashcards from notes",
            "Generate quiz from notes",
            "Generate video chapter suggestions from notes",
            "Back to user menu"
        ]
        
        while True:
            self.print_header("GENERATE AI CONTENT")
            self.print_menu(options)
            
            choice = self.get_menu_choice(options)
            
            if choice == 1:
                self.generate_ai_flashcards()
            elif choice == 2:
                self.generate_ai_quiz()
            elif choice == 3:
                self.generate_ai_video_chapters()
            elif choice == 4 or choice == 0:
                break
    
    def generate_ai_flashcards(self):
        """Generate AI flashcards from notes"""
        # First select a note
        if not self.select_note_for_generation("GENERATE AI FLASHCARDS"):
            return
            
        # Then select a module
        if not self.select_module_for_generation("GENERATE AI FLASHCARDS"):
            return
            
        # Generate flashcards
        self.print_header(f"GENERATING FLASHCARDS: {self.current_note['title']}")
        print(f"Generating flashcards for module: {self.current_module['title']}")
        print("This may take a moment...")
        
        success, result = self.content_manager.generate_flashcards_from_notes(
            note_id=self.current_note['_id'],
            user_id=self.current_user['id'],
            module_id=self.current_module['_id']
        )
        
        if success:
            print(f"\n✅ Flashcard deck created successfully with {result['card_count']} cards.")
            print(f"Title: {result['title']}")
            print(f"Added to module: {self.current_module['title']}")
        else:
            print(f"\n❌ Flashcard generation failed: {result}")
        
        self.wait_for_enter()
        
        # Reset selected items
        self.current_note = None
        self.current_module = None
    
    def generate_ai_quiz(self):
        """Generate AI quiz from notes"""
        # First select a note
        if not self.select_note_for_generation("GENERATE AI QUIZ"):
            return
            
        # Then select a module
        if not self.select_module_for_generation("GENERATE AI QUIZ"):
            return
            
        # Generate quiz
        self.print_header(f"GENERATING QUIZ: {self.current_note['title']}")
        print(f"Generating quiz for module: {self.current_module['title']}")
        print("This may take a moment...")
        
        success, result = self.content_manager.generate_quiz_from_notes(
            note_id=self.current_note['_id'],
            user_id=self.current_user['id'],
            module_id=self.current_module['_id']
        )
        
        if success:
            print(f"\n✅ Quiz created successfully with {result['question_count']} questions.")
            print(f"Title: {result['title']}")
            print(f"Added to module: {self.current_module['title']}")
        else:
            print(f"\n❌ Quiz generation failed: {result}")
        
        self.wait_for_enter()
        
        # Reset selected items
        self.current_note = None
        self.current_module = None
    
    def generate_ai_video_chapters(self):
        """Generate AI video chapter suggestions from notes"""
        # First select a note
        if not self.select_note_for_generation("GENERATE VIDEO CHAPTER SUGGESTIONS"):
            return
            
        # Then select a module
        if not self.select_module_for_generation("GENERATE VIDEO CHAPTER SUGGESTIONS"):
            return
            
        # Generate video chapter suggestions
        self.print_header(f"GENERATING VIDEO CHAPTERS: {self.current_note['title']}")
        print(f"Generating video chapter suggestions for module: {self.current_module['title']}")
        print("This may take a moment...")
        
        success, result = self.content_manager.suggest_video_chapters_from_notes(
            note_id=self.current_note['_id'],
            user_id=self.current_user['id'],
            module_id=self.current_module['_id']
        )
        
        if success:
            print(f"\n✅ Video chapter suggestions generated successfully.")
            print("\nSuggested chapters:")
            for i, chapter in enumerate(result['chapters'], 1):
                print(f"{i}. {chapter['title']}")
                print(f"   Description: {chapter['description']}")
                print()
                
            # Option to create video chapters
            create_chapters = input("\nWould you like to create these video chapters? (y/n): ").lower() == 'y'
            if create_chapters:
                self.create_video_chapters_from_suggestions(result['chapters'])
        else:
            print(f"\n❌ Video chapter suggestion generation failed: {result}")
        
        self.wait_for_enter()
        
        # Reset selected items
        self.current_note = None
        self.current_module = None
    
    def create_video_chapters_from_suggestions(self, chapters):
        """Create video chapters from AI suggestions"""
        self.print_header("CREATE VIDEO CHAPTERS")
        
        video_url = input("Enter a YouTube video URL for these chapters: ")
        if not video_url:
            print("❌ Video URL is required.")
            return
        
        for chapter in chapters:
            print(f"\nCreating chapter: {chapter['title']}")
            
            try:
                start_time = int(input("Start time (seconds): "))
                end_time = int(input("End time (seconds): "))
                
                if start_time < 0 or end_time <= start_time:
                    print("❌ Invalid timestamps. End time must be greater than start time.")
                    continue
            except ValueError:
                print("❌ Timestamps must be valid numbers.")
                continue
            
            success, result = self.content_manager.create_video_chapter(
                module_id=self.current_module['_id'],
                user_id=self.current_user['id'],
                title=chapter['title'],
                video_url=video_url,
                start_time=start_time,
                end_time=end_time,
                transcript=chapter['description']
            )
            
            if success:
                print(f"✅ Video chapter created successfully: {chapter['title']}")
            else:
                print(f"❌ Video chapter creation failed: {result}")
    
    def select_note_for_generation(self, title):
        """Select a note for AI content generation"""
        self.print_header(title)
        
        notes = self.content_manager.get_user_notes(self.current_user['id'])
        
        if not notes:
            print("You don't have any notes yet. Please upload notes first.")
            self.wait_for_enter()
            return False
        
        print("Select a note to generate content from:")
        for i, note in enumerate(notes, 1):
            print(f"{i}. {note['title']} - {note['topic']}")
        
        try:
            choice = int(input("\nEnter note number (0 to go back): "))
            if choice == 0:
                return False
            
            if 1 <= choice <= len(notes):
                self.current_note = notes[choice - 1]
                return True
            else:
                print("❌ Invalid note number.")
                self.wait_for_enter()
                return False
        except ValueError:
            print("❌ Please enter a valid number.")
            self.wait_for_enter()
            return False
    
    def select_module_for_generation(self, title):
        """Select a module for AI content generation"""
        self.print_header(title)
        
        # First select a course if none is selected
        if not self.current_course:
            courses = self.course_manager.get_user_courses(self.current_user['id'])
            
            if not courses:
                print("You don't have any courses yet. Please create a course first.")
                self.wait_for_enter()
                return False
            
            print("Select a course:")
            for i, course in enumerate(courses, 1):
                print(f"{i}. {course['title']}")
            
            try:
                choice = int(input("\nEnter course number (0 to go back): "))
                if choice == 0:
                    return False
                
                if 1 <= choice <= len(courses):
                    self.current_course = courses[choice - 1]
                else:
                    print("❌ Invalid course number.")
                    self.wait_for_enter()
                    return False
            except ValueError:
                print("❌ Please enter a valid number.")
                self.wait_for_enter()
                return False
        
        # Now select a module
        modules = self.course_manager.get_course_modules(self.current_course['_id'])
        
        if not modules:
            print(f"Course '{self.current_course['title']}' has no modules. Please create a module first.")
            self.wait_for_enter()
            # Reset current course
            self.current_course = None
            return False
        
        print(f"\nSelect a module from course '{self.current_course['title']}':")
        for i, module in enumerate(modules, 1):
            print(f"{i}. {module['title']}")
        
        try:
            choice = int(input("\nEnter module number (0 to go back): "))
            if choice == 0:
                # Reset current course
                self.current_course = None
                return False
            
            if 1 <= choice <= len(modules):
                self.current_module = modules[choice - 1]
                return True
            else:
                print("❌ Invalid module number.")
                self.wait_for_enter()
                # Reset current course
                self.current_course = None
                return False
        except ValueError:
            print("❌ Please enter a valid number.")
            self.wait_for_enter()
            # Reset current course
            self.current_course = None
            return False
    
    def view_profile(self):
        """View user profile information"""
        self.print_header("VIEW PROFILE")
        
        profile = self.profile_manager.get_user_profile(self.current_user['id'])
        
        if not profile:
            print("❌ Failed to retrieve profile.")
            self.wait_for_enter()
            return
        
        print(f"Username: {profile['username']}")
        print(f"Email: {profile['email']}")
        print(f"Name: {profile['first_name']} {profile['last_name']}")
        print(f"Account created: {profile['created_at']}")
        
        # Profile info
        if profile.get('profile'):
            print("\n--- PROFILE ---")
            print(f"Bio: {profile['profile'].get('bio') or 'Not set'}")
            print(f"Education: {profile['profile'].get('education_level') or 'Not set'}")
            subjects = profile['profile'].get('subjects', [])
            print(f"Subjects: {', '.join(subjects) if subjects else 'None'}")
        
        # Preferences
        if profile.get('preferences'):
            print("\n--- PREFERENCES ---")
            print(f"Theme: {profile['preferences'].get('theme', 'light')}")
            print(f"Language: {profile['preferences'].get('language', 'en')}")
            print(f"Email notifications: {'On' if profile['preferences'].get('notification_email', True) else 'Off'}")
            print(f"Study reminders: {'On' if profile['preferences'].get('study_reminder', False) else 'Off'}")
        
        self.wait_for_enter()
    
    def update_profile(self):
        """Update user profile information"""
        options = [
            "Update personal information",
            "Update preferences",
            "Back to user menu"
        ]
        
        while True:
            self.print_header("UPDATE PROFILE")
            self.print_menu(options)
            
            choice = self.get_menu_choice(options)
            
            if choice == 1:
                self.update_personal_info()
            elif choice == 2:
                self.update_preferences()
            elif choice == 3 or choice == 0:
                break
    
    def update_personal_info(self):
        """Update personal information"""
        self.print_header("UPDATE PERSONAL INFORMATION")
        
        profile = self.profile_manager.get_user_profile(self.current_user['id'])
        
        print("Leave fields blank to keep current values.")
        
        bio = input(f"Bio [{profile['profile'].get('bio', '')}]: ")
        education = input(f"Education level [{profile['profile'].get('education_level', '')}]: ")
        
        current_subjects = profile['profile'].get('subjects', [])
        subjects_str = input(f"Subjects (comma-separated) [{', '.join(current_subjects)}]: ")
        
        # Process subjects
        if subjects_str:
            subjects = [s.strip() for s in subjects_str.split(',') if s.strip()]
        else:
            subjects = current_subjects
        
        # Prepare updates
        updates = {
            "profile": {
                "bio": bio if bio else profile['profile'].get('bio'),
                "education_level": education if education else profile['profile'].get('education_level'),
                "subjects": subjects
            }
        }
        
        success, message = self.profile_manager.update_profile(self.current_user['id'], updates)
        
        print(f"\n{'✅' if success else '❌'} {message}")
        self.wait_for_enter()
    
    def update_preferences(self):
        """Update user preferences"""
        self.print_header("UPDATE PREFERENCES")
        
        profile = self.profile_manager.get_user_profile(self.current_user['id'])
        
        # Get current values
        current_theme = profile['preferences'].get('theme', 'light')
        current_language = profile['preferences'].get('language', 'en')
        current_notifications = profile['preferences'].get('notification_email', True)
        current_reminders = profile['preferences'].get('study_reminder', False)
        
        # Theme options
        print("1. Theme options:")
        print("   1. Light")
        print("   2. Dark")
        theme_choice = input(f"Select theme [current: {current_theme}]: ")
        
        if theme_choice == '1':
            theme = 'light'
        elif theme_choice == '2':
            theme = 'dark'
        else:
            theme = current_theme
        
        # Language options
        print("\n2. Language options:")
        print("   1. English (en)")
        print("   2. Spanish (es)")
        print("   3. French (fr)")
        language_choice = input(f"Select language [current: {current_language}]: ")
        
        if language_choice == '1':
            language = 'en'
        elif language_choice == '2':
            language = 'es'
        elif language_choice == '3':
            language = 'fr'
        else:
            language = current_language
        
        # Notification options
        notifications = input(f"\n3. Email notifications [current: {'On' if current_notifications else 'Off'}] (y/n): ")
        if notifications.lower() in ('y', 'n'):
            notifications = notifications.lower() == 'y'
        else:
            notifications = current_notifications
        
        # Reminder options
        reminders = input(f"\n4. Study reminders [current: {'On' if current_reminders else 'Off'}] (y/n): ")
        if reminders.lower() in ('y', 'n'):
            reminders = reminders.lower() == 'y'
        else:
            reminders = current_reminders
        
        # Prepare updates
        preference_updates = {
            "theme": theme,
            "language": language,
            "notification_email": notifications,
            "study_reminder": reminders
        }
        
        success, message = self.profile_manager.update_preferences(self.current_user['id'], preference_updates)
        
        print(f"\n{'✅' if success else '❌'} {message}")
        self.wait_for_enter()
    
    def manage_courses(self):
        """Manage user courses"""
        options = [
            "View my courses",
            "Create new course",
            "Back to user menu"
        ]
        
        while True:
            self.print_header("MANAGE COURSES")
            self.print_menu(options)
            
            choice = self.get_menu_choice(options)
            
            if choice == 1:
                self.view_courses()
            elif choice == 2:
                self.create_course()
            elif choice == 3 or choice == 0:
                break
    
    def view_courses(self):
        """View user's courses"""
        self.print_header("MY COURSES")
        
        courses = self.course_manager.get_user_courses(self.current_user['id'])
        
        if not courses:
            print("You don't have any courses yet.")
            self.wait_for_enter()
            return
        
        print(f"Found {len(courses)} courses:\n")
        
        for i, course in enumerate(courses, 1):
            print(f"{i}. {course['title']}")
            print(f"   Description: {course['description']}")
            print(f"   Created: {course['created_at']}")
            print(f"   Last updated: {course['last_updated']}")
            print()
        
        # Allow selecting a course
        try:
            choice = int(input("Enter course number to manage (0 to go back): "))
            if 1 <= choice <= len(courses):
                self.current_course = courses[choice - 1]
                self.manage_course()
        except ValueError:
            pass
            
        self.current_course = None
    
    def create_course(self):
        """Create a new course"""
        self.print_header("CREATE NEW COURSE")
        
        title = input("Course title: ")
        description = input("Course description: ")
        
        if not title:
            print("❌ Title is required.")
            self.wait_for_enter()
            return
        
        success, result = self.course_manager.create_course(
            user_id=self.current_user['id'],
            title=title,
            description=description
        )
        
        if success:
            print(f"\n✅ Course created successfully with ID: {result['id']}")
            manage_now = input("\nManage this course now? (y/n): ").lower() == 'y'
            
            if manage_now:
                # Get the full course object
                course = self.course_manager.get_course(result['id'])
                if course:
                    self.current_course = course
                    self.manage_course()
        else:
            print(f"\n❌ Course creation failed: {result}")
            self.wait_for_enter()
    
    def manage_course(self):
        """Manage a selected course"""
        options = [
            "View course details",
            "Edit course",
            "Manage modules",
            "Delete course",
            "Back to courses"
        ]
        
        while self.current_course:
            self.print_header(f"MANAGE COURSE: {self.current_course['title']}")
            self.print_menu(options)
            
            choice = self.get_menu_choice(options)
            
            if choice == 1:
                self.view_course_details()
            elif choice == 2:
                self.edit_course()
            elif choice == 3:
                self.manage_modules()
            elif choice == 4:
                if self.delete_course():
                    break
            elif choice == 5 or choice == 0:
                self.current_course = None
                break
    
    def view_course_details(self):
        """View details of the current course"""
        self.print_header(f"COURSE DETAILS: {self.current_course['title']}")
        
        print(f"Course ID: {self.current_course['_id']}")
        print(f"Title: {self.current_course['title']}")
        print(f"Description: {self.current_course['description']}")
        print(f"Created: {self.current_course['created_at']}")
        print(f"Last updated: {self.current_course['last_updated']}")
        
        # Get modules
        modules = self.course_manager.get_course_modules(self.current_course['_id'])
        
        if modules:
            print(f"\nModules ({len(modules)}):")
            for i, module in enumerate(modules, 1):
                print(f"  {i}. {module['title']}")
        else:
            print("\nThis course has no modules yet.")
        
        self.wait_for_enter()
    
    def edit_course(self):
        """Edit the current course"""
        self.print_header(f"EDIT COURSE: {self.current_course['title']}")
        
        print("Leave fields blank to keep current values.")
        
        title = input(f"Title [{self.current_course['title']}]: ")
        description = input(f"Description [{self.current_course['description']}]: ")
        
        # Prepare updates
        updates = {}
        if title:
            updates["title"] = title
        if description:
            updates["description"] = description
        
        if not updates:
            print("\nNo changes made.")
            self.wait_for_enter()
            return
        
        success, message = self.course_manager.update_course(
            course_id=self.current_course['_id'],
            user_id=self.current_user['id'],
            updates=updates
        )
        
        if success:
            print(f"\n✅ {message}")
            # Update the current course object with new values
            if title:
                self.current_course['title'] = title
            if description:
                self.current_course['description'] = description
        else:
            print(f"\n❌ {message}")
        
        self.wait_for_enter()
    
    def delete_course(self):
        """Delete the current course"""
        self.print_header(f"DELETE COURSE: {self.current_course['title']}")
        
        print("⚠️ WARNING: This will permanently delete the course and all its modules.")
        print("This action cannot be undone.")
        
        confirm = input("\nType the course title to confirm deletion: ")
        
        if confirm != self.current_course['title']:
            print("\n❌ Deletion canceled. Title does not match.")
            self.wait_for_enter()
            return False
            
        success, message = self.course_manager.delete_course(
            course_id=self.current_course['_id'],
            user_id=self.current_user['id']
        )
        
        if success:
            print(f"\n✅ {message}")
            self.wait_for_enter()
            return True
        else:
            print(f"\n❌ {message}")
            self.wait_for_enter()
            return False
    
    def manage_modules(self):
        """Manage modules for the current course"""
        options = [
            "View modules",
            "Create new module",
            "Back to course menu"
        ]
        
        while True:
            self.print_header(f"MANAGE MODULES: {self.current_course['title']}")
            self.print_menu(options)
            
            choice = self.get_menu_choice(options)
            
            if choice == 1:
                self.view_modules()
            elif choice == 2:
                self.create_module()
            elif choice == 3 or choice == 0:
                break
    
    def view_modules(self):
        """View modules for the current course"""
        self.print_header(f"MODULES: {self.current_course['title']}")
        
        modules = self.course_manager.get_course_modules(self.current_course['_id'])
        
        if not modules:
            print("This course doesn't have any modules yet.")
            self.wait_for_enter()
            return
        
        print(f"Found {len(modules)} modules:\n")
        
        for i, module in enumerate(modules, 1):
            print(f"{i}. {module['title']}")
            print(f"   Description: {module['description']}")
            print(f"   Created: {module['created_at']}")
            print(f"   Last updated: {module['last_updated']}")
            print()
        
        # Allow selecting a module
        try:
            choice = int(input("Enter module number to manage (0 to go back): "))
            if 1 <= choice <= len(modules):
                self.current_module = modules[choice - 1]
                self.manage_module()
        except ValueError:
            pass
            
        self.current_module = None
    
    def create_module(self):
        """Create a new module for the current course"""
        self.print_header(f"CREATE MODULE: {self.current_course['title']}")
        
        title = input("Module title: ")
        description = input("Module description: ")
        
        if not title:
            print("❌ Title is required.")
            self.wait_for_enter()
            return
        
        success, result = self.course_manager.create_module(
            course_id=self.current_course['_id'],
            user_id=self.current_user['id'],
            title=title,
            description=description
        )
        
        if success:
            print(f"\n✅ Module created successfully with ID: {result['id']}")
            manage_now = input("\nManage this module now? (y/n): ").lower() == 'y'
            
            if manage_now:
                # Get the full module object
                module = self.course_manager.get_module(result['id'])
                if module:
                    self.current_module = module
                    self.manage_module()
        else:
            print(f"\n❌ Module creation failed: {result}")
            self.wait_for_enter()
    
    def manage_module(self):
        """Manage a selected module"""
        options = [
            "View module details",
            "Edit module",
            "View module content",
            "Create flashcard deck",
            "Create quiz",
            "Create video chapter",
            "Delete module",
            "Back to modules"
        ]
        
        while self.current_module:
            self.print_header(f"MANAGE MODULE: {self.current_module['title']}")
            self.print_menu(options)
            
            choice = self.get_menu_choice(options)
            
            if choice == 1:
                self.view_module_details()
            elif choice == 2:
                self.edit_module()
            elif choice == 3:
                self.view_module_content()
            elif choice == 4:
                self.create_flashcard_deck()
            elif choice == 5:
                self.create_quiz()
            elif choice == 6:
                self.create_video_chapter()
            elif choice == 7:
                if self.delete_module():
                    break
            elif choice == 8 or choice == 0:
                self.current_module = None
                break
    
    def view_module_details(self):
        """View details of the current module"""
        self.print_header(f"MODULE DETAILS: {self.current_module['title']}")
        
        print(f"Module ID: {self.current_module['_id']}")
        print(f"Title: {self.current_module['title']}")
        print(f"Description: {self.current_module['description']}")
        print(f"Created: {self.current_module['created_at']}")
        print(f"Last updated: {self.current_module['last_updated']}")
        
        self.wait_for_enter()
    
    def edit_module(self):
        """Edit the current module"""
        self.print_header(f"EDIT MODULE: {self.current_module['title']}")
        
        print("Leave fields blank to keep current values.")
        
        title = input(f"Title [{self.current_module['title']}]: ")
        description = input(f"Description [{self.current_module['description']}]: ")
        
        # Prepare updates
        updates = {}
        if title:
            updates["title"] = title
        if description:
            updates["description"] = description
        
        if not updates:
            print("\nNo changes made.")
            self.wait_for_enter()
            return
        
        success, message = self.course_manager.update_module(
            module_id=self.current_module['_id'],
            user_id=self.current_user['id'],
            updates=updates
        )
        
        if success:
            print(f"\n✅ {message}")
            # Update the current module object with new values
            if title:
                self.current_module['title'] = title
            if description:
                self.current_module['description'] = description
        else:
            print(f"\n❌ {message}")
        
        self.wait_for_enter()
    
    def delete_module(self):
        """Delete the current module"""
        self.print_header(f"DELETE MODULE: {self.current_module['title']}")
        
        print("⚠️ WARNING: This will permanently delete the module and all its content.")
        print("This action cannot be undone.")
        
        confirm = input("\nType the module title to confirm deletion: ")
        
        if confirm != self.current_module['title']:
            print("\n❌ Deletion canceled. Title does not match.")
            self.wait_for_enter()
            return False
            
        success, message = self.course_manager.delete_module(
            module_id=self.current_module['_id'],
            user_id=self.current_user['id']
        )
        
        if success:
            print(f"\n✅ {message}")
            self.wait_for_enter()
            return True
        else:
            print(f"\n❌ {message}")
            self.wait_for_enter()
            return False
    
    def view_module_content(self):
        """View all content in the current module"""
        self.print_header(f"MODULE CONTENT: {self.current_module['title']}")
        
        content = self.content_manager.get_module_content(self.current_module['_id'])
        
        # Flashcard decks
        flashcards = content['flashcard_decks']
        if flashcards:
            print(f"\nFlashcard Decks ({len(flashcards)}):")
            for i, deck in enumerate(flashcards, 1):
                print(f"  {i}. {deck['title']} - {len(deck['cards'])} cards")
        else:
            print("\nNo flashcard decks in this module.")
        
        # Quizzes
        quizzes = content['quizzes']
        if quizzes:
            print(f"\nQuizzes ({len(quizzes)}):")
            for i, quiz in enumerate(quizzes, 1):
                print(f"  {i}. {quiz['title']} - {len(quiz['questions'])} questions")
        else:
            print("\nNo quizzes in this module.")
        
        # Video chapters
        videos = content['video_chapters']
        if videos:
            print(f"\nVideo Chapters ({len(videos)}):")
            for i, video in enumerate(videos, 1):
                duration = video['end_time'] - video['start_time']
                print(f"  {i}. {video['title']} - {duration} seconds")
        else:
            print("\nNo video chapters in this module.")
        
        self.wait_for_enter()
    
    def create_flashcard_deck(self):
        """Create a new flashcard deck for the current module"""
        self.print_header(f"CREATE FLASHCARD DECK: {self.current_module['title']}")
        
        title = input("Deck title: ")
        
        if not title:
            print("❌ Title is required.")
            self.wait_for_enter()
            return
        
        cards = []
        print("\nEnter flashcards (leave front empty when done):")
        
        while True:
            print("\n--- New Card ---")
            front = input("Front: ")
            
            if not front:
                break
                
            back = input("Back: ")
            
            if not back:
                print("❌ Back content is required.")
                continue
                
            cards.append({"front": front, "back": back})
            print(f"✅ Card added. Total cards: {len(cards)}")
        
        if not cards:
            print("\n❌ No cards added. Deck creation canceled.")
            self.wait_for_enter()
            return
        
        success, result = self.content_manager.create_flashcard_deck(
            module_id=self.current_module['_id'],
            user_id=self.current_user['id'],
            title=title,
            cards=cards
        )
        
        if success:
            print(f"\n✅ Flashcard deck created successfully with {result['card_count']} cards.")
        else:
            print(f"\n❌ Flashcard deck creation failed: {result}")
        
        self.wait_for_enter()
    
    def create_quiz(self):
        """Create a new quiz for the current module"""
        self.print_header(f"CREATE QUIZ: {self.current_module['title']}")
        
        title = input("Quiz title: ")
        
        if not title:
            print("❌ Title is required.")
            self.wait_for_enter()
            return
        
        questions = []
        print("\nEnter quiz questions (leave question text empty when done):")
        
        while True:
            print("\n--- New Question ---")
            question_text = input("Question: ")
            
            if not question_text:
                break
                
            # Get options
            options = []
            for i in range(1, 5):
                option = input(f"Option {i}: ")
                if option:
                    options.append(option)
                    
            if len(options) < 2:
                print("❌ At least 2 options are required.")
                continue
                
            # Select correct answer
            while True:
                print("\nSelect the correct answer:")
                for i, option in enumerate(options, 1):
                    print(f"{i}. {option}")
                    
                try:
                    correct_idx = int(input("\nCorrect option number: ")) - 1
                    if 0 <= correct_idx < len(options):
                        correct_answer = options[correct_idx]
                        break
                    print("❌ Invalid option number.")
                except ValueError:
                    print("❌ Please enter a valid number.")
            
            questions.append({
                "question": question_text,
                "options": options,
                "correct_answer": correct_answer
            })
            
            print(f"✅ Question added. Total questions: {len(questions)}")
        
        if not questions:
            print("\n❌ No questions added. Quiz creation canceled.")
            self.wait_for_enter()
            return
        
        success, result = self.content_manager.create_quiz(
            module_id=self.current_module['_id'],
            user_id=self.current_user['id'],
            title=title,
            questions=questions
        )
        
        if success:
            print(f"\n✅ Quiz created successfully with {result['question_count']} questions.")
        else:
            print(f"\n❌ Quiz creation failed: {result}")
        
        self.wait_for_enter()
    
    def create_video_chapter(self):
        """Create a new video chapter for the current module"""
        self.print_header(f"CREATE VIDEO CHAPTER: {self.current_module['title']}")
        
        title = input("Chapter title: ")
        video_url = input("Video URL (YouTube link): ")
        
        if not title or not video_url:
            print("❌ Title and video URL are required.")
            self.wait_for_enter()
            return
        
        # Get timestamps
        try:
            start_time = int(input("Start time (seconds): "))
            end_time = int(input("End time (seconds): "))
            
            if start_time < 0 or end_time <= start_time:
                print("❌ Invalid timestamps. End time must be greater than start time.")
                self.wait_for_enter()
                return
        except ValueError:
            print("❌ Timestamps must be valid numbers.")
            self.wait_for_enter()
            return
        
        # Get optional transcript
        transcript = input("Transcript (optional): ")
        
        success, result = self.content_manager.create_video_chapter(
            module_id=self.current_module['_id'],
            user_id=self.current_user['id'],
            title=title,
            video_url=video_url,
            start_time=start_time,
            end_time=end_time,
            transcript=transcript
        )
        
        if success:
            print(f"\n✅ Video chapter created successfully.")
            print(f"Duration: {end_time - start_time} seconds")
        else:
            print(f"\n❌ Video chapter creation failed: {result}")
        
        self.wait_for_enter()

    def manage_notes(self):
        """Manage user's notes"""
        options = [
            "View my notes",
            "Upload new notes",
            "Input notes directly",  # Added new option for direct text input
            "Generate AI content",   # Added direct access to AI generation
            "Back to user menu"
        ]
        
        while True:
            self.print_header("MANAGE NOTES")
            self.print_menu(options)
            
            choice = self.get_menu_choice(options)
            
            if choice == 1:
                self.view_notes()
            elif choice == 2:
                self.upload_notes()
            elif choice == 3:
                self.input_notes_directly()  # New function for direct text input
            elif choice == 4:
                self.generate_ai_content_menu()  # Direct access to AI menu
            elif choice == 5 or choice == 0:
                break

    def input_notes_directly(self):
        """Input notes directly as text rather than uploading a file"""
        self.print_header("INPUT NOTES DIRECTLY")
        
        title = input("Note title: ")
        topic = input("Note topic: ")
        
        if not title:
            print("❌ Title is required.")
            self.wait_for_enter()
            return
        
        print("\nEnter your notes below. Type 'END' on a new line when finished:")
        print("-" * 50)
        
        # Collect note content
        note_content = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            note_content.append(line)
        
        # Join the content into a single string
        content = "\n".join(note_content)
        
        if not content.strip():
            print("❌ Note content cannot be empty.")
            self.wait_for_enter()
            return
            
        # Save the note to the database
        try:
            note_id = str(ObjectId())
            timestamp = datetime.now()
            
            self.db['notes'].insert_one({
                "_id": ObjectId(note_id),
                "user_id": self.current_user['id'],
                "title": title,
                "topic": topic,
                "content": content,
                "content_preview": content[:200] + "..." if len(content) > 200 else content,
                "created_at": timestamp,
                "last_updated": timestamp,
                "source_type": "direct_input"  # Mark as directly input rather than uploaded
            })
            
            print(f"\n✅ Notes saved successfully with ID: {note_id}")
            
            # Offer to generate AI content right away
            generate_content = input("\nWould you like to generate AI content from these notes now? (y/n): ").lower() == 'y'
            if generate_content:
                # Get the full note object
                note = self.content_manager.get_note(note_id, self.current_user['id'])
                if note:
                    self.current_note = note
                    self.select_module_for_ai_content()
        except Exception as e:
            print(f"\n❌ Error saving notes: {str(e)}")
        
        self.wait_for_enter()

    def view_notes(self):
        """View user's notes"""
        self.print_header("MY NOTES")
        
        notes = self.content_manager.get_user_notes(self.current_user['id'])
        
        if not notes:
            print("You don't have any notes yet.")
            self.wait_for_enter()
            return
        
        print(f"Found {len(notes)} notes:\n")
        
        for i, note in enumerate(notes, 1):
            print(f"{i}. {note['title']}")
            print(f"   Topic: {note['topic']}")
            print(f"   Created: {note['created_at']}")
            print(f"   Preview: {note['content_preview']}")
            print()
        
        # Allow selecting a note
        try:
            choice = int(input("Enter note number to manage (0 to go back): "))
            if 1 <= choice <= len(notes):
                self.current_note = notes[choice - 1]
                self.manage_note()
        except ValueError:
            pass
            
        self.current_note = None

    def upload_notes(self):
        """Upload new notes"""
        self.print_header("UPLOAD NEW NOTES")
        
        file_path = input("Enter PDF file path: ")
        
        if not os.path.exists(file_path):
            print("❌ File not found.")
            self.wait_for_enter()
            return
        
        title = input("Note title: ")
        topic = input("Note topic: ")
        
        if not title:
            print("❌ Title is required.")
            self.wait_for_enter()
            return
        
        print("\nUploading and processing notes...")
        success, result = self.content_manager.upload_notes(
            user_id=self.current_user['id'],
            file_path=file_path,
            title=title,
            topic=topic
        )
        
        if success:
            print(f"\n✅ Notes uploaded successfully with ID: {result['id']}")
            
            # Offer to generate AI content right away
            generate_content = input("\nWould you like to generate AI content from these notes now? (y/n): ").lower() == 'y'
            if generate_content:
                # Get the full note object
                note = self.content_manager.get_note(result['id'], self.current_user['id'])
                if note:
                    self.current_note = note
                    self.select_module_for_ai_content()
            
            self.wait_for_enter()
        else:
            print(f"\n❌ Notes upload failed: {result}")
            self.wait_for_enter()

    def manage_note(self):
        """Manage a selected note"""
        options = [
            "View note details",
            "Generate AI content",
            "Delete note",
            "Back to notes"
        ]
        
        while self.current_note:
            self.print_header(f"MANAGE NOTE: {self.current_note['title']}")
            self.print_menu(options)
            
            choice = self.get_menu_choice(options)
            
            if choice == 1:
                self.view_note_details()
            elif choice == 2:
                self.select_module_for_ai_content()
            elif choice == 3:
                if self.delete_note():
                    break
            elif choice == 4 or choice == 0:
                self.current_note = None
                break

    def view_note_details(self):
        """View details of the current note"""
        self.print_header(f"NOTE DETAILS: {self.current_note['title']}")
        
        # Fetch full note content
        note = self.content_manager.get_note(self.current_note['_id'], self.current_user['id'])
        
        if not note:
            print("❌ Failed to retrieve note.")
            self.wait_for_enter()
            return
        
        print(f"Note ID: {note['_id']}")
        print(f"Title: {note['title']}")
        print(f"Topic: {note['topic']}")
        print(f"Created: {note['created_at']}")
        
        print("\nContent Preview (first 500 characters):")
        print("-" * 50)
        print(note['content'][:500] + "..." if len(note['content']) > 500 else note['content'])
        print("-" * 50)
        
        self.wait_for_enter()

    def delete_note(self):
        """Delete the current note"""
        self.print_header(f"DELETE NOTE: {self.current_note['title']}")
        
        print("⚠️ WARNING: This will permanently delete the note.")
        print("This action cannot be undone.")
        
        confirm = input("\nType the note title to confirm deletion: ")
        
        if confirm != self.current_note['title']:
            print("\n❌ Deletion canceled. Title does not match.")
            self.wait_for_enter()
            return False
            
        # Delete the note from the database
        try:
            self.db['notes'].delete_one({"_id": ObjectId(self.current_note['_id'])})
            print("\n✅ Note deleted successfully.")
            self.wait_for_enter()
            return True
        except Exception as e:
            print(f"\n❌ Error deleting note: {str(e)}")
            self.wait_for_enter()
            return False
            
    def view_study_statistics(self):
        """View user study statistics"""
        self.print_header("STUDY STATISTICS")
        
        stats = self.profile_manager.get_study_statistics(self.current_user['id'])
        
        if not stats:
            print("❌ Failed to retrieve study statistics.")
            self.wait_for_enter()
            return
        
        print(f"Total study time: {stats['total_study_time']} minutes")
        print(f"Quizzes completed: {stats['quizzes_completed']}")
        print(f"Flashcards reviewed: {stats['flashcards_reviewed']}")
        
        if stats.get('last_activity'):
            print(f"Last activity: {stats['last_activity']}")
        
        self.wait_for_enter()

    def account_settings(self):
        """Manage account settings"""
        options = [
            "Change password",
            "Request password reset",
            "Deactivate account",
            "Delete account",
            "Back to user menu"
        ]
        
        while True:
            self.print_header("ACCOUNT SETTINGS")
            self.print_menu(options)
            
            choice = self.get_menu_choice(options)
            
            if choice == 1:
                self.change_password()
            elif choice == 2:
                self.request_new_password_reset()
            elif choice == 3:
                if self.deactivate_account():
                    return
            elif choice == 4:
                if self.delete_account():
                    return
            elif choice == 5 or choice == 0:
                break

    def change_password(self):
        """Change user password"""
        self.print_header("CHANGE PASSWORD")
        
        current_password = getpass.getpass("Current password: ")
        
        # Get new password with confirmation
        while True:
            new_password = getpass.getpass("New password: ")
            confirm_password = getpass.getpass("Confirm new password: ")
            
            if new_password == confirm_password:
                break
            print("Passwords do not match. Please try again.")
        
        success, message = self.auth_manager.change_password(
            user_id=self.current_user['id'],
            current_password=current_password,
            new_password=new_password
        )
        
        print(f"\n{'✅' if success else '❌'} {message}")
        self.wait_for_enter()

    def request_new_password_reset(self):
        """Request a new password reset token"""
        self.print_header("REQUEST PASSWORD RESET")
        
        # We'll use the refresh password reset method
        success, result = self.auth_manager.refresh_password_reset(self.current_user['email'])
        
        if success:
            if isinstance(result, dict) and "token" in result:
                print("\n✅ New password reset token generated.")
                print(f"Reset token: {result['token']}")
                print("In a real system, this would be sent via email.")
                
                use_token = input("\nUse this token to reset your password now? (y/n): ").lower() == 'y'
                if use_token:
                    self.use_reset_token(result['token'])
            else:
                print("\n✅ Password reset link has been sent to your email.")
        else:
            print(f"\n❌ Password reset request failed: {result}")
        
        self.wait_for_enter()

    def deactivate_account(self):
        """Deactivate the current user account"""
        self.print_header("DEACTIVATE ACCOUNT")
        
        print("⚠️ WARNING: This will deactivate your account.")
        print("You will not be able to log in until the account is reactivated by an administrator.")
        
        confirm = input("\nType 'deactivate' to confirm: ")
        
        if confirm != "deactivate":
            print("\n❌ Deactivation canceled.")
            self.wait_for_enter()
            return False
        
        password = getpass.getpass("Enter your password to confirm: ")
        
        success, message = self.auth_manager.deactivate_user_account(
            user_id=self.current_user['id'],
            password=password
        )
        
        if success:
            print(f"\n✅ {message}")
            self.current_user = None
            self.wait_for_enter()
            return True
        else:
            print(f"\n❌ {message}")
            self.wait_for_enter()
            return False

    def delete_account(self):
        """Delete the current user account"""
        self.print_header("DELETE ACCOUNT")
        
        print("⚠️ WARNING: This will permanently delete your account and all your data.")
        print("This action cannot be undone.")
        
        confirm = input("\nType 'delete my account' to confirm: ")
        
        if confirm != "delete my account":
            print("\n❌ Deletion canceled.")
            self.wait_for_enter()
            return False
        
        password = getpass.getpass("Enter your password to confirm: ")
        
        success, message = self.auth_manager.delete_user_account(
            user_id=self.current_user['id'],
            password=password
        )
        
        if success:
            print(f"\n✅ {message}")
            self.current_user = None
            self.wait_for_enter()
            return True
        else:
            print(f"\n❌ {message}")
            self.wait_for_enter()
            return False

    def logout(self):
        """Log out the current user"""
        self.print_header("LOGOUT")
        
        print("Logging out...")
        time.sleep(1)
        self.current_user = None
        print("✅ You have been logged out successfully.")
        self.wait_for_enter()

    def exit_program(self):
        """Exit the program"""
        self.clear_screen()
        print("Thank you for using Axiom Learning Platform!")
        print("Goodbye!")

    def select_module_for_ai_content(self):
        """Select a module for adding AI-generated content from the current note"""
        self.print_header(f"SELECT MODULE: {self.current_note['title']}")
        
        if not self.current_course:
            # First select a course
            courses = self.course_manager.get_user_courses(self.current_user['id'])
            
            if not courses:
                print("You don't have any courses yet. Please create a course first.")
                self.wait_for_enter()
                return
            
            print("Select a course:")
            for i, course in enumerate(courses, 1):
                print(f"{i}. {course['title']}")
            
            try:
                choice = int(input("\nEnter course number (0 to go back): "))
                if choice == 0:
                    return
                
                if 1 <= choice <= len(courses):
                    self.current_course = courses[choice - 1]
                else:
                    print("❌ Invalid course number.")
                    self.wait_for_enter()
                    return
            except ValueError:
                print("❌ Please enter a valid number.")
                self.wait_for_enter()
                return
        
        # Now select a module
        modules = self.course_manager.get_course_modules(self.current_course['_id'])
        
        if not modules:
            print(f"Course '{self.current_course['title']}' has no modules. Please create a module first.")
            self.wait_for_enter()
            # Reset current course
            self.current_course = None
            return
       
        print(f"\nSelect a module from course '{self.current_course['title']}':")
        for i, module in enumerate(modules, 1):
            print(f"{i}. {module['title']}")
        
        try:
            choice = int(input("\nEnter module number (0 to go back): "))
            if choice == 0:
                # Reset current course
                self.current_course = None
                return
            
            if 1 <= choice <= len(modules):
                self.current_module = modules[choice - 1]
                self.generate_ai_content_menu_for_note()
            else:
                print("❌ Invalid module number.")
                self.wait_for_enter()
                # Reset current course
                self.current_course = None
                return
        except ValueError:
            print("❌ Please enter a valid number.")
            self.wait_for_enter()
            # Reset current course
            self.current_course = None
            return
           
    def generate_ai_content_menu_for_note(self):
        """Generate AI content options for the selected note and module"""
        options = [
            "Generate flashcards",
            "Generate quiz",
            "Generate video chapter suggestions",
            "Back to previous menu"
        ]
        
        while True:
            self.print_header(f"GENERATE AI CONTENT: {self.current_note['title']}")
            print(f"Selected module: {self.current_module['title']}")
            self.print_menu(options)
            
            choice = self.get_menu_choice(options)
            
            if choice == 1:
                self.generate_flashcards_from_note()
            elif choice == 2:
                self.generate_quiz_from_note()
            elif choice == 3:
                self.suggest_video_chapters_from_note()
            elif choice == 4 or choice == 0:
                # Reset selected course and module
                self.current_course = None
                self.current_module = None
                break
                
    def generate_flashcards_from_note(self):
        """Generate flashcards from the current note using AI"""
        self.print_header(f"GENERATE FLASHCARDS: {self.current_note['title']}")
        
        print(f"Generating flashcards for module: {self.current_module['title']}")
        print("This may take a moment...")
        
        success, result = self.content_manager.generate_flashcards_from_notes(
            note_id=self.current_note['_id'],
            user_id=self.current_user['id'],
            module_id=self.current_module['_id']
        )
        
        if success:
            print(f"\n✅ Flashcard deck created successfully with {result['card_count']} cards.")
            print(f"Title: {result['title']}")
            print(f"Added to module: {self.current_module['title']}")
        else:
            print(f"\n❌ Flashcard generation failed: {result}")
        
        self.wait_for_enter()

    def generate_quiz_from_note(self):
        """Generate a quiz from the current note using AI"""
        self.print_header(f"GENERATE QUIZ: {self.current_note['title']}")
        
        print(f"Generating quiz for module: {self.current_module['title']}")
        print("This may take a moment...")
        
        success, result = self.content_manager.generate_quiz_from_notes(
            note_id=self.current_note['_id'],
            user_id=self.current_user['id'],
            module_id=self.current_module['_id']
        )
        
        if success:
            print(f"\n✅ Quiz created successfully with {result['question_count']} questions.")
            print(f"Title: {result['title']}")
            print(f"Added to module: {self.current_module['title']}")
        else:
            print(f"\n❌ Quiz generation failed: {result}")
        
        self.wait_for_enter()

    def suggest_video_chapters_from_note(self):
        """Generate video chapter suggestions from the current note using AI"""
        self.print_header(f"SUGGEST VIDEO CHAPTERS: {self.current_note['title']}")
        
        print(f"Generating video chapter suggestions for module: {self.current_module['title']}")
        print("This may take a moment...")
        
        success, result = self.content_manager.suggest_video_chapters_from_notes(
            note_id=self.current_note['_id'],
            user_id=self.current_user['id'],
            module_id=self.current_module['_id']
        )
        
        if success:
            print(f"\n✅ Video chapter suggestions generated successfully.")
            print("\nSuggested chapters:")
            for i, chapter in enumerate(result['chapters'], 1):
                print(f"{i}. {chapter['title']}")
                print(f"   Description: {chapter['description']}")
                print()
                
            # Option to create video chapters
            create_chapters = input("\nWould you like to create these video chapters? (y/n): ").lower() == 'y'
            if create_chapters:
                self.create_video_chapters_from_suggestions(result['chapters'])
        else:
            print(f"\n❌ Video chapter suggestion generation failed: {result}")
        
        self.wait_for_enter()
        
    def admin_panel(self):
        """Admin panel for managing the platform"""
        options = [
            "Manage Users",
            "System Statistics", 
            "Promote User to Admin",
            "Back to User Menu"
        ]
        
        while True:
            self.print_header("ADMIN PANEL")
            print("🔑 ADMIN ACCESS: These features provide administrative control over the platform")
            print()
            
            self.print_menu(options)
            
            choice = self.get_menu_choice(options)
            
            if choice == 1:
                self.manage_users_admin()
            elif choice == 2:
                self.system_statistics()
            elif choice == 3:
                self.promote_user()
            elif choice == 4 or choice == 0:
                break

    def manage_users_admin(self):
        """Admin function to manage users"""
        self.print_header("MANAGE USERS")
        
        # Get all users (admin function)
        users = list(self.db['users'].find({}, {
            "username": 1, 
            "email": 1, 
            "first_name": 1, 
            "last_name": 1,
            "is_active": 1,
            "is_verified": 1,
            "is_admin": 1,
            "created_at": 1,
            "last_login": 1
        }))
        
        if not users:
            print("No users found in the system.")
            self.wait_for_enter()
            return
        
        print(f"Found {len(users)} users:\n")
        
        for i, user in enumerate(users, 1):
            status_badges = []
            if user.get('is_admin', False):
                status_badges.append("🔑 ADMIN")
            if not user.get('is_active', True):
                status_badges.append("❌ INACTIVE")
            if not user.get('is_verified', False):
                status_badges.append("⚠️ UNVERIFIED")
                
            status = f" [{' | '.join(status_badges)}]" if status_badges else ""
            
            print(f"{i}. {user['username']}{status}")
            print(f"   Name: {user.get('first_name', '')} {user.get('last_name', '')}")
            print(f"   Email: {user.get('email', '')}")
            print(f"   Created: {user.get('created_at', 'Unknown')}")
            print(f"   Last login: {user.get('last_login', 'Never')}")
            print()
        
        # Allow selecting a user
        try:
            choice = int(input("Enter user number to manage (0 to go back): "))
            if 1 <= choice <= len(users):
                selected_user = users[choice - 1]
                self.manage_user_admin(selected_user)
        except ValueError:
            pass

    def manage_user_admin(self, user):
        """Admin function to manage a specific user"""
        options = [
            "View user details",
            "Toggle admin status",
            "Toggle active status",
            "Reset user password",
            "Delete user account",
            "Back to user list"
        ]
        
        user_id = str(user['_id'])
        
        while True:
            self.print_header(f"MANAGE USER: {user['username']}")
            
            # Show current status
            status_badges = []
            if user.get('is_admin', False):
                status_badges.append("🔑 ADMIN")
            if not user.get('is_active', True):
                status_badges.append("❌ INACTIVE")
            if not user.get('is_verified', False):
                status_badges.append("⚠️ UNVERIFIED")
                
            status = f" [{' | '.join(status_badges)}]" if status_badges else ""
            print(f"User: {user['username']}{status}")
            print(f"Name: {user.get('first_name', '')} {user.get('last_name', '')}")
            print(f"Email: {user.get('email', '')}")
            print()
            
            self.print_menu(options)
            
            choice = self.get_menu_choice(options)
            
            if choice == 1:
                self.view_user_details_admin(user_id)
            elif choice == 2:
                user = self.toggle_admin_status(user_id, user)
            elif choice == 3:
                user = self.toggle_user_active_status(user_id, user)
            elif choice == 4:
                self.reset_user_password_admin(user_id)
            elif choice == 5:
                if self.delete_user_admin(user_id):
                    break
            elif choice == 6 or choice == 0:
                break

    def view_user_details_admin(self, user_id):
        """Admin function to view detailed user information"""
        self.print_header("USER DETAILS")
        
        # Get full user profile including stats
        user = self.db['users'].find_one({"_id": ObjectId(user_id)})
        
        if not user:
            print("❌ User not found.")
            self.wait_for_enter()
            return
        
        # Basic info
        print(f"Username: {user['username']}")
        print(f"Email: {user['email']}")
        print(f"Name: {user['first_name']} {user['last_name']}")
        print(f"Account created: {user['created_at']}")
        print(f"Last login: {user.get('last_login', 'Never')}")
        
        # Status
        print("\n--- STATUS ---")
        print(f"Admin: {'Yes' if user.get('is_admin', False) else 'No'}")
        print(f"Active: {'Yes' if user.get('is_active', True) else 'No'}")
        print(f"Verified: {'Yes' if user.get('is_verified', False) else 'No'}")
        
        # Profile info
        if user.get('profile'):
            print("\n--- PROFILE ---")
            print(f"Bio: {user['profile'].get('bio') or 'Not set'}")
            print(f"Education: {user['profile'].get('education_level') or 'Not set'}")
            subjects = user['profile'].get('subjects', [])
            print(f"Subjects: {', '.join(subjects) if subjects else 'None'}")
        
        # Study stats
        if user.get('study_stats'):
            print("\n--- STUDY STATISTICS ---")
            print(f"Total study time: {user['study_stats'].get('total_study_time', 0)} minutes")
            print(f"Quizzes completed: {user['study_stats'].get('quizzes_completed', 0)}")
            print(f"Flashcards reviewed: {user['study_stats'].get('flashcards_reviewed', 0)}")
            print(f"Last activity: {user['study_stats'].get('last_activity', 'Never')}")
        
        # Get user's content counts
        courses_count = self.db['courses'].count_documents({"user_id": ObjectId(user_id)})
        
        print("\n--- CONTENT SUMMARY ---")
        print(f"Total courses: {courses_count}")
        
        self.wait_for_enter()

    def toggle_admin_status(self, user_id, user):
        """Admin function to toggle a user's admin status"""
        current_status = user.get('is_admin', False)
        new_status = not current_status
        
        if new_status:
            print(f"⚠️ WARNING: You are about to grant ADMIN privileges to {user['username']}.")
            print("Admins have full control over the platform including user management.")
        else:
            print(f"⚠️ WARNING: You are about to remove ADMIN privileges from {user['username']}.")
        
        confirm = input(f"\nAre you sure you want to {'grant' if new_status else 'remove'} admin privileges? (y/n): ").lower() == 'y'
        
        if not confirm:
            print("\nOperation canceled.")
            self.wait_for_enter()
            return user
        
        try:
            self.db['users'].update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"is_admin": new_status}}
            )
            
            # Update the user object for the UI
            user['is_admin'] = new_status
            
            print(f"\n✅ Admin status {'granted to' if new_status else 'removed from'} {user['username']}.")
            self.wait_for_enter()
            return user
        except Exception as e:
            print(f"\n❌ Error updating admin status: {str(e)}")
            self.wait_for_enter()
            return user

    def toggle_user_active_status(self, user_id, user):
        """Admin function to activate or deactivate a user account"""
        current_status = user.get('is_active', True)
        new_status = not current_status
        
        if not new_status:
            print(f"⚠️ WARNING: You are about to deactivate {user['username']}'s account.")
            print("The user will not be able to log in until their account is reactivated.")
        else:
            print(f"You are about to reactivate {user['username']}'s account.")
        
        confirm = input(f"\nAre you sure you want to {'deactivate' if not new_status else 'reactivate'} this account? (y/n): ").lower() == 'y'
        
        if not confirm:
            print("\nOperation canceled.")
            self.wait_for_enter()
            return user
        
        try:
            self.db['users'].update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"is_active": new_status}}
            )
            
            # Update the user object for the UI
            user['is_active'] = new_status
            
            print(f"\n✅ Account {'deactivated' if not new_status else 'reactivated'} successfully.")
            self.wait_for_enter()
            return user
        except Exception as e:
            print(f"\n❌ Error updating account status: {str(e)}")
            self.wait_for_enter()
            return user

    def reset_user_password_admin(self, user_id):
        """Admin function to reset a user's password"""
        self.print_header("RESET USER PASSWORD")
        
        user = self.db['users'].find_one({"_id": ObjectId(user_id)}, {"username": 1})
        
        if not user:
            print("❌ User not found.")
            self.wait_for_enter()
            return
        
        print(f"You are about to reset the password for user: {user['username']}")
        print("A new random password will be generated.")
        
        confirm = input("\nProceed with password reset? (y/n): ").lower() == 'y'
        
        if not confirm:
            print("\nPassword reset canceled.")
            self.wait_for_enter()
            return
        
        # Generate a random password
        import random
        import string
        import bcrypt
        
        password_chars = string.ascii_letters + string.digits + "!@#$%^&*"
        new_password = ''.join(random.choice(password_chars) for _ in range(12))
        
        # Hash the new password
        salt = bcrypt.gensalt()
        new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), salt)
        
        try:
            self.db['users'].update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "password_hash": new_password_hash,
                        "security.last_password_change": datetime.now(),
                        "security.password_reset_token": None,
                        "security.password_reset_expiry": None,
                        "security.failed_login_attempts": 0
                    }
                }
            )
            
            print("\n✅ Password reset successfully.")
            print(f"New password: {new_password}")
            print("Please provide this password to the user.")
            
        except Exception as e:
            print(f"\n❌ Error resetting password: {str(e)}")
        
        self.wait_for_enter()

    def delete_user_admin(self, user_id):
        """Admin function to delete a user account"""
        self.print_header("DELETE USER ACCOUNT")
        
        user = self.db['users'].find_one({"_id": ObjectId(user_id)}, {"username": 1})
        
        if not user:
            print("❌ User not found.")
            self.wait_for_enter()
            return False
        
        print(f"⚠️ WARNING: You are about to permanently delete {user['username']}'s account.")
        print("This will remove all their courses, modules, content, and profile information.")
        print("This action cannot be undone.")
        
        confirm = input("\nType 'DELETE' to confirm: ")
        
        if confirm != "DELETE":
            print("\n❌ Deletion canceled.")
            self.wait_for_enter()
            return False
        
        success, message = self.auth_manager.admin_delete_user(
            admin_user_id=self.current_user['id'],
            target_user_id=user_id
        )
        
        if success:
            print(f"\n✅ {message}")
            self.wait_for_enter()
            return True
        else:
            print(f"\n❌ {message}")
            self.wait_for_enter()
            return False

    def system_statistics(self):
        """Admin function to view system-wide statistics"""
        self.print_header("SYSTEM STATISTICS")
        
        try:
            # User statistics
            total_users = self.db['users'].count_documents({})
            active_users = self.db['users'].count_documents({"is_active": True})
            admin_users = self.db['users'].count_documents({"is_admin": True})
            verified_users = self.db['users'].count_documents({"is_verified": True})
            
            # Content statistics
            total_courses = self.db['courses'].count_documents({})
            total_modules = self.db['modules'].count_documents({})
            total_flashcard_decks = self.db['flashcard_decks'].count_documents({})
            total_quizzes = self.db['quizzes'].count_documents({})
            total_video_chapters = self.db['video_chapters'].count_documents({})
            total_notes = self.db['notes'].count_documents({})
            
            # Calculate average content per user
            avg_courses_per_user = total_courses / total_users if total_users > 0 else 0
            avg_modules_per_course = total_modules / total_courses if total_courses > 0 else 0
            
            # Display statistics
            print("--- USER STATISTICS ---")
            print(f"Total users: {total_users}")
            print(f"Active users: {active_users} ({100 * active_users/total_users:.1f}% of total)" if total_users > 0 else "Active users: 0")
            print(f"Verified users: {verified_users} ({100 * verified_users/total_users:.1f}% of total)" if total_users > 0 else "Verified users: 0")
            print(f"Admin users: {admin_users}")
            
            print("\n--- CONTENT STATISTICS ---")
            print(f"Total courses: {total_courses}")
            print(f"Total modules: {total_modules}")
            print(f"Total flashcard decks: {total_flashcard_decks}")
            print(f"Total quizzes: {total_quizzes}")
            print(f"Total video chapters: {total_video_chapters}")
            print(f"Total notes: {total_notes}")
            
            print("\n--- AVERAGES ---")
            print(f"Average courses per user: {avg_courses_per_user:.2f}")
            print(f"Average modules per course: {avg_modules_per_course:.2f}")
            
            # Recent activity (last 7 days)
            from datetime import timedelta
            one_week_ago = datetime.now() - timedelta(days=7)
            recent_logins = self.db['users'].count_documents({"last_login": {"$gte": one_week_ago}})
            recent_courses = self.db['courses'].count_documents({"created_at": {"$gte": one_week_ago}})
            recent_notes = self.db['notes'].count_documents({"created_at": {"$gte": one_week_ago}})
            
            print("\n--- RECENT ACTIVITY (LAST 7 DAYS) ---")
            print(f"User logins: {recent_logins}")
            print(f"New courses created: {recent_courses}")
            print(f"New notes created: {recent_notes}")
            
            # Most active users (based on study time)
            top_users = list(self.db['users'].find(
                {"study_stats.total_study_time": {"$exists": True, "$gt": 0}}, 
                {"username": 1, "study_stats.total_study_time": 1}
            ).sort("study_stats.total_study_time", -1).limit(5))
            
            if top_users:
                print("\n--- TOP 5 USERS BY STUDY TIME ---")
                for i, user in enumerate(top_users, 1):
                    username = user.get("username", "Unknown")
                    study_time = user.get("study_stats", {}).get("total_study_time", 0)
                    print(f"{i}. {username}: {study_time} minutes")
            
        except Exception as e:
            print(f"❌ Error retrieving system statistics: {str(e)}")
        
        self.wait_for_enter()

    def promote_user(self):
        """Admin function to promote a user to admin"""
        self.print_header("PROMOTE USER TO ADMIN")
        
        username = input("Enter username to promote: ")
        
        if not username:
            print("❌ Username is required.")
            self.wait_for_enter()
            return
        
        # Find the user
        user = self.db['users'].find_one({"username": username})
        
        if not user:
            print(f"❌ User '{username}' not found.")
            self.wait_for_enter()
            return
        
        # Check if user is already an admin
        if user.get('is_admin', False):
            print(f"⚠️ User '{username}' is already an admin.")
            self.wait_for_enter()
            return
        
        print(f"You are about to promote '{username}' to admin status.")
        print("Admins have full control over the platform including user management.")
        
        confirm = input("\nAre you sure? (y/n): ").lower() == 'y'
        
        if not confirm:
            print("\nPromotion canceled.")
            self.wait_for_enter()
            return
        
        try:
            self.db['users'].update_one(
                {"_id": user['_id']},
                {"$set": {"is_admin": True}}
            )
            
            print(f"\n✅ User '{username}' has been promoted to admin successfully.")
        except Exception as e:
            print(f"\n❌ Error promoting user: {str(e)}")
        
        self.wait_for_enter()

if __name__ == "__main__":
   cli = AxiomCLI()
   try:
       cli.main_menu()
   except KeyboardInterrupt:
       print("\n\nProgram interrupted. Exiting...")
       cli.exit_program()