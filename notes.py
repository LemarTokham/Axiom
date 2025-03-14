import pymongo
from pdf_conv import PdfParser
from dotenv import load_dotenv
import os
from google import genai
from bson.objectid import ObjectId
from json import loads

load_dotenv()
api_key = os.getenv("API_KEY")
client = genai.Client(api_key=api_key)


my_client = pymongo.MongoClient("mongodb+srv://lcfaria:200805Lf.@cluster0.5imi7.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
my_db = my_client["axiom_db"]
my_col = my_db["notes"]

def add_note(source, topic, title):
    parser = PdfParser()
    res = parser.parse_pdf(source)
    mydict = { "title": title, "topic": topic, "content": res }
    x = my_col.insert_one(mydict)
    print(x.inserted_id)
    return x.inserted_id



def generate_quizzes(note_id):
    note = my_col.find_one({"_id": ObjectId(note_id)})
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config= {'response_mime_type':'application/json'},
        contents=f"Generate a multiple-choice quiz to test the student's knowledge on the following notes: {note['content']}. The quiz should be in JSON format with the following structure:\n{{\n  \"title\": \"{note['title']}\",\n  \"questions\": [\n    {{\"question_number\": 1, \"question\": \"What is the main topic discussed in the notes?\", \"options\": [\"Option A\", \"Option B\", \"Option C\", \"Option D\"], \"correct_option\": 1}},\n    {{\"question_number\": 2, \"question\": \"What is the key concept explained in the notes?\", \"options\": [\"Option A\", \"Option B\", \"Option C\", \"Option D\"], \"correct_option\": 2}},\n    {{\"question_number\": 3, \"question\": \"Provide an example mentioned in the notes.\", \"options\": [\"Option A\", \"Option B\", \"Option C\", \"Option D\"], \"correct_option\": 3}}\n  ]\n}}"
    )
    quiz = response.text
    quiz = loads(quiz)
    quiz.update({'note_id': note['_id']})
    return quiz

def upload_quiz(note_id):
    quiz = generate_quizzes(note_id)
    my_col = my_db["quizzes"]
    x = my_col.insert_one(quiz)
    print(x.inserted_id)



id = add_note("60781a24-0439-4f80-85db-4aa52bea9ff8_COMP_202_-_Adv_Algorithms.pdf", "Data Structures and Algorithms", "Data Structures and Algorithms")
upload_quiz(id)
