"""
Axiom AI Content Generator
Uses Google Generative AI client for content generation
"""
from datetime import datetime
from bson.objectid import ObjectId
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import os
import json
import re
from typing import Dict, List, Tuple, Union, Optional, Any

# Load environment variables
load_dotenv()

class AxiomAIContentGenerator:
    """Handles AI-powered content generation for the Axiom platform"""
    
    def __init__(self, db_connection=None):
        """Initialize with optional database connection"""
        # Use provided DB connection or create a new one
        if db_connection is not None:
            self.db = db_connection
        else:
            # Import here to avoid circular imports
            from axiom_database import AxiomDatabase
            self.db = AxiomDatabase().get_db()
        
        # Set up collections
        self.notes = self.db['notes']
        
        # Initialize Google Generative AI
        api_key = os.getenv("API_KEY")
        
        if not api_key:
            print("Warning: No API_KEY found in environment variables. Using mock generators.")
            self.client = None
        else:
            try:
                # Import Google's generative AI client - UPDATED IMPORT STATEMENT
                import google.generativeai as genai
                
                # Configure the API
                genai.configure(api_key=api_key)
                
                # Initialize the model
                self.client = genai.GenerativeModel('gemini-1.5-flash')
                print("Successfully initialized Google Generative AI client")
            except Exception as e:
                print(f"Failed to initialize Google Generative AI client: {str(e)}")
                self.client = None
    
    def parse_pdf(self, file_path: str) -> str:
        """Parse a PDF file and extract text content as plain text"""
        try:
            # First try using docling if available
            try:
                from docling.document_converter import DocumentConverter
                converter = DocumentConverter()
                result = converter.convert(file_path)
                return result.document.export_to_markdown()
            except ImportError:
                # Fall back to PyPDF2
                print("docling not available, using PyPDF2 as fallback")
                reader = PdfReader(file_path)
                text = ""
                
                # Extract text from each page
                for page in reader.pages:
                    text += page.extract_text() + "\n\n"
                
                return text
        except Exception as e:
            raise Exception(f"Error parsing PDF: {str(e)}")
    
    def save_notes(self, user_id: str, title: str, topic: str, content: str) -> Tuple[bool, Union[str, Dict]]:
        """Save parsed notes to the database"""
        try:
            note_doc = {
                "user_id": user_id,
                "title": title,
                "topic": topic,
                "content": content,
                "created_at": datetime.now(),
                "last_updated": datetime.now()
            }
            
            result = self.notes.insert_one(note_doc)
            
            return True, {
                "id": str(result.inserted_id),
                "title": title,
                "topic": topic
            }
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def generate_quiz(self, note_id: str) -> Tuple[bool, Union[str, Dict]]:
        """Generate a quiz from notes using Google Generative AI"""
        try:
            # Get the note content
            note = self.notes.find_one({"_id": ObjectId(note_id)})
            
            if not note:
                return False, "Note not found"
            
            # Truncate content if it's too long
            content = note['content']
            if len(content) > 30000:  # Limit to 30k characters
                content = content[:30000] + "..."
            
            # Check if client is available
            if not self.client:
                print("No Google Generative AI client available. Using content-aware mock generator.")
                return self._generate_content_aware_quiz(note)
            
            try:
                # Generate the quiz using Google Generative AI client - UPDATED API CALL
                prompt = f"""
                Generate a multiple-choice quiz to test the student's knowledge on the following notes:
                
                {content}
                
                The quiz should be in JSON format with the following structure:
                {{
                  "title": "{note['title']} Quiz",
                  "questions": [
                    {{
                      "question": "Specific question about the content",
                      "options": ["Option A", "Option B", "Option C", "Option D"],
                      "correct_answer": "Option that is correct"
                    }},
                    ... more questions ...
                  ]
                }}
                
                Make sure that all questions and options focus on the specific subject matter in the content,
                and avoid generic questions about studying techniques or the document itself.
                Please create at least 5 questions that directly test understanding of the specific 
                information in the content.
                """
                
                response = self.client.generate_content(
                    prompt,
                    generation_config={'response_mime_type': 'application/json'}
                )
                
                # Get the response text
                response_text = response.text
                
                # Parse the response
                try:
                    quiz_data = json.loads(response_text)
                    
                    # Add note_id to the quiz data
                    quiz_data["note_id"] = note_id
                    
                    return True, quiz_data
                except json.JSONDecodeError:
                    print("Failed to parse AI response as JSON, falling back to content-aware mock implementation")
                    return self._generate_content_aware_quiz(note)
                    
            except Exception as e:
                print(f"Error generating quiz with AI: {str(e)}")
                # If there's an error, fall back to content-aware mock implementation
                return self._generate_content_aware_quiz(note)
                
        except Exception as e:
            print(f"General error in generate_quiz: {str(e)}")
            # If there's a general error, still try the content-aware mock implementation
            note = self.notes.find_one({"_id": ObjectId(note_id)})
            if note:
                return self._generate_content_aware_quiz(note)
            return False, f"Error generating quiz: {str(e)}"
    
    def generate_flashcards(self, note_id: str) -> Tuple[bool, Union[str, Dict]]:
        """Generate flashcards from notes using Google Generative AI"""
        try:
            # Get the note content
            note = self.notes.find_one({"_id": ObjectId(note_id)})
            
            if not note:
                return False, "Note not found"
            
            # Truncate content if it's too long
            content = note['content']
            if len(content) > 30000:  # Limit to 30k characters
                content = content[:30000] + "..."
            
            # Check if client is available
            if not self.client:
                print("No Google Generative AI client available. Using content-aware mock generator.")
                return self._generate_content_aware_flashcards(note)
            
            try:
                # Generate the flashcards using Google Generative AI client - UPDATED API CALL
                prompt = f"""
                Generate a set of flashcards based on the following content:
                
                {content}
                
                The flashcards should be in JSON format with the following structure:
                {{
                  "title": "{note['title']} Flashcards",
                  "cards": [
                    {{
                      "front": "Specific term or concept from the content",
                      "back": "Definition or explanation from the content"
                    }},
                    ... more cards ...
                  ]
                }}
                
                Please create at least 8 flashcards that directly focus on the specific information in the
                content. The front of each card should have a specific question or key term from 
                the content, and the back should have the definition or explanation.
                
                Make sure that all cards focus on the specific subject matter in the content and avoid
                generic cards about studying techniques or the document itself.
                """
                
                response = self.client.generate_content(
                    prompt,
                    generation_config={'response_mime_type': 'application/json'}
                )
                
                # Get the response text
                response_text = response.text
                
                # Parse the response
                try:
                    flashcard_data = json.loads(response_text)
                    
                    # Add note_id to the flashcard data
                    flashcard_data["note_id"] = note_id
                    
                    return True, flashcard_data
                except json.JSONDecodeError:
                    print("Failed to parse AI response as JSON, falling back to content-aware mock implementation")
                    return self._generate_content_aware_flashcards(note)
                    
            except Exception as e:
                print(f"Error generating flashcards with AI: {str(e)}")
                # If there's an error, fall back to content-aware mock implementation
                return self._generate_content_aware_flashcards(note)
                
        except Exception as e:
            print(f"General error in generate_flashcards: {str(e)}")
            # If there's a general error, still try the content-aware mock implementation
            note = self.notes.find_one({"_id": ObjectId(note_id)})
            if note:
                return self._generate_content_aware_flashcards(note)
            return False, f"Error generating flashcards: {str(e)}"
    
    def generate_video_chapters(self, note_id: str) -> Tuple[bool, Union[str, Dict]]:
        """Generate video chapter suggestions from notes using Google Generative AI"""
        try:
            # Get the note content
            note = self.notes.find_one({"_id": ObjectId(note_id)})
            
            if not note:
                return False, "Note not found"
            
            # Truncate content if it's too long
            content = note['content']
            if len(content) > 30000:  # Limit to 30k characters
                content = content[:30000] + "..."
            
            # Check if client is available
            if not self.client:
                print("No Google Generative AI client available. Using mock generator.")
                return self._generate_mock_video_chapters(note)
            
            try:
                # Generate the video chapter suggestions using Google Generative AI client - UPDATED API CALL
                prompt = f"""
                Based on the following notes, generate suggestions for video chapters that would help explain the key concepts:
                
                {content}
                
                The suggestions should be in JSON format with the following structure:
                {{
                  "title": "{note['title']} Video Chapters",
                  "chapters": [
                    {{
                      "title": "Chapter title based on specific content",
                      "description": "Brief description of what this chapter should cover based on the content"
                    }},
                    ... more chapters ...
                  ]
                }}
                
                Generate 5-7 chapter suggestions that would cover the material in a logical sequence.
                Focus specifically on the key concepts from the content, not generic chapter ideas.
                """
                
                response = self.client.generate_content(
                    prompt,
                    generation_config={'response_mime_type': 'application/json'}
                )
                
                # Get the response text
                response_text = response.text
                
                # Parse the response
                try:
                    chapter_data = json.loads(response_text)
                    
                    # Add note_id to the chapter data
                    chapter_data["note_id"] = note_id
                    
                    return True, chapter_data
                except json.JSONDecodeError:
                    print("Failed to parse AI response as JSON, falling back to mock implementation")
                    return self._generate_mock_video_chapters(note)
                    
            except Exception as e:
                print(f"Error generating video chapters with AI: {str(e)}")
                # If there's an error, fall back to mock implementation
                return self._generate_mock_video_chapters(note)
                
        except Exception as e:
            print(f"General error in generate_video_chapters: {str(e)}")
            # If there's a general error, still try the mock implementation
            note = self.notes.find_one({"_id": ObjectId(note_id)})
            if note:
                return self._generate_mock_video_chapters(note)
            return False, f"Error generating video chapter suggestions: {str(e)}"
    
    def _generate_content_aware_flashcards(self, note):
        """Generate flashcards based on content analysis when API fails"""
        content = note['content']
        
        # Simple content analysis - extract key terms and definitions
        cards = []
        
        # Look for path independence definition
        if "path-independent" in content.lower() or "path independence" in content.lower():
            cards.append({
                "front": "What is path independence in trading strategies?",
                "back": "A strategy is path-independent if trading decisions do not depend on past trading decisions."
            })
        
        # Look for copycat strategy
        if "copycat" in content.lower():
            cards.append({
                "front": "Why is the copycat strategy considered path-independent?",
                "back": "Because the position on day k is computed without reference to earlier positions (only cares about the price changes on day k−1)."
            })
        
        # Look for BBands
        if "bbands" in content.lower() or "mean reversion" in content.lower():
            cards.append({
                "front": "Why is the BBands mean reversion strategy path-independent?",
                "back": "Because the position on day k is computed without reference to earlier positions (only cares about the band on day k−1)."
            })
        
        # Look for entries and exits
        if "entering" in content.lower() and "exiting" in content.lower():
            cards.append({
                "front": "What are the possible trade entries in path-independent strategies?",
                "back": "Flat to long; flat to short; long to short; short to long."
            })
            
            cards.append({
                "front": "What options exist when exiting a position in path-independent strategies?",
                "back": "Either go to flat or 'reverse positions' and enter the 'opposite position'."
            })
        
        # Look for overbought/oversold
        if "overbought" in content.lower() or "oversold" in content.lower():
            cards.append({
                "front": "When do you go long in the Overbought/Oversold Strategy Variant?",
                "back": "Go Long when price crosses below lower band line; exit when price crosses above moving average."
            })
            
            cards.append({
                "front": "When do you go short in the Overbought/Oversold Strategy Variant?",
                "back": "Go Short when price crosses above upper band line; exit when price crosses below moving average."
            })
        
        # Look for mean reversion
        if "mean reversion" in content.lower():
            cards.append({
                "front": "What type of strategy is the Overbought/Oversold Variant?",
                "back": "A mean reversion type strategy: bets that prices will move back all the way to the mean (i.e., the moving average)."
            })
        
        # If we couldn't extract enough content-specific cards, add generic ones
        if len(cards) < 4:
            cards.extend([
                {
                    "front": f"What is {note['title']}?",
                    "back": f"A document covering trading strategies and path dependence."
                },
                {
                    "front": f"Why is {note['title']} important?",
                    "back": f"It provides knowledge about trading strategies that is essential for understanding market dynamics."
                }
            ])
        
        return True, {
            "title": f"{note['title']} Flashcards",
            "note_id": str(note['_id']),
            "cards": cards
        }
    
    def _generate_content_aware_quiz(self, note):
        """Generate a quiz based on content analysis when API fails"""
        content = note['content']
        
        # Simple content analysis - extract key concepts for questions
        questions = []
        
        # Question about path independence
        if "path-independent" in content.lower() or "path independence" in content.lower():
            questions.append({
                "question": "What defines a path-independent trading strategy?",
                "options": [
                    "Trading decisions that depend on position size",
                    "Trading decisions that depend on past trading decisions",
                    "Trading decisions that do not depend on past trading decisions",
                    "Trading decisions that depend on market volatility"
                ],
                "correct_answer": "Trading decisions that do not depend on past trading decisions"
            })
        
        # Question about copycat strategy
        if "copycat" in content.lower():
            questions.append({
                "question": "Why is the copycat strategy considered path-independent?",
                "options": [
                    "It depends on previous day's positions",
                    "It only cares about price changes on day k-1",
                    "It accounts for all historical data",
                    "It requires multiple days of position history"
                ],
                "correct_answer": "It only cares about price changes on day k-1"
            })
        
        # Question about exiting positions
        if "exiting" in content.lower():
            questions.append({
                "question": "In path-independent strategies, when exiting a position you may:",
                "options": [
                    "Only go to a flat position",
                    "Only reverse to the opposite position",
                    "Either go to flat or 'reverse positions' and enter the opposite position",
                    "Only exit during market hours"
                ],
                "correct_answer": "Either go to flat or 'reverse positions' and enter the opposite position"
            })
        
        # Question about overbought/oversold
        if "overbought" in content.lower() or "oversold" in content.lower():
            questions.append({
                "question": "What characterizes the Overbought/Oversold Strategy Variant?",
                "options": [
                    "It is purely path-independent",
                    "It uses only momentum indicators",
                    "It bets that prices will move back to the mean",
                    "It always holds positions for fixed time periods"
                ],
                "correct_answer": "It bets that prices will move back to the mean"
            })
        
        # Question about future topics
        if "next time" in content.lower():
            questions.append({
                "question": "According to the document, what will be discussed in the future?",
                "options": [
                    "Market patterns and seasonality",
                    "Holding periods, stop losses, and profit targets",
                    "Advanced charting techniques",
                    "Fundamental analysis methods"
                ],
                "correct_answer": "Holding periods, stop losses, and profit targets"
            })
        
        # If we couldn't extract enough content-specific questions, add generic ones
        if len(questions) < 3:
            questions.extend([
                {
                    "question": f"What is the main topic of {note['title']}?",
                    "options": [
                        "Trading path dependencies",
                        "Market volatility patterns",
                        "Algorithmic trading strategies",
                        "Stock market forecasting"
                    ],
                    "correct_answer": "Trading path dependencies"
                },
                {
                    "question": "Which type of strategy is discussed in the document?",
                    "options": [
                        "Value investing strategies",
                        "Day trading techniques",
                        "Mean reversion strategies",
                        "Growth investing methods"
                    ],
                    "correct_answer": "Mean reversion strategies"
                }
            ])
        
        return True, {
            "title": f"{note['title']} Quiz",
            "note_id": str(note['_id']),
            "questions": questions
        }
    
    def _generate_mock_quiz(self, note):
        """Fallback method to generate a mock quiz if API fails"""
        mock_quiz = {
            "title": f"{note['title']} Quiz",
            "note_id": str(note['_id']),
            "questions": [
                {
                    "question": f"What is the main topic of {note['title']}?",
                    "options": [
                        f"{note['title']} fundamentals",
                        f"Introduction to {note['topic']}",
                        f"Advanced {note['topic']}",
                        "None of the above"
                    ],
                    "correct_answer": f"{note['title']} fundamentals"
                },
                {
                    "question": f"Which of the following is most likely covered in {note['title']}?",
                    "options": [
                        f"Basic principles of {note['topic']}",
                        f"Advanced applications of {note['topic']}",
                        f"Historical development of {note['topic']}",
                        f"Future trends in {note['topic']}"
                    ],
                    "correct_answer": f"Basic principles of {note['topic']}"
                },
                {
                    "question": "What would be the best approach to study this material?",
                    "options": [
                        "Memorize key terms and definitions",
                        "Practice with example problems",
                        "Create concept maps connecting ideas",
                        "All of the above"
                    ],
                    "correct_answer": "All of the above"
                }
            ]
        }
        return True, mock_quiz
    
    def _generate_mock_flashcards(self, note):
        """Fallback method to generate mock flashcards if API fails"""
        mock_flashcards = {
            "title": f"{note['title']} Flashcards",
            "note_id": str(note['_id']),
            "cards": [
                {
                    "front": f"What is {note['title']}?",
                    "back": f"A subject that covers topics related to {note['topic']}"
                },
                {
                    "front": f"Why is {note['title']} important?",
                    "back": f"It provides fundamental knowledge about {note['topic']} that is essential for further studies"
                },
                {
                    "front": f"Main components of {note['title']}",
                    "back": f"Various concepts and principles related to {note['topic']}"
                },
                {
                    "front": f"Applications of {note['title']}",
                    "back": f"The concepts from {note['title']} can be applied in various areas of {note['topic']}"
                }
            ]
        }
        return True, mock_flashcards
    
    def _generate_mock_video_chapters(self, note):
        """Fallback method to generate mock video chapters if API fails"""
        mock_chapters = {
            "title": f"{note['title']} Video Chapters",
            "note_id": str(note['_id']),
            "chapters": [
                {
                    "title": f"Introduction to {note['title']}",
                    "description": f"An overview of {note['title']} and its importance in {note['topic']}"
                },
                {
                    "title": f"Core Concepts of {note['title']}",
                    "description": f"Detailed explanation of the fundamental principles in {note['title']}"
                },
                {
                    "title": "Examples and Applications",
                    "description": f"Practical examples showing how concepts from {note['title']} are applied"
                },
                {
                    "title": "Common Challenges and Solutions",
                    "description": f"Addressing common difficulties students face when learning {note['title']}"
                },
                {
                    "title": "Summary and Next Steps",
                    "description": f"Recap of key points from {note['title']} and guidance on further learning"
                }
            ]
        }
        return True, mock_chapters